# Beautiful Activity + Budget + Expenditure Tracker

Desktop tracker built with **Python + Flask + HTML/CSS/JS + pywebview**.

## Includes
- Activity tracking
- Monthly budgets
- Expenditure entry (linked/unlinked to budgets)
- Beautiful glassmorphism UI
- Portable SQLite storage at `portable_data/tracker.db`

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Build desktop executable
```bash
pyinstaller --noconfirm --onefile --windowed \
  --add-data "templates:templates" \
  --add-data "static:static" \
  app.py
```
