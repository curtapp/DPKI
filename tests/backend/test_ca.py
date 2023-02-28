import pytest
from cryptography import x509

from dpki.x509cert.utils import create_csr, apply_csr, template as t
from csp import ed25519
from csp.provider import CSProvider


@pytest.fixture
def pem_ca_cert():
    yield \
        b'''-----BEGIN CERTIFICATE-----
        MIIBOjCB7aADAgECAhRuoZmAahCHXL7zlipiL9TIGCJraDAFBgMrZXAwKjELMAkG
        A1UEBhMCV04xGzAZBgNVBAMMEldvbmRlcmxhbmQgcm9vdCBDQTAgFw0yMzAyMjIw
        MDAwMDBaGA8yMDcwMDEwMTIzNTk1OVowKjELMAkGA1UEBhMCV04xGzAZBgNVBAMM
        EldvbmRlcmxhbmQgcm9vdCBDQTAqMAUGAytlcAMhABgV+zZLVpuQ0M9Z5nCpG9Nj
        qaM2D8YXRCskECfZ1gynoyMwITAPBgNVHRMBAf8EBTADAQH/MA4GA1UdDwEB/wQE
        AwIBhjAFBgMrZXADQQDWDpMKNrYzZO/2NdpW1//vRfjAO8FZCPwEIxjW7r1CWlEI
        DQNoSWOaaTPQ+Druk9d9fkQ8Zwyv3j+XAXchDLsM
        -----END CERTIFICATE-----'''


def test_ca_cert_deserialize(pem_ca_cert):
    cert = x509.load_pem_x509_certificate(pem_ca_cert)
    assert t.CA.matches(cert)


def test_create_ca_cert():
    csp = CSProvider()
    key = csp.key_gen(ed25519.KeyOpts())
    subject = "CN=First Wonderland CA, OU=Data center, C=WN, O=The Corporation"
    csr = create_csr(subject, key, template=t.CA, path_length=7)
    cert = apply_csr(csr, (csr, key), not_valid_after='2024-01-01')
    assert t.CA.matches(cert)


def test_create_node_cert():
    csp = CSProvider()
    ca_key = csp.key_gen(ed25519.KeyOpts())
    subject = "CN=First Wonderland CA, OU=Data center, C=WN, O=The Corporation"
    csr = create_csr(subject, ca_key, template=t.CA, path_length=7)
    ca_cert = apply_csr(csr, (csr, ca_key), not_valid_after='2025-01-01')
    assert t.CA.matches(ca_cert)
    key = csp.key_gen(ed25519.KeyOpts())
    subject = "CN=First Wonderland CA+DC=ca01, OU=Data center, C=WN+DC=wonderland, O=The Corporation+DC=thecorp"
    csr = create_csr(subject, key, template=t.Host, san=['cahost'])
    cert = apply_csr(csr, (ca_cert, ca_key), not_valid_after='2024-01-01')
    assert t.Host.matches(cert)
    assert not t.CA.matches(cert)
