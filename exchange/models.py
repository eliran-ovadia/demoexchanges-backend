#--------------------------------models is reffering to the way the database interracts with the responses/requests------------------------------------
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from .database import Base
from sqlalchemy.orm import relationship



class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key = True, index = True, unique = True) #UUID
    name = Column(String, nullable = False)
    email = Column(String, unique = True, nullable=False) #candidate key
    password = Column(String, nullable = False)
    
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
    user_id = Column(String, ForeignKey('users.id'))
    
    creator = relationship("User", back_populates = "portfolio")