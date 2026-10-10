# Licznik powtórzeń — założenia projektu (brief)

Budujemy od zera mały licznik powtórzeń ćwiczeń, który współpracuje z moim timerem treningowym. Ty piszesz oprogramowanie i prowadzisz mnie przez testy na sprzęcie. Ja lutuję, noszę urządzenie i wykonuję ćwiczenia. Odpowiadaj po polsku, kod i nazwy w repozytorium po angielsku.

## Cel
Urządzenie przyczepione magnesami do żeliwnego kettlebella albo do koszulki liczy powtórzenia i na bieżąco wysyła wynik przez Bluetooth do timera EMOM, który pokazuje licznik dla aktualnego ćwiczenia.

Ćwiczenia na start: biceps curl, situp press, side drags (naprzemiennie), swing, pompki, podciągnięcia. Overhead march jest na czas, więc go nie liczymy.

Side drags: na razie każda strona liczy się jako jedno powtórzenie. Docelowo w aplikacji ma być konfiguracja sposobu liczenia dla ćwiczenia (strona = 1 albo para = 1).

Docelowo licznik ma obsłużyć całą bibliotekę timera (70 ćwiczeń, z czego 12 jest na czas i ich nie liczymy). Ćwiczenia grupujemy w rodziny ruchu o podobnej sygnaturze dla czujnika:
- balistyczne z biodra (swingi, high pull, clean, RDL),
- wyciskanie i uginanie (curl, press, floor press, front raise),
- przysiady i wykroki z kettlem przy klatce (goblet squat, lunge, thruster),
- naprzemienne (side drags, halo, bent row alt, alternating swing),
- bez kettlebella, czujnik na ciele (pompki, podciągnięcia, burpee, plank taps),
- złożone, jedno powtórzenie z kilku podruchów (curl + press, swing clean push press).

Startowa szóstka dotyka pięciu z tych rodzin. Kolejne ćwiczenia dochodzą partiami: najpierw po jednym z rodziny jeszcze niepokrytej (np. goblet squat, thruster), potem reszta po 2–3 serie walidacyjne każde.

## Sprzęt, który mam
- Płytka Seeed Studio XIAO nRF52840 Sense: Bluetooth LE, akcelerometr z żyroskopem LSM6DS3TR-C, dioda RGB, ładowanie akumulatora przez USB-C, bootloader UF2 (podwójne wciśnięcie reset).
- Akumulator Li-Pol Akyga LP402025, 150 mAh, z zabezpieczeniem PCM. Jeszcze nieprzylutowany, pola BAT+ i BAT− są na spodzie płytki.
- Magnesy 6×3 mm i drukowana obudowa 24,4 × 31,3 × 15 mm.
- Komputer (Mac) z kablem USB-C, lutownica, multimetr. Telefon: iPhone.

## Co już istnieje
To repozytorium (`emom`) zawiera timer: `emom_timer.html`, samodzielna strona z timerem EMOM (duże odliczanie, sygnał co minutę). Timer wie, jakie ćwiczenie trwa w danej minucie. Przeczytaj ten plik, zanim zaproponujesz integrację. Licznik powstaje w tym samym repozytorium, w podfolderze `repcounter/`.

