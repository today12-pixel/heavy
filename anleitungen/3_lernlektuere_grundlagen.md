# Lernlektüre: Wie Heavy entstanden ist, von den Grundlagen bis Docker

Dieses Dokument ist für dich als Einsteiger geschrieben. Es erklärt nicht nur, **was** gemacht wurde, sondern
vor allem **warum**, also die Gedankengänge dahinter. Du musst es nicht am Stück lesen. Jedes Kapitel baut auf
dem vorherigen auf, steht aber auch einigermaßen für sich.

Am Ende jedes Kapitels steht ein Kasten **„Selbst ausprobieren“**. Nichts davon kann etwas kaputt machen.

**Inhalt**
1. Programme, Quellcode und warum Python
2. Die Kommandozeile
3. Bibliotheken und pip: auf den Schultern anderer
4. Daten speichern: Dateien, JSON, Datenbanken
5. Wie Programme mit dem Internet reden: HTTP und APIs
6. Anmeldung, Passwörter, Tokens und Sicherheit
7. Wie man Software baut, ohne sich zu verlaufen: Struktur und Tests
8. Das Dashboard: HTML, CSS, JavaScript und SVG
9. Automatisieren: Programme nach Zeitplan laufen lassen
10. Server und NAS: was eine Synology eigentlich ist
11. Docker, ausführlich
12. Betrieb und Sicherheit im Alltag
13. Wie ich vorgegangen bin: die Denkweise
14. Selbst weiterlernen
15. Glossar

---

## 1. Programme, Quellcode und warum Python

### Was ist ein Programm?
Ein Computer kann nur sehr einfache Dinge: Zahlen rechnen, Daten verschieben, vergleichen. Ein **Programm** ist
eine lange, genaue Liste solcher Anweisungen. Weil niemand Millionen Einzelanweisungen schreiben will, gibt es
**Programmiersprachen**. Darin schreibt man in einer halbwegs lesbaren Form, was passieren soll. Dieser Text
heißt **Quellcode**.

Ein Beispiel aus Heavy (`heavy/progression.py`) berechnet das geschätzte Maximalgewicht:

```python
def e1rm(kg, reps):
    if kg <= 0 or reps <= 0:
        return 0.0
    if reps == 1:
        return kg
    return kg * (1 + min(reps, 15) / 30.0)
```

Auf Deutsch: „Definiere eine Rechnung namens `e1rm` mit den Eingaben Gewicht und Wiederholungen. Ist eins davon
null oder kleiner, gib 0 zurück. Bei genau einer Wiederholung ist das Gewicht selbst das Ergebnis. Sonst rechne
Gewicht × (1 + Wdh/30), wobei mehr als 15 Wdh wie 15 zählen.“

### Warum Python?
Für Heavy habe ich **Python** gewählt, aus vier Gründen:

1. **Es gibt schon eine Garmin-Bibliothek in Python** (`garminconnect`). Das war der wichtigste Grund, mehr dazu in Kapitel 3.
2. **Python ist gut lesbar.** Selbst ohne Vorkenntnisse kann man oft erraten, was eine Zeile tut. Für dich als
   Einsteiger ist das ein Vorteil.
3. **Python läuft überall:** auf deinem Windows-PC genauso wie auf Linux, also auch auf der Synology.
4. **Python war schon installiert** (Version 3.12 auf deinem PC).

### Interpreter: wer führt den Code aus?
Python-Code wird von einem Programm namens **Interpreter** (`python.exe`) Zeile für Zeile gelesen und
ausgeführt. Wenn du `python -m heavy sync` tippst, startest du den Interpreter. Mit `-m heavy` sagst du ihm:
„Führe das **Modul** (Paket) `heavy` aus.“ Den Rest (`sync`) bekommt das Programm als Anweisung mit.

### Dateien und Pakete
Heavy besteht aus mehreren `.py`-Dateien im Ordner `heavy/`. So ein Ordner heißt **Paket**, jede Datei
**Modul**. Die Datei `__main__.py` ist der Einstiegspunkt, sie läuft bei `python -m heavy`. Die Datei
`__init__.py` markiert den Ordner als Paket.

> **Selbst ausprobieren:** Öffne `heavy\progression.py` im Editor und such die Funktion `e1rm`. Rechne mit dem
> Taschenrechner nach: 70 kg × 12 Wdh ergibt 70 × (1 + 12/30) = 98 kg geschätztes 1RM.

---

## 2. Die Kommandozeile

### Warum keine Klick-Oberfläche?
Programme mit Fenstern und Knöpfen sind aufwendig zu bauen. Eine **Kommandozeile** (bei dir **PowerShell**) ist
ein Textfenster: Du tippst einen Befehl, das Programm antwortet mit Text. Für Werkzeuge, die meist automatisch
laufen sollen, ist das ideal. Ein Zeitplan oder ein Server kann keine Knöpfe drücken, aber Befehle ausführen.

### Aufbau eines Befehls
```
.\heavy.cmd  --profil anna  progress  --dry-run
└────┬────┘  └─────┬────┘  └───┬───┘  └───┬───┘
 Programm    Option mit      Unter-    Schalter (an/aus)
             Wert            befehl
```

- **Programm:** `heavy.cmd` ist eine kleine Windows-Stapeldatei. Sie wechselt in den Heavy-Ordner und ruft
  `python -m heavy` mit allem auf, was du dahinter schreibst.
- **Unterbefehl:** `sync`, `progress`, `report` … Ein Programm, mehrere Aufgaben.
- **Optionen** beginnen mit `--`. Manche haben einen Wert (`--profil anna`), andere sind Schalter (`--dry-run`).
- `--help` zeigt bei fast jedem Programm, was es kann: `.\heavy.cmd --help`, `.\heavy.cmd progress --help`.

### Der aktuelle Ordner und das `.\`
Jedes Terminal „steht“ in einem Ordner, das zeigt die Eingabezeile: `PS C:\Users\<du>\Desktop\Heavy>`.
PowerShell führt aus Sicherheitsgründen **keine** Programme aus dem aktuellen Ordner aus, wenn man nur den
Namen tippt. Sonst könnte jemand eine Datei namens `dir.cmd` unterschieben. Deshalb `.\heavy.cmd`: Der Punkt
heißt „dieser Ordner“, der Backslash trennt Ordner und Datei.

