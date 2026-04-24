from datetime import date, datetime

from sqlalchemy import func, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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


class Payer(Base):
    __tablename__ = 'payers'

    id: Mapped[int] = mapped_column(primary_key=True)
    payer: Mapped[str] = mapped_column(unique=True)
    counter: Mapped[int] = mapped_column(default=1)


class PlaceCategory(Base):
    __tablename__ = 'place_categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    place: Mapped[str]
    category: Mapped[str]
    counter: Mapped[int] = mapped_column(default=1)

    __table_args__ = (
        UniqueConstraint('place', 'category', name="uq_place_category"),
    )