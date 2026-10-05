"""Small repository with equivalent MongoDB and persistent local SQLite backends."""
import json
import os
import sqlite3
from pathlib import Path
from uuid import uuid4

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


class Store:
    def __init__(self, backend="sqlite", path="data/finance.db", mongo_db=None):
        self.backend = backend
        if backend == "mongodb":
            if mongo_db is None:
                self.client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=5000)
                self.client.admin.command("ping")
                mongo_db = self.client[os.getenv("MONGO_DB", "personal_finance")]
            self.db = mongo_db
            self.db.users.create_index("email", unique=True)
            self.db.budgets.create_index([("user_id", 1), ("period", 1), ("category", 1)], unique=True)
            for collection in ("transactions", "goals", "scenarios", "saving_plans"):
                self.db[collection].create_index("user_id")
        elif backend == "sqlite":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.path = str(path)
            with self.connect() as con:
                con.execute("CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, owner TEXT NOT NULL, unique_key TEXT UNIQUE, body TEXT NOT NULL)")
                con.execute("CREATE INDEX IF NOT EXISTS owner_idx ON records(kind, owner)")
        else:
            raise ValueError("STORAGE_BACKEND must be sqlite or mongodb.")

    def connect(self):
        return sqlite3.connect(self.path, timeout=15)

    def find(self, kind, **query):
        if self.backend == "mongodb":
            return list(self.db[kind].find(query))
        with self.connect() as con:
            if "user_id" in query:
                rows = con.execute("SELECT body FROM records WHERE kind=? AND owner=?", (kind, query["user_id"]))
            else:
                rows = con.execute("SELECT body FROM records WHERE kind=?", (kind,))
            docs = [json.loads(r[0]) for r in rows]
        return [d for d in docs if all(d.get(k) == v for k, v in query.items())]

    def insert(self, kind, doc):
        doc = {**doc, "_id": uuid4().hex}
        try:
            if self.backend == "mongodb":
                self.db[kind].insert_one(doc.copy())
            else:
                key = None
                if kind == "users":
                    key = "email:" + doc["email"]
                if kind == "budgets":
                    key = f"budget:{doc['user_id']}:{doc['period']}:{doc['category']}"
                with self.connect() as con:
                    con.execute("INSERT INTO records VALUES (?,?,?,?,?)", (doc["_id"], kind, doc.get("user_id", ""), key, json.dumps(doc)))
        except (sqlite3.IntegrityError, DuplicateKeyError) as exc:
            raise ValueError("This account or budget already exists.") from exc
        return doc

    def update(self, kind, record_id, user_id, changes):
        changes = {k: v for k, v in changes.items() if k not in ("_id", "user_id")}
        if self.backend == "mongodb":
            found = self.db[kind].update_one({"_id": record_id, "user_id": user_id}, {"$set": changes}).matched_count
        else:
            with self.connect() as con:
                con.execute("BEGIN IMMEDIATE")
                row = con.execute("SELECT body FROM records WHERE id=? AND kind=? AND owner=?", (record_id, kind, user_id)).fetchone()
                found = bool(row)
                if row:
                    doc = {**json.loads(row[0]), **changes}
                    con.execute("UPDATE records SET body=? WHERE id=?", (json.dumps(doc), record_id))
        if not found:
            raise ValueError("Record not found.")

    def delete(self, kind, record_id, user_id):
        if self.backend == "mongodb":
            found = self.db[kind].delete_one({"_id": record_id, "user_id": user_id}).deleted_count
        else:
            with self.connect() as con:
                found = con.execute("DELETE FROM records WHERE id=? AND kind=? AND owner=?", (record_id, kind, user_id)).rowcount
        if not found:
            raise ValueError("Record not found.")
