import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation
from matplotlib import rcParams
from collections import deque
import numpy as np
import json
from urllib.request import urlopen
from urllib.error import URLError
import csv
import os
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
DATA_URL = "http://192.168.4.1/data"
MAX_POINTS = 100
UPDATE_INTERVAL_MS = 500

# ─────────────────────────────────────────────
#  CSV LOGGING SETUP
# ─────────────────────────────────────────────
record_choice = input("Record this telemetry session to CSV? (y/n): ").strip().lower()
logging_enabled = record_choice == "y"

csv_file = None
csv_writer = None
log_filename = None

if logging_enabled:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    timestamp_for_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(logs_dir, f"telemetry_{timestamp_for_filename}.csv")

    csv_file = open(log_filename, mode="w", newline="")
    csv_writer = csv.writer(csv_file)

    csv_writer.writerow([
        "timestamp",
        "sample",
        "temp_c",
        "temp_f",
        "pressure_hpa",
        "humidity_pct",
        "ax_mps2",
        "ay_mps2",
        "az_mps2",
        "gx_rads",
        "gy_rads",
        "gz_rads",
        "bme_found",
        "mpu_found"
    ])

    print(f"CSV logging enabled.")
    print(f"Saving data to: {log_filename}")
else:
    print("CSV logging disabled. Dashboard will run without recording.")

# ─────────────────────────────────────────────
#  GLOBAL THEME
# ─────────────────────────────────────────────
BG_COLOR    = '#0A0E17'
PANEL_COLOR = '#111827'
GRID_COLOR  = '#1E293B'
TICK_COLOR  = '#64748B'
TEXT_COLOR  = '#CBD5E1'
TITLE_COLOR = '#F1F5F9'

PALETTE = {
    'temp':     '#FF6B6B',
    'pressure': '#FFB347',
    'humidity': '#4ECDC4',
    'accel_x':  '#60A5FA',
    'accel_y':  '#A78BFA',
    'accel_z':  '#34D399',
}

rcParams.update({
    'figure.facecolor':  BG_COLOR,
    'axes.facecolor':    PANEL_COLOR,
    'axes.edgecolor':    GRID_COLOR,
    'axes.labelcolor':   TEXT_COLOR,
    'xtick.color':       TICK_COLOR,
    'ytick.color':       TICK_COLOR,
    'xtick.labelsize':   8,
    'ytick.labelsize':   8,
    'text.color':        TEXT_COLOR,
    'font.family':       'monospace',
    'legend.framealpha': 0.0,
    'legend.labelcolor': TEXT_COLOR,
    'legend.fontsize':   8,
})

# ─────────────────────────────────────────────
#  DATA BUFFERS
# ─────────────────────────────────────────────
x_data        = deque(maxlen=MAX_POINTS)
temp_f_data   = deque(maxlen=MAX_POINTS)
pressure_data = deque(maxlen=MAX_POINTS)
humidity_data = deque(maxlen=MAX_POINTS)
ax_data       = deque(maxlen=MAX_POINTS)
ay_data       = deque(maxlen=MAX_POINTS)
az_data       = deque(maxlen=MAX_POINTS)

count = 0
latest = {}

# ─────────────────────────────────────────────
#  FIGURE LAYOUT
# ─────────────────────────────────────────────
fig = plt.figure(figsize=(14, 10), dpi=110)
fig.patch.set_facecolor(BG_COLOR)

fig.text(
    0.5, 0.975, 'LIVE WIRELESS SENSOR TELEMETRY',
    ha='center', va='top',
    fontsize=15, fontweight='bold',
    color=TITLE_COLOR, fontfamily='monospace'
)

subtitle = "ESP32 WiFi · BME280 · MPU6050"
if logging_enabled:
    subtitle += " · CSV LOGGING ON"
else:
    subtitle += " · CSV LOGGING OFF"

fig.text(
    0.5, 0.945, subtitle,
    ha='center', va='top',
    fontsize=8, color=TICK_COLOR, fontfamily='monospace'
)

status_text = fig.text(
    0.92, 0.975, '● CONNECTING',
    ha='right', va='top',
    fontsize=9, color='#FACC15', fontfamily='monospace'
)

gs = gridspec.GridSpec(
    4, 2,
    figure=fig,
    top=0.88, bottom=0.07,
    left=0.07, right=0.97,
    hspace=0.55, wspace=0.35
)

