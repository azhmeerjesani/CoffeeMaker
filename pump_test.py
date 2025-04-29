#!/usr/bin/env python3
"""
One-at-a-time pump driver for a Raspberry Pi.

Key points
----------
• Each pump is driven through a relay/MOSFET that has its *own* power supply;
  the Pi only provides a 3 V logic signal.
• The script uses BCM numbering (17, 27, 22, …).
• Safety: the helper `stop_all_pumps()` is called **before** and **after** every
  pump cycle so a stray HIGH on any pin is immediately cleared.
"""

import time
import RPi.GPIO as GPIO

# ---------------------------------------------------------------------------
# 1) Configure your pumps in one place
# ---------------------------------------------------------------------------
PUMPS = {
    "pump_1": {"name": "Pump 1", "pin": 17, "value": "gin"},
    "pump_2": {"name": "Pump 2", "pin": 27, "value": "tonic"},
    "pump_3": {"name": "Pump 3", "pin": 22, "value": None},
    "pump_4": {"name": "Pump 4", "pin": 23, "value": None},
    "pump_5": {"name": "Pump 5", "pin": 24, "value": None},
    "pump_6": {"name": "Pump 6", "pin": 25, "value": None},
}

RUNTIME_SECONDS   = 30          # Time each pump stays ON
ACTIVE_STATE      = GPIO.HIGH   # Flip to GPIO.LOW if your relay is active-low
INTER_PUMP_PAUSE  = 0.3         # Pause (s) after cutting power before next ON

# ---------------------------------------------------------------------------
# 2) Basic GPIO setup
# ---------------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pump in PUMPS.values():
    GPIO.setup(pump["pin"], GPIO.OUT, initial=GPIO.LOW)

def stop_all_pumps() -> None:
    """Force every pump pin LOW."""
    for pump in PUMPS.values():
        GPIO.output(pump["pin"], GPIO.LOW)

print(
    "Running one-pump-at-a-time test – each pump will run for "
    f"{RUNTIME_SECONDS} s.\nPress Ctrl-C to abort.\n"
)

# ---------------------------------------------------------------------------
# 3) Main loop
# ---------------------------------------------------------------------------
try:
    for key, pump in PUMPS.items():
        name, pin = pump["name"], pump["pin"]

        # --- Safety first: be sure
