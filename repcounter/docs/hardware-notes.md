# Notatki sprzętowe — XIAO nRF52840 Sense (zweryfikowane 2026-10-05)

Każdy fakt ma źródło. „Do potwierdzenia na płytce” oznacza, że dokumentacja tego nie podaje wprost i sprawdzimy to w etapie 0.

## Piny w CircuitPythonie (nazwy `board.*`)
Źródło: definicja płytki w CircuitPythonie, `ports/nordic/boards/Seeed_XIAO_nRF52840_Sense/pins.c`
(https://github.com/adafruit/circuitpython/blob/main/ports/nordic/boards/Seeed_XIAO_nRF52840_Sense/pins.c)

| nazwa | pin nRF | uwagi |
|---|---|---|
| `LED`, `LED_RED` | P0_26 | dioda świeci przy stanie **niskim** (Seeed wiki) |
| `LED_GREEN` | P0_30 | j.w. |
| `LED_BLUE` | P0_06 | j.w. |
| `IMU_PWR` | P1_08 | zasilanie IMU, ustawić **wysoki** przed użyciem, odczekać ~50 ms |
| `IMU_SCL` / `IMU_SDA` | P0_27 / P0_07 | osobna magistrala I2C dla IMU (nie `SCL`/`SDA` na złączu) |
| `IMU_INT1` | P0_11 | przerwanie IMU, przyda się do budzenia ruchem (etap 5) |
| `VBATT` | P0_31 | ADC napięcia akumulatora przez dzielnik |
| `READ_BATT_ENABLE` | P0_14 | **niski** = pomiar włączony; wysoki = tor wyłączony |
| `CHARGE_STATUS` | P0_17 | niski = ładowanie trwa; wysoki = nie ładuje lub naładowany |
| `CHARGE_RATE` | P0_13 | wejście wysokiej impedancji = 50 mA (domyślnie); wyjście niskie = 100 mA. **Nie ruszamy.** |
| `MIC_PWR`, `PDM_CLK`, `PDM_DATA` | P1_10, P1_00, P0_16 | mikrofon, nieużywany |
| `D0`–`D10`, `A0`–`A5`, `SCL`/`SDA` (P0_05/P0_04) | złącze | wolne do użytku |

Uwaga: Seeed wiki podaje dla IMU „D4/D5”, ale definicja CircuitPythona używa P0_27/P0_07 jako `IMU_SCL`/`IMU_SDA` i biblioteka społeczności też. Trzymamy się `board.IMU_SCL`/`board.IMU_SDA`.

## IMU LSM6DS3TR-C
- Adres I2C 0x6A, biblioteka `adafruit_lsm6ds`, klasa `adafruit_lsm6ds.lsm6ds3.LSM6DS3`.
  Źródło: https://github.com/furbrain/CircuitPython_seeed_xiao_nRF52840/blob/main/seeed_xiao_nrf52840.py oraz https://learn.adafruit.com/adafruit-lsm6ds3tr-c-6-dof-accel-gyro-imu/python-circuitpython
- Sekwencja: `IMU_PWR` = True → sleep 0,05 s → `busio.I2C(board.IMU_SCL, board.IMU_SDA)` → `LSM6DS3(i2c)`.
- Maksymalna częstotliwość próbkowania w CircuitPythonie: **do zmierzenia w etapie 0** (cel: stabilne ≥ 50 Hz, lepiej 100 Hz).

## Akumulator i ładowanie
Źródło: Seeed wiki „Getting Started with XIAO nRF52840 Series” (https://wiki.seeedstudio.com/XIAO_BLE/)
- Układ ładowania BQ25101. Prąd domyślny ~50 mA (P0_13 jako wejście). 100 mA po ustawieniu P0_13 na niski. **Nie zmieniamy**: 150 mAh przy 50 mA to 0,33 C, bezpiecznie dla LP402025.
- Pomiar napięcia: ustawić `READ_BATT_ENABLE` niski, odczytać `VBATT`, potem pin z powrotem jako wejście. Cytat z wiki: gdy P0.14 jest wysoki, tor jest wyłączony, a P0.31 może zbliżyć się do granicy 3,6 V i uszkodzić pin. Dlatego **pomiar tylko z włączonym torem**.
- Przelicznik z biblioteki furbrain: `V = adc/65535 * reference_voltage * 3.1` (dzielnik ok. 1:3,1; wiki nie podaje stosunku, do skalibrowania multimetrem w etapie 0).
- Pady BAT+ / BAT− na spodzie płytki (wiki nie opisuje ich położenia; sprawdzić na nadruku i potwierdzić biegunowość multimetrem przed lutowaniem).
- Status ładowania: `CHARGE_STATUS` niski = ładuje (świeci czerwona dioda CHG).

## Bootloader i CircuitPython
- Wejście do bootloadera: dwukrotne szybkie wciśnięcie przycisku reset obok USB-C (Seeed wiki). Pojawia się dysk USB; nazwa **do potwierdzenia na płytce** (spodziewana `XIAO-SENSE`).
- CircuitPython 8.2+ dla nRF wymaga bootloadera UF2 **≥ 0.6.1**. Źródło: https://circuitpython.org/board/Seeed_XIAO_nRF52840_Sense/
- Najnowszy stabilny CircuitPython: **10.3.1**, plik `adafruit-circuitpython-Seeed_XIAO_nRF52840_Sense-en_US-10.3.1.uf2` (ta sama strona).
- Wersję bootloadera odczytujemy z pliku `INFO_UF2.TXT` na dysku bootloadera (do potwierdzenia na płytce).
- Aktualizacja bootloadera przez przeciągnięcie pliku UF2: najnowsze wydanie **0.11.0**, plik `update-xiao_nrf52840_ble_sense_bootloader-0.11.0_nosd.uf2`. Źródło: https://github.com/adafruit/Adafruit_nRF52_Bootloader/releases/latest (lista plików pobrana przez `gh api`).
- Po wgraniu CircuitPythona pojawia się dysk `CIRCUITPY` z plikiem `code.py`. Źródło: https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython
- Konsola szeregowa na Macu: `screen /dev/cu.usbmodem* 115200` (port pojawia się po wgraniu CircuitPythona; w systemie jest `screen`).

## Bluetooth
- CircuitPython: biblioteka `adafruit_ble` (instalacja przez `circup`, zainstalowany w `.venv`).
- Safari/iOS: brak Web Bluetooth w żadnej przeglądarce opartej o WebKit. Alternatywa na iPhonie: Bluefy (osobny stos BLE, wersja 3.9.3 ze stycznia 2026) lub WebBLE. Źródła: https://www.beaconzone.co.uk/blog/browser-support-for-web-bluetooth/ , https://pnnsoft.com/portfolio/detail/bluefy-web-bluetooth-api-solution-for-ios-devices
- Mac: Chrome zainstalowany, Bluetooth włączony (BCM_4387). Web Bluetooth w Chrome na Macu działa.

## Komputer (stan 2026-10-05)
macOS 26.6.2, Python 3.12.13 (Homebrew), `.venv` w katalogu repo: circup 3.1.0, pyserial, numpy, pandas, scipy, matplotlib. `screen` dostępny, brak minicom/picocom. Node 20 dostępny.

## Wyniki etapu 0 (2026-10-05, płytka na USB, bez akumulatora)
- Płytka: Seeed XIAO nRF52840 **Sense** (Board-ID `Seeed_XIAO_nRF52840_Sense`, naklejka bez słowa „Sense” jest wspólna dla obu wersji). UID `96409A09C7DC9BA7`.
- Bootloader fabryczny: UF2 0.6.1 (Nov 12 2021), SoftDevice S140 7.3.0. Dysk bootloadera nazywa się `XIAO-SENSE`. Aktualizacja do 0.11.0 niepotrzebna (minimum dla CircuitPythona to 0.6.1); plik leży w `firmware/dist/` na wszelki wypadek.
- Przycisk reset: srebrna kopułka ~1,5 mm pod napisem `RST`, obok gniazda USB-C. Wciskać wykałaczką.
- CircuitPython 10.3.1 wgrany przez przeciągnięcie pliku UF2. `cp` na macOS kończy się błędem „Input/output error”, bo płytka restartuje się w trakcie, zapis jest poprawny. Dysk `CIRCUITPY`, port `/dev/cu.usbmodem2101` (numer może się zmienić po zmianie gniazda USB).
- Biblioteki przez `circup install -r firmware/requirements-circup.txt`: adafruit_ble, adafruit_bus_device, adafruit_lsm6ds, adafruit_register.
- Test 1 (dioda): sekwencja czerwony, zielony, niebieski na konsoli potwierdzona.
- Test 2 (IMU): odpowiada pod 0x6A przez `board.IMU_SCL`/`board.IMU_SDA` po włączeniu `IMU_PWR`. Pętla odczytu acc+gyro w CircuitPythonie: **~316 Hz** (czujnik skonfigurowany na 208 Hz). Wniosek: CircuitPython wystarcza na próbkowanie 100–200 Hz; argument za C++ z tego powodu odpada. Spoczynkowy moduł przyspieszenia ~10,17 m/s² (ok. 3–4 % za dużo), kalibracja offsetu do zrobienia w etapie 1.
- Test 4 (napięcie, bez akumulatora): odczyt 3,9–4,3 V, pływający. Bez ogniwa pin widzi wyjście układu ładowania BQ25101 przy zasilaniu z USB. Nie jest to błąd pomiaru. Kalibracja dzielnika dopiero z akumulatorem i multimetrem.
- Test 3 (BLE): urządzenie rozgłasza się jako `EMOM-REP`. Skan z Maca (`tools/ble_scan.py`, biblioteka bleak): znaleziony, RSSI −59 dBm z odległości biurka, połączenie i echo przez Nordic UART działają.
  - Pułapka macOS: Python z Homebrew uruchamia się jako `Python.app`, którego Info.plist nie ma klucza `NSBluetoothAlwaysUsageDescription`. Bez niego macOS zabija proces (SIGABRT, raport w `~/Library/Logs/DiagnosticReports/Python-*.ips`, namespace TCC) zamiast zapytać o zgodę. Naprawa (wykonana 2026-10-05, kopia w `~/Desktop/Python-Info.plist.bak`):
    `plutil -insert NSBluetoothAlwaysUsageDescription -string "..." /opt/homebrew/Cellar/python@3.12/3.12.13_4/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/Info.plist`
    Aktualizacja Pythona przez Homebrew nadpisze ten plik; wtedy powtórzyć (ścieżka zmieni się razem z wersją).
  - Skrypty BLE uruchamiać z panelu terminala lub Terminala, nie z piaskownicy Claude Code.
- Akumulator (2026-10-05): biegunowość potwierdzona miernikiem (czerwony = +, czarny = −), 4,05 V na wtyczce przed podłączeniem. Przylutowany do padów na spodzie: czarny do pada „−” przy pinie 2, czerwony do pada „+” przy pinie 3. Wtyczka w połowie kabla zostaje jako rozłącznik. Goldpinów nie lutujemy, stykówka niepotrzebna (wszystko jest na płytce).
- Test 4 z akumulatorem (USB podłączone): stabilne 4,15 V przy współczynniku 3,1, `CHARGE_STATUS` niski = „charging”. Bez wpiętego ogniwa odczyt skacze między ~3,88 a ~4,28 V, a status mówi „nie ładuje”: tak wygląda ładowarka BQ25101 bez obciążenia, to sygnatura „brak akumulatora”, nie błąd pomiaru.
- Poprawka w `04_battery.py`: `READ_BATT_ENABLE` trzymany nisko przez cały czas pomiaru (niski to stan bezpieczny), uśrednianie 16 próbek, zielona dioda jako oznaka życia do testu pracy bez USB.
