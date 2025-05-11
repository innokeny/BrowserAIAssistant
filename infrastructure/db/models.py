from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .db_connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    user_role = Column(String(20), nullable=False, default="user")
    
    request_history = relationship("RequestHistory", back_populates="user")
    qwen_history = relationship("QwenHistory", back_populates="user")

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
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="request_history") 

class UserCredits(Base):
    __tablename__ = 'user_credits'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    balance = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

class CreditTransaction(Base):
    __tablename__ = 'credit_transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = Column(Integer, nullable=False)  # Positive for credits added, negative for spent
    transaction_type = Column(String(50), nullable=False)  # 'initial', 'scenario_usage', 'manual'
    scenario_type = Column(String(50), nullable=True)  # For scenario usage tracking
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc)) 

class QwenHistory(Base):
    __tablename__ = "qwen_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="qwen_history")