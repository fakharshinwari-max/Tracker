# Activity + Budget Tracker (Desktop)

A portable desktop tracker built with **Python + HTML/CSS/JS**.

## Features
- Track daily activities (title, category, date, duration, notes)
- Track monthly budgets (limit, spent, remaining)
- Local portable storage in `portable_data/tracker.db`
- Desktop app window via `pywebview`

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Build executable (portable)
```bash
pyinstaller --noconfirm --onefile --windowed \
  --add-data "templates:templates" \
  --add-data "static:static" \
  app.py
```

The executable will be created in `dist/`. Keep `portable_data/` next to it to preserve data portability.
