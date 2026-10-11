"""Title model for lumen-workbench-ryan-vo."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from ..core.db import Base, utc_now

class Title(Base):
    """Represents a PS5 title in the lumen-workbench."""
    __tablename__ = "titles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1024))
    status = Column(String(50), default="draft")  # draft, active, archived
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Title(id={self.id}, name='{self.name}')>"