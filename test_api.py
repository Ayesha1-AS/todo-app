import os, tempfile
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
from app import app
c = app.test_client()

def test_flow():
    assert c.post("/api/tasks", json={"title": "  "}).status_code == 400
    r = c.post("/api/tasks", json={"title": "Pay bills", "deadline": "2020-01-01", "priority": "High"})
    assert r.status_code == 201
    t = r.get_json(); assert t["overdue"] is True
    assert c.get("/api/tasks?overdue=1").get_json()[0]["id"] == t["id"]
    assert c.get("/api/tasks?search=bills").get_json()
    assert c.put(f"/api/tasks/{t['id']}", json={"title": "Pay rent"}).get_json()["title"] == "Pay rent"
    p = c.patch(f"/api/tasks/{t['id']}", json={"status": "Completed"}).get_json()
    assert p["status"] == "Completed" and p["overdue"] is False
    assert len(c.get("/api/tasks?status=Pending").get_json()) == 0
    assert c.delete(f"/api/tasks/{t['id']}").status_code == 204
    assert c.get(f"/api/tasks/{t['id']}").status_code == 404
