#!/usr/bin/env python
import time
import sys
import json
import threading
import traceback

# Simulated display and LED strip for command-line debug mode
from menu import MenuItem, Menu, Back, MenuContext, MenuDelegate
from drinks import drink_list, drink_options

class ConsoleDisplay:
    """Dummy display: prints to console with debug info."""
    def __init__(self, width=128, height=64):
        print(f"[DEBUG] ConsoleDisplay::__init__({width}x{height})")
        self.width = width
        self.height = height
    def begin(self): print("[DEBUG] ConsoleDisplay.begin() called")
    def clear_display(self): print("[DEBUG] ConsoleDisplay.clear_display() called\n" + "-"*self.width)
    def display(self): print("[DEBUG] ConsoleDisplay.display() called")
    def invert_display(self): print("[DEBUG] ConsoleDisplay.invert_display() called")
    def normal_display(self): print("[DEBUG] ConsoleDisplay.normal_display() called")
    def draw_text2(self, x, y, text, size): print(f"[DISPLAY] {text}")
    def draw_pixel(self, x, y): pass

class DummyStrip:
    """Dummy LED strip: prints debug actions."""
    def __init__(self, numpixels, datapin, clockpin):
        print(f"[DEBUG] DummyStrip::__init__(numpixels={numpixels})")
        self.numpixels = numpixels
    def begin(self): print("[DEBUG] DummyStrip.begin() called")
    def setBrightness(self, brightness): print(f"[DEBUG] DummyStrip.setBrightness({brightness})")
    def setPixelColor(self, i, color): pass
    def show(self): print("[DEBUG] DummyStrip.show() called")

# Constants
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
NUMBER_NEOPIXELS = 45
NEOPIXEL_DATA_PIN = 26
NEOPIXEL_CLOCK_PIN = 6
NEOPIXEL_BRIGHTNESS = 64
FLOW_RATE = 60.0/100.0

