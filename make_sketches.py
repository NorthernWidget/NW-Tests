#!/usr/bin/env python3
"""Write one Margay and one Okapi sketch per sensor library, in the shape of the
hand-written logger examples: the logger owns the loop; update() returns the
sensor's CSV string. Edit LIBRARIES and rerun; the sketches are committed so
they read as plain examples."""
from pathlib import Path

# name, header, class, I2C address expression ('' = none, e.g. serial sensors),
# begin() args, string call, header call, and anything the sketch must set after
# begin(). The last field is a dict of library name to the lines that follow
# sensor.begin() inside initialize(), for a device whose columns are optional.
LIBRARIES = [
    ("Apis",      "Apis.h",       "Apis",      "Apis::DEFAULT_ADDRESS",      "",      "getString()",     "getHeader()"),
    ("Walrus",    "Walrus_I2C.h", "Walrus",    "Walrus::DEFAULT_ADDRESS",    "",      "getString()",     "getHeader()"),
    ("Haar",      "Haar.h",       "Haar",      "Haar::DEFAULT_ADDRESS",      "",      "getString()",     "getHeader()"),
    ("Libelle",   "Libelle.h",    "Libelle",   "Libelle::DEFAULT_ADDRESS_UP", "",     "getString()",     "getHeader()"),
    ("Liasis",    "Liasis.h",     "Liasis",    "0x4A",                       "",      "getString()",     "getHeader()"),
    ("T9602",     "T9602.h",      "T9602",     "0x28",                       "",      "printDataRow(Serial)", "printDataHeader(Serial)"),
    ("MaxBotix",  "Maxbotix.h",   "Maxbotix",  "",                           "10",    "getString()",     "getHeader()"),
    ("NW_BME280", "NW_BME280.h",  "BME",       "0x76",                       "0x76",  "getString()",     "getHeader()"),
    ("Tally",     "Tally_I2C.h",  "Tally_I2C", "Tally_I2C::DEFAULT_ADDRESS", "",      "GetString()",     "GetHeader()"),
]

# What a sketch sets after begin(), per library. A column a device can be asked
# for and does not print by default belongs here rather than in a hand-edit of a
# generated file, which the next run of this script would discard.
AFTER_BEGIN = {
    "Walrus": """
    // The MS5803's own conversions, Page 2 Block 3, served on every reading from
    // firmware patch 2. Logged here so that the raw path is exercised end to
    // end: a reading can be recomputed from them afterwards.
    sensor.setADCColumns(true);""",
}

# Libraries on NW_Core, whose sensors a logger's status file can watch (NW_Sensor).
CORE_SENSORS = {"Apis", "Walrus", "Haar", "Libelle"}

LOGGERS = {
    "Margay": dict(include="Margay.h", decl="Margay Logger(MODEL_3v0);  // update to match your hardware version",
                   begin="Logger.begin();", run="Logger.run(updateRate);"),
    "Okapi":  dict(include="Okapi.h",  decl="Okapi Logger;",
                   begin="Logger.begin();", run="Logger.run(updateRate);"),
}


TEMPLATE = """// {name} on the {logger} data logger: compile test (NW-Tests).
// The logger owns the loop and writes each row from the sensors it was given:
// watch() states the sensor, its address and its column order in one place, and
// run() does the rest. The sketch keeps no header and no update() function.
#include <{linclude}>
#include <{header}>

{ldecl}
{cls} sensor;

uint32_t updateRate = 60;  // seconds between readings

void setup() {{
{sensor}    {lbegin}{after}
}}

void loop() {{
    {lrun}
}}
"""

for name, header, cls, addr, bargs, s, h in LIBRARIES:
    for logger, L in LOGGERS.items():
        d = Path("sketches") / f"{name}_{logger}"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}_{logger}.ino").write_text(TEMPLATE.format(
            name=name, logger=logger, linclude=L["include"], header=header, ldecl=L["decl"], cls=cls,
            addr=addr, addrnote="" if addr else "  // no I2C address: the logger's bus test has nothing to check",
            hdr=h, lbegin=L["begin"], lrun=L["run"], str=s, bargs=bargs,
            after=AFTER_BEGIN.get(name, ""),
            # On NW_Core: one line states the sensor, its address and its column
            # order, and the logger does the rest. Not on NW_Core: the logger
            # cannot hold it, so the sketch exercises the library itself and the
            # row never reaches the file.
            sensor=("    Logger.watch(sensor);  // address, columns and status rows, in one place\n"
                    if name in CORE_SENSORS else
                    f"    sensor.begin({bargs});\n"
                    # A library on the streaming interface prints into Serial
                    # itself; one that still returns a String is printed.
                    + (f"    sensor.{h};  // not on NW_Core: the logger cannot hold it\n"
                       f"    Serial.println();\n" if "(Serial)" in h else
                       f"    Serial.println(sensor.{h});  // not on NW_Core: the logger cannot hold it\n"))))
print(f"{2*len(LIBRARIES)} sketches written")
