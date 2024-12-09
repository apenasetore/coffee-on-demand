import time
from hx711 import HX711  # Make sure you have installed and imported the HX711 library

# Pin configuration for Raspberry Pi 4
DT = 5  # Data pin (Pin 11 on Raspberry Pi GPIO)
SCK = 27  # Clock pin (Pin 13 on Raspberry Pi GPIO)

# Initialize the HX711
hx = HX711(DT, SCK)

def clean_and_exit():
    print("Cleaning up...")
    hx.power_down()
    hx.power_up()
    exit()

def calibrate():
    print("Starting calibration...")
    try:
        # Tare the scale to zero
        print("Taring the scale. Remove any weight from the scale.")
        time.sleep(2)
        hx.set_reading_format("MSB", "MSB")
        hx.tare()
        print("Scale tared.")

        # Ask for a known weight
        input("Place a known weight on the scale and press Enter.")
        time.sleep(2)

        # Read raw data
        raw_value = hx.get_average_reading()
        print(f"Raw value from HX711: {raw_value}")

        # Ask for the known weight value
        known_weight = float(input("Enter the weight value (in your preferred unit): "))

        # Calculate scale factor
        scale_factor = raw_value / known_weight
        print(f"Calculated scale factor: {scale_factor}")

        # Set scale factor
        hx.set_scale(scale_factor)
        print("Calibration complete.")

        # Test the calibration
        input("Remove the weight and press Enter to test the tare.")
        hx.tare()
        print("Tare value after calibration:", hx.get_weight(5))

        input("Place the known weight again to verify calibration.")
        weight = hx.get_weight(5)
        print(f"Measured weight: {weight} (expected: {known_weight})")

    except Exception as e:
        print(f"Error: {e}")
        clean_and_exit()

if __name__ == "__main__":
    try:
        calibrate()
    except (KeyboardInterrupt, SystemExit):
        clean_and_exit()
