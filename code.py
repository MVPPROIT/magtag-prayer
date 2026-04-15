import time
import alarm
import board
import microcontroller
import json
from adafruit_magtag.magtag import MagTag

magtag = MagTag()
# ============================================================
# BEEP
# ============================================================
def beep(btype="startup"):
    if btype == "startup":
        magtag.peripherals.play_tone(440, 0.1)
    elif btype == "adhan":
        for _ in range(3):
            magtag.peripherals.play_tone(660, 0.15)
            time.sleep(0.1)
    else:
        magtag.peripherals.play_tone(880, 0.2)

beep("startup")

# ============================================================
# OTA UPDATE
# ============================================================
OTA_VERSION_URL = "https://raw.githubusercontent.com/MVPPROIT/magtag-prayer/main/version.txt"
OTA_CODE_URL    = "https://raw.githubusercontent.com/MVPPROIT/magtag-prayer/main/code.py"

def get_local_version():
    try:
        with open("/version.txt", "r") as f:
            return int(f.read().strip())
    except:
        return 0

def set_local_version(v):
    try:
        with open("/version.txt", "w") as f:
            f.write(str(v))
    except:
        pass

def check_ota():
    # Step 1: Fetch remote version
    try:
        resp = magtag.network.fetch(OTA_VERSION_URL)
        remote_raw = resp.text.strip()
        resp.close()
    except Exception as e:
        return  # No connection or URL failed — silently skip

    try:
        remote_ver = int(remote_raw)
    except Exception:
        return  # version.txt not a valid number

    local_ver = get_local_version()
    if remote_ver <= local_ver:
        return  # Already up to date

    # Step 2: Show update screen — add text boxes only now that we know update is needed
    magtag.add_text(text_position=(148, 45), text_scale=2, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 85), text_scale=2, text_anchor_point=(0.5, 0.5))
    magtag.set_text("Updating...", 0, auto_refresh=False)
    magtag.set_text("v" + str(local_ver) + " -> v" + str(remote_ver), 1, auto_refresh=True)
    beep("update")

    # Step 3: Download new code
    try:
        resp = magtag.network.fetch(OTA_CODE_URL)
        new_code = resp.text
        resp.close()
    except Exception:
        magtag.set_text("DL Failed", 0, auto_refresh=False)
        magtag.set_text("Try later", 1, auto_refresh=True)
        time.sleep(3)
        return

    # Step 4: Write new code to a temp file first, then rename
    try:
        with open("/code_new.py", "w") as f:
            f.write(new_code)
    except Exception:
        magtag.set_text("Write",   0, auto_refresh=False)
        magtag.set_text("Failed!", 1, auto_refresh=True)
        time.sleep(3)
        return

    # Step 5: Replace code.py with new file
    try:
        import os
        os.rename("/code_new.py", "/code.py")
    except Exception:
        # rename not available in older CircuitPython — write directly
        try:
            with open("/code.py", "w") as f:
                f.write(new_code)
        except Exception:
            magtag.set_text("Replace",  0, auto_refresh=False)
            magtag.set_text("Failed!",  1, auto_refresh=True)
            time.sleep(3)
            return

    # Step 6: Save new version and reboot
    set_local_version(remote_ver)
    magtag.set_text("Update Done!", 0, auto_refresh=False)
    magtag.set_text("Restarting...", 1, auto_refresh=True)
    time.sleep(2)
    microcontroller.reset()

# ============================================================
# CONFIG & PERSISTENCE
# ============================================================
try:
    with open("/masjid_id.txt", "r") as f:
        MASJID_ID = f.read().strip()
except Exception:
    MASJID_ID = "2093"

def get_view_mode():
    try:
        with open("/view_mode.txt", "r") as f:
            return f.read().strip()
    except:
        return "simple"

def set_view_mode(mode):
    try:
        with open("/view_mode.txt", "w") as f:
            f.write(mode)
    except:
        pass

def get_leds_enabled():
    try:
        with open("/makruh_led.txt", "r") as f:
            return f.read().strip() == "on"
    except:
        return True