### Pfade: absolut und relativ
- **Absolut:** der volle Weg vom Laufwerk aus, z. B. `C:\Users\<du>\Desktop\Heavy\config.json`
- **Relativ:** vom aktuellen Ordner aus, z. B. `data\heavy.db`
- Windows trennt mit `\`, Linux (Synology, Docker) mit `/`. Deshalb steht in den Docker-Dateien `/data/config.json`.

### Umgebungsvariablen
Das sind Einstellungen, die man einem Programm von außen mitgibt, ohne den Code zu ändern. Heavy liest z. B.
`HEAVY_HOME`, also den Ordner, in dem `config.json` und die Daten liegen. Am PC ist das nicht gesetzt, dann nimmt
Heavy den Projektordner. Im Docker-Container setzt das Startskript `HEAVY_HOME=/data/anna` für Annas Lauf.
**Ein und derselbe Code arbeitet so mit verschiedenen Daten.**

### Exit-Codes
Jedes Programm meldet beim Beenden eine Zahl: **0 = alles gut**, alles andere = Problem. Heavy gibt z. B. **2**
zurück, wenn die Garmin-Anmeldung fehlt. Die Windows-Aufgabenplanung und Docker werten das aus. Du hast es beim
Test gesehen: `LastResult=0`.

> **Selbst ausprobieren:** `.\heavy.cmd --help` und danach `.\heavy.cmd sync --help`. Dann `.\heavy.cmd profile`.

---

## 3. Bibliotheken und pip: auf den Schultern anderer

### Was ist eine Bibliothek?
Eine **Bibliothek** ist fertiger Code, den andere geschrieben haben und den man im eigenen Programm benutzt.
Bei Heavy steckt in der Bibliothek `garminconnect` das ganze Wissen, wie man sich bei Garmin anmeldet und mit
Garmins Servern spricht. Das selbst herauszufinden hätte Wochen gedauert.

### pip und PyPI
- **PyPI** (Python Package Index) ist das zentrale Verzeichnis aller öffentlichen Python-Bibliotheken.
- **pip** ist das Programm, das sie herunterlädt und installiert: `pip install garminconnect`.
- **`requirements.txt`** listet auf, was ein Projekt braucht. Bei Heavy steht dort `garminconnect>=0.3.20`,
  also „mindestens Version 0.3.20“. `pip install -r requirements.txt` installiert alles auf einmal. Genau das
  macht auch der Docker-Build (Kapitel 11).

### Abhängigkeiten von Abhängigkeiten
`garminconnect` braucht selbst wieder andere Bibliotheken: `requests` (Internetanfragen), `curl_cffi`
(Internetanfragen, die wie ein echter Browser aussehen), `tzdata` (Zeitzonen) und `ua-generator`. pip löst das
automatisch auf. Ich habe trotzdem nachgesehen, weil `curl_cffi` vorkompilierten Maschinencode enthält, und den
gibt es nicht für jeden Prozessor. Für deinen DS216+ (Intel) ist er vorhanden. Mehr dazu in Kapitel 10.

### Fremden Code prüfen
Bevor ich Heavy gebaut habe, habe ich die Bibliothek installiert und **ihren Code gelesen**. Ich habe
nachgesehen, welche Funktionen es gibt (`get_workout_by_id`, `update_workout`, `push_workout_to_device`,
`get_activity_exercise_sets`) und was sie genau tun. Daher stammt z. B. das Wissen, dass Gewichte in Gramm
gespeichert werden. Es steht als Kommentar im Code der Bibliothek. **Lehre: Vermute nicht, schau nach.**

> **Selbst ausprobieren:** `pip show garminconnect` zeigt Version und Abhängigkeiten. `pip list` zeigt alles,
> was in deinem Python installiert ist.

---

## 4. Daten speichern: Dateien, JSON, Datenbanken

### Textdateien und Formate
Programme müssen sich Dinge merken: Einstellungen, Trainings, was schon erledigt ist. Am einfachsten geht das in
**Dateien**. Damit ein Programm eine Datei wieder versteht, braucht sie ein festes **Format**.

### JSON: Einstellungen und Garmins Sprache
**JSON** ist ein Textformat für strukturierte Daten. Deine `config.json` sieht auszugsweise so aus:

```json
{
  "managed_workouts": [1234567890, 1234567891],
  "push_to_device": true,
  "default_rule": {
    "increment": 2.5,
    "rep_range": [8, 12],
    "allow_decrease": false
  }
}
```

- `{ … }` ist ein **Objekt**: Paare aus Name und Wert
- `[ … ]` ist eine **Liste**
- Werte sind Zahlen (`2.5`, mit Punkt statt Komma!), Texte in `"Anführungszeichen"`, `true`/`false` oder
  wieder Objekte und Listen

Warum JSON für die Einstellungen? Du kannst es mit jedem Editor lesen und ändern, und Python liest es mit einer
Zeile. Garmin spricht ebenfalls JSON: Ein Workout kommt als großes JSON-Objekt an, Heavy ändert darin zwei
Zahlen und schickt es zurück.

**Typische Fehler beim Bearbeiten:** ein fehlendes Komma zwischen zwei Einträgen, ein Komma hinter dem
letzten Eintrag oder ein deutsches Dezimalkomma (`2,5` statt `2.5`). Dann bricht Heavy mit einem JSON-Fehler ab.

### Warum zusätzlich eine Datenbank?
Für Trainings und Sätze reicht eine JSON-Datei nicht gut: Es werden schnell Tausende Einträge, und man will
gezielt fragen können, etwa „alle Sätze der Übung Leg Curl, sortiert nach Datum“. Dafür gibt es **Datenbanken**.

**SQLite** ist eine Datenbank, die komplett in **einer Datei** steckt (`data\heavy.db`). Man braucht keinen
Datenbankserver, und sie ist in Python eingebaut. Darin gibt es **Tabellen**, ähnlich wie in Excel:

| Tabelle | Inhalt |
|---|---|
| `activities` | ein Eintrag pro Training (ID, Datum, Name, Dauer) |
| `sets` | ein Eintrag pro Satz (Training, Übung, Wdh, kg) |
| `changes` | das Protokoll: welche Änderung wann aus welchem Grund |

Abgefragt wird mit der Sprache **SQL**, zum Beispiel:

```sql
SELECT reps, kg FROM sets WHERE name = 'WEIGHTED_LEG_CURL';
```

„Hole Wiederholungen und Gewicht aus der Tabelle `sets`, aber nur für den Leg Curl.“

### Warum das Protokoll so wichtig ist
Die Tabelle `changes` verhindert, dass Heavy dasselbe Training zweimal verrechnet (Kapitel 7). Deshalb gilt:
**Datenbank löschen = Protokoll weg.** Die Trainings selbst lassen sich jederzeit neu von Garmin holen, das
Protokoll nicht.

> **Selbst ausprobieren:** Öffne `config.json` im Editor und lies sie. Ändere nichts oder mach vorher eine Kopie.
> Wer mag, installiert das kostenlose Programm „DB Browser for SQLite“ und öffnet damit eine **Kopie** von
> `data\heavy.db`.

---

## 5. Wie Programme mit dem Internet reden: HTTP und APIs

### Client und Server
Wenn du garmin.com im Browser öffnest, ist dein Browser der **Client** (der Fragende) und Garmins Computer der
**Server** (der Antwortende). Heavy ist ebenfalls ein Client: Es stellt dieselben Fragen wie der Browser, nur
automatisch.

### HTTP: die Sprache dazwischen
Jede Anfrage im Web nutzt **HTTP**. Sie besteht aus:
- einer **Adresse (URL)**, z. B. `…/workout-service/workout/1234567891`
- einer **Methode**, also was man will:
  - `GET`: „Gib mir …“ (Workout lesen, Trainings auflisten)
  - `POST`: „Lege an / führe aus …“ (Workout an die Uhr senden)
  - `PUT`: „Ersetze …“ (Workout mit neuen Gewichten speichern)
  - `DELETE`: „Lösche …“ (benutzt Heavy nie)
- optional einem **Inhalt**, bei Garmin JSON

Die Antwort hat einen **Statuscode**:

| Code | Bedeutung |
|---|---|
| 200 | OK |
| 400 | Anfrage fehlerhaft. Das hatten wir: „Activity type cannot be an activity sub type“. |
| 401/403 | nicht angemeldet / nicht erlaubt |
| 404 | gibt es nicht |
| 429 | zu viele Anfragen, langsamer bitte |
| 500 | Fehler beim Server |

### API
Eine **API** (Programmierschnittstelle) ist die Menge an Adressen und Regeln, über die ein Programm mit einem
Dienst sprechen kann. Garmin hat eine **offizielle** API für Firmen und eine **interne**, die die Webseite
benutzt. Heavy nutzt die interne. Das funktioniert gut, aber Garmin verspricht nichts. Ändert Garmin eine
Adresse, muss die Bibliothek nachziehen.

### Die Lehre aus dem ersten Fehler
Der erste echte Sync scheiterte mit Code 400. Die Fehlermeldung verriet den Grund: `strength_training` ist bei
Garmin ein **Untertyp** von `fitness_equipment`. Die Lösung war, nach dem Obertyp zu fragen und selbst zu
filtern. **Fehlermeldungen sind deine Freunde, lies sie ganz.**

---

## 6. Anmeldung, Passwörter, Tokens und Sicherheit

### Passwort und Token
Würde Heavy alle 2 Stunden dein Passwort an Garmin schicken, müsste es irgendwo gespeichert sein. Das wäre
gefährlich. Deshalb läuft es so:

1. Du meldest dich **einmal** mit Passwort und MFA-Code an (`login`).
2. Garmin gibt dafür ein **Token** heraus, eine lange Zeichenkette, die wie ein befristeter Hausausweis
   funktioniert.
3. Heavy speichert nur das Token (`garmin_tokens.json`) und zeigt es bei jeder Anfrage vor.
4. Das Token läuft irgendwann ab und wird zwischendurch automatisch erneuert. Ist es endgültig ungültig, musst du
   dich neu anmelden.

Das **Passwort wird nie gespeichert**. Im Code wird es nach der Anmeldung sogar aktiv aus dem Speicher gelöscht.
Die Bibliothek macht das so.

### MFA
**Mehr-Faktor-Authentifizierung**: Zusätzlich zum Passwort braucht man einen Code von einem zweiten Gerät.
Deshalb kann die Anmeldung nicht automatisch auf der Synology passieren. Ein Mensch muss den Code eintippen.

### Warum ich dein Passwort nicht eingegeben habe
Ich habe das Login in einem Terminal gestartet, und **du** hast getippt. Passwörter gehören in die Hände ihres
Besitzers, nicht in die eines Assistenten oder Programms, das sie sehen könnte. Dasselbe gilt für weitere
Personen. Sie tippen selbst.

### Das Token ist ein Schlüssel
Wer `garmin_tokens.json` hat, kommt in dein Garmin-Konto, ohne Passwort. Deshalb:
- nie per Mail, Chat oder Cloud-Freigabe verschicken
- den Ordner `dist` nach dem Kopieren aufs NAS löschen
- auf dem NAS nicht übers Internet erreichbar machen (Kapitel 12)
- Wird ein Token versehentlich öffentlich: in Garmin Connect das Passwort ändern. Dann werden alte Anmeldungen ungültig.

---

## 7. Wie man Software baut, ohne sich zu verlaufen: Struktur und Tests

### Teile und herrsche
Heavy ist in Module aufgeteilt (Übersicht in Anleitung 2). Die wichtigste Regel dabei: **Die Rechenlogik kennt
die Außenwelt nicht.** `progression.py` weiß nichts von Garmin, Internet oder Datenbank. Es bekommt Zahlen und
gibt eine Entscheidung zurück. Das hat drei Vorteile:
1. Man kann sie **testen**, ohne Garmin-Konto.
2. Ändert sich Garmin, bleibt sie richtig.
3. Man versteht sie leichter, weil sie klein ist.

### Automatische Tests
Ein **Test** ist ein kleines Programm, das prüft, ob ein anderes Programm das Richtige tut. Ein Test aus Heavy:

```python
def test_increase_when_all_sets_hit_target(self):
    d = decide(Rule(increment=2.5), 8, [sess(1, 1, [(8, 80), (9, 80), (8, 80)])])
    self.assertEqual(d.new_kg, 82.5)
