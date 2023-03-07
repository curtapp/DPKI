import sys
import logging
import asyncio
import dpki.chainapp


def start_chain_app():
    from tend.abci import Server
    logging.basicConfig(level=logging.INFO)
    logger = logging.Logger('chainapp', level=logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    asyncio.run(Server(dpki.chainapp.Application(sys.argv[1], logger)).start())


if __name__ == '__main__':
    start_chain_app()


