"""Import record model for lumen-workbench-ryan-vo."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from ..core.db import Base

class ImportRecord(Base):
    """Represents a PS5 executable import record."""
    __tablename__ = "import_records"

    id = Column(Integer, primary_key=True, index=True)
    title_name = Column(String(255), nullable=False)
    version = Column(String(50))
    file_path = Column(String(512))
    status = Column(String(50), default="pending")  # pending, analyzing, complete, failed
    imported_at = Column(DateTime, default=datetime.utcnow)
    analyzed_by = Column(String(255))
    analysis_result = Column(String(2048))

    def __repr__(self):
        return f"<ImportRecord(id={self.id}, title_name='{self.title_name}', status='{self.status}')>"