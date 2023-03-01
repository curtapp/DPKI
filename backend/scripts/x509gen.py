import sys
import os.path
import argparse
from getpass import getpass

import httpx
from csp import ed25519
from csp.provider import CSProvider
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

import dpki.x509cert.template
from dpki import x509cert


def get_password(has_key):
    password = getpass(prompt='Password: ')
    if len(password) < 6:
        raise RuntimeError('Password must contain at least 6 characters')
    if not has_key:
        confirm = getpass(prompt='Confirm: ')
        if password != confirm:
            raise RuntimeError('Password is not confirmed')
    return password.encode('utf8')


def csr():
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0], ), description='CSE generator')
    parser.add_argument('subject', help='Certificate subject (distinguished) name')
    parser.add_argument('-o', '--output', help='Output files path')
    parser.add_argument('-k', '--key', help='PEM file with private key; will be generated if not given')
    parser.add_argument('-p', '--password', action='store_true', help='Key file encryption password')
    parser.add_argument('-t', '--template', help='Predefined template', choices=['CA', 'host', 'user'], default='user')
    args = parser.parse_args()

    output = args.output
    if args.key:
        if not os.path.exists(args.key):
            raise FileNotFoundError(f'File `{os.path.abspath(args.key)}` not found')
        if args.output is None:
            output = os.path.dirname(args.key)
    else:
        if args.output is None:
            output = os.path.curdir

    if not os.path.exists(output):
        raise FileNotFoundError(f'Output path `{os.path.abspath(output)}` not found')

    password = None
    if args.password:
        password = get_password(args.key is not None)

    if args.template == 'CA':
        template = x509cert.template.CA
    elif args.template == 'host':
        template = x509cert.template.Host
    else:
        template = x509cert.template.User

    if args.key is None:
        csp = CSProvider()
        key = csp.key_gen(ed25519.KeyOpts())
        encryption_algorithm = (serialization.BestAvailableEncryption(password)
                                if password else serialization.NoEncryption())
        with open(os.path.join(output, 'certificate.key'), 'wb') as file:
            file.write(key.raw.private_bytes(encoding=serialization.Encoding.PEM,
                                             format=serialization.PrivateFormat.PKCS8,
                                             encryption_algorithm=encryption_algorithm))
    else:
        with open(args.key, 'rb') as file:
            key = serialization.load_pem_private_key(file.read(), password, backend=default_backend())

    csr = x509cert.create_csr(args.subject, key, template=template)
    r = httpx.post('http://localhost:26657/check_tx',
                   data=dict(tx='0x' + csr.public_bytes(encoding=serialization.Encoding.PEM).hex()))
    print(r)
    # with open(os.path.join(output, 'certificate.csr'), 'wb') as file:
    #     file.write(csr.public_bytes(encoding=serialization.Encoding.PEM))


if __name__ == '__main__':
    csr()
