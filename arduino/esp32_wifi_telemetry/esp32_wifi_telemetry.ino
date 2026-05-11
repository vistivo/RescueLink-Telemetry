#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Adafruit_MPU6050.h>

// ----------------------
// WiFi Access Point Info
// ----------------------
const char* ssid = "RescueLink_Telemetry";
const char* password = "rescuelink123";  // must be at least 8 characters

// ----------------------
// Sensor Objects
// ----------------------
Adafruit_BME280 bme;
Adafruit_MPU6050 mpu;

// ----------------------
// Web Server
// ----------------------
WebServer server(80);

// ----------------------
// Sensor status flags
// ----------------------
bool bmeFound = false;
bool mpuFound = false;

void handleRoot() {
  String html = "";
  html += "<html><body>";
  html += "<h1>RescueLink ESP32 Telemetry</h1>";
  html += "<p>Go to <a href='/data'>/data</a> for live sensor JSON.</p>";
  html += "</body></html>";

  server.send(200, "text/html", html);
}

void handleData() {
  float tempC = -999;
  float pressureHpa = -999;
  float humidityPct = -999;

  float ax = 0;
  float ay = 0;
  float az = 0;

  float gx = 0;
  float gy = 0;
  float gz = 0;

  if (bmeFound) {
    tempC = bme.readTemperature();
    pressureHpa = bme.readPressure() / 100.0F;
    humidityPct = bme.readHumidity();
  }

  if (mpuFound) {
    sensors_event_t accel, gyro, temp;
    mpu.getEvent(&accel, &gyro, &temp);

    ax = accel.acceleration.x;
    ay = accel.acceleration.y;
    az = accel.acceleration.z;

    gx = gyro.gyro.x;
    gy = gyro.gyro.y;
    gz = gyro.gyro.z;
  }

  String json = "{";
  json += "\"temp_c\":" + String(tempC, 2) + ",";
  json += "\"pressure_hpa\":" + String(pressureHpa, 2) + ",";
  json += "\"humidity_pct\":" + String(humidityPct, 2) + ",";
  json += "\"ax_mps2\":" + String(ax, 2) + ",";
  json += "\"ay_mps2\":" + String(ay, 2) + ",";
  json += "\"az_mps2\":" + String(az, 2) + ",";
  json += "\"gx_rads\":" + String(gx, 2) + ",";
  json += "\"gy_rads\":" + String(gy, 2) + ",";
  json += "\"gz_rads\":" + String(gz, 2) + ",";
  json += "\"bme_found\":" + String(bmeFound ? "true" : "false") + ",";
  json += "\"mpu_found\":" + String(mpuFound ? "true" : "false");
  json += "}";

  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("Starting RescueLink WiFi Telemetry...");

  // Start I2C on ESP32 pins
  Wire.begin(21, 22);

  // ----------------------
  // Initialize BME280
  // ----------------------
  bmeFound = bme.begin(0x76);

  if (!bmeFound) {
    bmeFound = bme.begin(0x77);
  }

  if (bmeFound) {
    Serial.println("BME280 found.");
  } else {
    Serial.println("BME280 NOT found.");
  }

  // ----------------------
  // Initialize MPU6050
  // ----------------------
  mpuFound = mpu.begin();

  if (mpuFound) {
    Serial.println("MPU6050 found.");

    mpu.setAccelerometerRange(MPU6050_RANGE_2_G);
    mpu.setGyroRange(MPU6050_RANGE_250_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  } else {
    Serial.println("MPU6050 NOT found.");
  }

  // ----------------------
  // Start ESP32 WiFi Network
  // ----------------------
  WiFi.softAP(ssid, password);

  IPAddress ip = WiFi.softAPIP();

  Serial.println("WiFi network started.");
  Serial.print("Network name: ");
  Serial.println(ssid);
  Serial.print("Password: ");
  Serial.println(password);
  Serial.print("ESP32 IP address: ");
  Serial.println(ip);

  // ----------------------
  // Web Routes
  // ----------------------
  server.on("/", handleRoot);
  server.on("/data", handleData);

  server.begin();

  Serial.println("Web server started.");
  Serial.println("Open browser to: http://192.168.4.1/data");
}

void loop() {
  server.handleClient();
}