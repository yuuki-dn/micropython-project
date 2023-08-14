import uasyncio
import network

class wifi():
    def __init__(self, name, config):
        self.config = config

        self.client = network.WLAN(network.STA_IF)
        self.client.active(True)
        self.fallback = network.WLAN(network.AP_IF)
        self.fallback.config(ssid=f"[Fallback] {name}", security=4, key=name)

        self.client_up = False
        self.client_ip = None
        self.reconnect_flag = True
        self.fallback_state = False

        uasyncio.create_task(self.daemon())

    async def daemon(self):
        while True:
            if self.reconnect_flag:
                self.client.connect(self.config.get("ssid"), self.config.get("password"))
                print(f"Connecting to WiFi SSID: {self.config.get('ssid')}...")
                self.reconnect_flag = False

            await uasyncio.sleep(3)
            self.fallback.active(False)
            if self.client.isconnected():
                if not self.client_up:
                    print(f"Connected to WiFi SSID: {self.config.get('ssid')}, IP: {self.client.ifconfig()[0]}")
                    self.client_up = True
                    self.client_ip = self.client.ifconfig()[0]

                if self.fallback_state:
                    print("Stopping fallback mode...")
                    self.fallback.active(False)
                    self.fallback_state = False

            elif not self.client.isconnected():
                if self.client_up:
                    self.client_up = False
                    print(f"Disconnected from WiFi SSID: {self.config.get('client_ssid')}")
                    self.client_ip = None

                if not self.fallback_state:
                    print("Starting fallback mode...")
                    self.fallback.active(True)
                    self.fallback_state = True
    
    async def scan(self):
        return await self.client.scan()
    
    def info(self):
        status = ["IDLE", "CONNECTING", "WRONG_PASSWORD", "NO_AP_FOUND", "CONNECT_FAIL", "CONNECTED"]
        ifconfig = self.client.ifconfig() if self.client.isconnected() else None
        return {
            "client_status": status[self.client.status()],
            "signal": self.client.status("rssi") if self.client.isconnected() else None,
            "fallback": "ACTIVE" if self.fallback_state else "INACTIVE",
            "ip": ifconfig[0] if ifconfig else None,
            "netmask": ifconfig[1] if ifconfig else None,
            "gateway": ifconfig[2] if ifconfig else None,
            "dns": ifconfig[3] if ifconfig else None
        }