def set_leds_enabled(state):
    try:
        with open("/makruh_led.txt", "w") as f:
            f.write("on" if state else "off")
    except:
        pass

def get_prev_event_type():
    try:
        with open("/prev_event.txt", "r") as f:
            return f.read().strip()
    except:
        return ""

def set_prev_event_type(etype):
    try:
        with open("/prev_event.txt", "w") as f:
            f.write(etype if etype else "")
    except:
        pass

def get_prev_prayer_name():
    try:
        with open("/prev_prayer.txt", "r") as f:
            return f.read().strip()
    except:
        return ""

def set_prev_prayer_name(name):
    try:
        with open("/prev_prayer.txt", "w") as f:
            f.write(name if name else "")
    except:
        pass

def get_jamaat_until():
    try:
        with open("/jamaat_until.txt", "r") as f:
            return int(f.read().strip())
    except:
        return 0

def set_jamaat_until(secs_of_day):
    try:
        with open("/jamaat_until.txt", "w") as f:
            f.write(str(secs_of_day))
    except:
        pass

def clear_jamaat_until():
    try:
        with open("/jamaat_until.txt", "w") as f:
            f.write("0")
    except:
        pass

def get_jamaat_name():
    try:
        with open("/jamaat_name.txt", "r") as f:
            return f.read().strip()
    except:
        return ""

def set_jamaat_name(name):
    try:
        with open("/jamaat_name.txt", "w") as f:
            f.write(name if name else "")
    except:
        pass

def save_cache(data):
    try:
        with open("/cache.json", "w") as f:
            f.write(json.dumps(data))
    except:
        pass

def load_cache():
    try:
        with open("/cache.json", "r") as f:
            return json.loads(f.read())
    except:
        return None

# ============================================================
# UTILITIES
# ============================================================
def zpad(n):
    s = str(n)
    if len(s) < 2:
        return "0" + s
    return s

def time_to_secs(t_str):
    if not t_str or ":" not in t_str or t_str == "-":
        return 999999
    parts = t_str.split(':')
    return (int(parts[0]) * 3600) + (int(parts[1]) * 60)

def to_12h(t_str):
    if not t_str or ":" not in t_str or t_str == "-":
        return t_str
    parts = t_str.split(':')
    if not parts[0].lstrip('-').isdigit():
        return t_str
    h, m = int(parts[0]), int(parts[1])
    period = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return str(h12) + ":" + zpad(m) + " " + period

def to_12h_noperiod(t_str):
    if not t_str or ":" not in t_str or t_str == "-":
        return t_str
    parts = t_str.split(':')
    if not parts[0].lstrip('-').isdigit():
        return t_str
    h, m = int(parts[0]), int(parts[1])
    h12 = h % 12 or 12
    return str(h12) + ":" + zpad(m)

def fmt_pair(t1, t2):
    if not t1 or t1 == "-":
        return to_12h(t2) if t2 and t2 != "-" else "--:--"
    if not t2 or t2 == "-" or t2 == t1:
        return to_12h(t1)
    h1 = int(t1.split(':')[0])
    h2 = int(t2.split(':')[0])
    same_period = (h1 < 12) == (h2 < 12)
    if same_period:
        return to_12h_noperiod(t1) + " / " + to_12h(t2)
    else:
        return to_12h(t1) + " / " + to_12h(t2)

def make_progress(begin_s, jamaat_s, now_s, width=8):
    if jamaat_s <= begin_s or now_s <= begin_s:
        return "." * width
    if now_s >= jamaat_s:
        return "." * (width - 1) + "o"
    pos = int((now_s - begin_s) / (jamaat_s - begin_s) * width)
    pos = max(0, min(width - 1, pos))
    return "." * pos + "o" + "." * (width - 1 - pos)

def days_until_jumuah(now):
    wd = now.tm_wday
    if wd == 4:
        return 0
    return (4 - wd) % 7

