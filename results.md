# Compile results — 2026-10-03

Board `NorthernWidget:avr:NW1284p`; libraries from `/home/awickert/Dropbox/NorthernWidget/github`; sketchbook empty. Cells: flash B / RAM B, or the first error.

| Sensor | Margay | Okapi |
|---|---|---|
| Apis | ✅ 68012 / 3349 | ✅ 66376 / 3310 |
| Haar | ✅ 64060 / 3462 | ✅ 62340 / 3425 |
| Liasis | ✅ 57980 / 2978 | ✅ 56208 / 2939 |
| Libelle | ✅ 67512 / 3501 | ✅ 66732 / 3462 |
| MaxBotix | ❌ MaxBotix_Library/src/Maxbotix.cpp:101:10: error: 'softSerial' was not declared in this scope | ❌ MaxBotix_Library/src/Maxbotix.cpp:101:10: error: 'softSerial' was not declared in this scope |
| NW_BME280 | ✅ 57944 / 3044 | ✅ 56208 / 3007 |
| T9602 | ✅ 58384 / 3203 | ✅ 56550 / 3164 |
| Tally | ✅ 57916 / 2956 | ✅ 56146 / 2919 |
| Walrus | ✅ 65426 / 3194 | ✅ 63706 / 3155 |

Working trees with uncommitted changes (compiled as they are): NW_Core, Apis_Library, Walrus_Library, MaxBotix_Library
