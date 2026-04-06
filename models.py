from sqlalchemy import Column, Integer, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
