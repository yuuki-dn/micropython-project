import machine
import uasyncio
import json

class task():
    def __init__(self, start: set, end: set):
        self.start = start
        self.end = end
    
    def __repr__(self): return self.start

gate_pin = {"D5": 14, "D6": 12, "D7": 13, "D8": 15}
default_schedule = {
    "mode": "manual", # can be manual, daily or weekly
    "daily": [],
    "weekly": {
        "mon": [],
        "tue": [],
        "wed": [],
        "thu": [],
        "fri": [],
        "sat": [],
        "sun": []
    }
}

class gate():
    def __init__(self, gate, now, name = "", reverse = True):
        self.now: function = now
        self.gate = gate
        self.name = f"Gate_{gate_pin[gate]}" if name == "" else name
        self.pin = machine.Pin(gate_pin[gate], machine.Pin.OUT)
        self.reverse = reverse
        self.open = False
        if self.reverse: self.pin.value(1)
        try:
            with open(f"schedule/schedule_{self.gate}.json", "r") as f:
                self.schedule = json.loads(f.read())
        except: self.schedule = default_schedule
        
        print(f"Gate {self.name} (Pin: {gate_pin[gate]}) initialized")

        self.reload = True
        self.req = None

        uasyncio.create_task(self.daemon())

    def save(self):
        with open(f"schedule_{self.gate}.json", "w") as f:
            f.write(json.dumps(self.schedule))

    def __repr__(self) -> str:
        return f"{self.name} (Pin: {gate_pin[self.gate]}) [{self.open}]"
        
    def sys_on(self):
        if self.reverse: self.pin.value(0)
        else: self.pin.value(1)
        self.open = True
    
    def sys_off(self):
        if self.reverse: self.pin.value(1)
        else: self.pin.value(0)
        self.open = False
    
    def manual(self, mode, time=-1):
        if mode not in ["on", "off"]: return
        self.req = {"mode": mode, "time": time}
        print(f"Gate {self.name} (Pin: {gate_pin[self.gate]}) set to {mode} {'for ' + str(time) + ' seconds' if time != -1 else ''}")
    
    def set(self, start, end, type="daily"):
        if type == "daily":
            self.schedule["daily"].append(task(start, end))
        elif type == "weekly":
            weekday = self.now()[1]
            self.schedule["weekly"][weekday].append(task(start, end))
        self.reload = True
    
    async def daemon(self):
        mode = "manual"
        current_schedule = []
        end = ""
        weekday = ""
        req = None
        while True:
            if self.req != None:
                self.end = ""
                if self.req["mode"] == "on":
                    self.sys_on()
                    req = self.req["time"]
                elif self.req["mode"] == "off":
                    self.sys_off()
                    req = None
                self.req = None
            
            if req != None:
                if req == 0:
                    self.sys_off()
                    req = None
                elif req == -1: pass
                else: req -= 1
                await uasyncio.sleep(1)
                continue
            
            now = self.now()
            if self.reload or now[1] != weekday:
                weekday = now[1]
                mode = self.schedule["mode"]
                if mode == "manual": current_schedule = []
                elif mode == "daily": current_schedule = self.schedule["daily"]
                elif mode == "weekly": current_schedule = self.schedule["weekly"][weekday]
                self.save()
                self.end = ""
                self.reload = False

            if mode != "manual":            
                if now[0] in current_schedule:
                    s: task = current_schedule[current_schedule.index(now[0])]
                    self.sys_on()
                    end = s.end
                
                elif end == now[0]:
                    self.sys_off()
                    end = ""

            await uasyncio.sleep(10)