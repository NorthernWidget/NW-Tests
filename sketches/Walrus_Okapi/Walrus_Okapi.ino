// Walrus on the Okapi data logger: compile test (NW-Tests).
// The logger owns the loop and writes each row from the sensors it was given:
// watch() states the sensor, its address and its column order in one place, and
// run() does the rest. The sketch keeps no header and no update() function.
#include <Okapi.h>
#include <Walrus_I2C.h>

Okapi Logger;
Walrus sensor;

uint32_t updateRate = 60;  // seconds between readings

void setup() {
    Logger.watch(sensor);  // address, columns and status rows, in one place
    Logger.begin();
    // The MS5803's own conversions, Page 2 Block 3, served on every reading from
    // firmware patch 2. Logged here so that the raw path is exercised end to
    // end: a reading can be recomputed from them afterwards.
    sensor.setADCColumns(true);
}

void loop() {
    Logger.run(updateRate);
}
