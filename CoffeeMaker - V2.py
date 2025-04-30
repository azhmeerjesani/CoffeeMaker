import time
import sys
import json
import threading
import traceback
import RPi.GPIO as GPIO

FLOW_RATE = 60.0/100.0

with open('pump_config.json', 'r') as f:
    pump_configuration = json.load(f)

# print(pump_configuration['pump_1']['name']) # Example output: "Pump 1"

def pour(pin, waitTime):
    GPIO.output(pin, GPIO.LOW)   # energise relay / open MOSFET
    time.sleep(waitTime)         # keep it on for N seconds
    GPIO.output(pin, GPIO.HIGH)  # de-energise relay / close MOSFET


while True:



