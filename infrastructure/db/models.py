from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .db_connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # Store hashed password
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quotas = relationship("Quota", back_populates="user")
    request_history = relationship("RequestHistory", back_populates="user")

class Quota(Base):
    __tablename__ = "quotas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource_type = Column(String(50), nullable=False)  # e.g., "stt", "tts", "llm"
    limit = Column(Integer, nullable=False)  # Maximum allowed usage
    current_usage = Column(Integer, default=0)
    reset_date = Column(DateTime, nullable=False)  # When the quota resets
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="quotas")

class RequestHistory(Base):
    __tablename__ = "request_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_type = Column(String(50), nullable=False)  # e.g., "stt", "tts", "llm"
    request_data = Column(Text, nullable=True)  # Input data (truncated if needed)
    response_data = Column(Text, nullable=True)  # Response data (truncated if needed)
    status = Column(String(20), nullable=False)  # e.g., "success", "error"
    error_message = Column(Text, nullable=True)
    processing_time = Column(Integer, nullable=True)  # in milliseconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="request_history") 