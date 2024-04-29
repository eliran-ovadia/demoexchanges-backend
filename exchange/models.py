#--------------------------------models is reffering to the way the database interracts with the responses/requests------------------------------------
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from .database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key = True, index = True, unique = True)
    name = Column(String)
    email = Column(String, unique = True)
    password = Column(String)
    
    portfolio = relationship("Portfolio", back_populates = "creator")

class Portfolio(Base):
    __tablename__ = 'portfolio'
    id = Column(Integer, primary_key = True, index = True)
    symbol = Column(String)
    amount = Column(Integer)
    costPrice = Column(Float)
    lastPrice = Column(Float)
    totalValue = Column(Float)
    profit = Column(Float)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    creator = relationship("User", back_populates = "portfolio") 