# Etap 2 — algorytm bazowy (stan 2026-10-12)

Kod: `analysis/baseline.py` (algorytm), `analysis/evaluate.py` (raport), `analysis/debug_plot.py` (wykres diagnostyczny jednej serii), `analysis/dataset.py` (wczytanie i przepróbkowanie do 100 Hz). Raporty w `analysis/reports/`.

Uruchomienie (z `repcounter/`): `../.venv/bin/python -m analysis.evaluate`

## Metoda
Jedna wspólna procedura, profil ćwiczenia to tylko progi.
1. **Sygnał do liczenia:** pierwsza składowa główna (PCA) wektora przyspieszenia po filtracji do pasma powtórzeń, czyli rzut na kierunek największego ruchu. Pomysł użytkownika (wykorzystać wzorzec wielu osi, nie jedną oś); poprzednia wersja brała jedną oś o największej energii i dawała 28/34. Czyste liczenie obrotów fazy w płaszczyźnie PCA nie działa (ruch jest liniowy, nie kołowy: 0/34 bez żyroskopu), ale PCA jako sygnał dla reszty procedury tak.
2. **Tempo serii:** okres T z autokorelacji tego sygnału w granicach tempa z profilu; wśród kandydatów w 5 % od maksimum wygrywa najkrótszy. Normalizacja obciążona (porównano z nieobciążoną i ograniczoną: obciążona daje najmniej błędów; nieobciążona przy długich opóźnieniach łapie strukturę całej serii).
3. **Filtr pasmowy** wokół 1/T (0,5–1,6 × f0): tłumi drugą harmoniczną, czyli podwójne szczyty swingu i dwa podruchy curl + press.
4. **Ekstrema z bramkami:** szczyty i doliny w odstępie ≥ 0,6 T, wysokość ≥ 45 % mediany górnej połowy (odrzuca odstawienie/podniesienie), maks. |gyro| w oknie ±0,35 T w przedziale 0,35–2,2 × mediany (odrzuca obrót kettlebella dnem do góry i podniesienie bez obrotu w halo), bez izolowanych cykli dalej niż 2,5 T od sąsiadów.
5. **Liczba powtórzeń = min(szczyty, doliny):** pełny cykl potrzebuje obu; samotne ekstremum z wejścia w serię lub odstawienia nie liczy się.

Profile (granice tempa jednego powtórzenia, fizjologiczne): curl 0,8–8 s, swing 0,8–4, sumo 0,8–6, row 0,6–6, press 0,8–4,5, squat 1,3–8, curl+press 2,4–8 (podłoga powyżej podruchu), halo 1,5–5.

## Wynik na 34 czystych seriach (328 powtórzeń), kryterium |błąd| ≤ ceil(prawda/20)
| ćwiczenie | serie | w tolerancji | błędne powt. |
|---|---|---|---|
| Biceps Curl | 5 | 5 | 0 |
| Russian Swing | 4 | 4 | 0 |
| Sumo High Pull | 4 | 4 | 0 |
| Goblet Bent Row | 4 | 4 | 0 |
| Halo | 3 | 3 | 1 |
| Goblet Squat | 4 | 4 | 2 |
| Goblet Shoulder Press | 6 | 5 | 8 |
| Curl + Press | 4 | 2 | 11 |
| **razem** | **34** | **31 (91 %)** | **22 (6,7 %)** |

Przebieg iteracji: naiwne szczyty na jednej osi → 14 % błędu; + bramka obrotu i min(szczyty, doliny) → 11 %; + granice tempa w profilach → 9,1 %; + PCA zamiast jednej osi → 6,7 %. Wszystkie czyste serie w tempie normalnym, wolnym i szybkim liczą się w tolerancji; zostają brudne i mieszane.

## Znane błędy (stan po PCA)
- **Zmiana tempa w serii** (curl + press 200049: szybko, potem wolno): jeden globalny okres nie pasuje do obu połówek. Potrzebne tempo lokalne (okno przesuwne). Sprawdzono też fazę chwilową (Hilbert) zamiast ekstremów: 31/34 i 19 błędnych, ale psuje jedną czystą serię wyciskania, więc na razie zostają ekstrema.
- **Brudne wyciskanie** (160834) i **brudny curl + press** (200211): zakłócenia (odstawienie, poprawka chwytu) podobne do powtórzeń; tu pomoże dopiero klasyfikator cykli (etap 2b).
- Wcześniejsze błędy na wejściu w serię (squat) i wolnym wyciskaniu zniknęły po przejściu na PCA.

## Następne kroki
1. Tempo lokalne: okres szacowany w oknie ~4 powtórzeń, przesuwanym po serii.
2. Więcej danych tam, gdzie błędy: wyciskanie i curl + press (wolne, mieszane, brudne), halo z wideo, 12 kg.
3. Etap 2b: cechy per cykl (amplituda, czas, obrót) i klasyfikator cykl/nie-cykl zamiast ręcznych progów, uczony na tych samych nagraniach.
