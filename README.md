# Cambium Import Details Tool

## Quick Start
```bash
pip install pandas openpyxl
python3 server.py
```
Open: http://localhost:8000  
Password: **hazique123**

## Features
- 📊 Excel-like editable table — double-click any cell to edit inline
- ↩ Undo / Redo (Ctrl+Z / Ctrl+Y or buttons)
- 🔍 Search across all fields with highlighted matches
- 🔽 Filter by Brand, ASIN status, Inventory level
- 🔃 Sort by any column (click header)
- ➕ Add new rows via modal form
- ⧉ Duplicate rows
- ✕ Delete rows
- ⬇ Export filtered data as CSV or JSON
- 📈 Live stats bar (totals, missing ASIN count, etc.)
- 🔐 Password protected login screen

## Files
- `server.py`                       — run this to start
- `data.json`                       — live data (auto-saved on every edit)
- `Cambium_Import_Details.xlsx`     — original source
- `requirements.txt`                — Python deps

## Deploy to a Server
```bash
# Run in background
nohup python3 server.py &

# Or with screen
screen -S cambium
python3 server.py
```