def is_makruh_time(today, now_s):
    sr_s = time_to_secs(today.get('sr', '-'))
    db_s = time_to_secs(today.get('db', '-'))
    mj_s = time_to_secs(today.get('mj', '-'))
    if sr_s != 999999 and sr_s <= now_s <= sr_s + 1200:
        return True
    if db_s != 999999 and db_s - 900 <= now_s <= db_s:
        return True
    if mj_s != 999999 and mj_s - 1200 <= now_s <= mj_s:
        return True
    return False

def flash_adhan_leds():
    if not get_leds_enabled():
        return
    for _ in range(3):
        magtag.peripherals.neopixels.fill((255, 255, 255))
        time.sleep(0.2)
        magtag.peripherals.neopixels.fill((0, 0, 0))
        time.sleep(0.2)

def get_led_color(today, now_s, event_type=None):
    if not get_leds_enabled():
        return (0, 0, 0)
    if is_makruh_time(today, now_s):
        return (255, 0, 0)
    if event_type == "JAMAAT":
        return (0, 255, 0)
    return (0, 0, 0)

def update_leds(today, now_s, event_type=None):
    color = get_led_color(today, now_s, event_type)
    magtag.peripherals.neopixels.fill(color)
    return color



def sort_key(item):
    return item[1]

def build_events(today, now):
    evs = []
    evs.append(("Fajr",    time_to_secs(today['fb']), "NEXT",   today['fb'], today['fj']))
    evs.append(("Fajr",    time_to_secs(today['fj']), "JAMAAT", today['fb'], today['fj']))
    evs.append(("Sunrise", time_to_secs(today['sr']), "NEXT",   today['sr'], None))
    if now.tm_wday == 4:
        for i in range(1, 5):
            j_key = "j" + str(i)
            if j_key in today:
                val = today[j_key]
                if val != "-" and val != "":
                    name = "Jumuah" if i == 1 else "Jumuah " + str(i)
                    evs.append((name, time_to_secs(val), "JAMAAT", val, None))
    else:
        evs.append(("Dhuhr", time_to_secs(today['db']), "NEXT",   today['db'], today['dj']))
        evs.append(("Dhuhr", time_to_secs(today['dj']), "JAMAAT", today['db'], today['dj']))
    evs.append(("Asr",  time_to_secs(today['ab']), "NEXT",   today['ab'], today['aj']))
    evs.append(("Asr",  time_to_secs(today['aj']), "JAMAAT", today['ab'], today['aj']))
    evs.append(("Isha", time_to_secs(today['ib']), "NEXT",   today['ib'], today['ij']))
    evs.append(("Isha", time_to_secs(today['ij']), "JAMAAT", today['ib'], today['ij']))
    m_beg = today['mb']
    m_jam = today['mj']
    m_first = m_beg if (m_beg != "-" and m_beg != "") else m_jam
    evs.append(("Maghrib", time_to_secs(m_first), "NEXT",   m_first, m_jam))
    if time_to_secs(m_jam) > time_to_secs(m_first):
        evs.append(("Maghrib", time_to_secs(m_jam), "JAMAAT", m_first, m_jam))
    evs.sort(key=sort_key)
    return evs

def fetch_today(json_data, now):
    today = None
    for day_data in json_data["d"]:
        if day_data["dt"] == now.tm_mday:
            today = day_data
            break
    if today is None:
        today = json_data["d"][0]
    return today

def connect_with_retry(max_attempts=3):
    for attempt in range(max_attempts):
        try:
            magtag.network.connect()
            return True
        except Exception:
            if attempt < max_attempts - 1:
                time.sleep(2)
    return False

def fetch_prayer_data(now):
    connected = connect_with_retry()
    if connected:
        try:
            magtag.network.get_local_time()
            check_ota()
            url = (
                "https://cdn.masjid247.com/jsonfiles/iot/"
                + MASJID_ID + "/"
                + str(now.tm_year) + "/"
                + str(now.tm_mon) + ".json"
            )
            data = magtag.network.fetch(url).json()
            save_cache(data)
            return data, True
        except Exception:
            pass
    return load_cache(), False

# ============================================================
# SLEEP HELPERS
# ============================================================
def sleep_buttons_only():
    magtag.peripherals.deinit()
    a_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_A, value=False, pull=True)
    b_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_B, value=False, pull=True)
    c_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_C, value=False, pull=True)
    d_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_D, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(a_alarm, b_alarm, c_alarm, d_alarm)

