#!/usr/bin/env python3
"""
Sequential-pump driver for a Raspberry Pi.

• Each pump is switched by a GPIO pin that drives a relay or MOSFET.
• The pumps have their **own** power supply; the Pi only sends the control signal.
• Uses BCM pin numbering (the numbers printed on most wiring diagrams).
"""

import time
import RPi.GPIO as GPIO

# ---------------------------------------------------------------------------
# 1) Declare your pumps in one easy-to-read dictionary
# ---------------------------------------------------------------------------
PUMPS = {
    "pump_1": {"name": "Pump 1", "pin": 17, "value": "gin"},
    "pump_2": {"name": "Pump 2", "pin": 27, "value": "tonic"},
    "pump_3": {"name": "Pump 3", "pin": 22, "value": None},
    "pump_4": {"name": "Pump 4", "pin": 23, "value": None},
    "pump_5": {"name": "Pump 5", "pin": 24, "value": None},
    "pump_6": {"name": "Pump 6", "pin": 25, "value": None},
}

RUNTIME_SECONDS = 30           # How long to run each pump
ACTIVE_STATE     = GPIO.HIGH   # Change to GPIO.LOW if your relay is active-low

# ---------------------------------------------------------------------------
# 2) Basic GPIO setup
# ---------------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)         # Use BCM numbering (17, 27, …)
GPIO.setwarnings(False)

for pump in PUMPS.values():
    GPIO.setup(pump["pin"], GPIO.OUT, initial=GPIO.LOW)

print("Starting pump test – each pump will run for "
      f"{RUNTIME_SECONDS} s, one at a time.\n"
      "Press Ctrl-C to abort.\n")

# ---------------------------------------------------------------------------
# 3) Main loop: run each pump once
# ---------------------------------------------------------------------------
try:
    for key, pump in PUMPS.items():
        name = pump["name"]
        pin  = pump["pin"]

        print(f"[{name}] ON  (GPIO {pin})")
        GPIO.output(pin, ACTIVE_STATE)     # Turn pump on
        time.sleep(RUNTIME_SECONDS)
        GPIO.output(pin, not ACTIVE_STATE) # Turn pump off
        print(f"[{name}] OFF\n")

    print("All pumps have completed their 30-second run.")

except KeyboardInterrupt:
    print("\nUser interrupted – shutting everything down.")

finally:
    # -----------------------------------------------------------------------
    # 4) Always clean up the GPIO pins on exit
    # -----------------------------------------------------------------------
    GPIO.cleanup()
    print("GPIO cleanup done. Goodbye!")
