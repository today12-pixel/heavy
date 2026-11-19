# Anleitung 2: Warum Heavy so gebaut ist und wie die Logik funktioniert

Dieses Dokument erklärt die **Entscheidungen** hinter Heavy und die **Regeln**, nach denen es rechnet.
Wenn du eine Zahl im Dashboard oder ein neues Gewicht auf der Uhr nachvollziehen willst, findest du hier die Antwort.

---

## 1. Das Ausgangsproblem

Garmin trennt zwei Dinge strikt:

| | **Workout** (Vorlage) | **Aktivität** (Aufzeichnung) |
|---|---|---|
| Was | Der Plan: „Leg Curl, 3 Sätze, 12 Wdh, 70 kg“ | Was wirklich passiert ist: „12 Wdh @ 70 kg, 12 @ 70, 15 @ 65“ |
| Wo | Garmin Connect → Training → Workouts | Garmin Connect → Aktivitäten |
| Ändert sich durch Training? | **Nein** | Wird neu angelegt |

Erhöhst du auf der Fenix während des Trainings das Gewicht, landet das nur in der **Aktivität**. Die **Vorlage**
bleibt starr. Beim nächsten Mal steht wieder das alte Gewicht drin. Garmin bietet keine Einstellung, die das ändert.

**Heavys Kernidee:** Ein Programm liest nach jedem Training die Aktivität, entscheidet nach festen Regeln das
nächste Zielgewicht und schreibt es in die Vorlage zurück. Die Uhr holt sich die aktualisierte Vorlage beim
nächsten Sync.

### Welche Alternativen ich verworfen habe

| Alternative | Warum nicht |
|---|---|
| **App direkt auf der Uhr** (Connect IQ) | Connect-IQ-Apps können Garmins eingebaute Krafttraining-Workouts nicht umschreiben. Man müsste das ganze Krafttraining selbst nachbauen (Satzerkennung, Aufzeichnung, Anzeige). Das ist sehr viel Aufwand, und Garmins Wiederholungs- und Übungserkennung ginge verloren. |
| **Offizielle Garmin-Schnittstelle** | Garmins offizielle Entwickler-Schnittstellen sind für Firmen gedacht und brauchen eine Freischaltung. Für eine Privatperson sind sie praktisch nicht zugänglich. |
| **Gewichte nach jedem Training von Hand ändern** | Genau das sollte wegfallen. |
| **Eine fremde Trainings-App statt Garmin** | Du wolltest bei der Fenix und Garmin Connect bleiben. |

Gewählt habe ich deshalb die **inoffizielle Schnittstelle**, die auch die Garmin-Connect-Webseite selbst nutzt,
über die verbreitete Open-Source-Bibliothek `garminconnect`. Der Nachteil: Garmin kann diese Schnittstelle
jederzeit ändern, ohne Vorwarnung. Dann hilft meist ein Update der Bibliothek (`pip install -U garminconnect`).

---

## 2. Überblick: der Weg der Daten

```
 ┌──────────┐  Bluetooth   ┌────────────┐   Internet   ┌──────────────────┐
 │ Fenix 8  │ ───────────▶ │ Garmin-App │ ───────────▶ │  Garmin Connect  │
 └──────────┘              └────────────┘              │  (Garmins Server)│
      ▲                                                └────────┬─────────┘
      │ nächster Sync: neue Vorlage                     ① Sätze │ ▲ ③ Vorlage
      │                                                   lesen │ │ zurückschreiben
      │                                                         ▼ │ ④ an Uhr senden
      │                                                ┌──────────┴───────┐
      └──────────────────────────────────────────────  │      Heavy       │
                                                       │ (Synology / PC)  │
                                                       │ ② rechnen        │
                                                       │ ⑤ Dashboard      │
                                                       └──────────────────┘
```

Ein Lauf von `heavy auto` macht genau diese Schritte:

1. **sync:** neue Krafttrainings mit allen Sätzen holen und lokal speichern
2. **progress:** pro Übung der verwalteten Workouts das neue Ziel berechnen
3. die geänderten Workouts per **Update** zurück zu Garmin Connect schreiben
4. das Workout **an die Uhr senden**
5. **report:** das Dashboard neu erzeugen

---

## 3. Die Bausteine im Code

