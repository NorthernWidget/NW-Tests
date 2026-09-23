// Apis on the Margay data logger: compile test (NW-Tests).
// Same shape as the hand-written logger examples: the logger owns the loop and
// calls update() every updateRate seconds; update() returns the sensor's CSV row.
#include <Margay.h>
#include <Apis.h>

Margay Logger(MODEL_3v0);  // update to match your hardware version
Apis sensor;

uint8_t I2CVals[] = {Apis::DEFAULT_ADDRESS};
String header = "";
uint32_t updateRate = 60;  // seconds between readings

void setup() {
    header = sensor.getHeader();
    Logger.begin(I2CVals, sizeof(I2CVals), header);
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
}
