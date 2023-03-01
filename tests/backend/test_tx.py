import re
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
    yield re.sub(r'\n\s*', '\n',
                 '''-----BEGIN CERTIFICATE REQUEST-----
                 MIH5MIGsAgEAMDIxCzAJBgNVBAYTAldOMSMwDAYDVQQDDAVBbGVzaDATBgoJkiaJ
                 k/IsZAEBDAVhbGVzaDAqMAUGAytlcAMhAOiHZR7V+fFgzApaZM9Qt0zjzM91+IZy
                 30VhYY5iexOKoEcwRQYJKoZIhvcNAQkOMTgwNjAMBgNVHRMBAf8EAjAAMA4GA1Ud
                 DwEB/wQEAwIE8DAWBgNVHSUBAf8EDDAKBggrBgEFBQcDAjAFBgMrZXADQQC4PA0C
                 l3UQmBhUEay/WrpJRCa9hxcGaaZG5CcVbw+E9Eb0HVgOhh1UlQxGjg4LAydqWvuS
                 d9JXAIDcMAnQuvsL
                 -----END CERTIFICATE REQUEST-----''').encode('utf8')

@pytest.mark.asyncio
async def test_csr_tx(app, csr_tx):
    code, log = await TxChecker.run(app, csr_tx)
    assert code == 0