# 2022-07-30 14h34 PT. Modified the MAGTAG date_and_time script for:
# Updated the CircuitPython firmware to Version 8.0.0-alpha.1
# Updated all Adafruit CircuitPython libraries uses to the version 8.0 of date 2022-07-30.
# Using less global variables by introducing a classs my_data.
# Also trying to get rid of regular crashing of the app (maybe because of a memory leak)
# Adding algorithm to set, update and use the datetime of the built-in RTC. 
# The built_in RTC's datetime will be set with data 
# extracted from the Adafruit IO Time Service response.
# After initialization at start time, the built-in RTC will be synchronized every hour.
# The datetime from the built-in RTC will be displayed on the MAGTAG every minute.
#
# MagTag date and time circuitpython script
# modified by @Paulskpt
# Version of 2022-03-13
# MAGTAG flashed with TinyUF2 Bootloader version: 0.8.0
# MAGTAG flashed with CircuitPython version: 5.2.0
# Using library files from:
#    a) https://github.com/adafruit/Adafruit_CircuitPython_Bundle/adafruit-circuitpython-bundle-7.x-mpy-20220312.zip and from
#    b) https://github.com/adafruit/Adafruit_CircuitPython_Bundle/adafruit-circuitpython-bundle-py-20220312.zip
# IMPORTANT NOTE !!!
# Keep the library folder 'Adafruit_portalbase' (containing functions added by me) in the root folder '/',
# because Adafruit put an Adafruit_portalbase library containing a 'PortalBase' class into 'frozen'
# (this means they are integrated into the circuitpython UF2)
# and magtag.py has the following import: from Adafruit_portalbase import PortalBase'
#
import time
import secrets
from adafruit_magtag.magtag import MagTag
import gc, os
from adafruit_portalbase.wifi_esp32s2 import WiFi
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests
import rtc

tm_year = 0
tm_mon = 1
tm_mday=2
tm_hour= 3
tm_min = 4
tm_sec = 5
tm_wday = 6
tm_yday = 7
tm_isdst = 8

_debug = 0
_requests = 1
_response = 2
_time_url = 3
_same_time_cnt = 4
_last_hh = 5
_last_mm = 6
_wd = 7
_yd = 8
_sDt = 9
_start_clk = 10
_aio_username = 11
_aio_key = 12
_height = 13
_width = 14
_rtc_set = 15
_tz_offset = 16
_dst = 17
_tz = 18

class my_data:

    def __init__(self):
        self.data = {}

    def write(self, k, v):
        if k in self.data:
            self.data[k] = v # assign value to key
        else:
            #self.data.update({k, v}) # add key and value to dict
            self.data[k] = v

    def read(self, k):

        if k in self.data:
            return self.data[k]
        else:
            return None # was: self.data  but that's the whole dict ! We don't want!

    def clean(self):
        self.data = {}

# Classes
my_dat = my_data()

magtag = MagTag()

my_wifi = WiFi()  # create an instance of WiFi class
#print("dir(my_wifi) = ", dir(my_wifi))
# Get wifi details and more from a secrets.py file

rtc_bi = rtc.RTC() # Create an instance of the built_in RTC

my_dat.write(_debug, False)
my_dat.write(_requests, None)  # Placeholder
my_dat.write(_response, None)  # idem
my_dat.write(_time_url, None)  # idem
my_dat.write(_start_clk,time.monotonic())
my_dat.write(_same_time_cnt,0)
my_dat.write(_last_hh,0)
my_dat.write(_last_mm,0)
my_dat.write(_sDt,"")
my_dat.write(_wd,0) # day of the week
my_dat.write(_yd,0) # day of the year
my_dat.write(_aio_key, "")
my_dat.write(_aio_username, "")
my_dat.write(_height, 0)
my_dat.write(_width, 0)
my_dat.write(_rtc_set, False)
my_dat.write(_tz_offset, "")
my_dat.write(_dst, "")
my_dat.write(_tz, "")

weekdays = {0:"Monday", 1:"Tuesday",2:"Wednesday",3:"Thursday",4:"Friday",5:"Saturday",6:"Sunday"}

#--------------------------------------------
def mem_stat():
    s = "---------------------------"
    # Copied from UM's ProS3 code.py
    #--------------------------------------------
    # Show available memory
    print("\nMemory Info - gc.mem_free()")
    print(s)
    print("{} Bytes\n".format(gc.mem_free()))

    flash = os.statvfs('/')
    flash_size = flash[0] * flash[2]
    flash_free = flash[0] * flash[3]
    # Show flash size
    print("Flash - os.statvfs('/')")
    print(s)
    print("Size: {} Bytes\nFree: {} Bytes\n".format(flash_size, flash_free))
    print(s)

