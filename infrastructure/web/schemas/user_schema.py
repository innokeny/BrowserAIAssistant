from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo
from pydantic import ConfigDict


class UserBase(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr

class UserCreate(UserBase):
    """Схема для создания пользователя (админка)"""
    pass

class UserRegistration(BaseModel):
    """Схема регистрации с валидацией пароля"""
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=8)
    password_confirm: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну букву')
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v

    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo) -> str:
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Пароли не совпадают')
        return v

class UserLogin(BaseModel):
    """Схема авторизации"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Схема ответа с данными пользователя"""
    id: int
    name: str
    email: EmailStr
    user_role: str
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    """Схема ответа с токеном"""
    access_token: str
    token_type: str = "bearer"

class QuotaResponse(BaseModel):
    """Схема квот пользователя"""
    resource_type: str
    limit: int
    current_usage: int
    reset_date: Optional[str]

class RequestHistoryResponse(BaseModel):
    """Схема истории запросов"""
    id: int
    request_type: str
    status: str
    processing_time: Optional[int]
    created_at: str

class UserPreferences(BaseModel):
    """Схема пользовательских предпочтений"""
    theme: str = "light"
    language: str = "en"