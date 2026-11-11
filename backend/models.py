from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    meals = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
    weight_logs = relationship("WeightLog", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Métricas y objetivos móviles
    weight = Column(Float, nullable=False)  # ej. 82.40 kg
    height = Column(Float, nullable=False)  # ej. 175 cm
    goal = Column(String, default="recomposition")  # recomposición, pérdida de grasa, ganar músculo
    target_calories = Column(Integer, nullable=False)
    target_protein = Column(Float, nullable=False)
    target_carbs = Column(Float, nullable=False)
    target_fat = Column(Float, nullable=False)

    user = relationship("User", back_populates="profile")


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    meal_type = Column(String, nullable=False)  # Desayuno, Comida, Cena, Colación
    food_name = Column(String, nullable=False)  # ej. Pollo, Huevo, etc.
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="meals")


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    weight = Column(Float, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="weight_logs")