def setup():
    # global my_wifi

    mem_stat()

    TAG = "setup():     "
    TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
    JSON_QUOTES_URL = "https://www.adafruit.com/api/quotes.php"
    JSON_STARS_URL = "https://api.github.com/repos/adafruit/circuitpython"
    my_debug = my_dat.read(_debug)
    requests = my_dat.read(_requests)
    #TIME_URL = my_dat.read(_time_url)
    reponse = my_dat.read(_response)

    # Get wifi details and more from a secrets.py file
    try:
        from secrets import secrets
    except ImportError:
        print("WiFi secrets are kept in secrets.py, please add them there!")
        raise

    # Get our username, key and desired timezone
    aio_username = secrets["aio_username"]
    my_dat.write(_aio_username, aio_username)
    aio_key = secrets["aio_key"]
    my_dat.write(_aio_key, aio_key)
    location = secrets.get("timezone", None)
    TIME_URL = "https://io.adafruit.com/api/v2/%s/integrations/time/strftime?x-aio-key=%s" % (aio_username, aio_key)
    TIME_URL += "&fmt=%25Y-%25m-%25d+%25H%3A%25M%3A%25S.%25L+%25j+%25u+%25z+%25Z"
    my_dat.write(_time_url, TIME_URL)
    #my_dat.write(_same_time_cnt,0)

    print("ESP32-S2 Adafruit IO Time test")

    my_mac = my_wifi.get_mac_address()
    #my_mac = wifi.radio.mac_address
    ap_mac = my_wifi.get_mac_address_ap()
    #ap_mac = wifi.radio.mac_address_ap
    if not my_debug:
        print(TAG+"My MAC address: \'{:x}:{:x}:{:x}:{:x}:{:x}:{:x}\'".format(my_mac[0],my_mac[1],my_mac[2],my_mac[3],my_mac[4],my_mac[5]), end='\n')
        print(TAG+"AP MAC address: \'{:x}:{:x}:{:x}:{:x}:{:x}:{:x}\'".format(ap_mac[0],ap_mac[1],ap_mac[2],ap_mac[3],ap_mac[4],ap_mac[5]), end='\n')

    if my_debug:
        print("Available WiFi networks:")
        my_wifi.do_scan()
    print(TAG+"Connecting to %s"%secrets["ssid"])

    my_wifi.connect(secrets["ssid"], secrets["password"])
    time.sleep(2)
    if my_wifi.is_connected:
        print(TAG+"Connected to %s"%secrets["ssid"])
        print(TAG+"My IP address is \'{}\'".format(my_wifi.ip_address), end='\n')
        res = my_wifi.ping("8.8.8.8")
        time.sleep(1)
        ipv4 = ipaddress.ip_address("8.8.8.8")
        #res = wifi.radio.ping(ipv4)
        if isinstance(res, type(None)):
            print(TAG+"Ping to \'{}\' failed".format(ipv4))
            if my_wifi.is_connected:
                print("I am still connected to ", secrets["ssid"])
            else:
                my_wifi.connect(secrets["ssid"], secrets["password"])
                if my_wifi.is_connected:
                    print(TAG+"re-connected to ", ssid)
        else:
            if my_debug:
                print(TAG+"Ping to: \'{}\' = {} mSec.".format(ipv4, res))

        if my_debug:
            print(TAG+"Fetching text from", end='')
            print(TIME_URL)
        pool = socketpool.SocketPool(wifi.radio)
        requests = adafruit_requests.Session(pool, ssl.create_default_context())
        my_dat.write(_requests, requests)
        if my_debug:
            print(TAG+"type(requests) =",type(requests))
        if isinstance(requests, type(None)):
            print(TAG+"failed to create requests object. Exiting...")
            raise SystemExit
        response = my_wifi.get_url(TIME_URL)
        #response = requests.get(TIME_URL)
        my_dat.write(_response, response)
        if my_debug and not isinstance(response,  type(None)):
            print("-" * 40)
            print(response.text)
            print("-" * 40)

        height = magtag.graphics.display.height -1
        width  = magtag.graphics.display.width -1
        my_dat.write(_height, height)
        my_dat.write(_width, width)

        h0 = height // 6
        hlist = [h0, h0*3, h0*5]

        for _ in range (3):
            magtag.add_text(
                text_position=(
                    10,
                    hlist[_],
                ),
                text_scale=3,
            )
    else:
        print(TAG+"WiFi failed to connect to", secrets["ssid"])
        print("trying to connect to", secrets["ssid2"])
        my_wifi.connect(secrets["ssid2"], secrets["password"])
        time.sleep(3)
        if my_wifi.is_connected:
             print(TAG+"Connected to %s" % secrets["ssid2"])
        else:
            print(TAG+"WiFi failed to connect to", secrets["ssid2"])
            print("Exiting...")
            raise SystemExit

