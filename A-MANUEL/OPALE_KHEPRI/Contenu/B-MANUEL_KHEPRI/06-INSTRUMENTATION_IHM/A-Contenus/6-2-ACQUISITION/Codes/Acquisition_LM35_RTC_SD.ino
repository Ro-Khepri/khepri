// Acquisition de 10 capteurs LM35DZ avec horodatage (RTC DS1307) et enregistrement sur carte SD
// Croquis « sketch_may8b.ino », transcrit depuis l'annexe 3 du mémoire SFE 2025-01 (capture d'écran) :
// à comparer au fichier original s'il est retrouvé. Carte : Arduino Mega 2560.
#include <Wire.h>
#include <RTClib.h>
#include <SD.h>

RTC_DS1307 rtc;

const int chipSelect = 53;
File dataFile;

const int numSensors = 10;
const int analogPins[numSensors] = {A0, A1, A2, A3, A4, A5, A6, A7, A8, A9};

void setup() {
  Serial.begin(9600);
  Wire.begin();

  // Initialisation RTC
  if (!rtc.begin()) {
    Serial.println("RTC non détecté !");
    while (1);
  }

  if (!rtc.isrunning()) {
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }

  // Initialisation carte SD
  if (!SD.begin(chipSelect)) {
    Serial.println("Échec de la carte SD !");
    while (1);
  }

  // Création du fichier CSV s'il n'existe pas
  if (!SD.exists("tempLM35.csv")) {
    dataFile = SD.open("tempLM35.csv", FILE_WRITE);
    dataFile.print("Date,Heure");
    for (int i = 0; i < numSensors; i++) {
      dataFile.print(",LM35_");
      dataFile.print(i);
    }
    dataFile.println();
    dataFile.close();
  }

  Serial.println("Initialisation terminée.");
}

void loop() {
  DateTime now = rtc.now();

  String dataString = String(now.year()) + "-" + String(now.month()) + "-" + String(now.day()) + "," +
                      String(now.hour()) + ":" + String(now.minute()) + ":" + String(now.second());

  // Lire les 10 capteurs
  for (int i = 0; i < numSensors; i++) {
    int sensorValue = analogRead(analogPins[i]);
    float voltage = sensorValue * (5.0 / 1023.0);
    float temperature = voltage * 100; // LM35 : 10mV/°C
    dataString += "," + String(temperature, 2);
  }

  Serial.println(dataString);

  // Écriture dans le fichier CSV
  dataFile = SD.open("tempLM35.csv", FILE_WRITE);
  if (dataFile) {
    dataFile.println(dataString);
    dataFile.close();
  } else {
    Serial.println("Erreur lors de l'ouverture du fichier.");
  }

  delay(10000); // Intervalle de 5 secondes
}
