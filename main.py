# main.py -- put your code here!
import uasyncio as asyncio
import machine
import json
import os
from hashlib import sha256

from utils.rtc import rtc
from utils.wifi import wifi

gate_pin = {
    "D5": 14,
    "D6": 12,
    "D7": 13,
    "D8": 15,
}

class gate():
    def __init__(self, gate, name = "", reverse = True):
        self.name = f"Gate_{gate_pin[gate]}" if name == "" else name
        self.pin = machine.Pin(gate_pin[gate], machine.Pin.OUT)
        self.reverse = reverse
        self.open = False
        if self.reverse: self.pin.value(1)
        print(f"Gate {self.name} (Pin: {gate_pin[gate]}) initialized")
        
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
        if "config.json" in os.listdir():
            with open("config.json", "r") as f:
                self.config = json.loads(f.read())
        
        else:
            self.config = {
                            "client": {"enable": False, "ssid": "", "password": ""},
                            "http_server": {"port": 2080, "username": "admin", "password": "admin"},
                            "ws": {"enable": False, "server": ""},
                            "ntp": {"server": "0.pool.ntp.org", "timezone": 0},
                            "gate": {
                                "D5": {"enable": True, "name": "Gate 1 [D5]", "reverse": False},
                                "D6": {"enable": True, "name": "Gate 2 [D6]", "reverse": False},
                                "D7": {"enable": True, "name": "Gate 3 [D7]", "reverse": False},
                                "D8": {"enable": True, "name": "Gate 4 [D8]", "reverse": False}
                            }
                        }
        print("Configurations loaded")
    
    def get(self, key, alt=None):
        try:
            return self.config[key]
        except KeyError:
            return alt
    
    def set(self, key, value):
        self.config[key] = value
        with open("config.json", "w") as f:
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