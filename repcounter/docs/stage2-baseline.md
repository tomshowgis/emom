# Etap 2 — algorytm bazowy (stan 2026-10-11)

Kod: `analysis/baseline.py` (algorytm), `analysis/evaluate.py` (raport), `analysis/debug_plot.py` (wykres diagnostyczny jednej serii), `analysis/dataset.py` (wczytanie i przepróbkowanie do 100 Hz). Raporty w `analysis/reports/`.

Uruchomienie (z `repcounter/`): `../.venv/bin/python -m analysis.evaluate`

## Metoda
Jedna wspólna procedura, profil ćwiczenia to tylko progi.
1. **Wybór sygnału:** z 6 osi ta, która ma najwięcej energii w paśmie powtórzeń (1/period_max … 1/period_min). Nie zakładamy z góry, która oś niesie ruch.
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
| Halo | 3 | 3 | 2 |
| Goblet Squat | 4 | 3 | 4 |
| Goblet Shoulder Press | 6 | 3 | 15 |
| Curl + Press | 4 | 2 | 9 |
| **razem** | **34** | **28 (82 %)** | **30 (9,1 %)** |

Przebieg iteracji: naiwne szczyty na jednej osi → 14 % błędu; + bramka obrotu i min(szczyty, doliny) → 11 %; + granice tempa w profilach → 9,1 %. Brudne serie swingu, sumo i bent row liczą się bez błędu.

## Znane błędy (po jednej serii każdy)
- **Zmiana tempa w serii** (curl + press 200049: szybko, potem wolno; press 160802 mieszane): jeden globalny okres nie pasuje do obu połówek. Potrzebne tempo lokalne (okno przesuwne) albo liczenie bez wąskiego pasma.
- **Wejście w serię** (squat 153259): podniesienie z podłogi i pierwszy ruch dają ekstrema o 65–75 % wysokości powtórzenia, poniżej progu 45 %. Ostrzejszy próg psuje brudne serie (sprawdzono 0,55 i 0,65).
- **Wolne wyciskanie** (160725, 7 powt.): mała amplituda ruchu względem obrotów kettlebella na granicach.
- **Brudne wyciskanie** (160834) i **brudny curl + press** (200211): zakłócenia podobne do powtórzeń.

## Następne kroki
1. Tempo lokalne: okres szacowany w oknie ~4 powtórzeń, przesuwanym po serii.
2. Więcej danych tam, gdzie błędy: wyciskanie i curl + press (wolne, mieszane, brudne), halo z wideo, 12 kg.
3. Etap 2b: cechy per cykl (amplituda, czas, obrót) i klasyfikator cykl/nie-cykl zamiast ręcznych progów, uczony na tych samych nagraniach.
