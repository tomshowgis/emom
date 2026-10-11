# Dziennik nagrań i obserwacji sygnału (dla etapu 2)

Nagrania leżą lokalnie w `repcounter/data/raw/` (poza gitem). Tu tylko wnioski, które algorytm musi uwzględnić.

## Ustalenia ogólne
- 100 Hz, 0 zgubionych ramek we wszystkich seriach z 2026-10-05 i 2026-10-10 (biurko i pokój, kilka metrów od Maca).
- Maksymalne przyspieszenie: 44 m/s² swing szybki, 59 m/s² halo brudne; limit czujnika 78 m/s² (8 g). Zakres wystarcza przy 8 kg.
- Nagranie zaczyna się przed podniesieniem kettlebella z podłogi i kończy po odstawieniu. Ruchy przygotowawcze są w danych i algorytm musi je odrzucać; to realistyczne (w treningu też będą).
- Naiwne zliczanie szczytów (filtr 3 Hz, oś o największej wariancji, prominencja 0,5·σ, odstęp 0,6 s) to tylko podgląd, nie algorytm.

## Biceps Curl (kettlebell, USB do góry) — 5 serii po 10, 2026-10-05/10
- Najczystszy sygnał: żyroskop Y (±5–6 rad/s, jedna sinusoida na powtórzenie) oraz acc Z (przelewanie grawitacji).
- Naiwnie 10/10 w 4 seriach normalnych; w szybkiej 11, bo odstawienie kettlebella daje garb ~4× niższy od szczytu powtórzenia. Potrzebny próg względem typowej wysokości szczytu w serii.
- Brak jeszcze serii wolnej i brudnej.

## Russian Swing (kettlebell, USB do góry) — 5 serii po 10, 2026-10-10
- Dwa szczyty acc X na powtórzenie: duży na górze ruchu, mały (~1/3) przy przejściu przez dół. Naiwnie 19–21 na 10. Próg 50 % typowego szczytu zostawia 10.
- Żyroskop Y: 10 wyraźnych zębów piły na serię, niezależny drugi sygnał.
- Seria 144253 (wolna): liczba powtórzeń orientacyjna (`count_uncertain`), nie liczyć do trafności. Seria 144410: brudna (odstawienie po 5., poprawka chwytu).

## Halo (Alt) (kettlebell dnem do góry, USB w dół, czujnik po stronie ciała) — 5 serii, wpisane po 10, 2026-10-10
- Chwyt za rogi dnem do góry obraca front kuli do ciała: czujnik zostaje na tej samej ściance, ale jest między ćwiczącym a kettlebellem. Technika jak na https://youtube.com/shorts/k-YcemjRASg (kettlebell idzie lekko na ukos w pierwszej fazie, w stronę kierunku okrążenia).
- Ruch widać na wszystkich osiach; okrążenie = pełny cykl grawitacji na acc X i Y plus obrót wokół pionu (gyro Z ±4–7 rad/s) o znaku zmieniającym się co okrążenie (naprzemienność).
- Start serii: podniesienie z podłogi do klatki z obrotem dnem do góry. W seriach 150221, 150326, 150405 daje szczyt acc X **bez** obrotu gyro Z → do odrzucenia po żyroskopie. W 150133 pierwszy szczyt ma już obrót.
- Po odrzuceniu szczytów bez obrotu zostaje 10 (150221) albo 11 (150133, 150326, 150405). Rozbieżność ±1 nierozstrzygnięta: dodatkowe okrążenie przy liczeniu na głos albo powrót kettlebella na koniec serii wygląda jak okrążenie. **Do rozstrzygnięcia nagraniem z wideo.** Do tego czasu serie halo traktować jako prawdę ±1.
- **Seria 151425 z wideo (prawda = 4 okrążenia, pauzy 2 s po podniesieniu i przed odstawieniem):** na acc X 5 szczytów, z czego pierwszy (podniesienie, 4,9 s) ma gyro Z ≈ 0,5 rad/s, a cztery kolejne 2,3–3,0 rad/s. Reguła „szczyt acc X + obrót gyro Z ≥ ~1,5 rad/s” daje dokładnie 4/4. Odstawienie nie wytworzyło szczytu z obrotem.
- Wniosek: w seriach 150133, 150326, 150405 sygnał pokazuje 11 obrotów przy wpisanych 10, czyli najpewniej liczenie na głos zgubiło jedno okrążenie. Oznaczone `count_uncertain`.
- Wniosek metodyczny: przy ćwiczeniach naprzemiennych i złożonych prawda z liczenia na głos jest zawodna; wzorcem powinno być wideo z telefonu (pole `ground_truth: "video"` w JSON).

