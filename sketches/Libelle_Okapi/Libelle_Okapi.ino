// Libelle on the Okapi data logger: compile test (NW-Tests).
// Same shape as the hand-written logger examples: the logger owns the loop and
// calls update() every updateRate seconds; update() returns the sensor's CSV row.
#include <Okapi.h>
#include <Libelle.h>

Okapi Logger;
Libelle sensor;

uint8_t I2CVals[] = {Libelle::DEFAULT_ADDRESS_UP};
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
