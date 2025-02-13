
#include <Arduino.h>
#include <Wire.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_BMP085.h>
#include <ESP32Servo.h>
#include <MQ135.h>
#include <MQUnifiedsensor.h>
#include <string.h>
#define esp32_sample_rate 4096

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
float ppm = 0;
float pressure = 0;
float temperature = 0;
float altitude = 0;
float latitude = 0;
float longitude = 0;
float height_limit = 200;
float accx = 0;
float accy = 0;
float accz = 0;
float gyx = 0;
float gyy = 0;
float gyz = 0;

String message = "";
int msg_len = 0;

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
  altitude = bmp.readAltitude();

  accx = a.acceleration.x;
  accy = a.acceleration.y;
  accz = a.acceleration.z;
  gyx = g.gyro.x;
  gyy = g.gyro.y;
  gyz = g.gyro.z;

  message = "T:" + String(temperature) + ",P:" + String(pressure) + ",H:" + String(altitude) + ",PPM:" + String(ppm) + ",AX:" + String(accx) + ",AY:" + String(accy) + ",AZ:" + String(accz) + ",GX:" + String(gyx) + ",GY:" + String(gyy) + ",GZ:" + String(gyz) + ",LAT:" + String(latitude) + ",LON:" + String(longitude);
  msg_len = message.length() - 2;
  Serial.println(message);

  String str_Send = "AT+SEND=1," + String(msg_len) + "," + message; //--> "AT+SEND=Recipient/Destination Address, Payload Length, Data/Message".
  ReyaxLoRa.print(str_Send);
  Serial.print("Send to Receiver : ");
  Serial.print(str_Send);
  Serial.flush();
  if (ReyaxLoRa.available())
    Serial.println(ReyaxLoRa.readString());

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

//! Code for Servomotor

// void setup()
// {
//   myservo.attach(Servomotor);
//   myservo.write(0);
//   delay(10000);
// }

// void loop()
// {
//   myservo.write(90);
//   delay(1000);
// }

//! Code for GPS
// void setup()
// {
//   // Serial Monitor
//   Serial.begin(115200);

//   // Start Serial 2 with the defined RX and TX pins and a baud rate of 9600
//   gpsSerial.begin(GPS_BAUD, SERIAL_8N1, GPSRX, GPSTX);
//   Serial.println("Serial 2 started at 9600 baud rate");
// }

// void loop()
// {
//   // This sketch displays information every time a new sentence is correctly encoded.
//   unsigned long start = millis();

//   while (millis() - start < 1000)
//   {
//     while (gpsSerial.available() > 0)
//     {
//       // char gpsData = gpsSerial.read();
//       // Serial.print(gpsData);
//       gps.encode(gpsSerial.read());
//     }
//     if (gps.location.isUpdated())
//     {
//       Serial.print("LAT: ");
//       Serial.println(gps.location.lat(), 6);
//       Serial.print("LONG: ");
//       Serial.println(gps.location.lng(), 6);
//       Serial.print("SPEED (km/h) = ");
//       Serial.println(gps.speed.kmph());
//       Serial.print("ALT (min)= ");
//       Serial.println(gps.altitude.meters());
//       Serial.print("HDOP = ");
//       Serial.println(gps.hdop.value() / 100.0);
//       Serial.print("Satellites = ");
//       Serial.println(gps.satellites.value());
//       Serial.print("Time in UTC: ");
//       Serial.println(String(gps.date.year()) + "/" + String(gps.date.month()) + "/" + String(gps.date.day()) + "," + String(gps.time.hour()) + ":" + String(gps.time.minute()) + ":" + String(gps.time.second()));
//       Serial.println("");
//     }
//   }
// }

//! Code for MPU6050 and BMP180

