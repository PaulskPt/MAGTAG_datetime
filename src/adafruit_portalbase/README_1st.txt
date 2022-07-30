2021-09-24 15h32 PT

Because of a problem with internet yesterday, the MAGTAG date and time script came up with an error about a NoneType.
During an investigation that I started today, I discovered that there is in the lib/adafruit_portalbase a python script 'wifi_esp32s2.py'. I started to use this instead of the wifi.py.


In line 28 of code.py I added the line: from adafruit_portalbase.wifi_esp32s2 import WiFi
In line 97 of code.py I added the line: my_wifi = WiFi()  # create an instance of WiFi class

In the whole code.py script I deleted 'requests' variable

In file wifi_esp32s2.py added: import ipaddress  # function added by @Paulskpt on 2021-09-24

I added/created six functions to the wifi_esp32s2.py file, class: WiFi.
I had to put them in this script because from in there, within the WiFi class, it was possible to call the radio class.
Here are the three new functions:

    #@property                           # function added by @Paulskpt on 2021-09-24
    def get_url(self, url):
        return self.requests.get(url)
        
    #@property
    def ping(self, ip):                  # function added by @Paulskpt on 2021-09-24
        TAG = "WiFi.ping(): "
        ipv4 = ipaddress.ip_address(ip)
        res = wifi.radio.ping(ipv4)
        if isinstance(res, type(None)):
            print(TAG+"Ping to \'{}\' failed".format(ipv4))
            res = 999.99
        else:
            print(TAG+"Ping to: \'{}\' = {} mSec.".format(ipv4, res))
        return res
		
    #@property
    def do_scan(self):                  # function added by @Paulskpt on 2021-09-24
        print("Available WiFi networks:")
        for network in wifi.radio.start_scanning_networks():
            s = "\tSSID: {:20s}\tRSSI: {:d}\tChannel: {:2d}".format(str(network.ssid, "utf-8"),network.rssi, network.channel)
            print(s, end='\n')
        wifi.radio.stop_scanning_networks()
        print("", end='\n')
		
		    #@property
    def get_mac_address(self):                 # function added by @Paulskpt on 2021-09-24
        return wifi.radio.mac_address

    #@property
    def get_mac_address_ap(self):              # function added by @Paulskpt on 2021-09-24
        return wifi.radio.mac_address_ap

    def get_gateway_ip(self):                  # function added by @Paulskpt on 2022-02-08
        return wifi.radio.ipv4_gateway
		

After all these modifications the MAGTAG script ran again OK.

