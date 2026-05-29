from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class PlaceCategory(Base):
    __tablename__ = 'place_categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    place: Mapped[str]
    category: Mapped[str]
    counter: Mapped[int] = mapped_column(default=1)

    __table_args__ = (
        UniqueConstraint('place', 'category', name="uq_place_category"),
    )
