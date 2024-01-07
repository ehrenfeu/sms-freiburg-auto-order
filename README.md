# Freiburg school mensa lunch auto-order tool

## Setup

```bash
git clone https://github.com/ehrenfeu/sms-freiburg-auto-order
cd sms-freiburg-auto-order
python3 -m venv venv
pip install --upgrade pip selenium loguru ipython  # ipython is optional

cp credentials.example.py schulessen_credentials.py
editor schulessen_credentials.py  # adjust login credentials
```