def get_pr_dt(upd_fm_AIO):
    TAG = "get_pr_dt(): "
    my_debug = my_dat.read(_debug)
    mm_corr = 1 # Minutes correction because practice revealed the minutes are always 1 behind other (PC)Clocks
    response = None

    if not my_debug:
        print(TAG+"param upd_fm_AIO=", upd_fm_AIO)

    if upd_fm_AIO:
        requests = my_dat.read(_requests)
        TIME_URL = my_dat.read(_time_url)

        if my_debug:
            print(TAG+"requests=", requests)
            print(TAG+"TIME_URL=", TIME_URL)
        try:
            response = my_wifi.get_url(TIME_URL)
            if not my_debug:
                print(TAG+"response=", response)
                print(TAG+"response.text=", response.text)
            if my_debug:
                print(TAG+"type(requests) = ", type(requests))
            #response = requests.get(TIME_URL)
            #if not my_debug:
            #    print(TAG+"response=", response)
            my_dat.write(_response, response)
        except RuntimeError:
            print(TAG+"RuntimeError occurred. PASS")
            pass
        except Exception as e:
            s0 = e.args[0]
            s3 = "               "
            le = len(s0)
            if le >= 15:
                s = s0[:15]
                s2 = s0[15:].lstrip()
            else:
                s2 = s3
            print(TAG+"error {} occurred.".format(e), end='\n')
            n = s0.find("Refresh too soon")
            if n < 0: # Only display on MAGTAG when not this Refresh error
                magtag.set_text(s,  0, auto_refresh = False)
                magtag.set_text(s2, 1, auto_refresh = False)
                magtag.set_text(s3, 2, auto_refresh = False)
                magtag.display.refresh() # refresh the display

            return False

        if isinstance(response, type(None)):
            s = "DATE AND TIME"
            s2 = "UNAVAILABLE"

            print(TAG+s+" "+s2)
            magtag.set_text(s, 0, auto_refresh = False)
            magtag.set_text(s2,   1, auto_refresh = False)  # Display error message
            magtag.set_text(" ", 2, auto_refresh = False)
            my_dat.write(_sDt, "")
        else:
            tz = response.text[30:40]
            my_dat.write(_tz, tz)
            if my_debug:
                print(TAG+"tz= \"{}\"".format(tz))
            resp_lst = response.text.split(" ") # response split =  ['2022-03-13', '17:02:51.303', '072', '7', '+0000', 'WET']
            my_dat.write(_tz_offset, resp_lst[4])
            my_dat.write(_dst, resp_lst[5])
            if resp_lst[5] == 'WEST':
                dst = 1
            elif resp_lst[5] == 'WET':
                dst = 0
            else:
                dst = -1
            if my_debug:
                print(TAG+"dst=", dst)
                print(TAG+"response.text.split=", resp_lst)
            dt = response.text[:10]
            tm = response.text[11:16] # 23]
            hh = int(resp_lst[1][:2])
            mm = int(resp_lst[1][3:5]) # +mm_corr # add the correction
            ss = int(resp_lst[1][6:8])
            yd = int(resp_lst[2]) # day of the year
            wd = int(resp_lst[3])-1 # day of the week -- strftime %u (weekday base Monday = 1), so correct because CPY datetime uses base 0
            #sDt = "Day of the year: "+str(yd)+", "+weekdays[wd]+" "+resp_lst[0]+", "+resp_lst[1][:5]+" "+resp_lst[4]+" "+resp_lst[5]
            sDt = "Day of the year: {}, {} {} {} {} {}".format(yd, weekdays[wd], resp_lst[0], resp_lst[1][:5], resp_lst[4], resp_lst[5])
            if not my_debug:
                print(TAG+"sDt=", sDt)
            my_dat.write(_yd, yd)
            my_dat.write(_wd, wd)
            my_dat.write(_sDt, sDt)
            # Set the internal RTC
            yy = int(dt[:4])
            mo = int(dt[5:7])
            dd = int(dt[8:10])
            tm2 = (yy, mo, dd, hh, mm, ss, wd, yd, dst)
            tm3 = time.struct_time(tm2)
            if my_debug:
                print(TAG+"dt=",dt)
                print(TAG+"yy ={}, mo={}, dd={}".format(yy, mm, dd))
                print(TAG+"tm2=",tm2)
                print(TAG+"tm3=",tm3)
            rtc_bi.datetime = tm3 # set the built-in RTC
            if not my_debug:
                print(TAG+"built-in RTC synchronized from AIO time server")
            if not my_dat.read(_rtc_set):
                my_dat.write(_rtc_set, True) # Flag that built_in RTC is set

    """
        Get the datetime from the built-in RTC
        a) after being updated (synchronized) from the AIO time server;
        b) when not synchronized, at a change of a minute value
        Note: the built-in RTC datetime gives always -1 for tm_isdst
              We determine is_dst from resp_lst[5] extracted from the AIO time server response text
    """
    ct = rtc_bi.datetime  # read datetime from built_in RTC
    yy = ct[tm_year]
    mo = ct[tm_mon]
    dd = ct[tm_mday]
    hh = ct[tm_hour]
    mm = ct[tm_min]
    ss = ct[tm_sec]
    wd = ct[tm_wday] # Correct because built-in RTC weekday index is different from the AIO weekday
    yd = ct[tm_yday]
    is_dst = ct[tm_isdst]
    dt = "{}-{:02d}-{:02d}".format(yy, mo, dd)
    tm = "{:02d}:{:02d}".format(hh, mm)
    tz = my_dat.read(_tz)
    tz_off = my_dat.read(_tz_offset)
    sis_dst = my_dat.read(_dst)
    sDt = "Day of the year: {}, {} {:4d}-{:02d}-{:02d}, {:02d}:{:02d} {} {}".format(yd, weekdays[wd], yy, mo, dd, hh, mm, tz_off,sis_dst)

        #retval = "{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} {} {} {} {}".format(yy, mo, dd, hh, mm, ss, yd, wd, tz_off, sis_dst)

    if not my_debug:
        print(TAG+"RTC current_time=", ct)
        print(TAG+"Weekday=", weekdays[wd])

    if hh == my_dat.read(_last_hh) and mm == my_dat.read(_last_mm):
        same_time_cnt = my_dat.read(_same_time_cnt)
        if my_debug:
            print(TAG+"type(same_time_cnt)=", type(same_time_cnt))
        same_time_cnt += 1
        my_dat.write(_same_time_cnt, same_time_cnt)
        if same_time_cnt > 1:
            s = "TIME UNRELIABLE"
            print(TAG+s)
            magtag.set_text(" ", 0, auto_refresh = False)
            magtag.set_text(s,   1, auto_refresh = False)  # Display error message
            magtag.set_text(" ", 2, auto_refresh = False)
    else:
        last_hh = hh
        last_mm = mm
        my_dat.write(_last_hh, hh)
        my_dat.write(_last_mm, mm)
        same_time_cnt = my_dat.read(_same_time_cnt)
        same_time_cnt -= 1
        if same_time_cnt < 0:
            same_time_cnt = 0
        my_dat.write(_same_time_cnt, same_time_cnt)
        if my_debug:
            print(TAG+"Updated time: \'{:02d}:{:02d}\'".format(last_hh, last_mm))
            print(TAG+"type(same_time_cnt)=", type(same_time_cnt))
            print(TAG+"same_time_cnt=", same_time_cnt)
    #s = "time: {}, timzezone: {}".format(tm, tz)
    for _ in range(3):
        if _ == 0:
            magtag.set_text(dt, _, auto_refresh = False)  # Display the date
        elif _ == 1:
            magtag.set_text(tm, _, auto_refresh = False)
        elif _ == 2:
            magtag.set_text(tz, _, auto_refresh = False)
    try:
        magtag.display.refresh() # refresh the display
    except RuntimeError:
        pass  # reason: Refresh too soon
    return True