| Datei | Aufgabe |
|---|---|
| `heavy/__main__.py` | Kommandozeile: `login`, `sync`, `workouts`, `manage`, `progress`, `report`, `auto`, `demo`, `profile` |
| `heavy/garmin.py` | Anmeldung, Trainings und Sätze von Garmin holen |
| `heavy/db.py` | Lokale Datenbank (SQLite): Trainings, Sätze, Änderungsprotokoll |
| `heavy/progression.py` | **Die Rechenregeln**, ohne jede Garmin-Abhängigkeit, daher gut testbar |
| `heavy/workouts.py` | Garmin-Workouts lesen und gezielt ändern |
| `heavy/engine.py` | Verbindet alles: Workout holen → rechnen → zurückschreiben → an Uhr senden → protokollieren |
| `heavy/config.py` | Einstellungen (`config.json`), Regel-Zusammenbau, Profile |
| `heavy/muscles.py` | Welche Übung trifft welchen Muskel |
| `heavy/report.py` + `templates/dashboard.html` | Das Dashboard |
| `heavy/demo.py` | Simulierte 20 Wochen zum Ausprobieren ohne Garmin-Konto |
| `tests/test_heavy.py` | 20 automatische Tests |
| `synology/` | Docker-Dateien für die Synology |

**Warum diese Aufteilung?** Die Rechenregeln (`progression.py`) wissen nichts von Garmin, Datenbank oder
Internet. Man kann sie deshalb mit erfundenen Zahlen testen. Ändert Garmin seine Schnittstelle, betrifft das nur
`garmin.py`. Die Regeln bleiben richtig.

---

## 4. Schritt ①: Trainings holen (sync)

- Heavy fragt Garmin nach Aktivitäten vom Typ `fitness_equipment` und behält nur die mit dem Untertyp
  `strength_training`. Garmin verlangt das so: Fragt man direkt nach `strength_training`, kommt der
  Fehler „Activity type cannot be an activity sub type“. Das war beim ersten echten Test der Fall.
- Pro Training holt Heavy die **Satzliste** (`exerciseSets`). Jeder Satz enthält:
  - **Typ:** `ACTIVE` (Satz) oder `REST` (Pause). Pausen werden verworfen.
  - **Übung:** Die Uhr liefert mehrere Vermutungen mit Wahrscheinlichkeit. Heavy nimmt die wahrscheinlichste.
  - **Wiederholungen** und **Gewicht**
- **Gewichtseinheit:** Garmin speichert Gewichte intern meist in **Gramm** (60000 = 60 kg). Heavy rechnet
  Werte ab 500 als Gramm, kleinere als Kilogramm. 0,5 kg in Gramm wäre ja sinnlos.
- **Beim ersten Mal** lädt Heavy 365 Tage, danach nur noch ab dem letzten bekannten Training (minus 3 Tage
  Sicherheitspuffer). Bekannte Trainings werden übersprungen. `sync --refresh 14` lädt die letzten 14 Tage
  trotzdem neu, nützlich nach Korrekturen in Garmin Connect.

---

## 5. Schritt ②: Die Rechenregeln (das Herzstück)

Für jede Übung in einem verwalteten Workout:

### 5.1 Welches Training zählt?

Das **jüngste** Training, in dem diese Übung vorkam, erkannt am Schlüssel `KATEGORIE/ÜBUNG`, z. B.
`LEG_CURL/WEIGHTED_LEG_CURL`. Hat die Vorlage nur eine Kategorie ohne genaue Übung, nimmt Heavy die jüngste
Übung dieser Kategorie.

### 5.2 Arbeitssätze herausfiltern

- Sätze mit **0 Wiederholungen** fallen weg. Das sind meist Erkennungsfehler der Uhr.
- **Aufwärmsätze** fallen weg: alles unter **60 %** des schwersten Gewichts dieser Übung im Training
  (`warmup_ratio`).
- Das **Basisgewicht** ist das schwerste verbleibende Gewicht. Die **Topsätze** sind alle Sätze mit diesem Gewicht.

> **Darum wird die Änderung auf der Uhr übernommen:** Die Basis ist immer das, was du *gemacht* hast, nicht
> das, was in der Vorlage stand. Erhöhst du auf der Uhr von 70 auf 75 kg, ist 75 kg die Basis.

### 5.3 Doppel-Progression im Bereich 8–12 Wiederholungen

„Doppel-Progression“ heißt: Erst steigen die **Wiederholungen**, dann das **Gewicht**. Entscheidend ist der
schwächste Topsatz (die kleinste Wiederholungszahl):

| Schwächster Topsatz | Entscheidung | Neues Wdh-Ziel |
|---|---|---|
| **≥ 12** (Obergrenze) | Gewicht **+ Stufe** | zurück auf **8** |
| **8–11** (im Bereich) | Gewicht **halten** | schwächster Satz **+1** (max. 12) |
| **< 8** (unter Bereich) | Gewicht **halten**, Fehlversuch zählen | bleibt |
| **< 8 zum 3. Mal in Folge** mit gleichem Gewicht | **Deload**: −10 % | **8** |

