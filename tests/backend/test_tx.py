import pytest

from dpki.chainapp import TxChecker


@pytest.fixture
def app():
    yield None


@pytest.fixture
def unrecognized_tx():
    yield b'mkemckermcvklwefjckmkwpcmwecierjmnoiitvoimc2iop2emr'


@pytest.mark.asyncio
async def test_tx(app, unrecognized_tx):
    code, log = await TxChecker.run(app, unrecognized_tx)
    assert code > 0 and log is not None


@pytest.fixture
def csr_tx():
    yield \
b'''-----BEGIN CERTIFICATE REQUEST-----
MIIBFDCBxwIBADBNMQswCQYDVQQGEwJXTjERMA8GA1UEBwwIQ2hlc2hpcmUxFDAS
BgNVBAkMC0NhdCdzIGhvdXNlMRUwEwYDVQQDDAxDaGVzaGlyZSBDYXQwKjAFBgMr
ZXADIQAah1jNLzZvtKLJn9bd7ImZWW0nzM9qBBLmx10p1o+0HqBHMEUGCSqGSIb3
DQEJDjE4MDYwDAYDVR0TAQH/BAIwADAOBgNVHQ8BAf8EBAMCBPAwFgYDVR0lAQH/
BAwwCgYIKwYBBQUHAwIwBQYDK2VwA0EAZvY0JLT4rWn8pIWwuF1DR+brBtWEwZIT
VCTlb+gR/Hm0jnzd5J2qlQ6RmHXvHB3vYiBpLhyZCzcNYyYU7E6aDA==
-----END CERTIFICATE REQUEST-----'''


@pytest.mark.asyncio
async def test_csr_tx(app, csr_tx):
    code, log = await TxChecker.run(app, csr_tx)
    assert code == 0