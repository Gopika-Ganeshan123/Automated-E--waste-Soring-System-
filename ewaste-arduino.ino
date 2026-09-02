#include <WiFi.h>
#include <Firebase_ESP_Client.h>
#include <ESP32Servo.h>
#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"

#define WIFI_SSID "WiFi1"
#define WIFI_PASSWORD "987654321"
#define API_KEY "AIzaSyArvfpZW4sbErL6WRGgXs4z1tXp2x8spEM"
#define DATABASE_URL "https://ewaste-sorting-system-default-rtdb.asia-southeast1.firebasedatabase.app/"

FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;


Servo servo1;
Servo servo2;

#define SERVO1_PIN 27
#define SERVO2_PIN 26
#define SENSOR_PIN 34

#define SERVO1_INIT 90
#define SERVO2_INIT 0
#define SERVO_STEP_DELAY 15

int servo1Pos = SERVO1_INIT;
int servo2Pos = SERVO2_INIT;

// BIN 1
#define BIN1_TRIG 14
#define BIN1_ECHO 35

// BIN 2
#define BIN2_TRIG 12
#define BIN2_ECHO 32

// BIN 3
#define BIN3_TRIG 13
#define BIN3_ECHO 33

void moveServoSmooth(Servo &servo, int &currentPos, int targetPos) {
  if (currentPos < targetPos) {
    for (int pos = currentPos; pos <= targetPos; pos++) {
      servo.write(pos);
      delay(SERVO_STEP_DELAY);
    }
  } else {
    for (int pos = currentPos; pos >= targetPos; pos--) {
      servo.write(pos);
      delay(SERVO_STEP_DELAY);
    }
  }
  currentPos = targetPos;
}


float readUltrasonic(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);
  if (duration == 0) return -1;

  float distance = duration * 0.034 / 2;
  return distance;
}

void updateBinDistances() {
  float bin1 = readUltrasonic(BIN1_TRIG, BIN1_ECHO);
  float bin2 = readUltrasonic(BIN2_TRIG, BIN2_ECHO);
  float bin3 = readUltrasonic(BIN3_TRIG, BIN3_ECHO);

  Serial.println("Bin Distances:");
  Serial.printf("Bin1: %.2f cm | Bin2: %.2f cm | Bin3: %.2f cm\n", bin1, bin2, bin3);

  Firebase.RTDB.setFloat(&fbdo, "/bins/bin1_distance", bin1);
  Firebase.RTDB.setFloat(&fbdo, "/bins/bin2_distance", bin2);
  Firebase.RTDB.setFloat(&fbdo, "/bins/bin3_distance", bin3);
}


void setup() {
  Serial.begin(115200);

  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);

  moveServoSmooth(servo1, servo1Pos, SERVO1_INIT);
  moveServoSmooth(servo2, servo2Pos, SERVO2_INIT);

  pinMode(BIN1_TRIG, OUTPUT);
  pinMode(BIN1_ECHO, INPUT);
  pinMode(BIN2_TRIG, OUTPUT);
  pinMode(BIN2_ECHO, INPUT);
  pinMode(BIN3_TRIG, OUTPUT);
  pinMode(BIN3_ECHO, INPUT);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected");

  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;

  Firebase.signUp(&config, &auth, "", "");
  config.token_status_callback = tokenStatusCallback;

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
}

/* ================= LOOP ================= */
void loop() {

  if (Firebase.RTDB.getString(&fbdo, "/latest/label")) {

    String label = fbdo.stringData();
    Firebase.RTDB.getBool(&fbdo, "/latest/consumed");
    bool consumed = fbdo.boolData();

    if (!consumed) {
      if (label == "NON E-WASTE") handleNonEWaste();
      else if (label == "E-WASTE") handleEWaste();

      Firebase.RTDB.setBool(&fbdo, "/latest/consumed", true);
    }
  }

 
  updateBinDistances();

  delay(3000);
}


void handleNonEWaste() {
  moveServoSmooth(servo1, servo1Pos, 90);
  delay(500);
  moveServoSmooth(servo2, servo2Pos, 180);
  delay(5000);
  resetServos();
}

void handleEWaste() {
  int sensorValue = analogRead(SENSOR_PIN);

  if (sensorValue == 0) moveServoSmooth(servo1, servo1Pos, 0);
  else if (sensorValue == 4095) moveServoSmooth(servo1, servo1Pos, 180);

  delay(500);
  moveServoSmooth(servo2, servo2Pos, 180);
  delay(5000);
  resetServos();
}

void resetServos() {
  moveServoSmooth(servo2, servo2Pos, SERVO2_INIT);
  delay(500);
  moveServoSmooth(servo1, servo1Pos, SERVO1_INIT);
}
