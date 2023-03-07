import tend.abci.ext
from sqlalchemy.ext.asyncio import AsyncEngine
from tend import abci

from csp.provider import CSProvider
from dpki import database
from dpki.database.repository import AppState
from dpki.ca import CA

from .checker import TxChecker
from .keeper import TxKeeper


class Application(abci.ext.Application):
    """ ABCI Chain application
    """

    ca: CA
    database: AsyncEngine

    def __init__(self, home_path: str, logger=None):
        super().__init__(TxChecker(self), TxKeeper(self), logger)
        self.csp = CSProvider()
        self.database = database.engine_factory()
        self.ca = CA(self.database, home_path, logger)

    async def get_initial_app_state(self):
        async with self.database.begin() as ac:
            return await AppState.get_initial(ac)

    async def update_app_state(self, new_state: 'AppState'):
        await super().update_app_state(new_state)
        if new_state.block_height > 1:
            ca_subject = await self.ca.initialize()
            if ca_subject:
                self.logger.info(f"CA initialized on this node; subject: {ca_subject}")
