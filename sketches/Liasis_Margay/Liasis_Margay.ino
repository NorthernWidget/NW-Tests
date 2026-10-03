// Liasis on the Margay data logger: compile test (NW-Tests).
// The logger owns the loop and writes each row from the sensors it was given:
// watch() states the sensor, its address and its column order in one place, and
// run() does the rest. The sketch keeps no header and no update() function.
#include <Margay.h>
#include <Liasis.h>

Margay Logger(MODEL_3v0);  // update to match your hardware version
Liasis sensor;

uint32_t updateRate = 60;  // seconds between readings

void setup() {
    sensor.begin();
    Serial.println(sensor.getHeader());  // not on NW_Core: the logger cannot hold it
    Logger.begin();
}

void loop() {
    Logger.run(updateRate);
}