ax_temp  = fig.add_subplot(gs[0, 0])
ax_press = fig.add_subplot(gs[1, 0])
ax_hum   = fig.add_subplot(gs[2, 0])
ax_accel = fig.add_subplot(gs[0:3, 1])
ax_info  = fig.add_subplot(gs[3, :])


def style_axis(ax, title, unit, color, title_y=1.05):
    ax.set_facecolor(PANEL_COLOR)

    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)

    ax.tick_params(colors=TICK_COLOR, length=3)
    ax.grid(True, color=GRID_COLOR, linewidth=0.6, linestyle='--', alpha=0.7)
    ax.set_ylabel(unit, fontsize=8, color=TEXT_COLOR)

    ax.text(
        0.01, title_y, title,
        transform=ax.transAxes,
        fontsize=9, fontweight='bold',
        color=color, va='bottom',
        fontfamily='monospace'
    )


def fill_under(ax, x, y, color, alpha=0.12):
    if len(x) > 1:
        ax.fill_between(x, y, alpha=alpha, color=color)


def make_status_bar(ax, latest_values):
    ax.set_facecolor(BG_COLOR)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_xticks([])
    ax.set_yticks([])

    log_status = "ON" if logging_enabled else "OFF"

    labels = [
        ('TEMP',     f"{latest_values.get('temp', 0):.1f} °F",        PALETTE['temp']),
        ('PRESSURE', f"{latest_values.get('pressure', 0):.1f} hPa",   PALETTE['pressure']),
        ('HUMIDITY', f"{latest_values.get('humidity', 0):.1f} %",     PALETTE['humidity']),
        ('ACCEL X',  f"{latest_values.get('ax', 0):+.3f}",            PALETTE['accel_x']),
        ('ACCEL Y',  f"{latest_values.get('ay', 0):+.3f}",            PALETTE['accel_y']),
        ('ACCEL Z',  f"{latest_values.get('az', 0):+.3f}",            PALETTE['accel_z']),
        ('SAMPLES',  str(latest_values.get('count', 0)),              TICK_COLOR),
        ('LOGGING',  log_status,                                      '#22C55E' if logging_enabled else '#EF4444'),
    ]

    xs = np.linspace(0.02, 0.98, len(labels))

    for x, (lbl, val, col) in zip(xs, labels):
        ax.text(
            x, 0.75, lbl,
            ha='center', fontsize=7, color=TICK_COLOR,
            fontfamily='monospace', transform=ax.transAxes
        )
        ax.text(
            x, 0.20, val,
            ha='center', fontsize=11, color=col,
            fontfamily='monospace', fontweight='bold',
            transform=ax.transAxes
        )


def read_esp32_json():
    """
    Reads one JSON packet from the ESP32 web server.
    Expected ESP32 URL:
    http://192.168.4.1/data
    """
    with urlopen(DATA_URL, timeout=2) as response:
        raw_data = response.read().decode("utf-8")
        return json.loads(raw_data)


def write_csv_row(
    sample,
    temp_c,
    temp_f,
    pressure,
    humidity,
    accel_x,
    accel_y,
    accel_z,
    gyro_x,
    gyro_y,
    gyro_z,
    bme_found,
    mpu_found
):
    """
    Writes one sensor reading to the CSV file if logging is enabled.
    """
    if not logging_enabled or csv_writer is None:
        return

    timestamp_now = datetime.now().isoformat(timespec="seconds")

    csv_writer.writerow([
        timestamp_now,
        sample,
        temp_c,
        temp_f,
        pressure,
        humidity,
        accel_x,
        accel_y,
        accel_z,
        gyro_x,
        gyro_y,
        gyro_z,
        bme_found,
        mpu_found
    ])

    # Forces data to actually save to disk during the session
    csv_file.flush()


