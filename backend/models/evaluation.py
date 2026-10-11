"""Evaluation model for lumen-workbench-ryan-vo."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from ..core.db import Base

class Evaluation(Base):
    """Represents an evaluation of a title."""
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    title_id = Column(Integer, ForeignKey("titles.id"), nullable=False)
    score = Column(Float, nullable=False)  # 0.0 to 10.0
    comments = Column(String(2048))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Evaluation(id={self.id}, title_id={self.title_id}, score={self.score})>"