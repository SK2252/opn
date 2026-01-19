from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.models.base import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    vector_id = Column(String(64), unique=True, nullable=False)
    capabilities = Column(JSON, nullable=True, default=[])
    
    # Orchestration fields (for auto-execution)
    endpoint = Column(String(512), nullable=True)  # Agent's API endpoint
    payload_mapping = Column(JSON, nullable=True)  # Maps routing params to API payload
    timeout = Column(Integer, nullable=True, default=300)  # API call timeout in seconds
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
