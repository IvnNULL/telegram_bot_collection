from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class Payer(Base):
    __tablename__ = 'payers'

    id: Mapped[int] = mapped_column(primary_key=True)
    payer: Mapped[str] = mapped_column(unique=True)
    counter: Mapped[int] = mapped_column(default=1)
