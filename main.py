# main.py -- put your code here!
import uasyncio
import json
import os
from hashlib import sha256

from ext.rtc import rtc
from ext.wifi import wifi

class config():
    def __init__(self):
        if "config.json" in os.listdir():
            with open("config.json", "r") as f:
                self.config = json.loads(f.read())
            print("Loaded user configurations")
        
        else:
            self.config: dict = {
                "name": "NODE_ESP8266_x1000",
                "client": {"ssid": "Test", "password": "12345678"},
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
            print("Loaded default configurations")

    def save(self):
        with open("config.json", "w") as f:
            f.write(json.dumps(self.config))

class system():
    def __init__(self):
        self.config = config()

        self.name = self.config.get("name")
        self.version = "1.0.0"
        self.id = "10000011"
        self.api_secret = "sec_jio982jf8h32d798yo8hed981_x1000"

        self.gate = []
        self.rtc = rtc(self.config["ntp"])
        self.wifi = wifi(self.name, self.config["client"])
    
    async def startup(self):
        print(f"Starting {self.name} v{self.version}...")
        while True:
            await uasyncio.sleep(10)

_system = system()
uasyncio.run(_system.startup())