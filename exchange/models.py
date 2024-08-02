#--------------------------------models is reffering to the way the database interracts with the responses/requests------------------------------------
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, DateTime
from .database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key = True, index = True, unique = True) #UUID
    name = Column(String, nullable = False)
    last_name = Column(String, nullable = False)
    email = Column(String, unique = True, nullable=False) #candidate key
    password = Column(String, nullable = False)
    cash = Column(Float, nullable = False)
    is_admin = Column(Boolean, nullable = False)
    
    history = relationship("History", back_populates = "creator", cascade="all, delete-orphan")
    portfolio = relationship("Portfolio", back_populates = "creator", cascade="all, delete-orphan")


class History(Base):
    __tablename__ = 'history'
    order_id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    price = Column(Float)
    amount = Column(Integer)
    type = Column(String)
    value = Column(Float)
    profit = Column(Float)
    time_stamp = Column(DateTime)
    user_id = Column(String, ForeignKey('users.id'))

    creator = relationship("User", back_populates="history")
    
class Portfolio(Base):
    __tablename__ = 'portfolio'
    stock_id = Column(Integer, primary_key=True, index=True, unique=True)
    user_id = Column(String, ForeignKey('users.id'))
    symbol = Column(String)
    amount = Column(Integer)
    price = Column(Float)
    time_stamp = Column(DateTime)
    
    creator = relationship("User", back_populates="portfolio")