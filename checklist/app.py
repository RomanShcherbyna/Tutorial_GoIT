#!/usr/bin/env python3
"""Checklist server for the lapetitebloom content fixes.

Runs the same way locally and on Railway: `python app.py` (or uvicorn) and the
whole thing is one process plus a SQLite file. Status is stored server-side on
purpose — the point of a shared link is that when one person ticks a task off,
everyone sees it.

No login. The link is the access, which suits an internal team page; whoever
ticks a box just types their name once and it travels with each update so the
history says who did what.
"""
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DOCS = os.path.join(HERE, "documents")
STATIC = os.path.join(HERE, "static")
DB_PATH = os.environ.get("CHECKLIST_DB", os.path.join(DATA, "state.db"))

STATUSES = {"todo", "doing", "done", "skip"}

app = FastAPI(title="La Petite Bloom — чек-лист правок", docs_url=None,
              redoc_url=None)


# --------------------------------------------------------------------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with closing(db()) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS task_state (
            task_id    TEXT PRIMARY KEY,
            status     TEXT NOT NULL DEFAULT 'todo',
            comment    TEXT NOT NULL DEFAULT '',
            updated_by TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT ''
        )""")
        c.commit()


def load_checklist():
    path = os.path.join(DATA, "checklist.json")
    if not os.path.exists(path):
        return {"total_pages": 0, "total_fixes": 0, "groups": [],
                "severities": [], "issues": [], "claims": []}
    return json.load(open(path, encoding="utf-8"))


def valid_ids(checklist):
    """A page and any single fix inside it can both be ticked off."""
    ids = set()
    for g in checklist.get("groups", []):
        ids.add(g["key"])
        ids.update(f["id"] for f in g.get("fixes", []))
    return ids


init_db()
CHECKLIST = load_checklist()
VALID_IDS = valid_ids(CHECKLIST)


# --------------------------------------------------------------------------
BLANK = {"status": "todo", "comment": "", "updated_by": "", "updated_at": ""}


@app.get("/api/checklist")
def api_checklist():
    """Pages, their fixes, and every current status in one round trip."""
    with closing(db()) as c:
        state = {r["task_id"]: dict(r)
                 for r in c.execute("SELECT * FROM task_state")}
    data = dict(CHECKLIST)
    data["groups"] = [
        {**g,
         "state": state.get(g["key"], dict(BLANK)),
         "fixes": [{**f, "state": state.get(f["id"], dict(BLANK))}
                   for f in g["fixes"]]}
        for g in CHECKLIST["groups"]
    ]
    data["documents"] = list_documents()
    return JSONResponse(data)


@app.post("/api/state/{task_id}")
def api_set_state(task_id: str, payload: dict = Body(...)):
    status = payload.get("status", "todo")
    if status not in STATUSES:
        raise HTTPException(400, f"unknown status: {status}")
    if task_id not in VALID_IDS:
        raise HTTPException(404, f"unknown task: {task_id}")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    with closing(db()) as c:
        c.execute("""INSERT INTO task_state
                       (task_id, status, comment, updated_by, updated_at)
                     VALUES (?,?,?,?,?)
                     ON CONFLICT(task_id) DO UPDATE SET
                       status=excluded.status,
                       comment=excluded.comment,
                       updated_by=excluded.updated_by,
                       updated_at=excluded.updated_at""",
                  (task_id, status, (payload.get("comment") or "")[:2000],
                   (payload.get("who") or "")[:80], now))
        c.commit()
    return {"ok": True, "task_id": task_id, "status": status, "updated_at": now}


@app.get("/api/progress")
def api_progress():
    """Progress is counted in pages — that is the unit the team works in."""
    keys = {g["key"] for g in CHECKLIST["groups"]}
    with closing(db()) as c:
        rows = list(c.execute("SELECT task_id, status FROM task_state"))
    page_status = {r["task_id"]: r["status"] for r in rows if r["task_id"] in keys}
    closed = sum(1 for s in page_status.values() if s in ("done", "skip"))
    return {"pages": CHECKLIST["total_pages"], "pages_done": closed,
            "fixes": CHECKLIST["total_fixes"],
            "by_status": {s: sum(1 for v in page_status.values() if v == s)
                          for s in STATUSES}}


# --------------------------------------------------------------------------
def list_documents():
    """Everything dropped into documents/, newest-looking name first."""
    if not os.path.isdir(DOCS):
        return []
    out = []
    for root, _, files in os.walk(DOCS):
        for fn in sorted(files):
            if fn.startswith("."):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, DOCS)
            out.append({
                "name": fn,
                "path": rel.replace(os.sep, "/"),
                "folder": os.path.relpath(root, DOCS).replace(os.sep, "/"),
                "size": os.path.getsize(full),
            })
    return out


@app.get("/documents/{path:path}")
def get_document(path: str):
    full = os.path.normpath(os.path.join(DOCS, path))
    if not full.startswith(os.path.abspath(DOCS)) or not os.path.isfile(full):
        raise HTTPException(404, "not found")
    return FileResponse(full, filename=os.path.basename(full))


@app.get("/health")
def health():
    return {"ok": True, "pages": CHECKLIST["total_pages"], "fixes": CHECKLIST["total_fixes"]}


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(os.path.join(STATIC, "index.html"))


if os.path.isdir(STATIC):
    app.mount("/static", StaticFiles(directory=STATIC), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