**Beispiele aus deinen echten Daten:**
- Leg Curl: 12/12 @ 70 kg → alle ≥ 12 → **75 kg**, Ziel **8 Wdh**.
- Leg Press: 10/9/12 @ 69 kg → schwächster Satz 9 → Gewicht bleibt, Ziel **10 Wdh**.
- Weighted Crunch: 5 @ 40 kg → unter 8 → halten, Fehlversuch 1 von 3.

### 5.4 Steigerungsstufen

Die Stufe hängt vom Gerät ab. Erkannt wird das am Übungsnamen (`name_rules` in `config.json`):

| Stichwort im Namen | Stufe |
|---|---|
| `SMITH` | +2,5 kg |
| `DUMBBELL` | +1 kg |
| `CABLE`, `MACHINE`, `LEG_PRESS`, `CHEST_PRESS`, `LEG_CURL`, `SEATED`, `KICKBACK`, … | +5 kg |
| sonst | +2,5 kg (Standard) |

**Welche Regel gewinnt?** Heavy baut die Regel einer Übung in Schichten zusammen. Spätere Schichten
überschreiben frühere:

```
default_rule  →  category_rules  →  name_rules  →  exercise_rules
(für alle)       (z. B. CURL)       (z. B. DUMBBELL)  (genau eine Übung)
```

Gerundet wird auf 0,5 kg. Ein **Deload** rundet auf das Stufenraster (z. B. 2,5-kg-Schritte), damit die Scheiben passen.

### 5.5 „Nie senken“

Hast du leichter trainiert als geplant (z. B. Schulterdrücken mit 5 statt 7 kg), würde die Basis-Regel die
Vorlage auf 5 kg setzen. Mit `allow_decrease: false` (deine Einstellung) bleibt die Vorlage bei 7 kg. Gesenkt
wird nur durch einen Deload. Der Grund steht im Protokoll: „Vorlage bleibt 7 kg (nie senken)“.

### 5.6 Körpergewichtsübungen

Übungen mit 0 kg (z. B. Crunch ohne Gewicht) werden im Dashboard ausgewertet, aber nicht automatisch angepasst.

---

## 6. Schritt ③ und ④: Vorlage ändern und an die Uhr senden

- Heavy holt das **komplette** Workout als JSON (strukturierter Text) von Garmin.
- Ein Workout ist verschachtelt: **Segmente** → **Wiederholungsgruppen** („3 ×“) → **Schritte** (Übung,
  Pause). Heavy läuft alle Schritte durch und ändert **nur** bei Übungsschritten das Gewicht (`weightValue`,
  in Gramm) und ggf. die Wiederholungen (`endConditionValue`). Alles andere bleibt unangetastet: Pausen,
  Reihenfolge, Notizen.
- **Pyramiden:** Hat eine Übung unterschiedliche Gewichte pro Satz (z. B. 60/70/80), verschiebt Heavy alle
  um denselben Betrag. Aus 60/70/80 wird bei +5 kg also 65/75/85.
- Das geänderte Workout geht per **Update** (HTTP `PUT`) zurück. Die **Workout-ID bleibt gleich**, deshalb
  bleiben Kalendereinträge und Trainingspläne erhalten.
- Dann folgt der Befehl **„an Gerät senden“**. Die Uhr holt es beim nächsten Sync.
- Ändert sich im ganzen Workout nichts, wird es auch nicht hochgeladen.

---

## 7. Sicherheit gegen doppeltes Anwenden

Heavy läuft alle 2 Stunden, aber du trainierst vielleicht nur alle 2–3 Tage. Ohne Schutz würde jeder Lauf
erneut „+5 kg“ rechnen. Deshalb gibt es das **Änderungsprotokoll** (Tabelle `changes` in der Datenbank):

- Jede Entscheidung wird mit **Workout, Übung und Trainings-ID** gespeichert.
- Vor jeder Berechnung prüft Heavy, ob für dieses Training schon entschieden wurde. Wenn ja, überspringt es die Übung.
- Zusätzlich ist die Rechnung selbst stabil: Die Basis kommt aus dem Training, nicht aus der Vorlage. Selbst
  ohne Protokoll ergibt dasselbe Training immer dasselbe Ziel. Das hat sich bestätigt, als du die Datenbank
  gelöscht hast: Neu eingelesen kamen **0 Änderungen** heraus.

Fachbegriff dafür: **Idempotenz**. Eine Aktion mehrfach auszuführen hat dieselbe Wirkung wie einmal.

**Testlauf (`--dry-run`):** rechnet alles, sendet nichts und markiert nichts als erledigt.

---

## 8. Das Dashboard: woher die Zahlen kommen

