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
- Wniosek metodyczny: przy ćwiczeniach naprzemiennych i złożonych prawda z liczenia na głos jest zawodna; wzorcem powinno być wideo z telefonu.
