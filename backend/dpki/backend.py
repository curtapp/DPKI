import sys
import logging
import asyncio
import dpki.chainapp


def start_chain_app():
    from tend.abci import Server
    logging.basicConfig(level=logging.INFO)
    asyncio.run(Server(dpki.chainapp.Application(sys.argv[1])).start())


if __name__ == '__main__':
    start_chain_app()


