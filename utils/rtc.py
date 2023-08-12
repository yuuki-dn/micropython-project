from machine import Pin, I2C
from lib.ds3231 import DS3231
import socket
import struct

def RequestTimefromNtp(addr):
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(addr, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(2)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    return val - 2208988800

block_4y = [365, 730, 1096, 1461, 0]
month_norm = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365, 0]
month_leap = [31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366, 0]

def timestamp_to_readable(timestamp):
    hms = timestamp % 86400
    timestamp //= 86400
    year = 1970 + timestamp // 1461 * 4
    timestamp %= 1461
    for i in range(4):
        if timestamp < block_4y[i]: break
    year += i
    timestamp -= block_4y[i - 1]
    if i == 2: _month = month_leap
    else: _month = month_norm
    for i in range(12):
        if timestamp < _month[i]: break
    month = i + 1
    day = timestamp - _month[i - 1] + 1
    hour = hms // 3600
    hms %= 3600
    minute = hms // 60
    second = hms % 60
    return year, month, day, hour, minute, second

class rtc():
    def __init__(self, config):
        self.ds3231 = DS3231(I2C(scl=Pin(5), sda=Pin(4)))
        self.ntpserver = config["server"]
        self.timezone = config["timezone"]
        print("RTC initialized")

    def now(self):
        return self.ds3231.datetime()
    
    def set(self, year, month, day, hour, minute, second):
        self.ds3231.datetime((year, month, day, hour, minute, second, 0, 0))

    def sync(self):
        print("Syncing RTC with NTP server...")
        try:
            t = RequestTimefromNtp(self.ntpserver)
        except: return False
        t += self.timezone * 3600
        self.ds3231.datetime(timestamp_to_readable(t))
        return True