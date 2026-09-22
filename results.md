# Compile results — 2026-09-23

Board `NorthernWidget:avr:NW1284p`; libraries from `/home/awickert/Dropbox/NorthernWidget/github`; sketchbook empty. Cells: flash B / RAM B, or the first error.

| Sensor | Margay | Okapi |
|---|---|---|
| Apis | ✅ 56894 / 2561 | ❌ Okapi_Library/src/Okapi.cpp:747:47: error: 'MCP23018::Ports' has not been declared |
| Haar | ✅ 53316 / 2248 | ❌ Okapi_Library/src/Okapi.cpp:747:47: error: 'MCP23018::Ports' has not been declared |
| Liasis | ✅ 53138 / 2238 | ❌ MCP23018/MCP23018.h:26:11: error: expected ',' or '...' before numeric constant |
| Libelle | ✅ 54598 / 2358 | ❌ MCP23018/MCP23018.h:26:11: error: expected unqualified-id before numeric constant |
| MaxBotix | ❌ MaxBotix_Library/src/Maxbotix.cpp:101:10: error: 'softSerial' was not declared in this scope | ❌ Okapi_Library/src/Okapi.cpp:747:47: error: 'MCP23018::Ports' has not been declared |
| NW_BME280 | ✅ 52278 / 2288 | ❌ Okapi_Library/src/Okapi.cpp:747:47: error: 'MCP23018::Ports' has not been declared |
| T9602 | ✅ 52822 / 2216 | ❌ Okapi_Library/src/Okapi.cpp:747:47: error: 'MCP23018::Ports' has not been declared |
| Tally | ✅ 52922 / 2208 | ❌ Okapi_Library/src/Okapi.cpp:747:47: error: 'MCP23018::Ports' has not been declared |
| Walrus | ✅ 53048 / 2249 | ❌ Okapi_Library/src/Okapi.cpp:747:47: error: 'MCP23018::Ports' has not been declared |

Working trees with uncommitted changes (compiled as they are): MaxBotix_Library
