"""Per-session disposable repository; never writes to the user's database."""
from copy import deepcopy
from uuid import uuid4


class DemoRepository:
    backend = 'demo'

    def __init__(self):
        self.records = {}

    def find(self, kind, **query):
        return deepcopy([d for d in self.records.get(kind, []) if all(d.get(k) == v for k,v in query.items())])

    def insert(self, kind, doc):
        value = {**deepcopy(doc), '_id':uuid4().hex}
        self.records.setdefault(kind, []).append(value)
        return deepcopy(value)

    def update(self, kind, record_id, user_id, changes):
        for doc in self.records.get(kind, []):
            if doc['_id'] == record_id and doc.get('user_id') == user_id:
                doc.update({k:deepcopy(v) for k,v in changes.items() if k not in ('_id','user_id')})
                return
        raise ValueError('Record not found.')

    def delete(self, kind, record_id, user_id):
        for doc in self.records.get(kind, []):
            if doc['_id'] == record_id and doc.get('user_id') == user_id:
                self.records[kind].remove(doc)
                return
        raise ValueError('Record not found.')
