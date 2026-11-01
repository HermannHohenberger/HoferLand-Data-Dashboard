# HoferLand Data Dashboard (Phase 1 MVP)

MVP fuer den Vergleich der Bevoelkerungsentwicklung von 11 Regionen:

- Bayern (`09`)
- Oberfranken, Regierungsbezirk (`094`)
- Bayreuth, kreisfreie Stadt (`09462`)
- Hof, kreisfreie Stadt (`09464`)
- Bayreuth, Landkreis (`09472`)
- Hof, Landkreis (`09475`)
- Kronach, Landkreis (`09476`)
- Kulmbach, Landkreis (`09477`)
- Wunsiedel i.Fichtelgebirge, Landkreis (`09479`)
- Vogtlandkreis (`14523`)
- Saale-Orla-Kreis (`16075`)

Stack:

- Backend: FastAPI + SQLAlchemy + SQLite
- Frontend: React (Vite + TypeScript) + Recharts + Tailwind CSS
- Datenquelle: Genesis API (`regionalstatistik.de`)

## 1) Voraussetzungen

- Python 3.11+
- Node.js 22+
- Zugangsdaten fuer die Genesis API

## 2) Konfiguration

Im Projekt-Root eine `.env` erstellen:

```env
GENESIS_USERNAME=dein_username
GENESIS_PASSWORD=dein_passwort
GENESIS_BASE_URL=https://www.regionalstatistik.de/genesisws/rest/2020/
GENESIS_POPULATION_TABLE=12411-01-01-4
GENESIS_REGIONAL_VARIABLE=KREISE
ETL_START_YEAR=2014
```

## 3) Erstinstallation (einmalig)

### Backend (einmalig)

```bash
cd /Users/Hohenberger/CLI-Projekte/HoferLand-Data-Dashboard
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend (einmalig)

```bash
cd /Users/Hohenberger/CLI-Projekte/HoferLand-Data-Dashboard
cd frontend
npm install
```

## 4) Taeglicher Start (Startroutine)

Die typische Startroutine fuer die lokale Entwicklung:

1. Backend in Terminal 1 starten.
2. Frontend in Terminal 2 starten.
3. ETL (extract, transform, and load) ueber die Seite `/maintenance` einmal manuell ausfuehren.
4. Dashboard im Browser pruefen.

### Terminal 1: Backend starten

```bash
cd /Users/Hohenberger/CLI-Projekte/HoferLand-Data-Dashboard
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Backend ist dann unter `http://localhost:8000` verfuegbar.

### Terminal 2: Frontend starten

```bash
cd /Users/Hohenberger/CLI-Projekte/HoferLand-Data-Dashboard
cd frontend
npm run dev
```

Frontend ist dann unter `http://localhost:5173` verfuegbar.

### UI-Hinweise

- Standardauswahl beim Dashboard-Start:
  - Regionen: `Hof, kreisfreie Stadt` und `Hof, Landkreis`
  - Thema: `Bevoelkerung`
  - Bereich: `Bevoelkerung gesamt`
- Regionen werden ueber Checkboxen gewaehlt (Mehrfachauswahl).
- Bereiche koennen ebenfalls per Checkbox mehrfach ausgewaehlt werden.
- Die Linienbox zeigt pro Kombination aus Region/Bereich eine eigene Linie:
  - mehrere Regionen + mehrere Bereiche: `Region - Bereich`
  - eine Region + mehrere Bereiche: nur Bereichsname
  - mehrere Regionen + ein Bereich: nur Regionsname
- Die untere Box `Veraenderung` enthaelt:
  - Region
  - Aktueller Wert
  - Veraenderung absolut
  - Veraenderung in %
- Das Vergleichsjahr wird direkt in der unteren `Veraenderung`-Box gewaehlt.
- Die obere rechte Box `Datenquelle` zeigt:
  - Link zu `https://www.regionalstatistik.de`
  - verwendeten Tabellencode
  - Tabellenbeschreibung
- Hauptnavigation (oben):
  - sichtbar: `Dashboard`, `Ueber`, `Impressum`
  - `Maintenance` ist bewusst nicht verlinkt (nur direkt ueber `/maintenance` erreichbar).
- Statische Inhaltsseiten werden aus Markdown-Dateien geladen:
  - `frontend/public/ueber.md`
  - `frontend/public/impressum.md`
- Formatierung:
  - `Durchschnittsalter` (`AGE_*`), `Arbeitslosenquote` (`AL_RATE`) und `Auslaender Anteil %` (`BEV_FOREIGN_SHARE`) werden mit 1 Nachkommastelle angezeigt.

### ETL ausfuehren

Variante A (UI): Seite `/maintenance` verwenden und dort gezielt Bereiche starten.

Verfuegbare ETL-Bereiche:

- `bevoelkerung_gesamt`
- `auslaender`
- `durchschnittsalter`
- `wanderung_kreisgrenzen`
- `arbeitslose_gesamt`
- `arbeitslose_auslaender`
- `langzeitarbeitslose`
- `arbeitslosenquote`
- `derived`

Variante B (API, bereichsweise):

