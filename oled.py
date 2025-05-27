#OLED DISPLAY
# --- Import required modules ---
from machine import Pin, ADC, I2C, UART  # GPIO, analog input, I2C for OLED, UART for BLE
from OLED import SSD1306_I2C             # OLED display driver (make sure OLED.py is in your project)
from time import sleep, ticks_ms, ticks_diff  # Sleep and millisecond timing functions

# --- Initialize OLED Display ---
i2c = I2C(0, scl=Pin(13), sda=Pin(12))           # Set up I2C using GPIO13 (SCL) and GPIO12 (SDA)
oled = SSD1306_I2C(128, 64, i2c)                 # Create OLED object for 128x64 screen

# --- Initialize ECG Analog Input and BLE UART ---
ecg = ADC(Pin(26))                               # ECG analog signal input on GP26 (ADC0)
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))  # BLE module (e.g., HM-10) on UART0

# --- Configuration thresholds ---
THRESHOLD = 30000          # ADC value threshold for detecting ECG peaks (tune this!)
MIN_RR_INTERVAL_MS = 300   # Minimum interval between heartbeats (to avoid noise)
MAX_RR_INTERVAL_MS = 2000  # Maximum interval (exclude too slow signals)

# --- Variables for tracking heart rate ---
last_peak_time = 0         # Timestamp of last detected ECG peak
bpm = 0                    # Beats per minute (heart rate)
stress_level = "Normal"    # Stress level category

# --- Function: Update OLED Display ---
def display_data(hr, stress):
    oled.fill(0)  # Clear the display buffer
    oled.text("HR: {} BPM".format(hr), 0, 0)       # Line 1: Heart rate
    oled.text("Stress: {}".format(stress), 0, 10)  # Line 2: Stress estimate
    oled.text("Sending via BLE", 0, 20)            # Line 3: Status
    oled.show()  # Push buffer to OLED screen

# --- Function: Estimate stress level from BPM ---
def estimate_stress(bpm):
    if bpm < 60:
        return "Relaxed"
    elif bpm < 100:
        return "Normal"
    else:
        return "High"

# --- Main Loop ---
while True:
    value = ecg.read_u16()  # Read ECG signal (0–65535 range from 16-bit ADC)
    now = ticks_ms()        # Current timestamp in milliseconds

    # --- Simple ECG peak detection ---
    if value > THRESHOLD and ticks_diff(now, last_peak_time) > MIN_RR_INTERVAL_MS:
        rr_interval = ticks_diff(now, last_peak_time)  # Time between peaks
        last_peak_time = now                           # Update last peak time

        if rr_interval < MAX_RR_INTERVAL_MS:
            bpm = int(60000 / rr_interval)             # Calculate heart rate from RR interval
            stress_level = estimate_stress(bpm)        # Estimate stress based on HR

            display_data(bpm, stress_level)            # Show on OLED

            # Send data over BLE
            data = "HR:{} BPM | Stress: {}\n".format(bpm, stress_level)
            uart.write(data)

    sleep(0.01)  # Short delay to control sampling frequency (~100Hz)
