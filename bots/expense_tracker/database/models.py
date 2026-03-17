from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func
from datetime import date, datetime


class Base(DeclarativeBase):
    pass


class Expense(Base):
    __tablename__ = 'expenses'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    date: Mapped[date]
    category: Mapped[str]
    place: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    amount: Mapped[int]
    payer: Mapped[str]
    create_at: Mapped[datetime] = mapped_column(server_default=func.datetime('now'))
