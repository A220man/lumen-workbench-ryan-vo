"""Title status history model for lumen-workbench-ryan-vo."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from ..core.db import Base

class TitleStatusHistory(Base):
    """Represents a status change history for a title."""
    __tablename__ = "title_status_history"

    id = Column(Integer, primary_key=True, index=True)
    title_id = Column(Integer, ForeignKey("titles.id"), nullable=False)
    previous_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(255))
    changed_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String(1024))

    def __repr__(self):
        return f"<TitleStatusHistory(id={self.id}, title_id={self.title_id}, new_status='{self.new_status}')>"