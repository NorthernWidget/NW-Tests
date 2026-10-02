# Compile results — 2026-10-02

Board `NorthernWidget:avr:NW1284p`; libraries from `/home/awickert/Dropbox/NorthernWidget/github`; sketchbook empty. Cells: flash B / RAM B, or the first error.

| Sensor | Margay | Okapi |
|---|---|---|
| Apis | ✅ 67114 / 3099 | ✅ 65232 / 3092 |
| Haar | ✅ 63950 / 3212 | ✅ 61988 / 3207 |
| Liasis | ✅ 60166 / 2756 | ✅ 59082 / 2749 |
| Libelle | ✅ 67122 / 3247 | ✅ 66026 / 3240 |
| MaxBotix | ❌ MaxBotix_Library/src/Maxbotix.cpp:101:10: error: 'softSerial' was not declared in this scope | ❌ MaxBotix_Library/src/Maxbotix.cpp:101:10: error: 'softSerial' was not declared in this scope |
| NW_BME280 | ✅ 59454 / 2806 | ✅ 57484 / 2801 |
| T9602 | ✅ 59600 / 2953 | ✅ 57650 / 2946 |
| Tally | ✅ 59862 / 2726 | ✅ 57868 / 2719 |
| Walrus | ✅ 64694 / 2944 | ✅ 62728 / 2937 |

Working trees with uncommitted changes (compiled as they are): NW_Core, Apis_Library, Walrus_Library, Haar_Library, Libelle_Library, MaxBotix_Library, NW_BME280, Margay_Library, Okapi_Library
