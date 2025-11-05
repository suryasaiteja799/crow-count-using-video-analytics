# Crowd Count Using Video Analytics (Demo)

This is a simple demo app that lets users register/login, upload videos, and runs a basic OpenCV background-subtraction heuristic to estimate moving-object counts (a proxy for counting birds/crows or people). An admin user can view all users and records.

This is a demo. The video counting is not a trained crow detector — for production you'd integrate a trained object detector model.

Prerequisites
- Python 3.9+ installed
- Windows PowerShell (commands below assume PowerShell)

Quick start (PowerShell)

```powershell
# create and activate venv
python -m venv .venv; .\.venv\Scripts\Activate.ps1

# install dependencies
pip install -r requirements.txt

# run the app
python app.py
```

Open http://127.0.0.1:5000 in your browser.

Default admin user (created automatically):
- email: admin@local
- password: adminpass

Notes:
- Uploaded videos are saved to the `uploads/` folder.
- The counting algorithm in `video_process.py` uses background subtraction and contour area filtering — it's a heuristic.
