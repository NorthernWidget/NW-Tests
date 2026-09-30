// Walrus on the Margay data logger: compile test (NW-Tests).
// Same shape as the hand-written logger examples: the logger owns the loop and
// calls update() every updateRate seconds; update() returns the sensor's CSV row.
#include <Margay.h>
#include <Walrus_I2C.h>

Margay Logger(MODEL_3v0);  // update to match your hardware version
Walrus sensor;

uint8_t I2CVals[] = {Walrus::DEFAULT_ADDRESS};
String header = "";
uint32_t updateRate = 60;  // seconds between readings

void setup() {
    // begin() first: the header depends on what the sensor says about itself.
    // A Walrus whose Page 1 names no MS5803 converts nothing and reports its
    // own ADC conversions instead, and getHeader() can only know that once it
    // has read Page 1.
    initialize();
    header = sensor.getHeader();
    Logger.begin(I2CVals, sizeof(I2CVals), header);
    Logger.watch(sensor);  // its reports go to the status file
    initialize();
}

void loop() {
    Logger.run(update, updateRate);
}

String update() {
    initialize();
    return sensor.getString();
}

void initialize() {
    sensor.begin();
    // The MS5803's own conversions, Page 2 Block 3, served on every reading from
    // firmware patch 2. Logged here so that the raw path is exercised end to
    // end: a reading can be recomputed from them afterwards.
    sensor.setADCColumns(true);
}
