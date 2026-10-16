# To-Do Task Manager (Flask + SQLite)

## Run locally
    python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    python app.py          # http://127.0.0.1:5000
    pip install pytest && pytest -q   # API tests

## REST API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/tasks?status=&search=&overdue=1` | List / filter / search |
| GET | `/api/tasks/<id>` | Single task |
| POST | `/api/tasks` | Create (title required) |
| PUT | `/api/tasks/<id>` | Update task details |
| PATCH | `/api/tasks/<id>` | Change status `{"status":"Completed"}` |
| DELETE | `/api/tasks/<id>` | Delete |

## Deploy on Render
1. Push this folder to GitHub.
2. Render > New > Web Service > connect the repo.
3. Build: `pip install -r requirements.txt` | Start: `gunicorn app:app`
4. SQLite on free tiers is wiped on redeploy. Add a persistent disk and set env var `DB_PATH=/data/tasks.db` to keep tasks.