def dt_itm(itm):
    TAG = "dt_itm(): "
    my_debug = my_dat.read(_debug)
    ct = rtc_bi.datetime # get the (current time) datetime from the built-in RTC
    if my_debug:
        print(TAG+"RTC built_in, datetime=", ct)

    # hours = ct[3]
    # mins = ct[4]

    if itm >= 0 and itm <= 7:
        return ct[itm]


def main():
    TAG = "main(): "
    lStart = True
    setup()
    my_debug = my_dat.read(_debug)
    start_clk = my_dat.read(_start_clk)
    old_hh = dt_itm(3) # get the hour of the built_in RTC
    old_mi = dt_itm(4) # idem minutes
    dummy = None
    fail_cnt = 0

    while True:
        try:
            curr_mi = dt_itm(4)
            if old_mi != curr_mi:
                old_mi = curr_mi
                dummy = get_pr_dt(False)  # get dt from built-in RTC and print
            curr_hh = dt_itm(3)
            if lStart or old_hh != curr_hh:
                lStart = False
                old_hh = curr_hh
                while True:
                    if get_pr_dt(True): # synchronize built_in RTC with datetime from NTP server
                        break
                    else:
                        fail_cnt += 1
                        if fail_cnt == 5:
                            print(TAG+"five times error result calling get_pr_dt()")
                            break
                        time.sleep(1)

                start_clk = time.monotonic()
                my_dat.write(_start_clk, start_clk)
                #mem_stat()
        except KeyboardInterrupt:
            raise SystemExit

if __name__ == '__main__':
    main()