def sleep_detail():
    now = time.localtime()
    secs = 60 - now.tm_sec
    magtag.peripherals.deinit()
    t_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + secs)
    a_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_A, value=False, pull=True)
    b_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_B, value=False, pull=True)
    c_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_C, value=False, pull=True)
    d_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_D, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(t_alarm, a_alarm, b_alarm, c_alarm, d_alarm)

def sleep_normal(duration):
    magtag.peripherals.deinit()
    t_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + duration + 5)
    a_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_A, value=False, pull=True)
    b_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_B, value=False, pull=True)
    c_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_C, value=False, pull=True)
    d_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_D, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(t_alarm, a_alarm, b_alarm, c_alarm, d_alarm)

def jamaat_wait(duration):
    """If LEDs are ON, stay awake so LEDs remain lit. If OFF, deep sleep."""
    if not get_leds_enabled():
        sleep_normal(duration)
        return
    end_time = time.monotonic() + duration
    while time.monotonic() < end_time:
        time.sleep(1)
    microcontroller.reset()

def get_makruh_end(today, now_s):
    """Return seconds-of-day when current Makruh period ends, or 0 if not in one."""
    sr_s = time_to_secs(today.get('sr', '-'))
    db_s = time_to_secs(today.get('db', '-'))
    mj_s = time_to_secs(today.get('mj', '-'))
    if sr_s != 999999 and sr_s <= now_s <= sr_s + 1200:
        return sr_s + 1200           # Sunrise + 20 min
    if db_s != 999999 and db_s - 900 <= now_s <= db_s:
        return db_s                  # Dhuhr begin
    if mj_s != 999999 and mj_s - 1200 <= now_s <= mj_s:
        return mj_s                  # Maghrib jamaat
    return 0

def sleep_after_render(sleep_duration, today, now_s, event_type):
    """Sleep until next event, but stay awake during any active LED period."""
    if not get_leds_enabled():
        sleep_normal(sleep_duration)
        return

    # Check if currently in Makruh time
    makruh_end = get_makruh_end(today, now_s)
    if makruh_end > 0:
        # Stay awake until Makruh period ends
        makruh_remaining = makruh_end - now_s
        end_time = time.monotonic() + makruh_remaining
        while time.monotonic() < end_time:
            time.sleep(1)
        # Makruh over — turn off LEDs and sleep for remainder
        magtag.peripherals.neopixels.fill((0, 0, 0))
        remaining_sleep = sleep_duration - makruh_remaining
        if remaining_sleep > 5:
            sleep_normal(remaining_sleep)
        else:
            microcontroller.reset()
        return

    # Not in Makruh — normal sleep
    sleep_normal(sleep_duration)

# ============================================================
# RENDER FUNCTIONS
# ============================================================
JAMAAT_DURATIONS = {"Fajr": 540, "Dhuhr": 360, "Asr": 360, "Maghrib": 360, "Isha": 360}

def get_current_event(evs, now_s):
    for e in evs:
        if e[1] > now_s:
            return e
    return None

def build_display(name, etype, t1, t2, now_s, etime):
    title = "Next " + name if etype == "NEXT" else name
    d_time = fmt_pair(t1, t2)
    sleep_duration = etime - now_s
    set_prev_event_type(etype)
    set_prev_prayer_name(name)
    return title, d_time, sleep_duration

# ------ VIEW 1: Simple ------
def render_simple_view(today, now, now_s, evs):
    magtag.add_text(text_position=(148, 40), text_scale=4, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 95), text_scale=3, text_anchor_point=(0.5, 0.5))

    current = get_current_event(evs, now_s)

    if current is None:
        fajr_times = fmt_pair(today['fb'], today['fj'])
        magtag.set_text("Next Fajr", 0, auto_refresh=False)
        magtag.set_text(fajr_times,  1, auto_refresh=True)
        set_prev_event_type("NEXT")
        set_prev_prayer_name("Fajr")
        return (86400 - now_s) + time_to_secs(today['fb']), "NEXT"

    name  = current[0]
    etime = current[1]
    etype = current[2]
    t1    = current[3]
    t2    = current[4]

    title, d_time, sleep_duration = build_display(name, etype, t1, t2, now_s, etime)
    magtag.set_text(title,  0, auto_refresh=False)
    magtag.set_text(d_time, 1, auto_refresh=True)
    return sleep_duration, etype

