#!/usr/bin/env python3
"""Write one Margay and one Okapi sketch per sensor library, in the shape of the
hand-written logger examples: the logger owns the loop; update() returns the
sensor's CSV string. Edit LIBRARIES and rerun; the sketches are committed so
they read as plain examples."""
from pathlib import Path

# name, header, class, I2C address expression ('' = none, e.g. serial sensors), begin() args, string call, header call
LIBRARIES = [
    ("Apis",      "Apis.h",       "Apis",      "Apis::DEFAULT_ADDRESS",      "",      "getString()",     "getHeader()"),
    ("Walrus",    "Walrus_I2C.h", "Walrus",    "Walrus::DEFAULT_ADDRESS",    "",      "getString()",     "getHeader()"),
    ("Haar",      "Haar.h",       "Haar",      "0x42",                       "",      "getString()",     "getHeader()"),
    ("Libelle",   "Libelle.h",    "Libelle",   "0x40",                       "",      "getString()",     "getHeader()"),
    ("Liasis",    "Liasis.h",     "Liasis",    "0x4A",                       "",      "getString()",     "getHeader()"),
    ("T9602",     "T9602.h",      "T9602",     "0x28",                       "",      "getString(true)", "getHeader()"),
    ("MaxBotix",  "Maxbotix.h",   "Maxbotix",  "",                           "10",    "getString()",     "getHeader()"),
    ("NW_BME280", "NW_BME280.h",  "BME",       "0x76",                       "0x76",  "getString()",     "getHeader()"),
    ("Tally",     "Tally_I2C.h",  "Tally_I2C", "Tally_I2C::DEFAULT_ADDRESS", "",      "GetString()",     "GetHeader()"),
]

LOGGERS = {
    "Margay": dict(include="Margay.h", decl="Margay Logger(MODEL_3v0);  // update to match your hardware version",
                   begin="Logger.begin(I2CVals, sizeof(I2CVals), header);", run="Logger.run(update, updateRate);"),
    "Okapi":  dict(include="Okapi.h",  decl="Okapi Logger;",
                   begin="Logger.begin(I2CVals, sizeof(I2CVals), header);", run="Logger.Run(update, updateRate);"),
}

TEMPLATE = """// {name} on the {logger} data logger: compile test (NW-Tests).
// Same shape as the hand-written logger examples: the logger owns the loop and
// calls update() every updateRate seconds; update() returns the sensor's CSV row.
#include <{linclude}>
#include <{header}>

{ldecl}
{cls} sensor;

uint8_t I2CVals[] = {{{addr}}};{addrnote}
String header = "";
uint32_t updateRate = 60;  // seconds between readings

void setup() {{
    header = sensor.{hdr};
    {lbegin}
    initialize();
}}

void loop() {{
    {lrun}
}}

String update() {{
    initialize();
    return sensor.{str};
}}

void initialize() {{
    sensor.begin({bargs});
}}
"""

for name, header, cls, addr, bargs, s, h in LIBRARIES:
    for logger, L in LOGGERS.items():
        d = Path("sketches") / f"{name}_{logger}"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}_{logger}.ino").write_text(TEMPLATE.format(
            name=name, logger=logger, linclude=L["include"], header=header, ldecl=L["decl"], cls=cls,
            addr=addr, addrnote="" if addr else "  // no I2C address: the logger's bus test has nothing to check",
            hdr=h, lbegin=L["begin"], lrun=L["run"], str=s, bargs=bargs))
print(f"{2*len(LIBRARIES)} sketches written")
