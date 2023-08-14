from machine import Pin, I2C
from lib.ds3231 import DS3231
import socket
import struct
import uasyncio


NTP_QUERY = bytearray(48)
NTP_QUERY[0] = 0x1B

async def RequestTimefromNtp(addr):
    addr = socket.getaddrinfo(addr, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(2)
        s.sendto(NTP_QUERY, addr)
        msg = await s.recv(48)
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

def readable_to_timestamp(year, month, day, hour, minute, second):
    timestamp = 0
    for i in range(year - 1970):
        if i % 4 == 0: timestamp += 31622400
        else: timestamp += 31536000
    if year % 4 == 0: _month = month_leap
    else: _month = month_norm
    timestamp += _month[month - 1] * 86400
    timestamp += (day - 1) * 86400
    timestamp += hour * 3600
    timestamp += minute * 60
    timestamp += second
    return timestamp

class rtc():
    def __init__(self, config):
        self.ds3231 = DS3231(I2C(scl=Pin(5), sda=Pin(4)))
        self.ntpserver = config["server"]
        self.timezone = config["timezone"]
        print("RTC initialized")
    
    def set(self, year, month, day, hour, minute, second):
        self.ds3231.datetime((year, month, day, hour, minute, second, 0, 0))

    async def sync(self):
        print("Syncing RTC with NTP server...")
        try:
            t = await RequestTimefromNtp(self.ntpserver)
        except: return False
        t += self.timezone * 3600
        self.ds3231.datetime(timestamp_to_readable(t))
        return True
    
    def weekday(self, datetime = None):
        now = (readable_to_timestamp(datetime if datetime else self.ds3231.datetime()) // 86400 + 4) % 7
        if now == 0: return "sun"
        elif now == 1: return "mon"
        elif now == 2: return "tue"
        elif now == 3: return "wed"
        elif now == 4: return "thu"
        elif now == 5: return "fri"
        elif now == 6: return "sat"
    
    def time(self):
        return self.ds3231.datetime()
    
    def now(self):
        time = self.ds3231.datetime()
        hour = time[4]
        minute = time[5]
        weekday = self.weekday(time)
        return f"{hour}:{minute}", weekday