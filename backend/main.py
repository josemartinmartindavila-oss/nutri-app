from datetime import datetime, date, timedelta
from typing import Optional
import os

import bcrypt
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine, Base, SessionLocal
from models import User, UserProfile, MealLog, WeightLog
from schemas import (
    UserCreate,
    UserResponse,
    UserProfileCreate,
    UserProfileResponse,
    MealLogCreate,
    MealLogResponse,
    DailySummaryResponse,
    LoginRequest,
    TokenResponse,
    WeightLogCreate,
    WeightLogResponse
)

# Cargar las variables de entorno desde el archivo .env
load_dotenv()


# ==========================================
# 1. CONFIGURACIÓN GENERAL
# ==========================================

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Nutri-App Backend Mobile",
    version="1.0"
)


# ==========================================
# 2. CONFIGURACIÓN DE SEGURIDAD JWT (DESDE .ENV)
# ==========================================

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_in_case_env_missing")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return encoded_jwt


# ==========================================
# 3. CONEXIÓN A BASE DE DATOS
# ==========================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================
# 4. FUNCIONES DE SEGURIDAD Y DEPENDENCIAS
# ==========================================

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(
        pwd_bytes,
        bcrypt.gensalt()
    )
    return hashed.decode("utf-8")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# ==========================================
# 5. RUTA PRINCIPAL
# ==========================================

@app.get("/")
def read_root():
    return {
        "message": "Nutri-App Backend con Python y FastAPI funcionando para Celular"
    }


# ==========================================
# 6. MÓDULO DE REGISTRO DE USUARIOS
# ==========================================

@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
        user: UserCreate,
        db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(
        User.username == user.username
    ).first()

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )

    db_email = db.query(User).filter(
        User.email == user.email
    ).first()

    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está en uso"
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ==========================================
# 7. MÓDULO DE AUTENTICACIÓN (LOGIN)
# ==========================================

@app.post("/login", response_model=TokenResponse)
def login_user(
        form_data: LoginRequest,
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if not user or not bcrypt.checkpw(
            form_data.password.encode("utf-8")[:72],
            user.hashed_password.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id
    }


# ==========================================
# 8. MÓDULO DE PERFIL Y METAS NUTRICIONALES (PROTEGIDO)
# ==========================================

@app.post(
    "/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED
)
def create_or_update_profile(
        profile: UserProfileCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if db_profile:
        for key, value in profile.dict().items():
            setattr(db_profile, key, value)

        db.commit()
        db.refresh(db_profile)
        return db_profile

    new_profile = UserProfile(
        user_id=current_user.id,
        **profile.dict()
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return new_profile


# ==========================================
# 9. MÓDULO DE REGISTRO DE COMIDAS (PROTEGIDO)
# ==========================================

@app.post(
    "/meals",
    response_model=MealLogResponse,
    status_code=status.HTTP_201_CREATED
)
def create_meal_log(
        meal: MealLogCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    new_meal = MealLog(
        user_id=current_user.id,
        **meal.dict()
    )

    db.add(new_meal)
    db.commit()
    db.refresh(new_meal)

    return new_meal


@app.get(
    "/meals",
    response_model=list[MealLogResponse]
)
def get_meal_logs(
        query_date: Optional[str] = Query(None, alias="date"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    query = db.query(MealLog).filter(MealLog.user_id == current_user.id)

    if query_date:
        query = query.filter(func.date(MealLog.logged_at) == query_date)

    meals = query.all()
    return meals


@app.delete(
    "/meals/{meal_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_meal_log(
        meal_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    meal = db.query(MealLog).filter(
        MealLog.id == meal_id,
        MealLog.user_id == current_user.id
    ).first()

    if not meal:
        raise HTTPException(
            status_code=404,
            detail="Registro de comida no encontrado"
        )

    db.delete(meal)
    db.commit()
    return None


# ==========================================
# 10. MÓDULO DE RESUMEN NUTRICIONAL DIARIO (PROTEGIDO)
# ==========================================

@app.get(
    "/summary",
    response_model=DailySummaryResponse
)
def get_daily_summary(
        query_date: Optional[str] = Query(None, alias="date"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Perfil nutricional no configurado para este usuario"
        )

    target_date = query_date if query_date else str(date.today())

    meals = db.query(MealLog).filter(
        MealLog.user_id == current_user.id,
        func.date(MealLog.logged_at) == target_date
    ).all()

    consumed_calories = sum(meal.calories for meal in meals)
    consumed_protein = sum(meal.protein for meal in meals)
    consumed_carbs = sum(meal.carbs for meal in meals)
    consumed_fat = sum(meal.fat for meal in meals)

    remaining_calories = profile.target_calories - consumed_calories

    return {
        "target_calories": profile.target_calories,
        "consumed_calories": consumed_calories,
        "target_protein": profile.target_protein,
        "consumed_protein": consumed_protein,
        "target_carbs": profile.target_carbs,
        "consumed_carbs": consumed_carbs,
        "target_fat": profile.target_fat,
        "consumed_fat": consumed_fat,
        "remaining_calories": remaining_calories
    }


# ==========================================
# 11. MÓDULO DE EVOLUCIÓN DE PESO (PROTEGIDO)
# ==========================================

@app.post(
    "/weight-logs",
    response_model=WeightLogResponse,
    status_code=status.HTTP_201_CREATED
)
def create_weight_log(
        weight_data: WeightLogCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    new_weight = WeightLog(
        user_id=current_user.id,
        weight=weight_data.weight
    )
    db.add(new_weight)
    db.commit()
    db.refresh(new_weight)
    return new_weight


@app.get(
    "/weight-logs",
    response_model=list[WeightLogResponse]
)
def get_weight_logs(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    logs = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id
    ).order_by(WeightLog.logged_at.desc()).all()

    return logs


@app.delete(
    "/weight-logs/{weight_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_weight_log(
        weight_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    weight_log = db.query(WeightLog).filter(
        WeightLog.id == weight_id,
        WeightLog.user_id == current_user.id
    ).first()

    if not weight_log:
        raise HTTPException(
            status_code=404,
            detail="Registro de peso no encontrado"
        )

    db.delete(weight_log)
    db.commit()
    return None