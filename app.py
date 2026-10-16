import os, sqlite3
from datetime import date
from flask import Flask, g, jsonify, request, send_from_directory

DB = os.environ.get("DB_PATH", "tasks.db")
app = Flask(__name__, static_folder="static")
PRIORITIES = ("Low", "Medium", "High")
STATUSES = ("Pending", "Completed")

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close(_):
    d = g.pop("db", None)
    if d:
        d.close()

def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            deadline TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

def row(r):
    d = dict(r)
    d["overdue"] = bool(d["deadline"] and d["status"] == "Pending"
                        and d["deadline"] < date.today().isoformat())
    return d

def validate(data, partial=False):
    errors = {}
    if not partial or "title" in data:
        if not str(data.get("title") or "").strip():
            errors["title"] = "Title is required."
    if data.get("priority") not in (None, *PRIORITIES):
        errors["priority"] = "Priority must be Low, Medium or High."
    if data.get("status") not in (None, *STATUSES):
        errors["status"] = "Status must be Pending or Completed."
    dl = data.get("deadline")
    if dl:
        try:
            date.fromisoformat(dl)
        except ValueError:
            errors["deadline"] = "Deadline must be a valid date (YYYY-MM-DD)."
    return errors

def get_or_404(tid):
    r = db().execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    return r

@app.get("/")
def index():
    return send_from_directory("static", "index.html")

@app.get("/api/tasks")
def list_tasks():
    sql, args = "SELECT * FROM tasks WHERE 1=1", []
    status = request.args.get("status")
    if status in STATUSES:
        sql += " AND status=?"; args.append(status)
    q = request.args.get("search", "").strip()
    if q:
        sql += " AND (title LIKE ? OR description LIKE ?)"; args += [f"%{q}%"] * 2
    sql += " ORDER BY status='Completed', deadline IS NULL, deadline, id DESC"
    tasks = [row(r) for r in db().execute(sql, args)]
    if request.args.get("overdue") == "1":
        tasks = [t for t in tasks if t["overdue"]]
    return jsonify(tasks)

@app.get("/api/tasks/<int:tid>")
def one(tid):
    r = get_or_404(tid)
    return (jsonify(row(r)), 200) if r else (jsonify(error="Task not found"), 404)

@app.post("/api/tasks")
def create():
    d = request.get_json(silent=True) or {}
    errs = validate(d)
    if errs:
        return jsonify(errors=errs), 400
    cur = db().execute(
        "INSERT INTO tasks(title,description,deadline,priority) VALUES(?,?,?,?)",
        (d["title"].strip(), d.get("description", ""), d.get("deadline") or None,
         d.get("priority") or "Medium"))
    db().commit()
    return jsonify(row(get_or_404(cur.lastrowid))), 201

@app.put("/api/tasks/<int:tid>")
def update(tid):
    if not get_or_404(tid):
        return jsonify(error="Task not found"), 404
    d = request.get_json(silent=True) or {}
    errs = validate(d)
    if errs:
        return jsonify(errors=errs), 400
    db().execute("UPDATE tasks SET title=?,description=?,deadline=?,priority=? WHERE id=?",
                 (d["title"].strip(), d.get("description", ""), d.get("deadline") or None,
                  d.get("priority") or "Medium", tid))
    db().commit()
    return jsonify(row(get_or_404(tid)))

@app.patch("/api/tasks/<int:tid>")
def patch_status(tid):
    if not get_or_404(tid):
        return jsonify(error="Task not found"), 404
    d = request.get_json(silent=True) or {}
    errs = validate(d, partial=True)
    if errs or "status" not in d:
        return jsonify(errors=errs or {"status": "Status is required."}), 400
    db().execute("UPDATE tasks SET status=? WHERE id=?", (d["status"], tid))
    db().commit()
    return jsonify(row(get_or_404(tid)))

@app.delete("/api/tasks/<int:tid>")
def delete(tid):
    if not get_or_404(tid):
        return jsonify(error="Task not found"), 404
    db().execute("DELETE FROM tasks WHERE id=?", (tid,))
    db().commit()
    return "", 204

init_db()
if __name__ == "__main__":
    app.run(debug=True)