class Bartender(MenuDelegate):
    def __init__(self):
        print("[DEBUG] Bartender::__init__() start")
        self.running = False
        # Setup display
        self.led = ConsoleDisplay(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.led.begin(); self.led.clear_display(); self.led.display()
        self.led.invert_display(); time.sleep(0.2); self.led.normal_display(); time.sleep(0.2)
        # Load pumps
        print("[DEBUG] Loading pump configuration...")
        self.pump_configuration = Bartender.readPumpConfiguration()
        print(f"[DEBUG] Pump config: {self.pump_configuration}")
        # Setup strip
        self.strip = DummyStrip(NUMBER_NEOPIXELS, NEOPIXEL_DATA_PIN, NEOPIXEL_CLOCK_PIN)
        self.strip.begin(); self.strip.setBrightness(NEOPIXEL_BRIGHTNESS)
        for i in range(self.strip.numpixels): self.strip.setPixelColor(i, 0)
        self.strip.show()
        print("[DEBUG] Bartender initialization complete")

    @staticmethod
    def readPumpConfiguration():
        print("[DEBUG] readPumpConfiguration() called")
        config = json.load(open('pump_config.json'))
        print(f"[DEBUG] readPumpConfiguration loaded: {config}")
        return config

    @staticmethod
    def writePumpConfiguration(configuration):
        print(f"[DEBUG] writePumpConfiguration() called with {configuration}")
        with open("pump_config.json","w") as f: json.dump(configuration, f)
        print("[DEBUG] Pump configuration saved to file")

    def buildMenu(self, drink_list, drink_options):
        print("[DEBUG] buildMenu() start")
        m = Menu("Main Menu")
        # Drink options
        for d in drink_list:
            m.addOption(MenuItem('drink', d['name'], {'ingredients': d['ingredients']}))
        # Config menu
        config_menu = Menu("Configure")
        for p in sorted(self.pump_configuration):
            submenu = Menu(self.pump_configuration[p]['name'])
            for opt in drink_options:
                sel = '*' if opt['value']==self.pump_configuration[p]['value'] else ''
                submenu.addOption(MenuItem('pump_selection', f"{opt['name']} {sel}".strip(), {'key':p,'value':opt['value'],'name':opt['name']}))
            submenu.addOption(Back('Back')); submenu.setParent(config_menu)
            config_menu.addOption(submenu)
        config_menu.addOption(Back('Back')); config_menu.addOption(MenuItem('clean','Clean')); config_menu.setParent(m)
        m.addOption(config_menu)
        self.menuContext = MenuContext(m, self)
        print("[DEBUG] buildMenu() complete")

    def filterDrinks(self, menu):
        print(f"[DEBUG] filterDrinks(menu={menu.name})")
        for opt in menu.options:
            if opt.type=='drink':
                ingredients = opt.attributes['ingredients']; ok = all(
                    any(ing==self.pump_configuration[p]['value'] for p in self.pump_configuration)
                    for ing in ingredients)
                opt.visible = ok
            elif opt.type=='menu': self.filterDrinks(opt)

    def selectConfigurations(self, menu):
        print(f"[DEBUG] selectConfigurations(menu={menu.name})")
        for opt in menu.options:
            if opt.type=='pump_selection':
                key=opt.attributes['key']; val=opt.attributes['value']
                opt.name = f"{opt.attributes['name']}*" if self.pump_configuration[key]['value']==val else opt.attributes['name']
            elif opt.type=='menu': self.selectConfigurations(opt)

    def prepareForRender(self, menu):
        print(f"[DEBUG] prepareForRender(menu={menu.name})")
        self.filterDrinks(menu); self.selectConfigurations(menu); return True

    def menuItemClicked(self, item):
        print(f"[DEBUG] menuItemClicked(item={item.name}, type={item.type})")
        if item.type=='drink': return self.makeDrink(item.name,item.attributes['ingredients'])
        if item.type=='pump_selection':
            k,v=item.attributes['key'],item.attributes['value']; self.pump_configuration[k]['value']=v
            Bartender.writePumpConfiguration(self.pump_configuration); return True
        if item.type=='clean': return self.clean()
        return False

    def clean(self):
        print("[DEBUG] clean() start")
        self.running=True; wait=5
        threads=[]
        for p in self.pump_configuration:
            t=threading.Thread(target=self.pour,args=(self.pump_configuration[p]['pin'],wait)); threads.append(t); t.start()
        self.progressBar(wait)
        for t in threads: t.join()
        print("[DEBUG] clean() done")
        self.menuContext.showMenu(); time.sleep(0.5); self.running=False
        return True

    def displayMenuItem(self, item): print(f"[DISPLAY] Now showing: {item.name}")

    def cycleLights(self):
        print("[DEBUG] cycleLights() start")
        t=threading.currentThread()
        while getattr(t,'do_run',True): time.sleep(0.2)
        print("[DEBUG] cycleLights() end")

    def lightsEndingSequence(self):
        print("[DEBUG] lightsEndingSequence() start")
        print("[LIGHT] Simulate green lights on"); time.sleep(1); print("[LIGHT] Lights off")

    def pour(self, pin, wait):
        print(f"[PUMP] Pour on pin {pin} for {wait:.2f}s"); time.sleep(wait); print(f"[PUMP] Pin {pin} done")

    def progressBar(self, wait):
        print(f"[DEBUG] progressBar(wait={wait:.2f}) start")
        for x in range(1,101):
            filled=int(30*x/100);
            bar='#'*filled+'-'*(30-filled)
            sys.stdout.write(f"\rProgress: [{bar}] {x}%"); sys.stdout.flush(); time.sleep(wait/100)
        print(); print("[DEBUG] progressBar end")

    def makeDrink(self, drink, ingredients):
        print(f"[DEBUG] makeDrink({drink}) start")
        self.running=True; print(f"[ACTION] Making: {drink}")
        lt=threading.Thread(target=self.cycleLights); lt.do_run=True; lt.start()
        threads=[]; maxt=0
        for ing,qty in ingredients.items():
            for p in self.pump_configuration:
                if ing==self.pump_configuration[p]['value']:
                    tme=qty*FLOW_RATE; maxt=max(maxt,tme)
                    t=threading.Thread(target=self.pour,args=(self.pump_configuration[p]['pin'],tme))
                    threads.append(t); t.start()
        print(f"[DEBUG] Started {len(threads)} pumps, maxt={maxt:.2f}s")
        self.progressBar(maxt)
        for t in threads: t.join()
        print("[DEBUG] Pumps done")
        self.menuContext.showMenu(); lt.do_run=False; lt.join(); self.lightsEndingSequence(); time.sleep(0.5); self.running=False
        print(f"[DEBUG] makeDrink({drink}) end")
        return True

    def run(self):
        print("[DEBUG] Bartender.run() start")
        print("Welcome to the Bartender CLI!")
        self.menuContext.showMenu()
        while True:
            print(f"[DEBUG] Loop start, running={self.running}")
            if self.running: time.sleep(0.2); continue
            print("Commands: n=next, s=select, q=quit")
            choice=input("Choice: ").strip().lower()
            print(f"[DEBUG] Input received: '{choice}'")
            if choice=='q': print("Exiting... Bye!"); break
            if choice=='n': print("[ACTION] Advancing"); self.menuContext.advance(); self.menuContext.showMenu(); continue
            if choice=='s': print("[ACTION] Selecting"); self.menuContext.select(); self.menuContext.showMenu(); continue
            print("Invalid, please try.")
        print("[DEBUG] Bartender.run() end")

if __name__=="__main__":
    print("[INFO] Starting Bartender program...")
    try:
        b=Bartender(); b.buildMenu(drink_list, drink_options); b.run()
    except Exception as e:
        print(f"[ERROR] {e}"); traceback.print_exc()
