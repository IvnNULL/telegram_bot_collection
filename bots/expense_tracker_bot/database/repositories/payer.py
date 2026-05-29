import logging

from sqlalchemy import select

from database.models import Payer
from database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class PayerRepository(BaseRepository):
    async def add_payer(self, *, payer: str) -> None:
        db_payer = await self.session.scalar(
            select(Payer).where(Payer.payer == payer)
        )

        if db_payer:
            db_payer.counter += 1
        else:
            new_payer = Payer(payer=payer)
            self.session.add(new_payer)

        await self.session.commit()

    async def list_payers(self) -> list[Payer] | None:
        data = await self.session.scalars(
            select(Payer).order_by(Payer.counter.desc())
        )
        payers = data.all()
        return payers if payers else None
