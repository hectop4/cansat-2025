
#include <Arduino.h>
#include <Wire.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_BMP085.h>
#include <ESP32Servo.h>

#include <MQUnifiedsensor.h>
#include <string.h>
#define esp32_sample_rate 4096

unsigned long previousMillis = 0;
const long interval = 2000;
// I2C Pins
#define SDA 2
#define SCL 42
// Servomotor
#define Servomotor 41
// GPS Pins
#define GPSRX 47
#define GPSTX 21
#define GPS_BAUD 9600
// Lora RYLR998
#define LORARX 36
#define LORATX 37

// Air Quality Sensor Definitions
#define placa "ESP-32"
#define Voltage_Resolution 3.3
#define pin 1
#define type "MQ-135"
#define ADC_Bit_Resolution 12
#define RatioMQ135CleanAir 3.6 // RS / R0 = 3.6 ppm

// Initialize the sensors
Adafruit_MPU6050 mpu;
Adafruit_BMP085 bmp;
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);
Servo myservo;
MQUnifiedsensor MQ135(placa, Voltage_Resolution, ADC_Bit_Resolution, pin, type);
SoftwareSerial ReyaxLoRa(LORARX, LORATX); //--> RX, TX

// Variables
int ppm = 0;
int pressure = 0;
float temperature = 0;
int altitude = 0;
float latitude = 5.544513;
float longitude =  -73.364981;
float height_limit = 200;
float accx = 0;
float accy = 0;
float accz = 0;
float gyx = 0;
float gyy = 0;
float gyz = 0;

String message = "";
int msg_len = 0;
int height_init;

void setup()
{
  // Init the serial port communication - to debug the library
  Serial.begin(115200);
  // Init the LoRa module
  ReyaxLoRa.begin(115200);
  Serial.println("LoRa: OK");
  // Init Servomotor
  myservo.attach(Servomotor);
  myservo.write(0);
  Serial.println("Servomotor: OK");

  // Init GPS
  // Start Serial 2 with the defined RX and TX pins and a baud rate of 9600
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, GPSRX, GPSTX);
  Serial.println("GPS: OK");

  // Init BMP and MPU
  Wire.begin(SDA, SCL);
  if (!mpu.begin())
  {
    Serial.println("MPU: FAILED");
    while (1)
    {
      delay(10);
    }
  }
  Serial.println("MPU6050: OK");
  delay(500);
  if (!bmp.begin())
  {
    Serial.println("BMP: FAILED");
    while (1)
    {
      delay(10);
    }
  }

  Serial.println("BMP180: OK");
  delay(500);

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  Serial.println("Accelerometer range set to: +-8G");

  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  Serial.println("Gyro range set to: +- 500 deg/s");

  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.println("Filter bandwidth set to: 21 Hz");

  // Init MQ135
  // Set math model to calculate the PPM concentration and the value of constants
  MQ135.setRegressionMethod(1); //_PPM =  a*ratio^b
  MQ135.setA(110.47);
  MQ135.setB(-2.862); // Configure the equation to to calculate CO2 concentration

  /*
    Exponential regression:
  GAS      | a      | b
  CO       | 605.18 | -3.937
  Alcohol  | 77.255 | -3.18
  !CO2      | 110.47 | -2.862
  Toluen  | 44.947 | -3.445
  NH4      | 102.2  | -2.473
  Aceton  | 34.668 | -3.369
  */

  /*****************************  MQ Init ********************************************/
  // Remarks: Configure the pin of arduino as input.
  /************************************************************************************/
  MQ135.init();
  /*****************************  MQ CAlibration ********************************************/
  Serial.println("Calibrating MQ135 please wait.");
  float calcR0 = 0;
  for (int i = 1; i <= 10; i++)
  {
    MQ135.update();
    calcR0 += MQ135.calibrate(RatioMQ135CleanAir);
    Serial.print(".");
  }
  MQ135.setR0(calcR0 / 10);
  Serial.println("  done!.");

  if (isinf(calcR0))
  {
    Serial.println("MQ135 Calibration: FAILED (Open-Circuit)");
    while (1)
      ;
  }
  if (calcR0 == 0)
  {
    Serial.println("MQ135 Calibration: FAILED (Short-Circuit)");
    while (1)
      ;
  }
  /*****************************  MQ CAlibration ********************************************/
  MQ135.serialDebug(true);
  Serial.println("MQ135: OK");

  height_init=bmp.readAltitude();
}

void loop()
{
  unsigned long start = millis();
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  MQ135.update();
  ppm = MQ135.readSensor() * 100;
  // Serial.println(ppm);
  // delay(500);
  temperature = bmp.readTemperature();
  pressure = bmp.readPressure();
  altitude = height_init-bmp.readAltitude();

  accx = a.acceleration.x;
  accy = a.acceleration.y;
  accz = a.acceleration.z;
  gyx = g.gyro.x;
  gyy = g.gyro.y;
  gyz = g.gyro.z;



  unsigned long currentMillis = millis();
  //[t,p,h,ppm,ax,ay,az,gx,gz,gy,lat,lon]

  if (currentMillis - previousMillis >= interval) {
  message = "T:"+ String(temperature) + ",P:" + String(pressure) + ",H:" + String(altitude) + ",PPM:" + String(ppm) + "\r\n";
  msg_len = message.length() - 2;
  Serial.println(message);

  String str_Send = "AT+SEND=1," + String(msg_len) + "," + message; //--> "AT+SEND=Recipient/Destination Address, Payload Length, Data/Message".
  ReyaxLoRa.print(str_Send);
  }
  
  while (millis() - start < 1000)
  {
    while (gpsSerial.available() > 0)
    {
      // char gpsData = gpsSerial.read();
      // Serial.print(gpsData);
      gps.encode(gpsSerial.read());
    }
    if (gps.location.isUpdated())
    {
      // Serial.println(gps.location.lat(), 6);
      latitude = gps.location.lat();
      // Serial.println(gps.location.lng(), 6);
      longitude = gps.location.lng();
      // Serial.println("");
    }
  }
}

