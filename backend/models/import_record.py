"""Import record model for lumen-workbench-ryan-vo."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from ..core.db import Base, utc_now

class ImportRecord(Base):
    __tablename__ = "import_records"

    id = Column(Integer, primary_key=True, index=True)
    title_name = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")
    imported_at = Column(DateTime, default=utc_now)
    analyzed_by = Column(String(255))
    analysis_result = Column(String(2048))

    def __repr__(self):
        return f"<ImportRecord(id={self.id}, title_name='{self.title_name}', status='{self.status}')>"