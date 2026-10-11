"""Pending authentication model for lumen-workbench-ryan-vo."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from ..core.db import Base

class PendingAuth(Base):
    """Represents a pending OIDC authentication state."""
    __tablename__ = "pending_auths"

    id = Column(Integer, primary_key=True, index=True)
    user_code = Column(String(100), unique=True, nullable=False)
    state = Column(String(255), nullable=False)
    nonce = Column(String(255), nullable=False)
    redirect_uri = Column(String(512), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PendingAuth(id={self.id}, user_code='{self.user_code}')>"