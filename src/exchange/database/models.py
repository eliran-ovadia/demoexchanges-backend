from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .db_conn import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class User(Base, TimestampMixin):
    __tablename__ = 'users'
    id = Column(String, primary_key=True, index=True, unique=True)  # UUID
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)  # candidate key
    password = Column(String, nullable=False)
    cash = Column(Numeric(12, 2), nullable=False, default=0.00)
    is_admin = Column(Boolean, nullable=False, default=False)

    history = relationship("History", back_populates="creator", cascade="all, delete-orphan")
    portfolio = relationship("Portfolio", back_populates="creator", cascade="all, delete-orphan")
    watchlist_items = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")


class History(Base, TimestampMixin):
    __tablename__ = 'history'
    order_id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    price = Column(Numeric(12, 4), nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    value = Column(Numeric(12, 4), nullable=False)
    profit = Column(Numeric(12, 4))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)

    creator = relationship("User", back_populates="history")


class Portfolio(Base, TimestampMixin):
    __tablename__ = 'portfolio'
    stock_id = Column(Integer, primary_key=True, index=True, unique=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    symbol = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    price = Column(Numeric(12, 4), nullable=False)

    creator = relationship("User", back_populates="portfolio")


class WatchlistItem(Base, TimestampMixin):
    __tablename__ = 'watchlist_items'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    symbol = Column(String, nullable=False)

    user = relationship("User", back_populates="watchlist_items")
    __table_args__ = (UniqueConstraint('user_id', 'symbol', name='_user_symbol_uc'),)


class UsStocks(Base, TimestampMixin):
    __tablename__ = 'us_stocks'
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, unique=True)
    name = Column(String)
    currency = Column(String)
    exchange = Column(String)
    mic_code = Column(String)
    country = Column(String)
    type = Column(String)
    figi_code = Column(String)


class LastSplitDate(Base, TimestampMixin):
    __tablename__ = 'last_split_date'
    id = Column(Integer, primary_key=True, index=True)
    last_split_check = Column(DateTime(timezone=True))
