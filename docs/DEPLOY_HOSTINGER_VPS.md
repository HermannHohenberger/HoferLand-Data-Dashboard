# Deployment auf Hostinger VPS (Subdomain + Nginx Proxy Manager)

Dieses Setup nutzt Docker auf deinem VPS, Nginx Proxy Manager (NPM) fuer HTTPS und eine Subdomain.

## 1) DNS konfigurieren

Bei Hostinger fuer `hoferland.hanstx.cloud` setzen:

- `A` Record: `hoferland` -> `76.13.153.214`
- optional `AAAA`: `hoferland` -> `2a02:4780:79:4130::1`

Warten, bis DNS propagiert ist.

## 2) Projekt auf den VPS bringen

```bash
git clone <dein-repo-url> HoferLand-Data-Dashboard
cd HoferLand-Data-Dashboard
cp .env.example .env
```

`.env` fuellen (Genesis Zugangsdaten + CORS):

- `GENESIS_USERNAME=...`
- `GENESIS_PASSWORD=...`
- `CORS_ORIGINS=["https://hoferland.hanstx.cloud"]`
- `SQLITE_DB_PATH=/data/hoferland.db`

## 3) Container starten

```bash
docker compose build
docker compose up -d
docker compose ps
```

Der Stack nutzt lokal gebundene Ports:

- Frontend: `127.0.0.1:8080`
- Backend: `127.0.0.1:8000`

## 4) Nginx Proxy Manager einrichten

In NPM einen Proxy Host anlegen:

- **Domain Names**: `hoferland.hanstx.cloud`
- **Scheme**: `http`
- **Forward Hostname / IP**: `127.0.0.1`
- **Forward Port**: `8080`
- **Block Common Exploits**: aktiv
- **Websockets Support**: aktiv

Dann unter **Custom Locations**:

- **Location**: `/api`
- **Scheme**: `http`
- **Forward Hostname / IP**: `127.0.0.1`
- **Forward Port**: `8000`

Danach unter **SSL**:

- Let’s Encrypt Zertifikat holen
- `Force SSL` aktivieren
- `HTTP/2 Support` aktivieren

## 5) /maintenance absichern (empfohlen)

Da die Route nicht oeffentlich gedacht ist, in NPM (Advanced) z. B. IP-Allowlist:

```nginx
location /maintenance {
    allow 1.2.3.4;
    deny all;
}
```

Oder alternativ Basic Auth (wenn auf deinem NPM bereits konfiguriert).

## 6) Daten aktualisieren

ETL laeuft lokal, nicht auf dem VPS. `backend/hoferland.db` gehoert zum Repository. Beim Containerstart kopiert das Backend diese Datei nach `/data/hoferland.db` und ersetzt damit die bisherige Server-Kopie.

Ablauf nach einem lokalen ETL:

```bash
# lokal
git add backend/hoferland.db
git commit -m "Aktualisiere Datenstand"
git push

# auf dem VPS
cd ~/HoferLand-Data-Dashboard
git pull
docker compose up -d --build
```

## 7) Smoke-Test

```bash
curl -sS https://hoferland.hanstx.cloud/api/health
curl -sS "https://hoferland.hanstx.cloud/api/data/latest?region_id=1&indicator_id=2"
```

Erwartung:

- Website oeffnet sich unter `https://hoferland.hanstx.cloud`
- Healthcheck liefert `{"status":"ok"}`
- Die API liefert den mitgelieferten Datenstand, ohne ETL auf dem Server

## 8) SQLite Backup (einfach, taeglich)

Beispiel als Cron-Job (auf dem VPS):

```bash
mkdir -p /opt/backups/hoferland
cp /var/lib/docker/volumes/hoferland-data-dashboard_hoferland_data/_data/hoferland.db \
  /opt/backups/hoferland/hoferland_$(date +\%F).db
find /opt/backups/hoferland -name "hoferland_*.db" -mtime +14 -delete
```

Den Volume-Pfad ggf. an deinen Compose-Projektnamen anpassen.
