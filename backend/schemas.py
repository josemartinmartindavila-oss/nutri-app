from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# --- Esquemas de Usuario ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


# --- Esquemas de Perfil Nutricional del Usuario ---
class UserProfileCreate(BaseModel):
    weight: float
    height: float
    goal: str
    target_calories: int
    target_protein: float
    target_carbs: float
    target_fat: float

class UserProfileResponse(UserProfileCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# --- Esquemas del Módulo de Comidas (Meal Logs) ---
class MealLogCreate(BaseModel):
    meal_type: str
    food_name: str
    calories: float
    protein: float
    carbs: float
    fat: float

class MealLogResponse(MealLogCreate):
    id: int
    user_id: int
    logged_at: datetime

    class Config:
        from_attributes = True
# --- Esquema para el Resumen Diario ---
class DailySummaryResponse(BaseModel):
    target_calories: int
    consumed_calories: float
    target_protein: float
    consumed_protein: float
    target_carbs: float
    consumed_carbs: float
    target_fat: float
    consumed_fat: float
    remaining_calories: float
# --- Esquemas de Autenticación / Login ---
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
# --- Esquemas para Registro de Peso ---
class WeightLogCreate(BaseModel):
    weight: float

class WeightLogResponse(BaseModel):
    id: int
    user_id: int
    weight: float
    logged_at: datetime

    class Config:
        from_attributes = True