# ------ VIEW 2: Enhanced ------
def render_enhanced_view(today, now, now_s, evs):
    magtag.add_text(text_position=(148, 10),  text_scale=1, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 50),  text_scale=4, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 90),  text_scale=3, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 118), text_scale=1, text_anchor_point=(0.5, 0.5))

    hijri = today['h']
    days_jum = days_until_jumuah(now)
    if days_jum == 0:
        jum_str = "Today is Jumuah"
    elif days_jum == 1:
        jum_str = "Jumuah Tomorrow"
    else:
        jum_str = "Jumuah in " + str(days_jum) + " days"

    current = get_current_event(evs, now_s)

    if current is None:
        fajr_times = fmt_pair(today['fb'], today['fj'])
        magtag.set_text(hijri,       0, auto_refresh=False)
        magtag.set_text("Next Fajr", 1, auto_refresh=False)
        magtag.set_text(fajr_times,  2, auto_refresh=False)
        magtag.set_text(jum_str,     3, auto_refresh=True)
        set_prev_event_type("NEXT")
        set_prev_prayer_name("Fajr")
        return (86400 - now_s) + time_to_secs(today['fb']), "NEXT"

    name  = current[0]
    etime = current[1]
    etype = current[2]
    t1    = current[3]
    t2    = current[4]

    title, d_time, sleep_duration = build_display(name, etype, t1, t2, now_s, etime)
    magtag.set_text(hijri,   0, auto_refresh=False)
    magtag.set_text(title,   1, auto_refresh=False)
    magtag.set_text(d_time,  2, auto_refresh=False)
    magtag.set_text(jum_str, 3, auto_refresh=True)
    return sleep_duration, etype

# ------ VIEW 3: Detail ------
def render_detail_view():
    magtag.add_text(text_position=(148, 12),  text_scale=2, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 32),  text_scale=2, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 72),  text_scale=4, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 112), text_scale=2, text_anchor_point=(0.5, 0.5))

    # Sync time before reading it
    json_data, _ = fetch_prayer_data(time.localtime())
    now = time.localtime()
    now_s = (now.tm_hour * 3600) + (now.tm_min * 60)

    if json_data is None:
        magtag.set_text("Offline",    0, auto_refresh=False)
        magtag.set_text("No Data",    1, auto_refresh=False)
        magtag.set_text("",           2, auto_refresh=False)
        magtag.set_text("Check WiFi", 3, auto_refresh=True)
        beep("update")
        return

    m_name = json_data.get("n", "Masjid")
    if len(m_name) > 22:
        m_name = m_name[:22]
    t_str = to_12h(zpad(now.tm_hour) + ":" + zpad(now.tm_min))

    today = fetch_today(json_data, now)
    evs = build_events(today, now)
    current = get_current_event(evs, now_s)

    if current is None:
        prayer_name = "Fajr"
        begin_str   = today['fb'] if today['fb'] and today['fb'] != "-" else "--:--"
        jamaat_str  = today['fj'] if today['fj'] and today['fj'] != "-" else "--:--"
        progress    = "o" + "." * 7
        event_type  = None
    else:
        prayer_name = current[0]
        etype       = current[2]
        t1          = current[3]
        t2          = current[4]
        begin_str   = t1 if t1 and t1 != "-" else "--:--"
        jamaat_str  = t2 if t2 and t2 != "-" else "--:--"
        progress    = make_progress(time_to_secs(begin_str), time_to_secs(jamaat_str), now_s)
        event_type  = etype

    h1 = int(begin_str.split(':')[0]) if ":" in begin_str else 0
    h2 = int(jamaat_str.split(':')[0]) if ":" in jamaat_str else 0
    same_period = (h1 < 12) == (h2 < 12)
    begin_disp  = to_12h_noperiod(begin_str) if same_period else to_12h(begin_str)
    jamaat_disp = to_12h(jamaat_str)
    progress_line = begin_disp + " " + progress + " " + jamaat_disp

    magtag.set_text(m_name,        0, auto_refresh=False)
    magtag.set_text(t_str,         1, auto_refresh=False)
    magtag.set_text(prayer_name,   2, auto_refresh=False)
    magtag.set_text(progress_line, 3, auto_refresh=True)

    update_leds(today, now_s, event_type)
    beep("update")

