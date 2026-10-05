# Timer `emom_timer.html` — punkty zaczepienia dla licznika (stan 2026-10-05)

Mapa z odczytu pliku (numery linii z 2026-10-05, mogą się przesunąć).

## Skąd timer wie, co teraz trwa
- `EXERCISES` (L308–379): `id`, `name`, `reps`, `range`, `work` (na czas), `alt`, `sided`, `bw`, `rest`. `EXMAP` id→ćwiczenie (L380). To `id` będzie kluczem profilu w urządzeniu.
- Plan: `buildPlan()` (L506) → `plan.seq` z `seqOf()` (L513), jeden wpis na minutę/blok, z polami `id, name, side, reps, work, rest, bw, seg, slot, round`.
- Bieżący wpis: `curIdx()` (L815), `currentItem()` (L816). Stan: `state` idle|prep|run|paused|done, `elapsed`, `prepEnd`, `SL()` długość bloku.
- **Zmiana minuty / ćwiczenia**: `tick()` (L894–911), linia ~904 `if(inMin===0){ beepMinute(); state="run"; }`. Tu wyślemy do urządzenia „start minuty, ćwiczenie X, mocowanie Y”. Przejście praca→przerwa wewnątrz minuty: `inMin===it.work` (L907).
- Osobne silniki: AMRAP (`AM`, L1216, `amTick` L1252), kalistenika (`CAL`, L1010), piramida (`PY`, L1116). Pompki/podciągnięcia w CAL i PY, tam przycisk „Zrobione” to naturalne miejsce na licznik z czujnika.

## Gdzie zapisujemy wynik
- `DB.log` w localStorage `emom_v2`. EMOM: `openSummary()` (L956) → `makeEntry()` (L524) z `perMin[m]={reps,kg}`. Powtórzenia z czujnika trafią do `plan.repsMin[m]` (ten sam mechanizm co ręczna korekta `t-reps-apply`, L1548), więc podsumowanie i korekta działają bez zmian.
- Kopia zapasowa JSON: `exportBackup()` (L1312). Nowe pola w `perMin` (np. `sensorReps`, znaczniki czasu) przejdą przez eksport automatycznie.

## Ręczne wejścia już istniejące
- EMOM: `#reps` + modal `t-reps` (zakres „ta minuta” / „od teraz”), kafelki kg `renderTiles()` (L826).
- AMRAP: przycisk „Zaliczone ✓” → `amNext()` (L1262).
- CAL/PY: `calMain` (L1074), `pyrMain` (L1175).

## Gdzie pokazać licznik na żywo
- Ekran EMOM `#s-timer`: `renderTimerInner()` (L843), elementy `#name`, `#reps`, `#clock > #sec`, `#phase`, `#next`. `fitClock()` (L837) skaluje cyfry do wolnej wysokości, nowy element trzeba uwzględnić w pomiarze.
- Ekran wspólny `#s-cal` dla CAL/AMRAP/PY: `#cal-sets`, `#cal-reps`, `#cal-main`.

## Platforma
- Brak `navigator.bluetooth`, Web Serial, service workera. Wzorce detekcji funkcji już są (`wakeLock`, `vibrate`, `canShare`), więc licznik dodamy tak samo: brak Web Bluetooth = brak przycisku, timer działa jak dziś.
- Dźwięk przez `AudioContext`, PWA przez `manifest.webmanifest`. W Bluefy trzeba te dwie rzeczy przetestować osobno.
