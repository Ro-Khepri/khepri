// Régulation de température par paliers de couvertures chauffantes (Arduino Mega, 5 sondes DS18B20,
// écran LCD I2C 16x2, clavier 4x4, 4 relais). Code de l'annexe 1 du mémoire SFE 2026-03 (SLT Pierre BARAN),
// repris du fichier « Montage arduino.docx » (dossier 26, annexes).
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Keypad.h>
#define SONDE_PIN    4
#define RELAIS1_PIN  8
#define RELAIS2_PIN  9
#define RELAIS3_PIN  10
#define RELAIS4_PIN  11
#define LED_PIN      13
#define NB_SONDES    5
LiquidCrystal_I2C lcd(0x27, 16, 2);
// ── Clavier 4x4 ──────────────────────────────────
const byte ROWS = 4, COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {30, 31, 32, 33};
byte colPins[COLS] = {34, 35, 36, 37};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);
// ── Paliers (max 6) ───────────────────────────────
struct Palier {
  float consigne;
  long  duree_ms;
  float hysteresis;
  float vitesse_montee;
};
Palier profil[6];
int NB_PALIERS = 0;
OneWire oneWire(SONDE_PIN);
DallasTemperature sensors(&oneWire);
int   palier_actuel  = 0;
bool  en_attente     = true;
long  debut_palier   = 0;
long  debut_montee   = 0;
float temp_actuelle  = 0;
float temp_depart    = 20.0;
float temps[NB_SONDES] = {0, 0, 0, 0, 0};
int   ecran_actuel   = 0;
long  dernier_switch = 0;
#define SWITCH_INTERVAL 6000
void relaisON();
void relaisOFF();
void finProgramme();
void configurerPaliers();
// ── Lecture DS18B20 ───────────────────────────────
float lireMoyenne() {
  sensors.requestTemperatures();
  float somme   = 0;
  int   valides = 0;
  for (int i = 0; i < 4; i++) {
    float t = sensors.getTempCByIndex(i);
    if (t != DEVICE_DISCONNECTED_C && t > -50) {
      temps[i] = t;
      somme   += t;
      valides++;
    } else {
      temps[i] = -99;
    }
  }
  float t5 = sensors.getTempCByIndex(4);
  temps[4] = (t5 != DEVICE_DISCONNECTED_C && t5 > -50) ? t5 : -99;
  if (valides == 0) return DEVICE_DISCONNECTED_C;
  return somme / valides;
}
// ── Saisie numérique sur LCD ───────────────────────
float saisiNombre(String label1, String label2) {
  String val = "";
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(label1);
  lcd.setCursor(0, 1);
  lcd.print(label2);
  delay(3000);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(label1);
  lcd.setCursor(0, 1);
  lcd.print("> ");
  while (true) {
    char k = keypad.getKey();
    if (k) {
      if (k >= '0' && k <= '9') {
        val += k;
        lcd.setCursor(2, 1);
        lcd.print(val + "    ");
      } else if (k == '*') {
        if (val.length() > 0) val.remove(val.length() - 1);
        lcd.setCursor(2, 1);
        lcd.print(val + "    ");
      } else if (k == '#') {
        if (val.length() > 0) return val.toFloat();
      }
    }
  }
}
// ── Menu de configuration ─────────────────────────
void configurerPaliers() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Nb de paliers?");
  lcd.setCursor(0, 1);
  lcd.print("(1-6) puis #");
  int nb = 0;
  while (nb < 1 || nb > 6) {
    char k = keypad.getKey();
    if (k >= '1' && k <= '6') nb = k - '0';
  }
  NB_PALIERS = nb;
  for (int i = 0; i < NB_PALIERS; i++) {
    String titre = "Palier " + String(i + 1) + "/" + String(NB_PALIERS);
    float temp    = saisiNombre(titre, "Temp cible(C) #");
    profil[i].consigne = temp;
    float duree   = saisiNombre(titre, "Duree (min)  #");
    profil[i].duree_ms = (long)(duree * 60000);
    float hyst    = saisiNombre(titre, "Hysteresis   #");
    profil[i].hysteresis = hyst;
    float vitesse = saisiNombre(titre, "Montee C/min #");
    profil[i].vitesse_montee = vitesse;

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(titre);
    lcd.setCursor(0, 1);
    lcd.print((int)temp);
    lcd.print("C ");
    lcd.print((int)duree);
    lcd.print("m H:");
    lcd.print(hyst, 1);
    lcd.print(" V:");
    lcd.print((int)vitesse);
    delay(4000);
  }
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Config OK !");
  lcd.setCursor(0, 1);
  lcd.print("A=start D=reconf");

  while (true) {
    char k = keypad.getKey();
    if (k == 'A') break;
    if (k == 'D') { configurerPaliers(); return; }
  }
}

