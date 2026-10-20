// A schedule the board cannot keep, on purpose (NW-Tests, NW-Sim case margay_overrun).
// A 1 s interval under a 3 s watchdog: no legible step fits, since even 2 s plus a
// cycle reaches the ceiling, so the first cycle raises NO_SCHEDULE - and, if that
// cycle itself runs a full second, CYCLE_OVERRAN before it. Both must reach the
// first row's Note column and the boot verdict, which is what the case watches.
#include <Margay.h>

Margay Logger(MODEL_3v0);

void setup() {
    Logger.begin();
    // After begin(), not before: begin() reads Page 1, and a provisioned board's
    // page carries the real 2110 s, which would overwrite a value set earlier.
    Logger.wdtSeconds = 3;  // the ceiling, far below the board's real period
}

void loop() {
    Logger.run(1);
}
