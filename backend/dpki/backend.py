import logging
import asyncio
import dpki.chain


def start_chain_app():
    from tend.abci import Server
    logging.basicConfig(level=logging.INFO)
    asyncio.run(Server(dpki.chain.Application()).start())


if __name__ == '__main__':
    start_chain_app()
