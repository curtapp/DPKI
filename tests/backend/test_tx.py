import logging
import re
import pytest

from dpki.chainapp import TxChecker, TxKeeper


@pytest.fixture
def app_without_ca():

    class CA:
        cert = None

        def in_namespace(self, csr):
            return True

    class MockApp:
        """"""
        ca = CA()

    return MockApp()


@pytest.fixture
def req_with_csr():
    class Req:
        tx = re.sub(r'\n\s*', '\n',
                    '''-----BEGIN CERTIFICATE REQUEST-----
                    MIIBDjCBwQIBADAyMQswCQYDVQQGEwJXTjEjMAwGA1UEAwwFQWxlc2gwEwYKCZIm
                    iZPyLGQBAQwFYWxlc2gwKjAFBgMrZXADIQACWDPA9ZWqmpS3eFuykWZtfFGZ+Tyu
                    tDobRUfUs40d2KBcMFoGCSqGSIb3DQEJDjFNMEswDAYDVR0TAQH/BAIwADAOBgNV
                    HQ8BAf8EBAMCBPAwFgYDVR0lAQH/BAwwCgYIKwYBBQUHAwIwEwYDVR0RAQH/BAkw
                    B4EFYWxlc2gwBQYDK2VwA0EA5pOG7NAElobwG1It+utPlFMvIBQOZtsSALSQdLYn
                    EP06pk5KOsEw3YTaya5OGIsRyGX0XNoI1P7w1ma9RfTPBw==
                    -----END CERTIFICATE REQUEST-----
                    ''').encode('utf8')

    yield Req()


@pytest.mark.asyncio
async def test_check_tx(app_without_ca, req_with_csr):
    tx_checker = TxChecker(app_without_ca)
    resp = await tx_checker.check_tx(req_with_csr)
    assert resp.code == 0


@pytest.fixture
def app_with_ca():

    class CA:
        cert = True
        async def issue_iiiy(self, *args): return None
        def in_namespace(self, *args): return True

    class MockApp:
        """"""
        ca = CA()
        logger = logging.root


    return MockApp()


@pytest.mark.asyncio
async def test_check_tx_on_ca(app_with_ca, req_with_csr):
    tx_checker = TxChecker(app_with_ca)
    resp = await tx_checker.check_tx(req_with_csr)
    assert resp.code == 0


@pytest.mark.asyncio
async def test_deliver_tx(app_with_ca, req_with_csr):
    tx_keeper = TxKeeper(app_with_ca)
    resp = await tx_keeper.deliver_tx(req_with_csr)
    assert resp.code == 0