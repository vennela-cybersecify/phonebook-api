# =============================================================================
#                        PHONEBOOK API
#          Built with FastAPI + PostgreSQL + SQLAlchemy + JWT Auth
#
# Run:  uvicorn main:app --reload
# Test: http://localhost:8000/docs
# =============================================================================

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

import auth
import models
from database import Base, SessionLocal, engine, get_db

# Create all tables in PostgreSQL
Base.metadata.create_all(bind=engine)

# -------------------------------------------------------
# 1. Create the FastAPI app
# -------------------------------------------------------
app = FastAPI(title="Phonebook API")


# -------------------------------------------------------
# 2. Seed 4 dummy phone numbers on startup
# -------------------------------------------------------
@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    try:
        if db.query(models.PhoneNumber).count() == 0:
            dummy_numbers = [
                models.PhoneNumber(phone_number="1234567890"),
                models.PhoneNumber(phone_number="0987654321"),
                models.PhoneNumber(phone_number="1122334455"),
                models.PhoneNumber(phone_number="5544332211"),
            ]
            db.add_all(dummy_numbers)
            db.commit()
    finally:
        db.close()


# -------------------------------------------------------
# 3. Schemas
# -------------------------------------------------------
class SignupRequest(BaseModel):
    username: str
    email: str
    password: str


class PhoneCreate(BaseModel):
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class PhoneUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


# -------------------------------------------------------
# 4. AUTH ENDPOINTS
# -------------------------------------------------------
@app.post("/auth/signup", status_code=201, tags=["Auth"])
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == request.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(models.User).filter(models.User.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        username=request.username,
        email=request.email,
        hashed_password=auth.hash_password(request.password),
    )
    db.add(new_user)
    db.commit()
    return {"message": f"User '{request.username}' registered successfully!"}


@app.post("/auth/login", tags=["Auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


# -------------------------------------------------------
# 5. PHONEBOOK ENDPOINTS
# -------------------------------------------------------
@app.get("/phone", tags=["Phonebook"])
def get_all_phones(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    contacts = db.query(models.PhoneNumber).all()
    return {"total": len(contacts), "contacts": contacts}


@app.get("/phone/{phone_number}", tags=["Phonebook"])
def get_phone(
    phone_number: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    contact = db.query(models.PhoneNumber).filter(models.PhoneNumber.phone_number == phone_number).first()
    if not contact:
        raise HTTPException(status_code=404, detail=f"Phone number '{phone_number}' not found")
    return contact


@app.post("/phone", status_code=201, tags=["Phonebook"])
def add_phone(
    phone: PhoneCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    existing = db.query(models.PhoneNumber).filter(models.PhoneNumber.phone_number == phone.phone_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already exists")

    new_contact = models.PhoneNumber(
        phone_number=phone.phone_number,
        name=phone.name,
        email=phone.email,
        address=phone.address,
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return {"message": "Contact added!", "contact": new_contact}


@app.put("/phone/{phone_number}", tags=["Phonebook"])
def update_phone(
    phone_number: str,
    update: PhoneUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    contact = db.query(models.PhoneNumber).filter(models.PhoneNumber.phone_number == phone_number).first()
    if not contact:
        raise HTTPException(status_code=404, detail=f"Phone number '{phone_number}' not found")

    if update.phone_number is not None and update.phone_number != phone_number:
        duplicate = db.query(models.PhoneNumber).filter(models.PhoneNumber.phone_number == update.phone_number).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Updated phone number already exists")

    if update.name is not None:
        contact.name = update.name
    if update.phone_number is not None:
        contact.phone_number = update.phone_number
    if update.email is not None:
        contact.email = update.email
    if update.address is not None:
        contact.address = update.address

    db.commit()
    db.refresh(contact)
    return {"message": "Contact updated!", "contact": contact}


@app.delete("/phone/{phone_number}", tags=["Phonebook"])
def delete_phone(
    phone_number: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    contact = db.query(models.PhoneNumber).filter(models.PhoneNumber.phone_number == phone_number).first()
    if not contact:
        raise HTTPException(status_code=404, detail=f"Phone number '{phone_number}' not found")

    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted!"}
