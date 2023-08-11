# main.py -- put your code here!
import uasyncio as asyncio
import machine
import json
import os
from hashlib import sha256

from utils.rtc import rtc
from utils.wifi import wifi

class gate():
    def __init__(self):
        self.pin = machine.Pin(13, machine.Pin.OUT)
        self.reverse = True
        self.open = False
        if self.reverse: self.pin.value(1)
        
    def on(self):
        if self.reverse: self.pin.value(0)
        else: self.pin.value(1)
        self.open = True
    
    def off(self):
        if self.reverse: self.pin.value(1)
        else: self.pin.value(0)
        self.open = False
    
    def toggle(self):
        if self.open: self.off()
        else: self.on()

class config():
    def __init__(self):
        if "usrconf.json" in os.listdir("conf"):
            with open("config.json", "r") as f:
                self.config = json.loads(f.read())
        else:
            with open("conf/conf.json", "w") as f:
                self.config = {}
                f.write(json.dumps(self.config))
        print("Configurations loaded")
    
    def get(self, key, alt=None):
        try:
            return self.config[key]
        except KeyError:
            return alt
    
    def set(self, key, value):
        self.config[key] = value
        with open("conf/usrconf.json", "w") as f:
            f.write(json.dumps(self.config))

class system():
    def __init__(self):
        self.name = "NODE_ESP8266_x1000"
        self.version = "1.0.0"
        self.id = "10000011"
        self.api_secret = "sec_jio982jf8h32d798yo8hed981_x1000"

        self.gate = gate()
        self.config = config()
        self.rtc = rtc(self.config.get("ntp_server"), self.config.get("utc_offset"))
        self.wifi = wifi(self.name, self.config, self.rtc)
        self.wifi.start()
    
    async def startup(self):
        print(f"Starting {self.name} v{self.version}...")
        while True:
            await asyncio.sleep(10)

_system = system()
asyncio.run(_system.startup())