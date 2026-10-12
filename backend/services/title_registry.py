"""Title catalog service: CRUD, status history, diff, import."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import Title, TitleStatusHistory
from ..schemas.title import TitleCreate, TitleUpdate


@dataclass
class TitleListItem:
    id: int
    ppsa_id: str
    name: str
    version: str
    status: str
    updated_at: str


class TitleService:
    def __init__(self, db: Session):
        self.db = db

    def list(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[Title]:
        stmt = select(Title).order_by(desc(Title.updated_at)).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Title.status == status)
        return list(self.db.execute(stmt).scalars().all())

    def get(self, title_id: int) -> Optional[Title]:
        return self.db.get(Title, title_id)

    def get_by_ppsa(self, ppsa_id: str) -> Optional[Title]:
        return self.db.execute(select(Title).where(Title.ppsa_id == ppsa_id)).scalar_one_or_none()

    def create(self, data: TitleCreate) -> Title:
        t = Title(ppsa_id=data.ppsa_id, name=data.name, version=data.version, status=data.status.value if hasattr(data.status, 'value') else str(data.status))
        self.db.add(t)
        return t

    def update(self, title_id: int, data: TitleUpdate) -> Optional[Title]:
        t = self.get(title_id)
        if not t:
            return None
        if data.name is not None:
            t.name = data.name
        if data.version is not None:
            t.version = data.version
        if data.status is not None:
            t.status = data.status
        self.db.flush()
        return t

    def record_status(
        self,
        title_id: int,
        build_commit: str,
        status: str,
        stops: List[str],
        notes: str,
    ) -> TitleStatusHistory:
        t = self.get(title_id)
        if not t:
            raise ValueError("title not found")
        hist = TitleStatusHistory(
            title_id=title_id,
            build_commit=build_commit,
            status=status,
            stops=json.dumps(stops),
            notes=notes,
        )
        self.db.add(hist)
        t.status = status
        self.db.flush()
        return hist

    def history(self, title_id: int, limit: int = 20) -> List[TitleStatusHistory]:
        return list(
            self.db.execute(
                select(TitleStatusHistory)
                .where(TitleStatusHistory.title_id == title_id)
                .order_by(desc(TitleStatusHistory.created_at))
                .limit(limit)
            ).scalars().all()
        )

    def diff(self, title_id: int, base_commit: str, head_commit: str) -> dict:
        """Diff two recorded status snapshots."""
        base = self.db.execute(
            select(TitleStatusHistory)
            .where(TitleStatusHistory.title_id == title_id, TitleStatusHistory.build_commit == base_commit)
        ).scalar_one_or_none()
        head = self.db.execute(
            select(TitleStatusHistory)
            .where(TitleStatusHistory.title_id == title_id, TitleStatusHistory.build_commit == head_commit)
        ).scalar_one_or_none()
        if not base or not head:
            return {"error": "one or both commits not recorded"}
        base_stops = set(json.loads(base.stops))
        head_stops = set(json.loads(head.stops))
        return {
            "fixed": sorted(base_stops - head_stops),
            "new": sorted(head_stops - base_stops),
            "persistent": sorted(base_stops & head_stops),
            "base_status": base.status,
            "head_status": head.status,
        }

    def import_catalog(self, items: List[dict]) -> int:
        """Import a list of {ppsa_id, name, version} dicts; skip existing."""
        count = 0
        for it in items:
            if not it.get("ppsa_id"):
                continue
            if self.get_by_ppsa(it["ppsa_id"]):
                continue
            self.create(TitleCreate(ppsa_id=it["ppsa_id"], name=it["name"], version=it.get("version")))
            count += 1
        return count