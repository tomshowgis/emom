# Etap 1 — rejestrator i przeglądarka nagrań

## Uruchomienie
1. Płytka z firmware `firmware/stream/code.py` (skopiowane na `CIRCUITPY/code.py`). Po starcie rozgłasza się jako `EMOM-REP`; czerwona dioda = czeka na połączenie, niebieska = połączono, zielona mruga przy wysyłaniu ramek.
2. Na Macu, **w Terminalu lub panelu terminala** (nie w piaskownicy Claude Code, bo macOS blokuje tam Bluetooth):
   ```
   cd /Users/tszoldrowski/repo/emom && .venv/bin/python repcounter/tools/recorder_app.py
   ```
3. Chrome: http://127.0.0.1:8050

## Nagrywanie serii
1. „Połącz” → status „połączono”, napięcie baterii.
2. Wybierz ćwiczenie (lista z `EXERCISES` timera + pompki/podciągnięcia) i mocowanie.
3. „Start serii” tuż przed pierwszym powtórzeniem, „Stop” zaraz po ostatnim. Wykres na żywo pokazuje ostatnie 10 s.
4. Wpisz faktyczną liczbę powtórzeń (liczoną na głos), tempo, uwagi → „Zapisz”.
   Pliki: `data/raw/YYYY-MM-DD/HHMMSS_<ćwiczenie>_<mocowanie>.csv` (t_ms, ax, ay, az [m/s²], gx, gy, gz [rad/s]) + `.json` z opisem. Folder `data/` jest poza gitem.

## Przeglądanie
Zakładka „Przeglądanie”: zaznacz jedną lub kilka sesji → osobne wykresy dla każdej osi, moduł przyspieszenia i prędkości kątowej, wspólna oś czasu od 0 s, przybliżanie myszą (zaznacz obszar; dwuklik = reset).

## Protokół strumienia (firmware ↔ host)
- Nordic UART. Ramka: `A5 5A`, typ (1 = IMU, 2 = status), `seq` u16, dalej payload. IMU: `t_ms` u32 pierwszej próbki, `n`, `dt_ms`, potem n × 6 × int16 (acc ×400, gyro ×1000). Status co 2 s: `t_ms`, `vbat_mV`, ładowanie, czy strumień, częstotliwość.
- Komendy hosta: `S` start, `X` stop, `B` status, `M<n>` rozmiar pakietu hosta (MTU−3). CircuitPython zgłasza `max_packet_length` = 20 mimo negocjacji, dlatego host podaje własny MTU; macOS daje 247 → 19 próbek w ramce.
- Zmierzone 2026-10-05: 100,1 Hz, 0 zgubionych ramek w 10 s, RSSI −60…−67 dBm przy biurku. Odstępy próbek 4–16 ms (drgania pętli), średnio 10 ms.

## Co dalej w etapie 1
- Pierwsze nagrania prawdziwych serii (swing 8 kg, płytka na przodzie kettlebella w połowie wysokości, USB do góry, pod spodem taśma izolująca od żeliwa), sprawdzenie zasięgu i gubienia ramek w ruchu.
- Kalibracja offsetu akcelerometru (moduł w spoczynku ~10,1 zamiast 9,81).
- Zaznaczanie początku/końca serii wewnątrz nagrania, jeśli start/stop ręczny okaże się za mało dokładny.
