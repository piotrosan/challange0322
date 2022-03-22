# Przygotowanie

#### A. Przygotowany jest docker, i docker compose w wersji 3.3.
##### 1. Uruchamiamy dockera
    docker-compose up
##### Niestey nie sparametryzował czy ma byc baza w zaleznosci od parametru 
##### i trzeba ja jak cos przekopiować ręcznie z katalogu bin
##### jeśli ma byc pusta baza to wtedy nie kopiujemy
##### 2. do basha dostać się możemy 
    docker exec -it <id kontenera> bash
##### wchodzimy i odpalamy migracje 
#### 3. W zadaniach są opisy przy rozwiązaniach
#### Plik challenge.py zawiera rozwiązania dwóch zadań
#### Wszystkie zadania można uruchomić zapomocą polecenia
    ./manage.py run_migrates
#### uruchamia się ono podczas budowy dockera gdy wybierzemy istniejącą baze danych

#### B. Niestety Zadanie drugie nie chce sie uruchomić przez ta bibliotekę do SQLite3
#### działa ten sql w kliencie SQLlitewoym, poniżej link do niego 
    https://sqlitebrowser.org/
#### Nie chciałem już przedłużać z tym zadaniem więc nie przechodziłem na
#### zwykłą baze danych