```

„Wenn alle drei Sätze mit 80 kg das Ziel von 8 Wdh schaffen, muss das neue Gewicht 82,5 kg sein.“
`assertEqual` schlägt Alarm, wenn etwas anderes herauskommt.

Heavy hat 20 solcher Tests: Gewichtseinheiten, Übernahme spontaner Erhöhungen, Steigern, Halten, Deload,
Scheibenraster, 8–12-Bereich, „nie senken“, Regel-Reihenfolge, das Ändern von Workout-JSON, das Lesen von
Garmins Satzdaten, Profilnamen und ein kompletter Durchlauf mit einem **Fake-Garmin**. Das ist ein Ersatzobjekt,
das sich wie Garmin verhält, aber nur im Speicher existiert.

**Warum der Aufwand?** Nach jeder Änderung laufen alle Tests in unter einer Sekunde. Bricht dabei etwas, merkt
man es sofort und nicht erst, wenn deine Uhr ein falsches Gewicht zeigt. Ein Test hat übrigens auch **mich**
korrigiert. Bei den neuen Regeln schlug einer fehl, weil mein Testfall falsch war, nicht der Code. Auch das
gehört dazu.

### Demo und Simulation
Bevor echte Daten im Spiel waren, habe ich mit `demo` 20 Wochen Training **simuliert**. Ein erfundener Sportler
mit „wahrer Kraft“, die langsam steigt, mit Zufallsschwankungen und gelegentlichen spontanen Erhöhungen auf der
Uhr. Die Simulation nutzt dieselbe Engine wie der echte Betrieb. So ließ sich das ganze System prüfen, ohne
dein Konto anzufassen.

### Erst testen, dann senden
Jeder Schritt, der etwas an Garmin ändert, hatte vorher einen **Testlauf** (`--dry-run`), und du hast entschieden.
Grundsatz: **Was nach außen wirkt, wird vorher gezeigt.**

### Idempotenz
Ein Fachwort, das du dir merken solltest: Eine Aktion ist **idempotent**, wenn mehrfaches Ausführen dasselbe
bewirkt wie einmaliges. Lichtschalter auf „an“ stellen ist idempotent, „umschalten“ nicht. Heavy läuft alle
2 Stunden. Wäre es nicht idempotent, würde es bei jedem Lauf erneut +5 kg rechnen. Zwei Sicherungen verhindern
das: das Protokoll und eine Rechnung, die ihre Basis aus dem Training nimmt statt aus der Vorlage.

### Echte Daten finden echte Fehler
Mit der Demo lief alles. Mit deinen echten Daten kamen sofort vier Dinge ans Licht:
1. der Untertyp-Fehler (Kapitel 5)
2. die Brustpresse in der Kategorie `SLED`, die als Beintraining gezählt wurde
3. der Wochenschnitt, gerechnet über 12 Wochen, obwohl du erst 2 Wochen Daten hattest
4. Sätze mit 0 Wiederholungen durch Erkennungsfehler der Uhr

Schon vorher fiel beim Bauen ein **Zeitzonenfehler** auf: JavaScript rechnete Daten in Weltzeit (UTC) um. In
Deutschland (UTC+1) wäre so aus Mitternacht am 10.11. der 9.11., 23 Uhr geworden, und das Dashboard hätte
falsche Tage gezeigt. Solche Fehler findet man nur, wenn man genau hinsieht.

> **Selbst ausprobieren:** `python -m unittest tests.test_heavy -v` lässt alle Tests laufen. Ändere testweise
> in `progression.py` die Zahl `30.0` in `e1rm` auf `20.0`, starte die Tests erneut, sieh zu, welcher fehlschlägt,
> und mach die Änderung wieder rückgängig.

---

## 8. Das Dashboard: HTML, CSS, JavaScript und SVG

Eine Webseite besteht aus drei Sprachen:

| Sprache | Aufgabe | Beispiel in Heavy |
|---|---|---|
| **HTML** | Struktur: Überschriften, Kacheln, Tabellen | `<h2>Größte Steigerungen</h2>` |
| **CSS** | Aussehen: Farben, Abstände, Schrift, Dark Mode | `.tile { border-radius: 12px; }` |
| **JavaScript** | Verhalten: rechnen, filtern, auf Klicks reagieren | Zeitraum wechseln, Muskel anklicken |

### Wie die Daten in die Seite kommen
Die Vorlage `heavy/templates/dashboard.html` enthält eine Platzhalterzeile `const D = /*__DATA__*/null;`.
`report.py` liest die Datenbank, packt alles in JSON und ersetzt den Platzhalter. Heraus kommt **eine einzige
Datei**, die alles enthält. Das JavaScript rechnet dann im Browser: Zeiträume filtern, Steigerungen,
Muskelwerte. Deshalb reagiert das Dashboard sofort, wenn du einen Zeitraum klickst. Niemand muss neu rechnen.

### Bibliothek aus dem Netz (CDN)
Die Diagramme zeichnet **Chart.js**. Die Datei lädt der Browser von einem **CDN** (einem Netz von Servern, die
beliebte Bibliotheken verteilen), mit fester Versionsnummer `4.4.1`. Die feste Version verhindert, dass ein
Update der Bibliothek dein Dashboard plötzlich verändert. Ohne Internet erscheint statt der Diagramme ein
Hinweis, der Rest funktioniert.

### SVG: die Muskelkarte
**SVG** ist ein Grafikformat aus Text. Statt Pixeln beschreibt man Formen:

```
M99,82 C92,81 85,80 80,81 C75,86 72,93 71,101 … Z
```

Das heißt: „Gehe zu Punkt (99,82), zeichne eine Kurve zu (80,81), dann eine Kurve zu (71,101) … schließe die
Form.“ So ist der Brustmuskel gezeichnet. Ich habe nur die **linke Körperhälfte** gezeichnet. Die rechte
entsteht durch **Spiegelung** an der Mittellinie (`matrix(-1,0,0,1,200,0)`), das spart die halbe Arbeit und
hält beide Seiten symmetrisch. Jede Muskelform trägt einen Namen (`data-m="chest"`), so weiß das JavaScript
beim Einfärben und beim Hover, welcher Muskel gemeint ist. Die erste Version aus Ellipsen sah „komisch“ aus,
wie du richtig angemerkt hast. Die zweite folgt den echten Muskelformen.

### Farben mit System
Farben sind als **Variablen** definiert (`--series-1`, `--seq-4` …), einmal für hell und einmal für dunkel. Stellt
dein Gerät auf Dark Mode, tauscht das CSS alle Werte auf einmal. Die Farbskalen sind bewusst gewählt:
**eine** Farbe hell→dunkel für Mengen (Sätze, Volumen), **zwei** Farben mit grauer Mitte für Richtungen
(Rückgang rot, Steigerung blau). Ein Regenbogen wäre schwerer zu lesen, und rot/grün können viele Menschen mit
Farbsehschwäche nicht unterscheiden.

### Was sich der Browser merkt
Zeitraum, Kennzahl und gewählte Übung speichert das Dashboard im **localStorage** deines Browsers, einem
kleinen Speicher pro Webseite. Deshalb öffnet es beim nächsten Mal so, wie du es verlassen hast.

> **Selbst ausprobieren:** Öffne das Dashboard, drücke **F12** (Entwicklerwerkzeuge), dann Reiter „Elemente“.
> Fahre mit der Maus über die Zeilen im Code, dann leuchtet der zugehörige Teil der Seite auf. Im Reiter
> „Konsole“ tippst du `D.exercises.length` und Enter: Du siehst die Zahl deiner Übungen.

---

## 9. Automatisieren: Programme nach Zeitplan laufen lassen

Damit Heavy ohne dich arbeitet, muss es regelmäßig von selbst starten. Dafür gibt es drei übliche Wege:

| Weg | Wo | Wie |
|---|---|---|
| **Aufgabenplanung** | Windows | Systemdienst startet Programme nach Zeitplan. Haben wir eingerichtet und auf deinen Wunsch wieder entfernt. |
| **cron** | Linux | dasselbe Prinzip unter Linux, der DSM-Aufgabenplaner baut darauf auf |
| **Endlosschleife** | im Container | das Programm selbst wartet: arbeiten → 2 h schlafen → arbeiten |

Im Container habe ich die **Schleife** gewählt, weil sie keine zusätzliche Einrichtung in DSM braucht. Alles
steckt in einer Datei, und die Protokolle landen gesammelt im Container-Protokoll. Nachteil: Ändert man das
Intervall, muss der Container neu gestartet werden. Das ist hier unwichtig.

Ein Detail von der Windows-Variante: `python.exe` öffnet ein Konsolenfenster, `pythonw.exe` nicht. Ich hatte auf
`pythonw` umgestellt, du wolltest das zurück, dann ganz ohne Zeitplan. Auf der Synology gibt es dieses Problem
nicht, dort hat niemand einen Bildschirm.

---

## 10. Server und NAS: was eine Synology eigentlich ist

### Ein Server ist ein Computer, der dient
„Server“ klingt groß, heißt aber nur: ein Computer, der dauerhaft läuft und Dienste für andere anbietet. Deine
Synology **ist** ein Server: ein kleiner, stromsparender Computer mit Festplatten.

### DSM ist Linux
Das Betriebssystem der Synology, **DSM**, basiert auf **Linux**. Deshalb laufen dort Linux-Programme, und
deshalb verwenden die Docker-Dateien Linux-Schreibweisen (`/`, `sh`, Zeilenenden ohne `\r`, Kapitel 11).

### Prozessor-Architektur: warum ich nach dem Modell gefragt habe
Prozessoren sprechen unterschiedliche „Maschinensprachen“:
- **x86_64** (Intel/AMD): dein PC und dein **DS216+** (Intel Celeron)
- **ARM**: Handys und viele günstige Synology-Modelle (z. B. „j“-Modelle)

Programme in Maschinencode laufen nur auf der Architektur, für die sie gebaut wurden. Python-Code selbst ist
egal, aber die Bibliothek `curl_cffi` enthält Maschinencode. Außerdem bietet Synology den Container Manager nur
für bestimmte Modelle an. Der DS216+ passt in beiden Punkten.

### Warum überhaupt das NAS statt des PCs?
Der PC ist nicht immer an. Die Synology läuft rund um die Uhr. Dein Training wird also auch verarbeitet, wenn
der PC aus ist, und das Dashboard ist vom Handy aus erreichbar.

---

## 11. Docker, ausführlich

### Das Problem, das Docker löst
Ein Programm braucht eine **Umgebung**: die richtige Python-Version, die richtigen Bibliotheken in passenden
Versionen, Zeitzonen-Daten und so weiter. Auf deinem PC habe ich das von Hand eingerichtet. Auf der Synology
müsste man das alles wiederholen, auf einem fremden Linux, und bei jedem DSM-Update könnte etwas kaputtgehen.
Der Klassiker unter Entwicklern: „Bei mir läuft's doch!“

**Docker** packt das Programm **mitsamt seiner Umgebung** in eine Kiste, die überall gleich läuft, wo Docker
installiert ist.

### Container und virtuelle Maschine
- Eine **virtuelle Maschine** simuliert einen kompletten Computer mit eigenem Betriebssystem. Das ist schwer
  und braucht viel Arbeitsspeicher.
- Ein **Container** teilt sich den Linux-Kern des Gastgebers und bringt nur seine eigenen Dateien mit. Er ist
  leicht und startet in Sekunden. Für den DS216+ mit 1 GB Arbeitsspeicher ist das wichtig.

Ein Container ist trotzdem gut **abgeschottet**. Er sieht nur seine eigenen Dateien und genau die Ordner, die
man ihm ausdrücklich freigibt.

### Die vier Grundbegriffe

| Begriff | Bild | Bei Heavy |
|---|---|---|
| **Image** | Bauplan plus fertig gepackte Kiste (unveränderlich) | `heavy:latest`, gebaut aus dem Dockerfile |
| **Container** | eine laufende Kiste, erzeugt aus dem Image | `heavy`, läuft dauerhaft |
| **Volume / Bind-Mount** | ein Ordner vom Gastgeber, in die Kiste „hineingereicht“ | `docker/heavy/daten` → `/data` |
| **Port** | eine Tür von außen in die Kiste | NAS-Port 8080 → Container-Port 8080 |

**Ganz wichtig:** Alles, was **im** Container geschrieben wird und nicht in einem Volume liegt, ist beim
Neubauen weg. Deshalb liegen Datenbank, Config und Token in `daten`, also **außerhalb** der Kiste auf dem NAS.
Programm und Daten sind getrennt. Das Programm kann man beliebig neu bauen, die Daten bleiben.

### Registry und Basis-Image
Niemand baut Images von null. Man startet von einem **Basis-Image** aus einer **Registry**, einem
Online-Verzeichnis. Das bekannteste ist **Docker Hub**. Heavy startet von `python:3.12-slim`, dem offiziellen
Python-Image auf Basis von Debian Linux in der schlanken Variante. Darin ist Python 3.12 schon fertig installiert.

### Das Dockerfile, Zeile für Zeile
Das **Dockerfile** ist das Rezept für das Image (`synology/Dockerfile`):

```dockerfile
FROM python:3.12-slim
```
Nimm das offizielle Python-3.12-Image als Grundlage. Beim ersten Bauen lädt die Synology es von Docker Hub
herunter, etwa 50 MB.

```dockerfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata \
 && rm -rf /var/lib/apt/lists/*
```
`RUN` führt beim Bauen einen Befehl aus. `apt-get` ist der Paketmanager von Debian, wie pip, nur für
Linux-Programme. Installiert werden die **Zeitzonen-Daten**. Ohne sie wüsste der Container nicht, was
„Europe/Berlin“ heißt, und alle Zeiten im Protokoll wären eine Stunde daneben. Danach wird der Download-Zwischenspeicher
gelöscht, damit das Image klein bleibt. Die `&&` verketten: Der nächste Befehl läuft nur, wenn der vorige geklappt hat.

```dockerfile
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Berlin \
    HAUPTPROFIL=haupt \
    INTERVAL_HOURS=2 \
    PORT=8080
```
`ENV` setzt **Umgebungsvariablen** (Kapitel 2) mit Standardwerten:
- `PYTHONUNBUFFERED=1`: Ausgaben sofort ins Protokoll schreiben statt sie zu sammeln. Sonst sähest du im
  Container Manager lange nichts.
- `PYTHONDONTWRITEBYTECODE=1`: keine `__pycache__`-Ordner anlegen, sie wären im Container unnütz.
- `TZ`: die Zeitzone.
- Die übrigen drei liest das Startskript. `HAUPTPROFIL` wird beim Packen auf den Wert `hauptprofil` aus deiner `config.json` gesetzt (Standard `haupt`).

```dockerfile
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY heavy ./heavy
COPY entrypoint.sh /app/entrypoint.sh
```
- `WORKDIR /app`: Arbeitsordner im Container.
- Erst nur `requirements.txt` kopieren, dann pip ausführen, **dann** erst den Code kopieren. Warum die
  Reihenfolge? Docker baut in **Schichten** und merkt sich jede. Änderst du später nur Heavys Code, kann Docker
  die teure pip-Schicht wiederverwenden und baut nur die letzten, billigen Schichten neu. Ein Update dauert
  dadurch Sekunden statt Minuten.
- `--no-cache-dir`: pips Download-Zwischenspeicher nicht behalten, damit das Image kleiner bleibt.

```dockerfile
EXPOSE 8080
CMD ["sh", "/app/entrypoint.sh"]
```
- `EXPOSE`: Dokumentation, dass die Kiste auf Port 8080 etwas anbietet.
- `CMD`: Das wird ausgeführt, wenn ein Container aus dem Image startet: das Startskript mit der Shell `sh`.
  Ich rufe es bewusst über `sh` auf, statt es direkt auszuführen. So muss die Datei nicht als „ausführbar“
  markiert sein, ein Linux-Recht, das beim Kopieren von Windows leicht verloren geht.

### Was beim „Erstellen“ auf deiner Synology passiert
Wenn du im Container Manager das Projekt erstellst, läuft im Hintergrund `docker compose up --build`:

1. **Lesen** der `docker-compose.yml`: Dort steht `build: .`, also „baue aus dem Dockerfile in diesem Ordner“.
2. **Basis-Image laden:** `python:3.12-slim` von Docker Hub (nur beim ersten Mal).
3. **Schicht für Schicht bauen:** tzdata installieren → `requirements.txt` → `pip install` (lädt garminconnect
   und Abhängigkeiten aus dem Internet) → Code kopieren. Jede Schicht wird zwischengespeichert.
4. **Image fertig:** Es heißt `heavy:latest` und liegt auf dem NAS.
5. **Container erzeugen** aus dem Image, mit den Einstellungen aus der Compose-Datei (Ordner, Port, Variablen).
6. **Starten:** `CMD` läuft, also das Startskript.

Auf dem DS216+ dauert Schritt 3 beim ersten Mal einige Minuten. Die CPU ist eher gemütlich.

### Die Compose-Datei, Zeile für Zeile
**Docker Compose** beschreibt, *wie* ein oder mehrere Container laufen sollen, als Datei statt als langer Befehl:

```yaml
services:
  heavy:
    build: .
    image: heavy:latest
    container_name: heavy
    restart: unless-stopped
    environment:
      - INTERVAL_HOURS=2
      - HAUPTPROFIL=haupt
    volumes:
      - ./daten:/data
    ports:
      - "8080:8080"
```

| Zeile | Bedeutung |
|---|---|
| `services:` / `heavy:` | Es gibt einen Dienst namens heavy |
| `build: .` | aus dem Dockerfile im selben Ordner bauen |
| `image: heavy:latest` | so heißt das gebaute Image |
| `container_name: heavy` | fester Name, so findest du ihn im Container Manager |
| `restart: unless-stopped` | nach Absturz oder NAS-Neustart automatisch wieder starten, außer du hast ihn selbst gestoppt |
| `environment:` | Umgebungsvariablen, überschreiben die `ENV`-Standards aus dem Dockerfile |
| `volumes: ./daten:/data` | Der NAS-Ordner `daten` erscheint im Container als `/data`. Links Gastgeber, rechts Container. |
| `ports: "8080:8080"` | NAS-Port 8080 führt auf Container-Port 8080. Links Gastgeber, rechts Container. |

Das Format heißt **YAML**. Die **Einrückung** (Leerzeichen am Zeilenanfang) bestimmt, was wozu gehört. Ein
falsches Leerzeichen, und die Datei ist ungültig. Tabulatoren sind verboten.

### Das Startskript, Zeile für Zeile
`entrypoint.sh` ist ein **Shell-Skript**, die Kommandozeilen-Sprache von Linux. Das Prinzip kennst du aus
PowerShell, die Schreibweise ist anders. Die wichtigsten Stellen:

```sh
mkdir -p /web
python -m http.server "$PORT" --directory /web --bind 0.0.0.0 >/dev/null 2>&1 &
```
- Ordner `/web` anlegen (`-p`: ohne Fehler, falls er schon existiert).
- Einen kleinen **Webserver** starten, der den Ordner `/web` ausliefert. Er ist in Python eingebaut.
  `0.0.0.0` heißt „auf allen Netzwerkkarten erreichbar“. `>/dev/null 2>&1` verwirft seine Ausgaben, damit das
  Protokoll lesbar bleibt. Das `&` am Ende ist entscheidend: Der Server läuft **im Hintergrund**, und das Skript
  macht sofort weiter.

```sh
run_profile() {
  dir="$1"; name="$2"
  …
  HEAVY_HOME="$dir" HEAVY_TOKENSTORE="$dir/.garminconnect-heavy" HEAVY_PROFILE="$name" \
    python -m heavy auto || echo "Lauf für $name fehlgeschlagen"
  …
  cp "$dir/report/dashboard.html" "/web/$name/index.html"
}
```
- Eine **Funktion**: ein benannter Block, den man mehrfach aufrufen kann. `$1` und `$2` sind ihre Eingaben.
- Vor `python` werden drei Umgebungsvariablen **nur für diesen einen Befehl** gesetzt. Das ist der Trick hinter
  den Profilen (Kapitel 2).
- `|| echo …`: Schlägt der Lauf fehl, wird nur eine Meldung geschrieben, und das Skript läuft weiter. Ein
  Fehler bei Anna darf deinen Lauf nicht verhindern.
- Danach wird **nur das Dashboard** nach `/web` kopiert. Das ist die Sicherheitsentscheidung: Der Webserver sieht
  nur `/web`, nie `/data` mit den Tokens.

```sh
while true; do
  …
  if [ -f /data/config.json ]; then run_profile /data "$HAUPTPROFIL"; fi
  for d in /data/*/; do
    [ -f "$d/config.json" ] || continue
    run_profile "$d" "$(basename "$d")"
  done
  … Übersichtsseite schreiben …
  sleep $((INTERVAL_HOURS * 3600))