```bash
curl "http://localhost:8000/api/etl/areas"
curl -X POST "http://localhost:8000/api/etl/run-sequential?areas=bevoelkerung_gesamt,auslaender,derived&start_year=2014"
```

Hinweise zum ETL-Verhalten:

- Fuer mehrere Bereiche werden Genesis-Zeitreihen (`/data/timeseries`) genutzt, damit Jahre ab `start_year` geladen werden koennen.
- Bei fehlenden Daten im gewaehlten Startjahr wird automatisch auf fruehere Jahre bis `ETL_START_YEAR` zurueckgefallen.
- Die Antwort pro Bereich enthaelt `inserted_or_updated`, `status` (`ok|empty|error`) und optional `message`.
- Beim Bereich `durchschnittsalter` werden Teilfehler pro Quelltabelle/Jahr gesammelt; wenn trotzdem Daten geladen wurden, bleibt der Status `ok` und die Message weist auf Teilfehler hin.
- `Arbeitslose DE` (`AL_GERMAN`) wird automatisch bei Arbeitsmarkt-ETL mitberechnet (aus `Arbeitslose gesamt - Arbeitslose Auslaender`), auch wenn `derived` nicht explizit ausgewaehlt ist.
- Weitere abgeleitete Kennzahlen (z. B. `Auslaender Anteil %`) werden weiterhin im Bereich `derived` berechnet.

### Schnellchecks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/regions
curl http://localhost:8000/api/indicators
```

Wenn ETL erfolgreich war, liefern die ETL-Endpunkte Antworten wie:

```json
{
  "indicator_id": 2,
  "total_inserted_or_updated": 264,
  "results": [
    {
      "area": "arbeitslose_gesamt",
      "inserted_or_updated": 132,
      "status": "ok",
      "message": "Zeitreihe 2014-2025 geladen."
    },
    {
      "area": "arbeitslose_auslaender",
      "inserted_or_updated": 132,
      "status": "ok",
      "message": "Zeitreihe 2014-2025 geladen."
    }
  ]
}
```

Hinweis:

- `pip install -r requirements.txt` nur bei Erstinstallation, neuer venv oder geaenderten Python-Abhaengigkeiten.
- `npm install` nur bei Erstinstallation oder geaenderten Node-Abhaengigkeiten (`package.json`/`package-lock.json`).

## 5) API-Endpunkte (MVP)

- `GET /health`
- `GET /api/regions`
- `GET /api/indicators`
- `GET /api/data?region_id=1&indicator_id=1&start_year=2014&end_year=2024`
- `GET /api/data/latest?region_id=1&indicator_id=1`
- `GET /api/etl/areas`
- `POST /api/etl/run-sequential?areas=...&start_year=...`
- `POST /api/etl/run`
- `POST /api/etl/run-aggregates`

## 6) Deployment (Hostinger VPS, Subdomain + Nginx)

Ziel fuer den ersten Testbetrieb:

- Deployment auf Hostinger VPS mit Docker
- Erreichbarkeit ueber Subdomain `hoferland.hanstx.cloud`
- Reverse Proxy ueber Nginx Proxy Manager mit Let’s Encrypt
- SQLite wird lokal gepflegt und mit dem Deploy auf den VPS kopiert

Kurzer Ablauf:

1. DNS setzen (`A` und optional `AAAA` fuer `hoferland`).
2. Auf dem VPS `.env` fuellen und `docker compose up -d` starten.
3. In Nginx Proxy Manager:
   - Host `/` -> `127.0.0.1:8080` (Frontend)
   - Custom Location `/api` -> `127.0.0.1:8000` (Backend)
   - SSL/Force HTTPS aktivieren.
4. `/maintenance` zusaetzlich per Proxy absichern (IP-Allowlist oder Basic Auth).

Details und Schritt-fuer-Schritt:

- Siehe `docs/DEPLOY_HOSTINGER_VPS.md`

## 7) Welche Systeme muss ich starten?

### Lokal (Entwicklung)

Du brauchst 2 Prozesse:

1. **Backend (FastAPI)**
2. **Frontend (Vite)**

Start:

```bash
# Terminal 1
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2
cd frontend
npm run dev
```

Optional danach ETL ueber `/maintenance` ausfuehren.

### Server (Hostinger VPS, Produktiv/Test)

Du brauchst 2 Docker-Container aus diesem Projekt:

1. `backend`
2. `frontend`

Start/Neustart:

```bash
cd ~/HoferLand-Data-Dashboard
docker compose up -d --build
```

Status:

```bash
docker compose ps
```

Zusatz fuer oeffentliche Erreichbarkeit:

- **Nginx Proxy Manager** muss laufen (separater Container auf dem VPS).
- DNS fuer `hoferland.hanstx.cloud` muss auf den VPS zeigen.

### Empfohlene Reihenfolge nach Server-Neustart

1. Docker/Container-Umgebung hochfahren
2. Projekt-Stack starten: `docker compose up -d`
3. Pruefen: `docker compose ps`
4. Healthcheck API: `curl http://127.0.0.1:8000/health`
5. Website unter `https://hoferland.hanstx.cloud` testen
