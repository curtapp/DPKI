import tend.abci.ext
from tend import abci
from tend.abci.handlers import ResultCode, ResponseCheckTx


class TxChecker(abci.ext.TxChecker):
    """ TX checker
    """

    async def check_tx(self, req):
        return ResponseCheckTx(code=ResultCode.OK)
