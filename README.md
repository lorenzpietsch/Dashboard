# Portfolio Dashboard

Interaktives Portfolio-Dashboard mit [Streamlit](https://streamlit.io/). Alle
Daten sind synthetisch (generierte Namen, erfundene Zahlen).

## Features

- Filter nach Business Organisation, Project Phase und Project Classification
- Donut-Charts (Capex by invest, Classification), Balken- und gestapeltes
  Phasen-Diagramm
- Detaillierte Hover-Tooltips (Capex-Volumen, Anteil, Projektanzahl)
- Klick auf eine Organisation filtert die Tabelle und färbt sie in der
  Org-Farbe ein
- Detail-Tabelle mit RAG-Ampel-Färbung der PMR-Spalten

## Lokal starten

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Das Dashboard öffnet sich unter `http://localhost:8501`.

Daten neu generieren (optional):

```bash
python data_generator.py
```

## Online veröffentlichen (Streamlit Community Cloud)

1. Auf [share.streamlit.io](https://share.streamlit.io) mit GitHub anmelden.
2. **"Create app" → "Deploy a public app from GitHub"**.
3. Auswählen:
   - Repository: `lorenzpietsch/Dashboard`
   - Branch: `main`
   - Main file path: `app.py`
4. **"Deploy"** klicken.

Streamlit installiert automatisch die Pakete aus `requirements.txt` und stellt
das Dashboard unter einer öffentlichen URL bereit. Jeder Push auf `main`
aktualisiert die App automatisch.

## Dateien

| Datei | Zweck |
|-------|-------|
| `app.py` | Streamlit-Dashboard |
| `data_generator.py` | Erzeugt den synthetischen Datensatz |
| `portfolio_data.csv` | Vorgenerierte Daten (App startet sofort) |
| `requirements.txt` | Python-Abhängigkeiten |
| `.streamlit/config.toml` | Streamlit-Konfiguration |