// Haar on the Okapi data logger: compile test (NW-Tests).
// The logger owns the loop and writes each row from the sensors it was given:
// watch() states the sensor, its address and its column order in one place, and
// run() does the rest. The sketch keeps no header and no update() function.
#include <Okapi.h>
#include <Haar.h>

Okapi Logger;
Haar sensor;

uint32_t updateRate = 60;  // seconds between readings

void setup() {
    Logger.watch(sensor);  // address, columns and status rows, in one place
    Logger.begin();
}

void loop() {
    Logger.run(updateRate);
}
