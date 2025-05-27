# --- Import required modules ---
from machine import Pin, SPI, ADC
import time
import os
import sdcard

# --- Initialize ECG Sensor on ADC pin ---
ecg = ADC(26)  # ADC0 (GPIO26) is used for ECG analog input

# --- Setup SPI and SD card interface ---
# SPI0: SCK=GP2, MOSI=GP3, MISO=GP4
spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cs = Pin(5, Pin.OUT)  # Chip Select (CS) for SD card module

# --- Try to mount the SD card safely ---
try:
    os.umount("/sd")
except OSError:
    pass  # If not mounted yet, continue

try:
    sd = sdcard.SDCard(spi, cs)
    vfs = os.VfsFat(sd)
    os.mount(vfs, "/sd")
    print("SD card mounted successfully.")
except OSError as e:
    print("Failed to mount SD card:", e)
    raise SystemExit  # Stop the program if mount fails

# --- Test write to ensure functionality ---
try:
    with open("/sd/test.txt", "w") as testfile:
        testfile.write("SD card test successful.\n")
except Exception as e:
    print("Failed to write to SD card:", e)
    raise SystemExit

# --- File Handling Parameters ---
file_interval = 5 * 60  # 5 minutes (in seconds)
samples_per_second = 100
sample_interval = 1 / samples_per_second
last_file_time = time.time()

# --- Function to generate a dashcam-style filename ---
def get_filename():
    t = time.localtime()
    return "/sd/ECG_{:02d}{:02d}{:02d}_{:02d}{:02d}.csv".format(
        t[0] % 100, t[1], t[2], t[3], t[4]
    )

# --- Start ECG Logging ---
filename = get_filename()
logfile = open(filename, "w")
logfile.write("Timestamp_ms,ECG_Value\n")

print("📈 Starting ECG recording...")

try:
    while True:
        # Rotate file every 5 minutes
        if time.time() - last_file_time >= file_interval:
            logfile.close()
            filename = get_filename()
            logfile = open(filename, "w")
            logfile.write("Timestamp_ms,ECG_Value\n")
            last_file_time = time.time()

        # Read ECG value and log with timestamp
        timestamp = time.ticks_ms()
        ecg_value = ecg.read_u16()  # 16-bit ADC value (0–65535)
        logfile.write("{},{}\n".format(timestamp, ecg_value))
        logfile.flush()  # Force write immediately

        time.sleep(sample_interval)

except KeyboardInterrupt:
    logfile.close()
    print("Logging stopped by user.")
