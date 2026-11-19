# Anleitung 1: Eine weitere Person hinzufügen

Diese Anleitung zeigt Schritt für Schritt, wie eine zweite Person Heavy mit **ihrem eigenen** Garmin-Konto nutzt.
Als Beispielname verwenden wir `anna`. Ersetze ihn überall durch den echten Namen.

> **Kurz erklärt:** Jede Person bekommt ein eigenes **Profil**. Ein Profil ist ein Ordner mit eigener
> Garmin-Anmeldung, eigenen Workouts, eigenen Regeln, eigener Datenbank und eigenem Dashboard.
> Die Profile wissen nichts voneinander. Annas Trainings landen nie in deinem Dashboard und umgekehrt.

---

## Was du brauchst

| Was | Warum |
|---|---|
| Deinen PC mit dem Heavy-Ordner (`C:\Users\<du>\Desktop\Heavy`) | Die Anmeldung bei Garmin passiert einmalig am PC |
| Die Person selbst (vor Ort oder am Telefon) | Sie gibt **ihre** E-Mail, **ihr** Passwort und den MFA-Code selbst ein |
| Eigene Krafttraining-Workouts in ihrem Garmin-Connect-Konto | Heavy passt nur eigene Workouts an, keine Garmin-Coach-Pläne |
| Zugriff auf die Synology (Explorer oder File Station) | Dort läuft Heavy dauerhaft |

**Regeln für den Profilnamen:** nur Kleinbuchstaben, Ziffern, `-` und `_`, keine Leerzeichen, keine Umlaute.
Gesperrt sind Namen, die Heavy selbst benutzt (`data`, `report`, `profile`, `heavy`, `tests`, `dist`, `synology`).
Gute Namen sind z. B. `anna`, `max`, `anna-m`.

---

## Schritt 1: Terminal im Heavy-Ordner öffnen

Öffne im Explorer den Ordner `C:\Users\<du>\Desktop\Heavy`, klicke in die Adresszeile, tippe `powershell`
und drücke Enter. Alle folgenden Befehle tippst du in dieses Fenster.

> Das `.\` vor `heavy.cmd` ist in PowerShell Pflicht. Es heißt „aus diesem Ordner“. Ohne meldet PowerShell,
> dass der Befehl nicht gefunden wurde.

## Schritt 2: Die Person meldet sich an

```bash
.\heavy.cmd --profil anna login
```

- Beim ersten Aufruf erscheint: `Neues Profil 'anna' angelegt (Regeln vom Hauptprofil übernommen)`.
- Dann fragt Heavy nach **E-Mail**, **Passwort** und ggf. **MFA-Code**. Die **Person tippt selbst**.
  Das Passwort bleibt bei der Eingabe unsichtbar und wird **nicht gespeichert**.
- Erfolg sieht so aus: `Angemeldet als <Name>. Token gespeichert …`

Gespeichert wird nur ein **Token** (eine Art befristeter Hausausweis) in `profile\anna\.garminconnect-heavy\`.
Dein eigenes Token bleibt davon unberührt.

## Schritt 3: Ihre Trainings laden

```bash
.\heavy.cmd --profil anna sync
```

Heavy lädt alle Krafttrainings der letzten 365 Tage. Pro Training erscheint eine Zeile mit `+`.

## Schritt 4: Ihre Workouts anzeigen und auswählen

```bash
.\heavy.cmd --profil anna workouts --details
```

Du siehst ihre Krafttraining-Workouts mit **ID** (lange Zahl), Übungen und Gewichten, zum Beispiel:

```
    1761234567  Ganzkörper A
      - Leg Press: 12 Wdh @ 60 kg
      ...