// ── Setup ─────────────────────────────────────────
void setup() {
  Serial.begin(9600);
  pinMode(RELAIS1_PIN, OUTPUT);
  pinMode(RELAIS2_PIN, OUTPUT);
  pinMode(RELAIS3_PIN, OUTPUT);
  pinMode(RELAIS4_PIN, OUTPUT);
  pinMode(LED_PIN,     OUTPUT);
  digitalWrite(RELAIS1_PIN, HIGH);
  digitalWrite(RELAIS2_PIN, HIGH);
  digitalWrite(RELAIS3_PIN, HIGH);
  digitalWrite(RELAIS4_PIN, HIGH);
  digitalWrite(LED_PIN,     LOW);
  sensors.begin();
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Regulateur T");
  lcd.setCursor(0, 1);
  lcd.print("Sondes: ");
  lcd.print(sensors.getDeviceCount());
  lcd.print("/5      ");
  delay(3000);
  configurerPaliers();
  palier_actuel  = 0;
  en_attente     = true;
  dernier_switch = millis();
  delay(1000);
  temp_actuelle = lireMoyenne();
  if (temp_actuelle == DEVICE_DISCONNECTED_C || temp_actuelle < -50)
    temp_depart = 20.0;
  else
    temp_depart = temp_actuelle;

  debut_montee = millis();
}
// ── Boucle principale ──────────────────────────────
void loop() {
  char k = keypad.getKey();
  if (k == 'D') {
    relaisOFF();
    palier_actuel = 0;
    en_attente    = true;
    configurerPaliers();
    delay(1000);
    temp_actuelle = lireMoyenne();
    if (temp_actuelle == DEVICE_DISCONNECTED_C || temp_actuelle < -50)
      temp_depart = 20.0;
    else
      temp_depart = temp_actuelle;
    debut_montee   = millis();
    dernier_switch = millis();
    return;
  }
  if (palier_actuel >= NB_PALIERS) {
    finProgramme();
    return;
  }
  temp_actuelle = lireMoyenne();
  if (temp_actuelle == DEVICE_DISCONNECTED_C) {
    lcd.setCursor(0, 0);
    lcd.print("ERREUR SONDES ! ");
    lcd.setCursor(0, 1);
    lcd.print("Verif cablage   ");
    relaisOFF();
    delay(6000);
    return;
  }
  float consigne = profil[palier_actuel].consigne;
  float hyst     = profil[palier_actuel].hysteresis;
  float vitesse  = profil[palier_actuel].vitesse_montee;
  float consigne_active = consigne;
  if (en_attente && vitesse > 0.1) {
    float minutes   = (millis() - debut_montee) / 60000.0;
    consigne_active = temp_depart + vitesse * minutes;
    if (consigne_active > consigne) consigne_active = consigne;
    if (consigne_active < temp_depart) consigne_active = temp_depart;
  }
  if (temp_actuelle < (consigne_active - hyst))      relaisON();
  else if (temp_actuelle > (consigne_active + hyst)) relaisOFF();
  if (en_attente) {
    if (temp_actuelle >= consigne - hyst) {
      en_attente   = false;
      debut_palier = millis();
    }
  } else {
    if (millis() - debut_palier >= profil[palier_actuel].duree_ms) {
      temp_depart  = temp_actuelle;
      debut_montee = millis();
      palier_actuel++;
      en_attente   = true;
    }
  }
  if (millis() - dernier_switch >= SWITCH_INTERVAL) {
    ecran_actuel = (ecran_actuel + 1) % 3;
    dernier_switch = millis();
    lcd.clear();
  }
  long restant = 0;
  if (!en_attente && palier_actuel < NB_PALIERS) {
    restant = (profil[palier_actuel].duree_ms - (millis() - debut_palier)) / 1000;
    if (restant < 0) restant = 0;
  }
  if (ecran_actuel == 0) {
    lcd.setCursor(0, 0);
    lcd.print("Moy:");
    lcd.print(temp_actuelle, 1);
    lcd.print("C C:");
    lcd.print(consigne, 0);
    lcd.print("C  ");
    lcd.setCursor(0, 1);
    lcd.print("P");
    lcd.print(palier_actuel + 1);
    lcd.print("/");
    lcd.print(NB_PALIERS);
    if (en_attente) {
      if (vitesse > 0.1) {
        lcd.print(" ");
        lcd.print((int)vitesse);
        lcd.print("C/m   ");
      } else {
        lcd.print(" Montee   ");
      }
    } else {
      lcd.print(" ");
      lcd.print(restant / 60);
      lcd.print("m");
      lcd.print(restant % 60);
      lcd.print("s  ");
    }
  } else if (ecran_actuel == 1) {
    lcd.setCursor(0, 0);
    lcd.print("S1:");
    if (temps[0] == -99) lcd.print("ERR  ");
    else { lcd.print(temps[0], 1); lcd.print("C "); }
    lcd.print("S2:");
    if (temps[1] == -99) lcd.print("ERR ");
    else { lcd.print(temps[1], 1); lcd.print("C"); }
    lcd.setCursor(0, 1);
    lcd.print("S3:");
    if (temps[2] == -99) lcd.print("ERR  ");
    else { lcd.print(temps[2], 1); lcd.print("C "); }
    lcd.print("S4:");
    if (temps[3] == -99) lcd.print("ERR ");
    else { lcd.print(temps[3], 1); lcd.print("C"); }
  } else {
    lcd.setCursor(0, 0);
    lcd.print("Sonde 5 :       ");
    lcd.setCursor(0, 1);
    if (temps[4] == -99) {
      lcd.print("ERR sonde 5     ");
    } else {
      lcd.print("S5:");
      lcd.print(temps[4], 1);
      lcd.print(" C          ");
    }
  }
  Serial.print(temp_actuelle, 1);
  Serial.print(" ");
  Serial.print(consigne, 1);
  Serial.print(" ");
  for (int i = 0; i < NB_SONDES; i++) {
    Serial.print(temps[i] == -99 ? 0 : temps[i], 1);
    if (i < NB_SONDES - 1) Serial.print(" ");
  }
  Serial.println();
  delay(1000);
}
void relaisON() {
  digitalWrite(RELAIS1_PIN, LOW);
  digitalWrite(RELAIS2_PIN, LOW);
  digitalWrite(RELAIS3_PIN, LOW);
  digitalWrite(RELAIS4_PIN, LOW);
  digitalWrite(LED_PIN,     HIGH);
}
void relaisOFF() {
  digitalWrite(RELAIS1_PIN, HIGH);
  digitalWrite(RELAIS2_PIN, HIGH);
  digitalWrite(RELAIS3_PIN, HIGH);
  digitalWrite(RELAIS4_PIN, HIGH);
  digitalWrite(LED_PIN,     LOW);
}
void finProgramme() {
  relaisOFF();
  lcd.setCursor(0, 0);
  lcd.print("Programme fini  ");
  lcd.setCursor(0, 1);
  lcd.print("Refroidissement ");
  Serial.println("0 0 0 0 0 0 0");
  delay(5000);
}
