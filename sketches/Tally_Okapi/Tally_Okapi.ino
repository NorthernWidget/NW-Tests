// Tally on the Okapi data logger: compile test (NW-Tests).
// Same shape as the hand-written logger examples: the logger owns the loop and
// calls update() every updateRate seconds; update() returns the sensor's CSV row.
#include <Okapi.h>
#include <Tally_I2C.h>

Okapi Logger;
Tally_I2C sensor;

uint8_t I2CVals[] = {Tally_I2C::DEFAULT_ADDRESS};
String header = "";
uint32_t updateRate = 60;  // seconds between readings

void setup() {
    header = sensor.GetHeader();
    Logger.begin(I2CVals, sizeof(I2CVals), header);
    initialize();
}

void loop() {
    Logger.run(update, updateRate);
}

String update() {
    initialize();
    return sensor.GetString();
}

void initialize() {
    sensor.begin();
}