# ------ All Prayers View ------
def render_all_prayers_view(json_data, now):
    magtag.add_text(text_position=(148, 10),  text_scale=1, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 30),  text_scale=1, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 50),  text_scale=1, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 70),  text_scale=1, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 90),  text_scale=1, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 110), text_scale=1, text_anchor_point=(0.5, 0.5))

    today = fetch_today(json_data, now)
    d_str = zpad(now.tm_mday) + "/" + zpad(now.tm_mon) + "/" + str(now.tm_year)

    if now.tm_wday == 4:
        j1 = today.get('j1', '-')
        mid_str = "Jumuah   " + (to_12h(j1) if j1 and j1 != '-' and j1 != '' else '--:--')
    else:
        mid_str = "Dhuhr    " + fmt_pair(today['db'], today['dj'])

    magtag.set_text(d_str,                                              0, auto_refresh=False)
    magtag.set_text("Fajr     " + fmt_pair(today['fb'], today['fj']),  1, auto_refresh=False)
    magtag.set_text(mid_str,                                            2, auto_refresh=False)
    magtag.set_text("Asr      " + fmt_pair(today['ab'], today['aj']),  3, auto_refresh=False)
    magtag.set_text("Maghrib  " + fmt_pair(today['mb'], today['mj']),  4, auto_refresh=False)
    magtag.set_text("Isha     " + fmt_pair(today['ib'], today['ij']),  5, auto_refresh=True)

    beep("update")

# ------ Jamaat screen ------
def render_jamaat_display(prayer_name, today, now_s):
    magtag.add_text(text_position=(148, 40), text_scale=4, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 95), text_scale=3, text_anchor_point=(0.5, 0.5))
    magtag.set_text(prayer_name + " Jamaat", 0, auto_refresh=False)

    # Show the jamaat time on the second line
    jamaat_time = ""
    if today:
        prayer_key_map = {
            "Fajr":    "fj",
            "Dhuhr":   "dj",
            "Asr":     "aj",
            "Maghrib": "mj",
            "Isha":    "ij",
        }
        key = prayer_key_map.get(prayer_name, None)
        if key and key in today and today[key] and today[key] != "-":
            jamaat_time = to_12h(today[key])
        elif prayer_name.startswith("Jumuah"):
            j1 = today.get("j1", "")
            if j1 and j1 != "-":
                jamaat_time = to_12h(j1)

    magtag.set_text(jamaat_time, 1, auto_refresh=True)

    update_leds(today, now_s, "JAMAAT")
    beep("update")

# ============================================================
# SETTINGS
# ============================================================
def run_settings():
    padded_id = ("0000" + MASJID_ID)[-4:]
    cid = list(padded_id)
    cur = 0
    while True:
        id_parts = []
        for i in range(len(cid)):
            if i == cur:
                id_parts.append("[" + cid[i] + "]")
            else:
                id_parts.append(" " + cid[i] + " ")
        id_display = "".join(id_parts)
        magtag.set_text("A:+ B:- C:Next D:SAVE", 0, auto_refresh=False)
        magtag.set_text(id_display,               1, auto_refresh=False)
        magtag.set_text("",                        2, auto_refresh=True)
        time.sleep(0.5)
        waiting = True
        while waiting:
            if magtag.peripherals.button_a_pressed:
                cid[cur] = str((int(cid[cur]) + 1) % 10)
                waiting = False
            elif magtag.peripherals.button_b_pressed:
                cid[cur] = str((int(cid[cur]) - 1) % 10)
                waiting = False
            elif magtag.peripherals.button_c_pressed:
                cur = (cur + 1) % 4
                waiting = False
            elif magtag.peripherals.button_d_pressed:
                try:
                    with open("/masjid_id.txt", "w") as f:
                        f.write("".join(cid))
                except:
                    pass
                microcontroller.reset()
            else:
                time.sleep(0.1)

