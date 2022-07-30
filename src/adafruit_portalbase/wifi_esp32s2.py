# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_portalbase.wifi_esp32s2`
================================================================================

WiFi Helper module for the ESP32-S2 based boards.


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import gc
import ssl
import wifi
import socketpool
import adafruit_requests
import ipaddress  # function added by @Paulskpt on 2021-09-24

__version__ = "1.10.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PortalBase.git"



class WiFi():
    """Class representing the WiFi portion of the ESP32-S2.

    :param status_led: The initialized object for status DotStar, NeoPixel, or RGB LED. Defaults
                       to ``None``, to not use the status LED

    """

    def __init__(self, *, status_led=None):
        if status_led:
            self.neopix = status_led
        else:
            self.neopix = None
        self.neo_status(0)
        self.requests = None
        self.pool = None
        self._connected = False

        gc.collect()

    def connect(self, ssid, password):
        """
        Connect to the WiFi Network using the information provided

        :param ssid: The WiFi name
        :param password: The WiFi password

        """
        try:
            wifi.radio.connect(ssid, password)
        except ConnectionError as exc:
            print("WiFi.connect(): ConnectionError: ", exc.args[0])
            return
        self.pool = socketpool.SocketPool(wifi.radio)
        self.requests = adafruit_requests.Session(
            self.pool, ssl.create_default_context()
        )
        self._connected = True

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

    def neo_status(self, value):
        """The status DotStar.

        :param value: The color to change the DotStar.

        """
        if self.neopix:
            self.neopix.fill(value)

    @property
    def is_connected(self):
        """
        Return whether we have already connected since reconnections are handled automatically.

        """
        return self._connected

    @property
    def ip_address(self):
        """
        Return the IP Version 4 Address

        """
        return wifi.radio.ipv4_address

    @property
    def enabled(self):
        """
        Return whether the WiFi Radio is enabled

        """
        return wifi.radio.enabled

    @enabled.setter
    def enabled(self, value):
        wifi.radio.enabled = bool(value)
        if not wifi.radio.enabled:
            self._connected = False
