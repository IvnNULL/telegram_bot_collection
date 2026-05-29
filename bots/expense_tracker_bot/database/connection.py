from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


def create_session_maker(url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(url, echo=False)
    return async_sessionmaker(engine, expire_on_commit=False)
