// Walrus on the Okapi data logger: compile test (NW-Tests).
// Same shape as the hand-written logger examples: the logger owns the loop and
// calls update() every updateRate seconds; update() returns the sensor's CSV row.
#include <Okapi.h>
#include <Walrus_I2C.h>

Okapi Logger;
Walrus sensor;

uint8_t I2CVals[] = {Walrus::DEFAULT_ADDRESS};
String header = "";
uint32_t updateRate = 60;  // seconds between readings

void setup() {
    header = sensor.getHeader();
    Logger.begin(I2CVals, sizeof(I2CVals), header);
    initialize();
}

void loop() {
    Logger.Run(update, updateRate);
}

String update() {
    initialize();
    return sensor.getString();
}

void initialize() {
    sensor.begin();
}