## Goblet Squat (kettlebell, USB do góry) — 4 serie (10, 10, 6 wolna, 7 szybka), 2026-10-11
- Powtórzenie = mały szczyt acc X na starcie zejścia, głęboka dolina na dole (hamowanie i zawrócenie), drugi szczyt na górze. Naiwnie 22 na 10. Dolin dokładnie 10; dla przysiadu znacznikiem jest minimum, nie maksimum.
- Żyroskop prawie milczy (std < 0,5 rad/s). Podniesienie z podłogi = pojedynczy szczyt 2× wyższy od reszty.
- Wniosek na algorytm bazowy: liczyć pełne cykle (filtr pasmowy wokół wykrytego tempa + przejścia przez zero), a nie szczyty o zadanej polaryzacji; profil ćwiczenia trzyma tylko progi (tempo, amplituda, obrót).

## Goblet Shoulder Press (kettlebell dnem do góry, USB w dół, czujnik od strony zewnętrznej: czujnik–kettlebell–człowiek) — 6 serii, 2026-10-11
- Obrót dnem do góry przerzuca acc X z −10 na +10 na czas serii; powtórzenia to oscylacje ±5 m/s² na tym plateau. Naiwnie 11–12 na 10: jeden dodatkowy garb w obrębie plateau (prawdopodobnie ustawienie po obrocie lub ostatnie opuszczenie) plus odstawienie poza plateau.
- Sygnał słabszy względem tła niż w curlu i swingu; dobry test czułości dla liczenia cykli. Żyroskop nieużyteczny poza momentem obrotu kettlebella (gyro X/Z ±4 rad/s na starcie i końcu = wyraźne granice serii!).
- Seria 160834 brudna, 160725 wolna (7 powt.).

## Sumo High Pull (kettlebell, USB do góry) — 4 serie (10, 10, 5 szybka, 6 brudna), 2026-10-11
- Najłatwiejszy dotąd przypadek: naiwnie 10/10, 10/10, 5/5 na acc X (jeden wyraźny szczyt na powtórzenie, podniesienie i odstawienie nie generują szczytów o podobnej wysokości). Brudna seria (164226, „kilka powtórzeń nie czysto technicznie”): 8 przy 6.
- Ruch w acc X z lekkim udziałem gyro Y; brak podwójnego szczytu jak w swingu mimo tej samej rodziny balistycznej.

## Luki czasu w nagraniach z 2026-10-11 po 16:40
- Serie 164018, 164051, 164112, 164226 (sumo high pull) i 164533, 164626, 164706, 164737 (curl + press) mają 2,8–12,6 s brakującego czasu (`gaps: true`). Nie liczyć do trafności; do powtórzenia. Przyczyna i naprawa: `hardware-notes.md`, sekcja „Przepustowość BLE”.
- Wstępne obserwacje z tych serii (wymagają potwierdzenia na czystych nagraniach): sumo high pull = jeden szczyt acc X na powtórzenie, naiwnie trafia; curl + press = szerokie plateau acc Z na powtórzenie z dwoma garbami (curl i press), naiwnie 17 na 10.
