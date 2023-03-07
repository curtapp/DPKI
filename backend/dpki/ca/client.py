import httpx
import logging


class ClientRPC:
    """ HTTP client to calling chain RPC
    """
    def __init__(self, laddr):
        self.base_url = f'http://{laddr.split("//")[1]}'

    async def send_tx(self, tx: bytes):
        r = httpx.post('http://localhost:26657/broadcast_tx_async', data=dict(tx='0x' + tx.hex()))
        if r.is_error:
            raise RuntimeError('Cannot send TX')
