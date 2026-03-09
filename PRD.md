Dieses Product Requirements Document (PRD) dient als Grundlage für die Entwicklung des **HoferLand Dashboards**. Es beschreibt die Vision, die funktionalen und technischen Anforderungen sowie die Roadmap für die Implementierung.

---

# Product Requirements Document (PRD): HoferLand Data Dashboard

## 1. Projektübersicht
### 1.1 Vision
Ein zentrales, webbasiertes Dashboard für die Region „HoferLand“ (Stadt Hof und Landkreis Hof), das komplexe statistische Daten der Regionalstatistik (Genesis-Datenbank) visualisiert. Das Tool soll Entscheidungsträgern und Bürgern helfen, Trends in den Bereichen Demografie, Wirtschaft und Soziales zu verstehen.

### 1.2 Ziele
*   **Automatisierung:** Datenabruf über die Genesis REST-API mittels POST-Methoden.
*   **Lokale Entwicklung:** Erstbetrieb auf einem MacBook (Localhost).
*   **Skalierbarkeit:** Einfaches Hinzufügen weiterer Regionen (Nachbarlandkreise) und Kennzahlen (Kaufkraft, Arbeitslosigkeit).
*   **Historisierung:** Speicherung von Daten ab 2014 bis zum aktuell verfügbaren Zeitpunkt.

---

## 2. Zielgruppe
*   Regionale Planer und Entscheider im HoferLand.
*   Interessierte Bürger und lokale Medien.
*   (Später) Wirtschaftsförderungen der umliegenden Landkreise.

---

## 3. Funktionale Anforderungen

### 3.1 Datenbeschaffung (ETL-Prozess)
*   **API-Integration:** Anbindung an `https://www.regionalstatistik.de/genesisws/rest/2020/`.
*   **Authentifizierung:** Sicherer Umgang mit den Zugangsdaten (Benutzername/Passwort/Code) über Umgebungsvariablen. (.env)
*   **POST-Abfragen:** Implementierung der Schnittstellen unter Verwendung von POST-Requests (gemäß WADL), um spezifische Tabellen oder Zeitreihen abzurufen.
*   **Initial-Load:** Abruf der Daten für Stadt Hof (AGS: `09464`) und Landkreis Hof (AGS: `09475`) ab dem Jahr 2014.
*   **Update-Logik:** Mechanismus zur Überprüfung auf neue Daten (da die Genesis-Daten oft zeitverzögert erscheinen).

### 3.2 Datenspeicherung
*   **Lokale Datenbank:** Nutzung einer relationalen Datenbank (z.B. PostgreSQL oder SQLite), um die API-Antworten persistent zu speichern.
*   **Normalisierung:** Trennung von Geografien (Regionen), Indikatoren (Kaufkraft, Arbeitslose) und Zeitreihen (Werte pro Jahr/Monat).

### 3.3 Visualisierung & Dashboard
*   **Filteroptionen:** Auswahl von Region (Stadt vs. Landkreis), Zeitraum und Indikator.
*   **Diagrammtypen:** Liniendiagramme für Zeitreihen, Balkendiagramme für Vergleiche, einfache Kacheln für aktuelle Kennzahlen.
*   **Responsivität:** Das Dashboard muss im Browser auf dem MacBook flüssig laufen.

---

## 4. Technische Anforderungen (Stack-Vorschlag)

### 4.1 Backend
*   **Sprache:** Python (ideal für Datenverarbeitung und API-Handling).
*   **Framework:** FastAPI oder Flask für die API-Logik.
*   **API-Client:** `requests` oder `httpx` Bibliothek für die POST-Requests an Genesis.
*   **Task-Scheduling:** Ein einfaches Skript oder Cronjob zum regelmäßigen Datenabgleich.

### 4.2 Frontend
*   **Framework:** Streamlit (für schnelles Prototyping) oder React (für maximale Flexibilität).
*   **Charts:** Plotly oder Chart.js.

### 4.3 Infrastruktur
*   **Lokal:** Docker Desktop auf dem MacBook (erleichtert den späteren Umzug ins Internet).
*   **Datenbank:** PostgreSQL Container.
*   **Webserver:** Nginx (lokal als Proxy).

---

## 5. Datenstruktur & API-Spezifika

### 5.1 Relevante Parameter für Genesis-API
*   **Endpoint:** `data/tablefile` (für große Tabellen) oder `data/timeseries`.
*   **Method:** POST.
*   **Format:** JSON (muss im Request-Header spezifiziert sein).
*   **Wichtige IDs:**
    *   Stadt Hof: `09464`
    *   Landkreis Hof: `09475`
    *   (Zukünftig z.B. Wunsiedel: `09479`, Bayreuth Land: `09472`)

### 5.2 Geplante Daten-Ebenen
1.  **Basis:** Bevölkerung (Bestand, Zu-/Fortzug).
2.  **Soziales:** Migrationsanteil, Arbeitslosenquote.
3.  **Wirtschaft:** Kaufkraft, Gewerbeanmeldungen.

---

## 6. Roadmap

### Phase 1: MVP (Minimum Viable Product) - *Fokus: HoferLand Basis*
*   Setup der lokalen Entwicklungsumgebung (Docker/Python).
*   Implementierung der POST-Requests für die Tabelle "Bevölkerung" (2014-heute).
*   Speicherung in lokaler DB.
*   Einfache Visualisierung der Bevölkerungsentwicklung in Streamlit.

### Phase 2: Erweiterung - *Fokus: Tiefe & Breite*
*   Implementierung weiterer Kennzahlen (Arbeitslose, Kaufkraft).
*   Hinzufügen der Nachbarlandkreise zur Vergleichbarkeit.
*   Optimierung der UI (Kartenansicht der Region).

### Phase 3: Deployment - *Fokus: Internetpräsenz*
*   Hosting auf einem Cloud-Server (z.B. Hetzner, AWS oder DigitalOcean).
*   Einrichtung einer Domain (z.B. dashboard.hoferland.de).
*   Absicherung über HTTPS (Let's Encrypt).

---

## 7. Risiken und Herausforderungen
*   **API-Komplexität:** Die Genesis-API ist mächtig, aber komplex strukturiert (Codes für Merkmale). Eine saubere Mapping-Tabelle im Backend ist essenziell.
*   **Datenaktualität:** Statistische Ämter veröffentlichen Daten teils mit 1-2 Jahren Verzug. Das Dashboard muss "N/A" Zustände sauber abfangen.
*   **Performance:** Bei vielen Landkreisen und Jahren müssen die Daten effizient indiziert sein.

---

## 8. Nächste Schritte
1.  **Zugangsdaten prüfen:** Sicherstellen, dass ein gültiger Login für `regionalstatistik.de` vorliegt.
2.  **API-Test:** Erster manueller POST-Request via `Postman` oder `curl`, um die Tabellenstruktur der Stadt Hof zu validieren.
3.  **Datenmodellierung:** Entwurf der SQL-Tabellen für die Zeitreihen.

---
*Erstellt am: 24. Mai 2024*
*Status: Entwurf / In Planung*