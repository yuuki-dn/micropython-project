from micropython import const

DATETIME_REG    = const(0)
STATUS_REG      = const(15)

def dectobcd(decimal):
    """Convert decimal to binary coded decimal (BCD) format"""
    return (decimal // 10) << 4 | (decimal % 10)

def bcdtodec(bcd):
    """Convert binary coded decimal to decimal"""
    return ((bcd >> 4) * 10) + (bcd & 0x0F)

class DS3231:
    "DS3231 RTC driver."

    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self._timebuf = bytearray(7)
        self._buf = bytearray(1)
        self._al1_buf = bytearray(4)
        self._al2buf = bytearray(3)

    def datetime(self, datetime=None):
        """Get or set datetime
        Always sets or returns in 24h format, converts to 24h if clock is set to 12h format
        datetime : tuple, (0-year, 1-month, 2-day, 3-hour, 4-minutes[, 5-seconds[, 6-weekday]])"""
        if datetime is None:
            self.i2c.readfrom_mem_into(self.addr, DATETIME_REG, self._timebuf)
            seconds = bcdtodec(self._timebuf[0])
            minutes = bcdtodec(self._timebuf[1])

            if (self._timebuf[2] & 0x40) >> 6:
                hour = bcdtodec(self._timebuf[2] & 0x9f)
                if (self._timebuf[2] & 0x20) >> 5:
                    # PM
                    hour += 12
            else:
                # 24h mode
                hour = bcdtodec(self._timebuf[2] & 0xbf)

            weekday = bcdtodec(self._timebuf[3])
            day = bcdtodec(self._timebuf[4])
            month = bcdtodec(self._timebuf[5] & 0x7f)
            year = bcdtodec(self._timebuf[6]) + 2000

            if self.OSF():
                print("WARNING: Oscillator stop flag set. Time may not be accurate.")

            return (year, month, day, weekday, hour, minutes, seconds, 0)
        
        try:
            self._timebuf[3] = dectobcd(datetime[6])
        except IndexError:
            self._timebuf[3] = 0
        try:
            self._timebuf[0] = dectobcd(datetime[5]) # Seconds
        except IndexError:
            self._timebuf[0] = 0
        self._timebuf[1] = dectobcd(datetime[4])
        self._timebuf[2] = dectobcd(datetime[3])
        self._timebuf[4] = dectobcd(datetime[2])
        self._timebuf[5] = dectobcd(datetime[1]) & 0xff
        self._timebuf[6] = dectobcd(int(str(datetime[0])[-2:]))
        self.i2c.writeto_mem(self.addr, DATETIME_REG, self._timebuf)
        self._OSF_reset()
        return True

    def OSF(self):
        return bool(self.i2c.readfrom_mem(self.addr, STATUS_REG, 1)[0] >> 7)

    def _OSF_reset(self):
        self.i2c.readfrom_mem_into(self.addr, STATUS_REG, self._buf)
        self.i2c.writeto_mem(self.addr, STATUS_REG, bytearray([self._buf[0] & 0x7f]))

    def _is_busy(self):
        return bool(self.i2c.readfrom_mem(self.addr, STATUS_REG, 1)[0] & (1 << 2))