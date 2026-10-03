// NW_BME280 on the Margay data logger: compile test (NW-Tests).
// The logger owns the loop and writes each row from the sensors it was given:
// watch() states the sensor, its address and its column order in one place, and
// run() does the rest. The sketch keeps no header and no update() function.
#include <Margay.h>
#include <NW_BME280.h>

Margay Logger(MODEL_3v0);  // update to match your hardware version
BME sensor;

uint32_t updateRate = 60;  // seconds between readings

void setup() {
    sensor.begin(0x76);
    sensor.printDataHeader(Serial);  // not on NW_Core: the logger cannot hold it
    Serial.println();
    Logger.begin();
}

void loop() {
    Logger.run(updateRate);
}
