# EMOM — repozytorium

Odpowiadaj po polsku. Kod, nazwy plików i identyfikatory po angielsku. Komunikaty commitów po polsku (jak dotąd).

## Co tu jest
- `emom_timer.html` — cała aplikacja treningowa w jednym pliku (timer EMOM/tabata, AMRAP, kalistenika, piramida, dziennik, eksport FIT i kopia JSON). Działa offline i z pliku na iPhonie (PWA). Produkcja: GitHub Pages, repo `tomshowgis/emom`, URL https://tomshowgis.github.io/emom/emom_timer.html
- `yt_embed.html` — pośrednik dla playera YouTube przy otwarciu z `file://`.
- `manifest.webmanifest`, `icon-*.png`, `icon.svg` — PWA.
- `emom_timer_v1.html` — stara wersja, nie ruszać.
- `repcounter/` — licznik powtórzeń na XIAO nRF52840 Sense (projekt w toku). Założenia: `repcounter/docs/brief.md`. Fakty o sprzęcie ze źródłami: `repcounter/docs/hardware-notes.md`. Punkty zaczepienia w timerze: `repcounter/docs/timer-integration-notes.md`.
- `.venv/` — Python do narzędzi licznika (circup, pyserial, numpy, pandas, scipy, matplotlib). Uruchamiaj przez `.venv/bin/python`.

## Zasady dla timera
- Jeden plik, bez bundlera i zależności. Każda zmiana ma działać także offline i z `file://`.
- Dane użytkownika w localStorage pod kluczem `emom_v2`; zmiany schematu muszą być zgodne wstecz i przechodzić przez kopię JSON (`exportBackup`/`parseBackup`).
- Numer wersji widoczny na ekranie głównym; podbijaj przy wdrożeniu.
- Testy: statyczny serwer z `.claude/launch.json`, interakcje przez JS w podglądzie przeglądarki.
- Timer ma działać normalnie bez czujnika. Funkcje licznika tylko za detekcją `navigator.bluetooth`.

## Zasady dla licznika (`repcounter/`)
- Pełna lista ustaleń w `repcounter/docs/brief.md`. Najważniejsze:
  - Urządzenie nie rozpoznaje ćwiczenia; timer wysyła `id` ćwiczenia i miejsce mocowania, urządzenie stosuje profil. Kanał BLE dwukierunkowy.
  - Profil ćwiczenia to dane kluczowane po `id` z `EXERCISES`. Licznik tylko dla ćwiczeń z zatwierdzonym profilem.
  - Najpierw dane, potem algorytm. Bazowe wykrywanie szczytów, potem ML na tych samych nagraniach z uczciwym porównaniem i wyjaśnieniem każdego kroku.
  - CircuitPython na start; środowisko Arduino (C++ na tej samej płytce) dopiero po pomiarze, który pokaże, że nie wystarcza.
  - Faktów o płytce nie bierz z pamięci; sprawdź w dokumentacji i zapisz ze źródłem w `hardware-notes.md`.
  - Akumulator: biegunowość multimetrem przed lutowaniem; prąd ładowania domyślny; napięcie czytać tylko z włączonym torem (`READ_BATT_ENABLE` niski).
  - Surowych nagrań w `repcounter/data/` nigdy nie nadpisuj.
- Po każdym etapie zatrzymaj się i poczekaj na wynik testu użytkownika. Użytkownik nie widzi tego, co Ty: przy teście podawaj kroki i oczekiwany efekt.
- Struktura: `firmware/` (CircuitPython), `tools/` (rejestrator, wizualizacja), `data/` (CSV + metadane), `analysis/` (algorytmy, ML, raporty), `hardware/` (obudowa), `docs/`.
