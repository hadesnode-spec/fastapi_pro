import sqlalchemy
from sqlalchemy.orm import  declarative_base, relationship
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func,
)
Base=declarative_base()

class User(Base):
    __tablename__="users"
    id=sqlalchemy.Column(sqlalchemy.Integer,primary_key=True)
    name=sqlalchemy.Column(sqlalchemy.String,nullable=False)
    email=sqlalchemy.Column(sqlalchemy.String,nullable=False,unique=True)
    password_hash=sqlalchemy.Column(sqlalchemy.String,nullable=False)
    is_active = sqlalchemy.Column(Boolean, nullable=False, default=True)  
    created_at = sqlalchemy.Column(DateTime(timezone=True), server_default=sqlalchemy.func.now(), nullable=False)  
    products = relationship("Product", back_populates="owner")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan") 

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="products")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    token_hash = sqlalchemy.Column(sqlalchemy.String(64), nullable=False, unique=True, index=True)

    expires_at = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True), nullable=False)
    revoked_at = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True), nullable=True)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.func.now(), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

