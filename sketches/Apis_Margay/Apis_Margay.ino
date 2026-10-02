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
    // begin() first: a device's header can depend on what begin() read from it.
    // A Walrus whose Page 1 names no MS5803 converts nothing and reports its own
    // ADC conversions instead, and getHeader() can only know that once Page 1 has
    // been read. A file's header must mean the same thing for its whole life.
    initialize();
    header = sensor.getHeader();
    Logger.begin(I2CVals, sizeof(I2CVals), header);
    Logger.watch(sensor);  // its reports go to the status file
    // Section 14 step 3: the streamed header must equal the composed one.
    String streamed = "";
    NW_StringPrint headerSink(streamed);
    Logger.printFileHeader(headerSink);
    if (streamed != Logger.dataHeader()) {
        Serial.print(F("HEADER MISMATCH: streamed="));
        Serial.println(streamed);
    }
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