## Ustalenia, których się trzymamy
- Urządzenie nie rozpoznaje ćwiczenia. Timer mówi mu, co teraz trwa, a urządzenie stosuje progi dobrane pod to ćwiczenie (oś ruchu, amplituda, realistyczne tempo).
- Profil ćwiczenia to dane, nie kod: tabela parametrów kluczowana po `id` z listy `EXERCISES` w timerze. Timer wysyła id, urządzenie wybiera profil. Nieznane id oznacza profil ogólny rodziny albo „nie liczę”.
- Timer pokazuje licznik tylko dla ćwiczeń z zatwierdzonym profilem i oznacza je w bibliotece. Żadnych przypadkowych liczb dla ćwiczeń bez walidacji.
- Z tego wynika, że kanał Bluetooth musi być dwukierunkowy: timer → urządzenie (ćwiczenie, miejsce mocowania, start minuty / zerowanie), urządzenie → timer (zdarzenia). Droga „urządzenie jako klawiatura Bluetooth” jest jednokierunkowa i nie spełnia tego wymagania; można ją rozważyć tylko jako awaryjny tryb z ręcznym wyborem ćwiczenia.
- Docelowo liczenie odbywa się w urządzeniu, a przez Bluetooth idą tylko zdarzenia, nie surowy strumień. Każde powtórzenie jest wysyłane osobno ze znacznikiem czasu, nie tylko suma. Timer sam przypisuje powtórzenie do minuty; zostaje pełny ślad do ręcznej korekty.
- Dla każdego powtórzenia urządzenie zapisuje proste cechy (czas trwania, amplituda, szczyt przyspieszenia, obrót). Na razie ich nie używamy; ocena jakości wykonania jest odłożona na później.
- Jedno miejsce mocowania nie obsłuży wszystkiego: przy ćwiczeniach z kettlebellem czujnik jest na nim, przy pompkach i podciągnięciach na ciele.
- Miejsce na kettlebellu (decyzja 2026-10-05): **przód kuli, w połowie wysokości**, płytka spodem do żeliwa, USB do góry w stronę uchwytu. Nie dno, bo urządzenie byłoby miażdżone przy odstawianiu. Powierzchnia wypukła: obudowa potrzebuje wklęsłej ścianki lub magnesów na środku. Na czas nagrań (etapy 1–2) mocowanie to gumki recepturki i tym się nie zajmujemy; docelowe mocowanie z szybkim przenoszeniem między kettlebellami wymyśla użytkownik później.
- Najpierw dane, potem algorytm. Żadnych progów zgadywanych bez nagrań.
- Uczenie maszynowe jest celem projektu, także edukacyjnym: chcę je zrozumieć, nie tylko użyć. Kolejność: najpierw proste wykrywanie szczytów jako punkt odniesienia (etap 2), potem ML na tych samych nagraniach (etap 2b) z uczciwym porównaniem trafności. Do urządzenia trafia to, co wygrywa na danych testowych i mieści się na płytce. Każdy krok ML tłumacz mi po drodze: jakie cechy, jaki model, dlaczego, jak ocenić, gdzie się przeucza.
- Nagrania robię przy okazji normalnych treningów, nie jako osobne sesje. Rejestrator ma to umożliwiać: wybieram set w timerze, urządzenie nagrywa, po minucie wpisuję prawdziwą liczbę powtórzeń.
- Minimum nagrań na ćwiczenie w etapie 2: 5 serii, w tym tempo wolne i szybkie oraz celowo „brudne” serie (odstawienie kettlebella, poprawka chwytu, przerwa w środku serii).
- Zacznij od CircuitPythona, bo znam Pythona. Zmianę na środowisko Arduino (C++ na tej samej płytce XIAO, nie na innym sprzęcie) zaproponuj dopiero wtedy, gdy pokażesz pomiarem, że częstotliwość próbkowania albo czas pracy na baterii nie wystarcza, albo gdy wybrany model ML nie da się uruchomić w CircuitPythonie.
- Safari na iPhonie nie obsługuje Web Bluetooth. Decyzja (2026-10-05): w etapach 0–3 łączymy się Mac ↔ urządzenie (Chrome z Web Bluetooth i skrypty Pythona). W etapie 4 powstaje natywna nakładka iOS (Swift, WKWebView z timerem + CoreBluetooth). Telefon dochodzi po fazie testów. Bluefy nie używamy.

## Etapy
Po każdym etapie zatrzymaj się i poczekaj na mój wynik testu.

