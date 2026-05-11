# RescueLink Telemetry

RescueLink Telemetry is a wireless sensor telemetry prototype built with an ESP32, BME280 environmental sensor, MPU6050 IMU, and a Python dashboard.

The ESP32 reads environmental and motion data, creates a local WiFi network, and serves the latest sensor readings as JSON. The Python dashboard connects to the ESP32 over WiFi, graphs the live data, and can save telemetry sessions to CSV logs.

## Current Features

- ESP32 WiFi access point
- JSON telemetry endpoint at `http://192.168.4.1/data`
- BME280 temperature, pressure, and humidity readings
- MPU6050 acceleration and gyroscope readings
- Python live dashboard
- CSV logging option for test sessions
- Basic sensor health indicators

## System Architecture

Sensors → ESP32 → WiFi → Python Dashboard → Live Graphs + CSV Logs

## Hardware

- ESP32 development board
- BME280 environmental sensor
- MPU6050 IMU
- Breadboard and jumper wires
- USB power source

## Wiring

Both sensors use I2C.

ESP32 to BME280:

- 3V3 → VCC
- GND → GND
- GPIO 21 → SDA
- GPIO 22 → SCL

ESP32 to MPU6050:

- 3V3 → VCC
- GND → GND
- GPIO 21 → SDA
- GPIO 22 → SCL

## Running the ESP32 Code

1. Open the Arduino sketch in Arduino IDE.
2. Select the ESP32 board and correct COM port.
3. Upload the sketch.
4. The ESP32 creates a WiFi network called `RescueLink_Telemetry`.
5. Connect the laptop to that WiFi network.
6. Open `http://192.168.4.1/data` to verify the JSON telemetry output.

## Running the Python Dashboard

1. Connect the laptop to the `RescueLink_Telemetry` WiFi network.
2. Open the `python-dashboard` folder.
3. Run:

```bash
python sensor_plot.py
```

4. Choose whether to record the session to CSV.
5. The dashboard will show live telemetry graphs.
6. If logging is enabled, a CSV file will be saved inside the `python-dashboard/logs` folder.

## Project Folder Structure

```text
RescueLink-Telemetry
├── arduino
│   └── esp32_wifi_telemetry
│       └── esp32_wifi_telemetry.ino
├── python-dashboard
│   ├── sensor_plot.py
│   └── logs
├── docs
│   ├── screenshots
│   └── notes
├── sample-data
├── README.md
└── .gitignore
```

## Project Status

Phase 1 is complete: basic telemetry pipeline and live dashboard.

Phase 2 is in progress: wireless telemetry, CSV logging, documentation, and reliability improvements.

Completed so far:

- Wired ESP32 telemetry
- Wireless ESP32 telemetry using WiFi
- Python live dashboard
- CSV logging
- Sensor health/status indicators

Next steps:

- Add better documentation
- Save screenshots of the dashboard
- Add a system diagram
- Improve project organization
- Eventually test portable power and drone-related use cases

## Long-Term Goal

The long-term goal is to expand this into RescueLink: a modular UAV mission system for search-and-rescue telemetry, mission monitoring, and situational awareness.