# ============================================================
# SHARED RENDER + SLEEP
# ============================================================
def render_and_sleep_normal(view):
    # Step 1: Connect and sync time FIRST so now_s is accurate
    connected = connect_with_retry()
    if connected:
        try:
            magtag.network.get_local_time()
            check_ota()
        except Exception:
            pass

    # Step 2: Get time AFTER NTP sync
    now = time.localtime()
    now_s = (now.tm_hour * 3600) + (now.tm_min * 60)

    # Step 3: Check if still inside a Jamaat window (survives resets)
    jamaat_until = get_jamaat_until()
    jamaat_name  = get_jamaat_name()
    if jamaat_until > 0 and now_s < jamaat_until and jamaat_name:
        json_data = None
        if connected:
            try:
                url = (
                    "https://cdn.masjid247.com/jsonfiles/iot/"
                    + MASJID_ID + "/"
                    + str(now.tm_year) + "/"
                    + str(now.tm_mon) + ".json"
                )
                json_data = magtag.network.fetch(url).json()
                save_cache(json_data)
            except Exception:
                json_data = load_cache()
        if json_data is None:
            json_data = load_cache()
        today = fetch_today(json_data, now) if json_data else None
        render_jamaat_display(jamaat_name, today, now_s)
        remaining = jamaat_until - now_s
        if remaining > 5:
            jamaat_wait(remaining)
        else:
            clear_jamaat_until()
            set_jamaat_name("")
        return

    if jamaat_until > 0 and now_s >= jamaat_until:
        clear_jamaat_until()
        set_jamaat_name("")

    # Step 4: Fetch prayer data (connection already open)
    json_data = None
    if connected:
        try:
            url = (
                "https://cdn.masjid247.com/jsonfiles/iot/"
                + MASJID_ID + "/"
                + str(now.tm_year) + "/"
                + str(now.tm_mon) + ".json"
            )
            json_data = magtag.network.fetch(url).json()
            save_cache(json_data)
        except Exception:
            json_data = load_cache()
    if json_data is None:
        json_data = load_cache()

    if json_data is None:
        magtag.add_text(text_position=(148, 40), text_scale=4, text_anchor_point=(0.5, 0.5))
        magtag.add_text(text_position=(148, 95), text_scale=3, text_anchor_point=(0.5, 0.5))
        magtag.set_text("Offline",        0, auto_refresh=False)
        magtag.set_text("Retrying 5 min", 1, auto_refresh=True)
        set_prev_event_type("")
        set_prev_prayer_name("")
        sleep_normal(300)
        return

    today = fetch_today(json_data, now)
    evs = build_events(today, now)

    if view == "enhanced":
        sleep_duration, event_type = render_enhanced_view(today, now, now_s, evs)
    else:
        sleep_duration, event_type = render_simple_view(today, now, now_s, evs)

    update_leds(today, now_s, event_type)
    sleep_after_render(sleep_duration, today, now_s, event_type)

# ============================================================
# MAIN
# ============================================================
wake = alarm.wake_alarm

# ---- 3am daily reboot ----
if isinstance(wake, alarm.time.TimeAlarm):
    _t = time.localtime()
    if _t.tm_hour == 3 and _t.tm_min < 5:
        time.sleep(2)
        microcontroller.reset()

# ---- BUTTON B: LED toggle (all LEDs) ----
if isinstance(wake, alarm.pin.PinAlarm) and wake.pin == board.BUTTON_B:
    new_state = not get_leds_enabled()
    set_leds_enabled(new_state)
    magtag.add_text(text_position=(148, 55), text_scale=2, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 85), text_scale=3, text_anchor_point=(0.5, 0.5))
    magtag.set_text("LEDs", 0, auto_refresh=False)
    if new_state:
        magtag.set_text("ON",  1, auto_refresh=True)
    else:
        magtag.set_text("OFF", 1, auto_refresh=True)
    beep("update")
    time.sleep(3)
    microcontroller.reset()