| Element | Berechnung |
|---|---|
| **Geschätztes 1RM** | Formel nach Epley: `Gewicht × (1 + Wdh / 30)`, Wdh begrenzt auf 15. Bester Arbeitssatz des Trainings. So werden Sätze mit unterschiedlichen Wdh vergleichbar. |
| **Größte Steigerungen** | 1RM des **ersten** vs. **letzten** Trainings im gewählten Zeitraum, nur Übungen mit ≥ 2 Trainings. In % oder kg. |
| **Neue Bestwerte** | Trainings, deren 1RM höher war als alles davor bei dieser Übung |
| **Bewegte Last** | Summe Gewicht × Wdh aller Arbeitssätze |
| **Muskelkarte: Progression** | Mittelwert der 1RM-Veränderungen aller Übungen, die den Muskel treffen. Hauptmuskel zählt 1, Hilfsmuskel ½. |
| **Muskelkarte: Sätze/Woche** | Arbeitssätze pro Woche. Hilfsmuskeln zählen halb, z. B. Bankdrücken: Brust 1 Satz, Trizeps ½. |
| **Heatmap** | Wie Sätze/Woche, aber pro Kalenderwoche |
| **Wochenschnitt** | gerechnet ab deinem **ersten** Training, nicht ab Beginn des Zeitraums |

**Zuordnung Übung → Muskel** (`muscles.py`): zuerst Regeln nach Stichwort im Namen (z. B. `ROMANIAN` →
Beinbeuger und Gesäß, `CHEST_PRESS` → Brust), sonst nach Garmin-Kategorie (z. B. `ROW` → oberer Rücken und
Latissimus). Die Stichwortregel für `CHEST_PRESS` brauchte es, weil deine Uhr die Brustpresse der Kategorie
`SLED` zuordnet. Ohne die Regel hätte die Karte sie als Beintraining gezählt.

**Farben:** Grau heißt nicht trainiert, dunkelgrau heißt trainiert, aber kaum Veränderung (±1 %), blau heißt
Steigerung, rot heißt Rückgang. Die Farbstufen sind so gewählt, dass sie auch bei Farbsehschwäche
unterscheidbar bleiben.

**Warum eine HTML-Datei und keine App?** Eine einzelne Datei läuft in jedem Browser, auf PC und Handy, ohne
Installation und ohne Server, der dauerhaft rechnen muss. Die Daten stecken direkt in der Datei. Die
Diagramme zeichnet die Bibliothek Chart.js, die beim Öffnen aus dem Internet nachgeladen wird. Ohne Internet
erscheint an Stelle der Diagramme ein Hinweis. Kacheln, Steigerungsliste, Muskelkarte, Tabellen und Heatmap
funktionieren weiter. Die Muskelkarte ist selbst gezeichnetes SVG (Vektorgrafik).

---

## 9. Profile (mehrere Personen)

- **Hauptprofil:** der Projektordner selbst (`config.json`, `data/`, `report/`). Das Token liegt in
  `C:\Users\<du>\.garminconnect-heavy`.
- **Weitere Personen:** `profile\<name>\` mit eigener `config.json`, Datenbank, Dashboard und eigenem Token im
  Profilordner.
- `--profil <name>` stellt Heavy für diesen einen Befehl auf den Ordner um.
- Ein neues Profil kopiert die **Regeln** des Hauptprofils, aber **nicht** die Workouts und **nicht** die Anmeldung.

---

## 10. Die Synology-Variante

- Ein **Docker-Container** (Erklärung in Anleitung 3) läuft dauerhaft und wiederholt in einer Schleife:
  für jedes Profil `heavy auto`, dann Übersichtsseite schreiben, dann 2 Stunden schlafen.
- `daten/` auf dem NAS ist das Hauptprofil, `daten/<name>/` sind weitere Personen. Erkannt wird ein Profil
  an einer `config.json` im Ordner.
- **Sicherheitsentscheidung:** Der eingebaute Webserver liefert nur den Ordner `/web` aus. Dorthin kopiert
  Heavy nach jedem Lauf **nur die Dashboards**. Die Datenordner mit den Garmin-Tokens sind übers Netz nicht
  erreichbar. Port 8080 ist trotzdem nur fürs Heimnetz gedacht.
- Der Container startet nach einem NAS-Neustart von selbst (`restart: unless-stopped`).

---

## 11. Bekannte Grenzen

- **Inoffizielle Schnittstelle:** kann sich ohne Vorwarnung ändern.
- **Garmin-Coach- und adaptive Pläne** lassen sich nicht ändern, nur eigene Workouts.
- **Übungserkennung:** Erkennt die Uhr eine Übung falsch oder zählt 0 Wiederholungen, rechnet Heavy mit
  falschen Daten. Korrigiere das in Garmin Connect und lade neu (`sync --refresh`).
- **Token-Ablauf:** Irgendwann muss man sich neu anmelden, mit MFA nur am PC.
- **Nicht getestet:** Das Docker-Image selbst lief noch nicht auf einer echten Synology, weil am PC kein Docker
  installiert ist. Getestet ist der Programmcode im Container-Modus.
