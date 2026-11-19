# Heavy auf der Synology (DS216+, Container Manager)

Der Container läuft dauerhaft auf dem NAS:
- **Alle 2 Stunden** führt er `heavy auto` aus (Sync → Progression → Uhr → Dashboard), außerdem sofort bei jedem Start.
- Er liefert das **Dashboard im Heimnetz** aus: `http://<IP-der-Synology>:8080`, auch am Handy.

## Einmalige Einrichtung

1. **Container Manager installieren:** DSM → Paketzentrum → „Container Manager“.
2. **Ordner anlegen:** In der Freigabe `docker` den Ordner `heavy` anlegen (File Station). Gibt es die Freigabe `docker` noch nicht, wird sie mit dem Container Manager angelegt.
3. **Dateien kopieren:** Den **Inhalt** von `dist\heavy-synology` (auf dem PC) nach `docker/heavy` kopieren.
   Am einfachsten im Windows-Explorer über `\\<IP-der-Synology>\docker\heavy`. Der versteckte Ordner
   `daten\.garminconnect-heavy` muss mit (er enthält das Garmin-Token).
   Danach sieht es so aus:
   ```
   docker/heavy/
     Dockerfile  docker-compose.yml  entrypoint.sh  requirements.txt  heavy/
     daten/  config.json  data/heavy.db  report/  .garminconnect-heavy/garmin_tokens.json
   ```
4. **Projekt anlegen:** Container Manager → **Projekt** → **Erstellen**
   - Projektname: `heavy`
   - Pfad: `/docker/heavy`
   - Quelle: **„Vorhandene docker-compose.yml verwenden“**
   - Web-Portal-Einstellungen überspringen → **Fertig**.
   Das Image wird jetzt gebaut. Das dauert auf dem DS216+ einige Minuten. Danach startet der Container.
5. **Prüfen:** Container Manager → **Container** → `heavy` → **Protokoll**. Dort sollte stehen:
   `Synchronisiere Krafttrainings …` und `Dashboard: /data/report/dashboard.html`.
6. **Dashboard öffnen:** `http://<IP-der-Synology>:8080` (Übersicht), dein Dashboard liegt unter `/haupt/` (bzw. dem Namen, den du in `config.json` unter `hauptprofil` einträgst).
   Den Namen legt `HAUPTPROFIL` in `docker-compose.yml` fest.

**Wichtig:** Ab jetzt ist die Synology „der Chef“. Führe `.\heavy.cmd auto` oder `progress` nicht mehr zusätzlich
am PC aus, sonst laufen zwei getrennte Datenbanken. Die PC-Kopie kannst du als Backup behalten.
Port 8080 **nicht** im Router freigeben, das Dashboard ist nur fürs Heimnetz gedacht.

## Alltag

| Was | Wie |
|---|---|
| Sofort ausführen (statt 2 h warten) | Container `heavy` → **Neu starten** |
| Regeln ändern | `docker/heavy/daten/config.json` bearbeiten, gilt ab dem nächsten Lauf |
| Intervall ändern | `INTERVAL_HOURS` in `docker-compose.yml` → Projekt → **Erstellen** |
| Protokoll ansehen | Container `heavy` → **Protokoll** |
| Pausieren | Projekt `heavy` → **Stoppen** |

## Weitere Person einrichten
Jede Person hat ein eigenes Profil: eigene Garmin-Anmeldung, eigene Workouts und Regeln, eigenes Dashboard.

1. **Am PC** (die Person gibt ihre Garmin-Daten selbst ein), Beispiel für den Namen `anna`:
   ```
   .\heavy.cmd --profil anna login
   .\heavy.cmd --profil anna sync
   .\heavy.cmd --profil anna workouts --details
   .\heavy.cmd --profil anna manage <Workout-ID> <Workout-ID>
   .\heavy.cmd --profil anna progress --dry-run
   ```
   Das Profil übernimmt deine Regeln (Stufen, 8–12 Wdh). Anpassen kann man sie in `profile\anna\config.json`.
2. **Paket nur für diese Person bauen:**
   `powershell -ExecutionPolicy Bypass -File .\synology_paket.ps1 -Profil anna`
3. Den Ordner `dist\heavy-synology\daten\anna` nach `docker/heavy/daten/anna` kopieren (mit dem versteckten Ordner `.garminconnect-heavy`).
4. Container `heavy` → **Neu starten**. Im Protokoll erscheint `--- Profil: anna ---`.
5. Dashboard: `http://<IP-der-Synology>:8080/anna/`. Die Übersicht unter `http://<IP-der-Synology>:8080` listet alle Personen.

Alle Profile anzeigen: `.\heavy.cmd profile`. Eine Person entfernen: Ordner `docker/heavy/daten/<name>` löschen und den Container neu starten.

## Garmin-Anmeldung abgelaufen
Im Protokoll steht dann „Bitte einmal `heavy login` ausführen“.
1. Am PC: `.\heavy.cmd login`, bei einer weiteren Person `.\heavy.cmd --profil <name> login`.
2. Die neue `garmin_tokens.json` aufs NAS kopieren (überschreiben):
   - Hauptprofil: von `C:\Users\<du>\.garminconnect-heavy\` nach `docker/heavy/daten/.garminconnect-heavy/`
   - weitere Person: von `profile\<name>\.garminconnect-heavy\` nach `docker/heavy/daten/<name>/.garminconnect-heavy/`
3. Container neu starten.

## Programm-Update
1. Am PC: `powershell -ExecutionPolicy Bypass -File .\synology_paket.ps1 -NurCode`
2. Inhalt von `dist\heavy-synology` nach `docker/heavy` kopieren (**ohne** `daten`, das bleibt auf dem NAS).
3. Container Manager → Projekt `heavy` → **Aktion → Erstellen** (baut das Image neu).
