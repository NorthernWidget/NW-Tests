// Tally on the Margay data logger: compile test (NW-Tests).
// Same shape as the hand-written logger examples: the logger owns the loop and
// calls update() every updateRate seconds; update() returns the sensor's CSV row.
#include <Margay.h>
#include <Tally_I2C.h>

Margay Logger(MODEL_3v0);  // update to match your hardware version
Tally_I2C sensor;

uint8_t I2CVals[] = {Tally_I2C::DEFAULT_ADDRESS};
String header = "";
uint32_t updateRate = 60;  // seconds between readings

void setup() {
    // begin() first: a device's header can depend on what begin() read from it.
    // A Walrus whose Page 1 names no MS5803 converts nothing and reports its own
    // ADC conversions instead, and getHeader() can only know that once Page 1 has
    // been read. A file's header must mean the same thing for its whole life.
    initialize();
    header = sensor.GetHeader();
    Logger.begin(I2CVals, sizeof(I2CVals), header);
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