```

Dann wählst du die Workouts, die automatisch mitwachsen sollen:

```bash
.\heavy.cmd --profil anna manage 1761234567 1761234999
```

(Oder `.\heavy.cmd --profil anna manage --all` für alle Krafttraining-Workouts.)

## Schritt 5: Testlauf, noch ohne etwas zu senden

```bash
.\heavy.cmd --profil anna progress --dry-run
```

Heavy zeigt, was es ändern **würde**: `✎` heißt Änderung, `=` heißt alles bleibt. Am Ende steht
`(Testlauf – nichts an Garmin gesendet)`. Sprecht die Liste kurz gemeinsam durch.

**Regeln anpassen (optional):** Das neue Profil hat deine Regeln übernommen: 8–12 Wdh, nie senken,
Maschinen +5 kg, Kurzhanteln +1 kg, Smith +2,5 kg. Hat Anna andere Geräte oder Vorlieben, bearbeite
`profile\anna\config.json` mit dem Editor. Die Bedeutung der Felder steht im README im Abschnitt „Feineinstellung“.
Danach den Testlauf wiederholen.

## Schritt 6: Dashboard am PC ansehen (optional)

```bash
.\heavy.cmd --profil anna report --open
```

Oben im Dashboard steht `Heavy · Kraftprogression · Anna`.

> **Hinweis:** Schicke die Änderungen am PC nicht mit `.\heavy.cmd --profil anna progress` ab, wenn Anna ohnehin
> auf die Synology kommt. Die Synology übernimmt das. Sonst führen PC und NAS zwei getrennte Protokolle.

---

## Schritt 7: Paket nur für diese Person bauen

```bash
powershell -ExecutionPolicy Bypass -File .\synology_paket.ps1 -Profil anna
```

Das erzeugt **nur** `dist\heavy-synology\daten\anna\`. Programm und deine Daten sind darin nicht enthalten.
So kann beim Kopieren nichts von dir überschrieben werden.

Prüfe, dass im Ordner `daten\anna\.garminconnect-heavy\` die Datei `garmin_tokens.json` liegt.
Falls die Warnung `Kein Garmin-Token` erschien: Schritt 2 wiederholen.

## Schritt 8: Auf die Synology kopieren

1. Explorer → Adresszeile: `\\<IP-der-Synology>\docker\heavy\daten`
2. Den Ordner `anna` aus `dist\heavy-synology\daten\` dorthin kopieren.
3. Ergebnis auf dem NAS:
   ```
   docker/heavy/daten/
     config.json, data/, report/, .garminconnect-heavy/   ← du (Hauptprofil)
     anna/
       config.json
       data/heavy.db
       report/dashboard.html
       .garminconnect-heavy/garmin_tokens.json             ← Annas Zugang
   ```

> Der Ordner `.garminconnect-heavy` beginnt mit einem Punkt. Unter Linux heißt das „versteckt“. Er muss
> trotzdem mitkopiert werden. Im Windows-Explorer ist er normal sichtbar.

## Schritt 9: Container neu starten

DSM → **Container Manager** → **Container** → `heavy` → **Neu starten**.

Im **Protokoll** des Containers erscheint jetzt pro Lauf:

```
===== 2026-11-19 18:00 =====
--- Profil: haupt ---
...
--- Profil: anna ---
Synchronisiere Krafttrainings …
...
```

## Schritt 10: Dashboard öffnen

- Übersicht aller Personen: `http://<IP-der-Synology>:8080`
- Annas Dashboard: `http://<IP-der-Synology>:8080/anna/`

## Schritt 11: Aufräumen

Lösche den Ordner `dist` am PC. Er enthält Annas Garmin-Zugang.
Der Ordner `profile\anna` am PC bleibt als Backup und für spätere Neu-Anmeldungen.

---

## Häufige Fragen und Probleme

**Muss Anna dafür an meinen PC?**
Nur für die einmalige Anmeldung (Schritt 2), wegen Passwort und MFA-Code. Danach läuft alles auf der Synology.
Per Telefon geht es auch: Sie sagt dir den MFA-Code. Das Passwort sollte sie aber selbst tippen.

**Im Protokoll steht `Bitte einmal .\heavy.cmd --profil anna login ausführen`.**
Annas Token ist abgelaufen. Dann am PC `.\heavy.cmd --profil anna login`, die neue Datei
`profile\anna\.garminconnect-heavy\garmin_tokens.json` nach `docker/heavy/daten/anna/.garminconnect-heavy/`
kopieren (überschreiben) und den Container neu starten.

**Anna hat neue Workouts angelegt.**
Am PC `.\heavy.cmd --profil anna workouts --details` und `.\heavy.cmd --profil anna manage <neue ID>`. Dann die
geänderte `profile\anna\config.json` nach `docker/heavy/daten/anna/config.json` kopieren. Alternativ trägst
du die ID direkt auf dem NAS in `managed_workouts` ein.

**Annas Regeln auf dem NAS ändern.**
`docker/heavy/daten/anna/config.json` bearbeiten. Das gilt ab dem nächsten Lauf, ein Neustart macht es sofort.

**Person wieder entfernen.**
Auf dem NAS den Ordner `docker/heavy/daten/anna` löschen und den Container neu starten. Am PC kannst du
`profile\anna` löschen. In Annas Garmin-Konto bleibt alles, wie es zuletzt war.

**Alle Profile auf einen Blick (am PC):**
```bash
.\heavy.cmd profile
```
