# Etap 0 — plan testów (płytka na stykówce, zasilanie z USB)

Kod testów: `firmware/stage0/`. Każdy test kopiujesz na dysk `CIRCUITPY` jako `code.py`. Płytka restartuje program automatycznie po zapisie.

## Przygotowanie
1. Wlutuj listwy goldpinów (po 7 na stronę) i wepnij płytkę w stykówkę. Akumulatora jeszcze nie podłączaj.
2. Podłącz kablem USB-C do Maca.

## Krok 1 — bootloader
1. Dwa razy szybko wciśnij reset (mały przycisk obok USB-C).
2. W Finderze powinien pojawić się dysk (spodziewana nazwa `XIAO-SENSE`).
3. Otwórz na nim plik `INFO_UF2.TXT` i wklej mi jego treść. Szukamy linii z wersją bootloadera.

## Krok 2 — aktualizacja bootloadera (tylko gdy wersja < 0.6.1)
1. Przeciągnij `update-xiao_nrf52840_ble_sense_bootloader-0.11.0_nosd.uf2` na dysk bootloadera.
2. Płytka zrestartuje się, dysk zniknie i wróci. Powtórz krok 1 i wklej nową treść.

## Krok 3 — CircuitPython
1. Przeciągnij `adafruit-circuitpython-Seeed_XIAO_nRF52840_Sense-en_US-10.3.1.uf2` na dysk bootloadera.
2. Po kilku sekundach pojawia się dysk `CIRCUITPY`.
3. W terminalu: `ls /dev/cu.usbmodem*` — powinien być nowy port.
4. Biblioteki: `.venv/bin/circup install -r repcounter/firmware/requirements-circup.txt`.
5. Konsola: `screen /dev/cu.usbmodem<numer> 115200` (wyjście: Ctrl-A, potem K, potem Y).

## Test 1 — dioda
Skopiuj `01_blink.py` jako `CIRCUITPY/code.py`. Oczekiwane: czerwony, zielony, niebieski, każdy 1 s, w kółko. Na konsoli nazwy kolorów.

## Test 2 — IMU i częstotliwość próbkowania
Skopiuj `02_imu.py`. Oczekiwane co 2 s linia z 6 liczbami i `poll NNN Hz`.
- Płytka leży płasko: jedna z osi przyspieszenia ≈ ±9,8, pozostałe ≈ 0. Zapisz, która to oś i ze znakiem.
- Obróć płytkę na bok: 9,8 przechodzi na inną oś.
- Potrząśnij: żyroskop odchyla się od zera.
- Wklej mi 3 linie w spoczynku i wartość `poll`. To pierwszy pomiar pod decyzję CircuitPython kontra C++.

## Test 3 — Bluetooth
Skopiuj `03_ble_advertise.py`.
- iPhone: zainstaluj nRF Connect (Nordic, bezpłatna), skanuj, powinien być `EMOM-REP`. Połącz: niebieska dioda się zapala. W zakładce Nordic UART wyślij tekst, wróci `echo: ...`.
- Mac: w Chrome otwórz `chrome://bluetooth-internals`, zakładka Devices, Start Scan, szukaj `EMOM-REP`.
Wklej mi, co widziałeś (nazwa, siła sygnału RSSI, czy echo wróciło).

## Test 4 — napięcie akumulatora
1. Skopiuj `04_battery.py` bez akumulatora. Oczekiwane: `vbat` blisko 0 V lub szum, status „not charging / full”. Wklej linię.
2. **Multimetr na wtyczce akumulatora (zakres DC 20 V)**: czerwona sonda na jeden styk, czarna na drugi. Odczyt dodatni około 3,7–4,1 V oznacza, że czerwona sonda jest na BAT+. Zapisz, który kolor przewodu to plus. Wklej mi wynik, zanim cokolwiek przylutujesz.
3. Dopiero po moim potwierdzeniu: odłącz USB, przylutuj końcówki od strony płytki do padów BAT+ i BAT− na spodzie (wtyczka w połowie kabla zostaje jako rozłącznik). Sprawdź multimetrem na padach, że nie ma zwarcia i że biegunowość się zgadza.
4. Wepnij wtyczkę, podłącz USB. Oczekiwane: status „charging”, czerwona dioda CHG świeci, `vbat` 3,6–4,2 V. Porównaj z multimetrem na wtyczce i wklej obie liczby do kalibracji.

## Co zapisujemy po etapie 0
Wersja bootloadera, orientacja osi płytki, zmierzona częstotliwość odczytu, RSSI, przelicznik napięcia. Wszystko trafia do `hardware-notes.md`.