0. Uruchomienie: CircuitPython na płytce, miganie diodą, odczyt akcelerometru i żyroskopu na porcie szeregowym, widoczność urządzenia w Bluetooth, odczyt napięcia akumulatora. Porównanie dróg Bluetooth dla iPhone'a.
1. Rejestrator i narzędzie analityczne (osobna aplikacja na komputer, w `repcounter/tools/`): płytka wysyła surowe odczyty z czasem, aplikacja zapisuje sesje do CSV z opisem: ćwiczenie (id z timera), miejsce mocowania, faktyczna liczba powtórzeń podana przeze mnie, tempo, uwagi. Ta sama aplikacja pokazuje nagrania: wykresy osobno dla każdej osi akcelerometru i żyroskopu oraz wektor wypadkowy, z zaznaczonymi seriami i ćwiczeniami na osi czasu, z możliwością przybliżania i porównania kilku serii obok siebie. Później dochodzą tu wykryte powtórzenia nałożone na sygnał i raporty trafności. Technologię (np. Python + Plotly/Dash w przeglądarce) zaproponuj z uzasadnieniem.
2. Algorytm bazowy na komputerze: wykrywanie powtórzeń na nagranych danych, osobno dla każdej rodziny i ćwiczenia, z raportem trafności względem moich liczb. Cel: błąd najwyżej 1 powtórzenie na 20. Nagrania służą jako dane testowe.
2b. Uczenie maszynowe na komputerze: te same nagrania, porównanie z algorytmem bazowym, wyjaśnienie każdego kroku. Decyzja, co idzie na płytkę.
3. Liczenie w urządzeniu: przeniesienie algorytmu na płytkę i protokół Bluetooth (zdarzenia powtórzeń ze znacznikiem czasu, wybór ćwiczenia i miejsca mocowania, zerowanie / start minuty, stan baterii).
4. Integracja z timerem: licznik na żywo, zerowanie przy zmianie ćwiczenia, zapis wyniku każdej minuty, ręczna korekta, konfiguracja sposobu liczenia dla ćwiczenia. Timer ma działać normalnie także bez czujnika.
5. Zasilanie: usypianie, budzenie ruchem, pomiar czasu pracy na baterii.

## Jak pracujemy
- Nie widzisz sprzętu. Przy każdym teście podaj mi dokładne kroki i to, co powinienem zobaczyć. Wynik wkleję Ci z powrotem.
- Faktów o płytce (piny, adresy, biblioteki, sposób wgrywania) nie bierz z pamięci. Sprawdź je w dokumentacji Seeed i CircuitPython i zapisz ze źródłem w `repcounter/docs/hardware-notes.md`.
- Akumulator: zanim każesz mi lutować, każ sprawdzić biegunowość multimetrem. Nie zmieniaj prądu ładowania z domyślnego. Sprawdź w dokumentacji Seeed, jak bezpiecznie czytać napięcie akumulatora podczas ładowania.
- Struktura w repozytorium: `repcounter/firmware/`, `repcounter/tools/` (rejestrator i narzędzie analityczne), `repcounter/data/` (surowe nagrania CSV z metadanymi), `repcounter/analysis/` (algorytmy, ML, raporty), `repcounter/hardware/`, `repcounter/docs/`. Aplikacją treningową jest istniejący `emom_timer.html` w katalogu głównym. Surowych nagrań nigdy nie nadpisuj.
- Środowisko Pythona na komputerze: `.venv` w katalogu głównym repo (circup, pyserial, numpy, pandas, scipy, matplotlib).
- Utwórz `CLAUDE.md` w katalogu głównym repo. Ma opisywać całe repozytorium: istniejący timer i licznik, z powyższymi ustaleniami. Aktualizuj go, gdy coś zmienimy.

## Pierwszy krok
Przeczytaj pliki w repozytorium, sprawdź system na moim komputerze, zadaj mi pytania, bez których nie ruszysz, i przedstaw plan etapu 0. Kodu jeszcze nie pisz.

## Otwarta propozycja (2026-10-10): tryb treningowy rejestratora
Treningi użytkownika na najbliższy czas = zbieranie danych. Zamiast klikać start/stop na każdą serię: rejestrator nagrywa ciągiem, timer wysyła znaczniki (początek minuty, id ćwiczenia, przerwa, koniec), a liczby powtórzeń pochodzą z podsumowania timera po treningu (ręczna korekta jak dziś). Realizacja: rejestrator na Macu serwuje stronę timera w sieci lokalnej (`http://<mac>.local:8050/timer`), iPhone otwiera ją zamiast GitHub Pages; dziennik z tej instancji scala się później przez kopię JSON. To pierwsza część etapu 4 po Wi-Fi; przy natywnej nakładce te same znaczniki idą po BLE. Czeka na decyzję użytkownika.