# ---- BUTTON C: All prayers view toggle ----
elif isinstance(wake, alarm.pin.PinAlarm) and wake.pin == board.BUTTON_C:
    if get_view_mode() == "prayers":
        set_view_mode("simple")
        microcontroller.reset()
    else:
        set_view_mode("prayers")
        now = time.localtime()
        json_data, _ = fetch_prayer_data(now)
        if json_data:
            render_all_prayers_view(json_data, now)
        sleep_buttons_only()

# ---- BUTTON D: Info / Settings ----
elif isinstance(wake, alarm.pin.PinAlarm) and wake.pin == board.BUTTON_D:
    magtag.add_text(text_position=(148, 25),  text_scale=2, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 65),  text_scale=4, text_anchor_point=(0.5, 0.5))
    magtag.add_text(text_position=(148, 105), text_scale=2, text_anchor_point=(0.5, 0.5))

    now = time.localtime()
    json_data, _ = fetch_prayer_data(now)

    m_name = json_data.get("n", "Masjid") if json_data else "Offline"
    if len(m_name) > 15:
        m_name = m_name[:15]

    t_str = zpad(now.tm_hour) + ":" + zpad(now.tm_min)
    d_str = zpad(now.tm_mday) + "/" + zpad(now.tm_mon) + "/" + str(now.tm_year)

    magtag.set_text(m_name, 0, auto_refresh=False)
    magtag.set_text(t_str,  1, auto_refresh=False)
    magtag.set_text(d_str,  2, auto_refresh=True)

    start_wait = time.monotonic()
    entered_settings = False
    while time.monotonic() - start_wait < 5.0:
        if magtag.peripherals.button_d_pressed:
            entered_settings = True
            break
        time.sleep(0.1)

    if entered_settings:
        run_settings()
    else:
        microcontroller.reset()

# ---- BUTTON A: Cycle views ----
elif isinstance(wake, alarm.pin.PinAlarm) and wake.pin == board.BUTTON_A:
    current_view = get_view_mode()
    if current_view == "simple":
        set_view_mode("enhanced")
        new_view = "enhanced"
    elif current_view == "enhanced":
        set_view_mode("detail")
        new_view = "detail"
    elif current_view == "detail":
        set_view_mode("simple")
        new_view = "simple"
    else:
        set_view_mode("simple")
        new_view = "simple"

    if new_view == "detail":
        render_detail_view()
        sleep_detail()
    else:
        render_and_sleep_normal(new_view)

# ---- TIMER / POWER-ON ----
else:
    view = get_view_mode()
    prev_type = get_prev_event_type()
    prev_name = get_prev_prayer_name()

    if view == "detail":
        render_detail_view()
        sleep_detail()

    elif view == "prayers":
        now = time.localtime()
        json_data, _ = fetch_prayer_data(now)
        if json_data:
            render_all_prayers_view(json_data, now)
        sleep_buttons_only()

    elif prev_type == "JAMAAT" and prev_name:
        now = time.localtime()
        now_s = (now.tm_hour * 3600) + (now.tm_min * 60)
        json_data, _ = fetch_prayer_data(now)
        today = fetch_today(json_data, now) if json_data else None

        duration = 1800 if prev_name.startswith("Jumuah") else JAMAAT_DURATIONS.get(prev_name, 360)
        jamaat_end = now_s + duration
        set_jamaat_until(jamaat_end)
        set_jamaat_name(prev_name)

        render_jamaat_display(prev_name, today, now_s)

        set_prev_event_type("")
        set_prev_prayer_name("")

        sleep_normal(duration)

    else:
        if isinstance(wake, alarm.time.TimeAlarm) and prev_type == "NEXT":
            flash_adhan_leds()
            beep("adhan")

        render_and_sleep_normal(view)
