import time
import sys
import json
import threading
import traceback
import RPi.GPIO as GPIO

from drinks import drink_list

FLOW_RATE = 60.0 / 100.0   # seconds per mL

with open('pump_config.json', 'r') as f:
    pump_configuration = json.load(f)

# --- REQUIRED GPIO INITIALISATION ---
GPIO.setmode(GPIO.BCM)      # use BCM pin numbers (matches pump_config.json)
GPIO.setwarnings(False)     # optional: silences re-use warnings

# --------------------------------------------------------------------------
def pour(pin, wait_time):
    GPIO.output(pin, GPIO.LOW)    # relay ON
    time.sleep(wait_time)
    GPIO.output(pin, GPIO.HIGH)   # relay OFF


def display(text):
    print(text)


def start_up():
    display("Welcome To The Bartender!")
    display("Press Ctrl+C to exit")
    display("Select Your Drinks And Have An Automatic Brew")

    for pump in pump_configuration.keys():
        GPIO.setup(
            pump_configuration[pump]["pin"],
            GPIO.OUT,
            initial=GPIO.HIGH          # pumps start OFF (active-low wiring)
        )


def select_options():
    display("Select Your Drink:")
    for i, drink in enumerate(drink_list):
        display(f"{i + 1}. {drink['name']}")
    display("0. Exit")

    try:
        choice = int(input("Enter your choice: "))
        if choice == 0:
            display("Exiting…")
            clean_up()
            sys.exit()
        elif 1 <= choice <= len(drink_list):
            selected_drink = drink_list[choice - 1]
            pour_drink(selected_drink)
        else:
            display("Invalid choice. Please try again.")
    except ValueError:
        display("Invalid input. Please enter a number.")


def pour_drink(drink):
    display(f"Pouring {drink['name']}…")
    for ingredient, amount in drink['ingredients'].items():
        for pump in pump_configuration.keys():
            if ingredient == pump_configuration[pump]['value']:
                wait_time = amount * FLOW_RATE
                pour(pump_configuration[pump]['pin'], wait_time)
                display(f"Poured {amount} mL of {ingredient}")
    display(f"{drink['name']} is ready!")


def clean_up():
    GPIO.cleanup()
    display("Cleaned up GPIO pins.")


# --------------------------------------------------------------------------
def main():
    start_up()
    try:
        while True:
            select_options()
            print("-" * 35)
    except KeyboardInterrupt:
        pass
    finally:
        clean_up()


if __name__ == "__main__":
    main()