// void setup()
// {
//   Wire.begin(SDA, SCL);
//   Serial.begin(115200);
//   if (!mpu.begin())
//   {
//     Serial.println("Failed to find MPU6050 chip");
//     while (1)
//     {
//       delay(10);
//     }
//   }
//   Serial.println("MPU6050 Found!");
//   delay(500);
//   if (!bmp.begin())
//   {
//     Serial.println("Failed to find BMP180 chip");
//     while (1)
//     {
//       delay(10);
//     }
//   }

//   Serial.println("BMP180 Found!");
//   delay(500);

//   mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
//   Serial.print("Accelerometer range set to: ");
//   switch (mpu.getAccelerometerRange())
//   {
//   case MPU6050_RANGE_2_G:
//     Serial.println("+-2G");
//     break;
//   case MPU6050_RANGE_4_G:
//     Serial.println("+-4G");
//     break;
//   case MPU6050_RANGE_8_G:
//     Serial.println("+-8G");
//     break;
//   case MPU6050_RANGE_16_G:
//     Serial.println("+-16G");
//     break;
//   }
//   mpu.setGyroRange(MPU6050_RANGE_500_DEG);
//   Serial.print("Gyro range set to: ");
//   switch (mpu.getGyroRange())
//   {
//   case MPU6050_RANGE_250_DEG:
//     Serial.println("+- 250 deg/s");
//     break;
//   case MPU6050_RANGE_500_DEG:
//     Serial.println("+- 500 deg/s");
//     break;
//   case MPU6050_RANGE_1000_DEG:
//     Serial.println("+- 1000 deg/s");
//     break;
//   case MPU6050_RANGE_2000_DEG:
//     Serial.println("+- 2000 deg/s");
//     break;
//   }

//   mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

//   Serial.print("Filter bandwidth set to: ");
//   switch (mpu.getFilterBandwidth())
//   {
//   case MPU6050_BAND_260_HZ:
//     Serial.println("260 Hz");
//     break;
//   case MPU6050_BAND_184_HZ:
//     Serial.println("184 Hz");
//     break;
//   case MPU6050_BAND_94_HZ:
//     Serial.println("94 Hz");
//     break;
//   case MPU6050_BAND_44_HZ:
//     Serial.println("44 Hz");
//     break;
//   case MPU6050_BAND_21_HZ:
//     Serial.println("21 Hz");
//     break;
//   case MPU6050_BAND_10_HZ:
//     Serial.println("10 Hz");
//     break;
//   case MPU6050_BAND_5_HZ:
//     Serial.println("5 Hz");
//     break;
//   }
// }

// void loop()
// {

//   /* Get new sensor events with the readings */
//   sensors_event_t a, g, temp;
//   mpu.getEvent(&a, &g, &temp);

//   Serial.print("Temperature = ");
//   Serial.print(bmp.readTemperature());
//   Serial.println(" *C");

//   Serial.print("Pressure = ");
//   Serial.print(bmp.readPressure());
//   Serial.println(" Pa");

//   // Calculate altitude assuming 'standard' barometric
//   // pressure of 1013.25 millibar = 101325 Pascal
//   Serial.print("Altitude = ");
//   Serial.print(bmp.readAltitude());
//   Serial.println(" meters");

//   Serial.print("Pressure at sealevel (calculated) = ");
//   Serial.print(bmp.readSealevelPressure());
//   Serial.println(" Pa");

//   /* Print out the values */
//   Serial.print("Acceleration X: ");
//   Serial.print(a.acceleration.x);
//   Serial.print(", Y: ");
//   Serial.print(a.acceleration.y);
//   Serial.print(", Z: ");
//   Serial.print(a.acceleration.z);
//   Serial.println(" m/s^2");

//   Serial.print("Rotation X: ");
//   Serial.print(g.gyro.x);
//   Serial.print(", Y: ");
//   Serial.print(g.gyro.y);
//   Serial.print(", Z: ");
//   Serial.print(g.gyro.z);
//   Serial.println(" rad/s");

//   Serial.print("Temperature: ");
//   Serial.print(temp.temperature);
//   Serial.println(" degC");

//   Serial.println();
//   delay(500);
// }