done
```
- `while true`: eine **Endlosschleife**. Sie läuft, bis der Container gestoppt wird.
- `[ -f datei ]`: „existiert diese Datei?“
- `for d in /data/*/`: für jeden Unterordner. `|| continue` überspringt Ordner ohne `config.json`, z. B. `data`
  und `report` des Hauptprofils.
- `basename`: der letzte Teil eines Pfads, aus `/data/anna/` wird `anna`.
- `sleep $((2 * 3600))`: 7200 Sekunden warten. `$(( … ))` rechnet in der Shell.

### Ein Stolperstein: Zeilenenden
Am Ende jeder Textzeile steht ein unsichtbares Zeichen. **Windows** nutzt zwei (`\r\n`, „CRLF“), **Linux** eins
(`\n`, „LF“). Läuft ein Windows-Shell-Skript unter Linux, sieht die Shell überall ein zusätzliches `\r` und
scheitert mit rätselhaften Fehlern. Deshalb wandelt `synology_paket.ps1` die Zeilenenden von `entrypoint.sh` beim
Packen um, und ich habe danach geprüft, dass kein `\r` mehr drin ist (`CR im entrypoint: False`).

### Was ich nicht testen konnte
Auf deinem PC ist kein Docker installiert und keine Linux-Umgebung. Den Python-Teil habe ich im Container-Modus
simuliert: mit dem Code aus dem Paket, `HEAVY_HOME` auf den `daten`-Ordner und dem Token von dort. Das Skript
habe ich auf Kompatibilität mit `sh` durchgesehen. Ob das Image auf dem DS216+ ohne Fehler baut, zeigt erst der
echte Build. Das Protokoll im Container Manager sagt dir dann, wo es hakt.

> **Selbst ausprobieren (auf der Synology):** Container Manager → **Image**: Dort siehst du `python` und `heavy`
> mit ihrer Größe. **Container** → `heavy` → **Details**: Unter „Volume“ und „Port“ findest du genau die Zuordnungen
> aus der Compose-Datei. Unter **Terminal** kannst du eine Shell *im* Container öffnen und `ls /data` tippen.

---

## 12. Betrieb und Sicherheit im Alltag

### Heimnetz und Internet
Dein Router trennt dein **Heimnetz** vom Internet. Geräte zu Hause erreichen sich gegenseitig, von außen kommt
niemand herein. Es sei denn, man richtet eine **Portfreigabe** ein. Dann wäre `http://<deine-adresse>:8080` für
die ganze Welt offen. Der eingebaute Python-Webserver ist einfach gebaut und nicht für das offene Internet
gedacht, und die Dashboards zeigen persönliche Trainingsdaten. **Deshalb: keine Portfreigabe für 8080.** Willst du
das Dashboard unterwegs sehen, ist ein VPN ins Heimnetz der richtige Weg, z. B. über die VPN-Funktion der
Synology oder deines Routers.

### Protokolle lesen
Wenn etwas nicht klappt, steht der Grund fast immer im **Protokoll**: Container Manager → Container `heavy` →
Protokoll. Lies von unten nach oben und such nach Wörtern wie `Fehler`, `Error`, `WARNUNG`, `fehlgeschlagen`.

### Backups
Wichtig zum Sichern sind nur die Ordner `daten` (NAS) bzw. `config.json`, `data\heavy.db` und `profile\` (PC).
Alles andere lässt sich neu erzeugen. Hyper Backup auf der Synology kann `docker/heavy/daten` mitsichern.

---

## 13. Wie ich vorgegangen bin: die Denkweise

Die Technik ist nur die halbe Miete. Die Reihenfolge der Schritte ist mindestens so wichtig:

1. **Das Problem genau verstehen.** Nicht „Garmin ist doof“, sondern: Vorlage und Aufzeichnung sind getrennt,
   und nichts verbindet sie.
2. **Den Lösungsraum abstecken.** Was wäre möglich (Uhr-App, offizielle API, inoffizielle API)? Was ist
   realistisch? Anleitung 2 zeigt, warum die anderen Wege ausschieden.
3. **Werkzeuge prüfen, bevor man baut.** Bibliothek installieren, ihren Code lesen, Funktionen und Datenformate
   bestätigen.
4. **Klein und getrennt bauen.** Rechenlogik ohne Außenwelt, dann Garmin-Anbindung, dann Dashboard.
5. **Mit Simulation testen.** Demo-Daten und Fake-Garmin, bevor das echte Konto im Spiel ist.
6. **Mit echten Daten prüfen, zuerst nur lesend.** Sync, ansehen, ob die Werte plausibel sind (Gramm oder kg?).
7. **Entscheidungen dem Menschen überlassen.** Wie die Steigerung laufen soll, ist deine Sache, nicht meine.
   Deshalb kamen die Fragen zu „nie senken“, Stufen und 8–12 Wdh.
8. **Testlauf vor jeder Wirkung nach außen**, dann senden und **danach nachprüfen** (Workouts zurücklesen).
9. **Ehrlich sein, was nicht geprüft ist.** Das Docker-Image und die Anzeige auf der Uhr konnte ich nicht testen,
   und das steht überall dabei.
10. **Fehler als Information sehen.** Jeder Fehler auf dem Weg (Untertyp, Zeitzone, SLED, Wochenschnitt) hat
    Heavy besser gemacht.

---

## 14. Selbst weiterlernen

### Kleine Übungen mit Heavy, von leicht nach schwer
1. `.\heavy.cmd demo --open` ausführen und im Demo-Dashboard alles anklicken.
2. In einer **Kopie** von `config.json` die Stufe für Kurzhanteln auf 2 kg ändern und mit
   `.\heavy.cmd progress --dry-run` schauen, was sich ändern würde. Danach zurückstellen.
3. Die Tests laufen lassen und absichtlich einen kaputt machen (Kapitel 7).
4. Im Dashboard mit F12 die Daten erkunden (Kapitel 8).
5. In `heavy/muscles.py` eine Regel ändern, z. B. dass `FACE_PULL` zusätzlich den Trapez (`"traps": S`) als
   Hilfsmuskel zählt, dann `.\heavy.cmd report --open`. (Deine Workouts enthalten keinen Face Pull, also probier
   es im Demo-Dashboard mit `.\heavy.cmd demo --open`.)
6. Auf der Synology im Container-Terminal `ls -la /data` und `cat /data/config.json` ausprobieren.

### Wo man weiterlernt
- **Python:** das offizielle Python-Tutorial (docs.python.org, gibt es auch auf Deutsch)
- **Kommandozeile:** Microsofts PowerShell-Dokumentation, Abschnitt „Erste Schritte“
- **Web (HTML/CSS/JavaScript):** MDN Web Docs von Mozilla, sehr gut und auf Deutsch verfügbar
- **Docker:** die offizielle Anleitung „Get started“ unter docs.docker.com
- **Git:** Versionsverwaltung, der nächste sinnvolle Schritt. Damit hättest du jede Änderung an Heavy als
  rückholbaren Zwischenstand. Heavy ist bisher **nicht** unter Versionsverwaltung.

Der beste Lehrer ist ein eigenes kleines Problem. Du hast mit Heavy schon eins. Lies den Code, ändere
Kleinigkeiten, mach sie kaputt und repariere sie wieder.

---

## 15. Glossar

| Begriff | Erklärung |
|---|---|
| **API** | Schnittstelle, über die Programme mit einem Dienst sprechen |
| **Argument / Option** | Zusatzangaben zu einem Befehl, z. B. `--dry-run` |
| **Basis-Image** | Fertiges Image, auf dem man aufbaut (`python:3.12-slim`) |
| **CDN** | Servernetz, das Dateien wie Chart.js schnell ausliefert |
| **Client / Server** | Der Fragende / der Antwortende im Netz |
| **Container** | Laufende, abgeschottete Kiste aus einem Image |
| **CRLF / LF** | Zeilenende-Zeichen unter Windows / Linux |
| **CSS** | Sprache für das Aussehen von Webseiten |
| **Deload** | Geplante Gewichtsreduktion nach wiederholtem Scheitern |
| **Docker Compose** | Datei, die beschreibt, wie Container laufen |
| **Dockerfile** | Rezept zum Bauen eines Images |
| **Doppel-Progression** | Erst Wiederholungen steigern, dann Gewicht |
| **Dry-Run / Testlauf** | Alles rechnen, nichts verändern |
| **e1RM** | Geschätztes Maximalgewicht für eine Wiederholung |
| **Exit-Code** | Zahl, mit der ein Programm Erfolg (0) oder Fehler meldet |
| **HTML** | Sprache für die Struktur von Webseiten |
| **HTTP** | Protokoll für Anfragen im Web (GET, POST, PUT …) |
| **Idempotent** | Mehrfach ausführen wirkt wie einmal |
| **Image** | Unveränderliches Paket aus Programm und Umgebung |
| **Interpreter** | Programm, das Python-Code ausführt |
| **JavaScript** | Programmiersprache im Browser |
| **JSON** | Textformat für strukturierte Daten |
| **localStorage** | Kleiner Speicher des Browsers pro Webseite |
| **MFA** | Anmeldung mit zweitem Faktor (Code vom Handy) |
| **Modul / Paket** | Eine Python-Datei / ein Ordner davon |
| **NAS** | Netzwerkspeicher, hier die Synology |
| **pip / PyPI** | Installationsprogramm / Verzeichnis für Python-Bibliotheken |
| **Port** | Nummerierte „Tür“ eines Computers fürs Netzwerk |
| **Portfreigabe** | Router-Einstellung, die eine Tür ins Internet öffnet (hier nicht machen!) |
| **Profil** | Heavys Ordner pro Person mit eigenen Daten und eigener Anmeldung |
| **Registry** | Online-Verzeichnis für Images (Docker Hub) |
| **Schicht (Layer)** | Zwischenstand beim Image-Bau, wird wiederverwendet |
| **Shell / sh** | Kommandozeilen-Sprache unter Linux |
| **SQL / SQLite** | Abfragesprache / Datenbank in einer einzigen Datei |
| **SVG** | Vektorgrafik aus Text (die Muskelkarte) |
| **Test (Unit-Test)** | Kleines Programm, das prüft, ob Code das Richtige tut |
| **Token** | Befristeter digitaler Ausweis statt Passwort |
| **Umgebungsvariable** | Einstellung, die einem Programm von außen mitgegeben wird |
| **Volume / Bind-Mount** | Ordner des Gastgebers, der im Container erscheint |
| **x86_64 / ARM** | Prozessor-Architekturen (Intel/AMD bzw. Handy-artig) |
| **YAML** | Textformat der Compose-Datei, Einrückung zählt |