def update(_frame):
    global count

    try:
        data = read_esp32_json()
    except (URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        print("Network read error:", e)
        status_text.set_text("● DISCONNECTED")
        status_text.set_color("#EF4444")
        return

    print(data)

    # Check sensor health flags from ESP32
    bme_found = data.get("bme_found", False)
    mpu_found = data.get("mpu_found", False)

    if not bme_found or not mpu_found:
        status_text.set_text("● SENSOR ERROR")
        status_text.set_color("#F97316")
        return

    try:
        temp_c   = float(data["temp_c"])
        pressure = float(data["pressure_hpa"])
        humidity = float(data["humidity_pct"])

        accel_x  = float(data["ax_mps2"])
        accel_y  = float(data["ay_mps2"])
        accel_z  = float(data["az_mps2"])

        gyro_x   = float(data.get("gx_rads", 0.0))
        gyro_y   = float(data.get("gy_rads", 0.0))
        gyro_z   = float(data.get("gz_rads", 0.0))

    except (KeyError, ValueError, TypeError) as e:
        print("Bad data format:", e)
        status_text.set_text("● BAD DATA")
        status_text.set_color("#F97316")
        return

    temp_f = (temp_c * 9 / 5) + 32

    x_data.append(count)
    temp_f_data.append(temp_f)
    pressure_data.append(pressure)
    humidity_data.append(humidity)
    ax_data.append(accel_x)
    ay_data.append(accel_y)
    az_data.append(accel_z)

    # Save this reading before count changes
    write_csv_row(
        sample=count,
        temp_c=temp_c,
        temp_f=temp_f,
        pressure=pressure,
        humidity=humidity,
        accel_x=accel_x,
        accel_y=accel_y,
        accel_z=accel_z,
        gyro_x=gyro_x,
        gyro_y=gyro_y,
        gyro_z=gyro_z,
        bme_found=bme_found,
        mpu_found=mpu_found
    )

    count += 1

    latest.update(dict(
        temp=temp_f,
        pressure=pressure,
        humidity=humidity,
        ax=accel_x,
        ay=accel_y,
        az=accel_z,
        count=count
    ))

    status_text.set_text("● LIVE")
    status_text.set_color("#22C55E")

    xd = list(x_data)

    ax_temp.clear()
    ax_press.clear()
    ax_hum.clear()
    ax_accel.clear()

    # Temperature
    ax_temp.plot(xd, list(temp_f_data), color=PALETTE['temp'], linewidth=1.6)
    fill_under(ax_temp, xd, list(temp_f_data), PALETTE['temp'])
    style_axis(ax_temp, 'TEMPERATURE', '°F', PALETTE['temp'])

    # Pressure
    ax_press.plot(xd, list(pressure_data), color=PALETTE['pressure'], linewidth=1.6)
    fill_under(ax_press, xd, list(pressure_data), PALETTE['pressure'])
    style_axis(ax_press, 'PRESSURE', 'hPa', PALETTE['pressure'])

    # Humidity
    ax_hum.plot(xd, list(humidity_data), color=PALETTE['humidity'], linewidth=1.6)
    fill_under(ax_hum, xd, list(humidity_data), PALETTE['humidity'])
    style_axis(ax_hum, 'HUMIDITY', '%', PALETTE['humidity'])
    ax_hum.set_xlabel('Sample #', fontsize=8, color=TICK_COLOR)

    # Acceleration
    ax_accel.plot(xd, list(ax_data), color=PALETTE['accel_x'], linewidth=1.4, label='X-axis')
    ax_accel.plot(xd, list(ay_data), color=PALETTE['accel_y'], linewidth=1.4, label='Y-axis')
    ax_accel.plot(xd, list(az_data), color=PALETTE['accel_z'], linewidth=1.4, label='Z-axis')

    ax_accel.axhline(0, color=GRID_COLOR, linewidth=0.8, linestyle='--')
    style_axis(ax_accel, 'ACCELEROMETER', 'm/s²', PALETTE['accel_x'], title_y=1.0125)
    ax_accel.legend(loc='upper right')
    ax_accel.set_xlabel('Sample #', fontsize=8, color=TICK_COLOR)

    # Status bar
    ax_info.clear()
    make_status_bar(ax_info, latest)

    fig.canvas.draw_idle()


print("Starting wireless live graph...")
print("Make sure your laptop is connected to the ESP32 WiFi network:")
print("Network: RescueLink_Telemetry")
print("URL:", DATA_URL)
print("Close the graph window or press Ctrl+C in the terminal to stop.")

ani = FuncAnimation(fig, update, interval=UPDATE_INTERVAL_MS, cache_frame_data=False)

try:
    plt.show()
except KeyboardInterrupt:
    print("Stopping program...")

finally:
    if csv_file is not None:
        csv_file.close()
        print(f"CSV log saved to: {log_filename}")

print("Program ended.")