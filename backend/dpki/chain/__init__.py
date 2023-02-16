import tend.abci.ext
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncEngine
from tend import abci
from tend.abci.ext import AppState

from csp.provider import CSProvider
from dpki import database, database as t
from .checker import TxChecker
from .keeper import TxKeeper


class Application(abci.ext.Application):
    """ ABCI Chain application
    """
    database: AsyncEngine

    def __init__(self, logger=None):
        self.csp = CSProvider()
        self.database = database.engine_factory()
        super().__init__(TxChecker(self), TxKeeper(self), logger)

    async def get_initial_app_state(self):
        async with self.database.begin() as ac:
            select_stmt = select(t.app_state).order_by(desc(t.app_state.c.created_at)).limit(1)
            async for obj in await ac.stream(select_stmt):
                return AppState(block_height=obj.block_height, app_hash=obj.app_hash)
        return AppState()
