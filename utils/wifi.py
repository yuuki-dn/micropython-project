import uasyncio
import network

class wifi():
    def __init__(self, name, config):
        self.config = config

        self.client = network.WLAN(network.STA_IF)
        self.client.active(True)
        self.fallback = network.WLAN(network.AP_IF)
        self.fallback.config(ssid=f"{name}_AP", authmode=network.AUTH_WPA_WPA2_PSK, password="12345678")
        
        self.client_up = False
        self.client_ip = None
        self.reconnect_flag = True
        self.fallback_state = False

        uasyncio.create_task(self.daemon())
        uasyncio.create_task(self.fallback_mode())

    async def daemon(self):
        while True:
            if self.reconnect_flag:
                self.client.connect(self.config.get("client_ssid"), self.config.get("client_password"))
                print(f"Connecting to WiFi SSID: {self.config.get('client_ssid')}...")
                self.reconnect_flag = False

            await uasyncio.sleep(3)
            if self.client.isconnected() and not self.client_up:
                print(f"Connected to WiFi SSID: {self.config.get('client_ssid')}, IP: {self.client.ifconfig()[0]}")
                self.client_up = True
                self.client_ip = self.client.ifconfig()[0]

            elif not self.client.isconnected() and self.client_up:
                self.client_up = False
                print(f"Disconnected from WiFi SSID: {self.config.get('client_ssid')}")
                self.client_ip = None

    async def fallback_mode(self):
        await uasyncio.sleep(10)
        while True:
            if not self.client_up and not self.fallback_state:
                print("Starting fallback mode...")
                self.fallback.active(True)
                self.fallback_state = True

            elif self.client_up and self.fallback_state:
                print("Stopping fallback mode...")
                self.fallback.active(False)
                self.fallback_state = False

            await uasyncio.sleep(3)