#!/bin/sh
# Heavy im Container: alle INTERVAL_HOURS Stunden "heavy auto" für jedes Profil.
#   /data             = Hauptprofil (Name aus HAUPTPROFIL)
#   /data/<name>/     = weitere Personen (je eigene config.json, Datenbank, Garmin-Token)
# Ausgeliefert wird nur /web (die Dashboards) - nie /data mit den Tokens.
mkdir -p /web
python -m http.server "$PORT" --directory /web --bind 0.0.0.0 >/dev/null 2>&1 &
echo "Heavy gestartet: Lauf alle ${INTERVAL_HOURS} h, Dashboards auf Port ${PORT}"

run_profile() {
  dir="$1"; name="$2"
  echo "--- Profil: $name ---"
  if [ ! -f "$dir/.garminconnect-heavy/garmin_tokens.json" ]; then
    echo "WARNUNG: kein Garmin-Token in $dir/.garminconnect-heavy/ - siehe ANLEITUNG.md"
  fi
  HEAVY_HOME="$dir" HEAVY_TOKENSTORE="$dir/.garminconnect-heavy" HEAVY_PROFILE="$name" \
    python -m heavy auto || echo "Lauf für $name fehlgeschlagen (Details oben)"
  if [ -f "$dir/report/dashboard.html" ]; then
    mkdir -p "/web/$name"
    cp "$dir/report/dashboard.html" "/web/$name/index.html"
  fi
}

while true; do
  echo "===== $(date '+%Y-%m-%d %H:%M') ====="
  names=""
  if [ -f /data/config.json ]; then
    run_profile /data "$HAUPTPROFIL"
    names="$HAUPTPROFIL"
  fi
  for d in /data/*/; do
    d="${d%/}"
    [ -f "$d/config.json" ] || continue
    n="$(basename "$d")"
    run_profile "$d" "$n"
    names="$names $n"
  done

  # Übersichtsseite
  {
    echo '<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Heavy</title>'
    echo '<style>body{font:16px system-ui,sans-serif;margin:0;padding:32px 16px;background:#f9f9f7;color:#0b0b0b}@media(prefers-color-scheme:dark){body{background:#0d0d0d;color:#f0efec}a{background:#1a1a19!important;color:#f0efec!important}}h1{font-size:22px}a{display:block;max-width:420px;margin:8px 0;padding:14px 16px;border-radius:12px;background:#fff;border:1px solid rgba(128,128,128,.25);color:#0b0b0b;text-decoration:none;font-weight:600;text-transform:capitalize}</style></head><body><h1>Heavy · Kraftprogression</h1>'
    for n in $names; do echo "<a href=\"$n/\">$n</a>"; done
    echo "<p style=\"color:#898781;font-size:13px\">Stand $(date '+%d.%m.%Y %H:%M')</p></body></html>"
  } > /web/index.html

  sleep $((INTERVAL_HOURS * 3600))
done
