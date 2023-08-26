# main.py -- put your code here!
import json
from network import WLAN, STA_IF, AP_IF
from lib.ds3231 import DS3231
from machine import Pin, I2C
import lib.blynklib_mp as blynklib
import time
import socket
import struct

# Load configuration
with open('config.json') as config_file: CONFIG = json.load(config_file)

LIST_KEY = ["wlan_ssid", "wlan_password", "timezone", "webpassword", "blynk_server", "blynk_port", "authtoken"]

def save_config(config: dict):
    save = {}
    for key in LIST_KEY: save[key] = config.get(key, CONFIG[key])
    with open('config.json', 'w') as config_file: json.dump(save, config_file)

# RTC setup
ds3231 = DS3231(I2C(scl=Pin(5), sda=Pin(4)))
if ds3231.OSF(): ds3231.datetime((2023, 1, 1, 0, 0, 0, 0, 0))

def ntptime():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(2)
        s.sendto(NTP_QUERY, socket.getaddrinfo("0.pool.ntp.org", 123)[0][-1])
        msg = s.recv(48)
    finally: s.close()

    EPOCH_YEAR = time.gmtime(0)[0]
    if EPOCH_YEAR == 2000: NTP_DELTA = 3155673600
    elif EPOCH_YEAR == 1970: NTP_DELTA = 2208988800
    else: raise Exception("Unsupported epoch.")

    return struct.unpack("!I", msg[40:44])[0] - NTP_DELTA + 3600 * CONFIG["timezone"]

def sync_ntp():
    tm = time.gmtime(ntptime())
    ds3231.datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

# Network setup
wlan = WLAN(STA_IF)
wlan.active(True)
if CONFIG["wlan_password"] == "":
    wlan.connect(CONFIG["wlan_ssid"])
else:
    wlan.connect(CONFIG["wlan_ssid"], CONFIG["wlan_password"])
fallback_ap = WLAN(AP_IF)
fallback_ap.active(True)
try: fallback_ap.config(essid="ESP8266")
except: pass

# Switch setup
class Switch():
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.OUT)
        self.state = False
        self.off()
    
    def on(self):
        self.pin.value(0)
        self.state = True
    
    def off(self):
        self.pin.value(1)
        self.state = False

sw = [Switch(14), Switch(12), Switch(13), Switch(15)]

# Main function (with Blynk)
blynk = blynklib.Blynk(CONFIG["blynk_token"], server=CONFIG["blynk_server"], port=CONFIG["blynk_port"])

# Example
# @blynk.handle_event('write V4')
# def write_virtual_pin_handler(pin, value):
#     print(pin, value)

# @blynk.handle_event('read V11')
# def read_virtual_pin_handler(pin):
#     blynk.virtual_write(pin, 0)

@blynk.handle_event('read V0')
def devstate(pin):
    string = ""
    

@blynk.handle_event('write V0')
def wv0_handle(pin, value): sw[0].on() if value[0] == '1' else sw[0].off()

@blynk.handle_event('write V1')
def wv1_handle(pin, value): sw[1].on() if value[0] == '1' else sw[1].off()

@blynk.handle_event('write V2')
def wv2_handle(pin, value): sw[2].on() if value[0] == '1' else sw[2].off()

@blynk.handle_event('write V3')
def wv3_handle(pin, value): sw[3].on() if value[0] == '1' else sw[3].off()

@blynk.handle_event('read V0')
def rv0_handle(pin): blynk.virtual_write(pin, '1' if sw[0].state else '0')

@blynk.handle_event('read V1')
def rv1_handle(pin): blynk.virtual_write(pin, '1' if sw[1].state else '0')

@blynk.handle_event('read V2')
def rv2_handle(pin): blynk.virtual_write(pin, '1' if sw[2].state else '0')

@blynk.handle_event('read V3')
def rv3_handle(pin): blynk.virtual_write(pin, '1' if sw[3].state else '0')

# Main loop
while True:
    if not wlan.isconnected():
        if not fallback_ap.active(): fallback_ap.active(True)
        time.sleep(1)
        continue
    if not blynk.connected():
        if not fallback_ap.active(): fallback_ap.active(True)
        blynk.connect()
    else: 
        if fallback_ap.active(): fallback_ap.active(False)
        blynk.run()