import os.path

import tend.abci.ext
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncEngine
from tend import abci
from tend.abci.ext import AppState

from csp.provider import CSProvider
from dpki import database, database as t
from dpki.ca import CA
from .checker import TxChecker
from .keeper import TxKeeper
from .utils import load_from_key_file, load_config, normalize_config


class Application(abci.ext.Application):
    """ ABCI Chain application
    """

    database: AsyncEngine
    ca: CA | None

    def __init__(self, home_path: str, logger=None):
        super().__init__(TxChecker(self), TxKeeper(self), logger)
        self.csp = CSProvider()
        self.database = database.engine_factory()

        config = load_config(home_path)
        self.ca = None
        if 'ca' in config:
            ca_key = load_from_key_file(os.path.join(home_path, config['ca']['ca_key_file']))
            ca_config = normalize_config({**CA.DEFAULT_CONFIG,
                                            **dict((key, value) for key, value in config.items()
                                                   if key in tuple(CA.DEFAULT_CONFIG.keys()))})
            self.ca = CA(self.database, ca_key, **ca_config)

    async def get_initial_app_state(self):
        async with self.database.begin() as ac:
            select_stmt = select(t.app_state).order_by(desc(t.app_state.c.created_at)).limit(1)
            async for obj in await ac.stream(select_stmt):
                return AppState(block_height=obj.block_height, app_hash=obj.app_hash)
        return AppState()

    async def update_app_state(self, new_state: 'AppState'):
        await super().update_app_state(new_state)
        if new_state.block_height > 1 and self.ca and not self.ca.ready:
            ca_subject = await self.ca.initialize()
            if ca_subject:
                self.logger.info(f"CA initialized on this node; subject: {ca_subject}")
