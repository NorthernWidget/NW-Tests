// MaxBotix on the Margay data logger: compile test (NW-Compile-Tests).
// Same shape as the hand-written logger examples: the logger owns the loop and
// calls update() every updateRate seconds; update() returns the sensor's CSV row.
#include <Margay.h>
#include <Maxbotix.h>

Margay Logger(MODEL_3v0);  // update to match your hardware version
Maxbotix sensor;

uint8_t I2CVals[] = {};  // no I2C address: the logger's bus test has nothing to check
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
    sensor.begin(10);
}
