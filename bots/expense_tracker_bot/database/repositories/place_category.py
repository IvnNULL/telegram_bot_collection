import logging

from sqlalchemy import select, delete

from database.models import PlaceCategory
from database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class PlaceCategoryRepository(BaseRepository):
    async def add_place_category(self, *, place: str, category: str) -> None:
        item = await self.session.scalar(
            select(PlaceCategory).where(PlaceCategory.place == place, PlaceCategory.category == category)
        )

        if item:
            item.counter += 1
        else:
            new_item = PlaceCategory(place=place, category=category)
            self.session.add(new_item)

        await self.session.commit()

    async def get_category_by_place(self, *, place: str) -> list[str]:
        db_categories = await self.session.scalars(
            select(PlaceCategory.category).where(PlaceCategory.place == place).order_by(PlaceCategory.counter.desc())
            # .limit(3)
        )
        categories = db_categories.all()
        return categories

    async def get_all_data(self) -> list[PlaceCategory]:
        db_data = await self.session.scalars(select(PlaceCategory))
        return db_data.all()

    async def update(self, list_pc: list[PlaceCategory]) -> None:
        await self.session.execute(delete(PlaceCategory))
        self.session.add_all(list_pc)
        await self.session.commit()
