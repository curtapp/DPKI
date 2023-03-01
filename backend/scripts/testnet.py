import json
import os.path
import shutil
import subprocess
import sys
from base64 import b64encode
from collections.abc import Mapping

import pytoml
from cryptography.hazmat.primitives import serialization

from csp import ed25519
from csp.provider import CSProvider
import dpki.x509cert.template
from dpki import x509cert
from dpki.chainapp.utils import JSONEncoder


def deep_update(dst: dict, src: dict):
    if all((isinstance(d, Mapping) for d in (dst, src))):
        for k, v in src.items():
            dst[k] = deep_update(dst.get(k), v)
        return dst
    return src


def make_node(root_path, moniker, pv=False, tmpl=None):
    home_path = os.path.join(root_path, moniker)
    os.makedirs(home_path)
    if tmpl is None:
        subprocess.run(['tendermint', '--home', home_path, 'init'], stdout=subprocess.PIPE)
        with open(os.path.join(home_path, 'config', 'genesis.json')) as file:
            return json.load(file)
    else:
        subprocess.run(['tendermint', '--home', home_path, 'gen-node-key'], stdout=subprocess.PIPE)
        if pv:
            p = subprocess.Popen(['tendermint', '--home', home_path, 'gen-validator'], stdout=subprocess.PIPE)
            pv_data = json.loads(p.communicate()[0])
            with open(os.path.join(home_path, 'data', 'priv_validator_state.json'), 'w') as file:
                json.dump(pv_data['LastSignState'], file)
            with open(os.path.join(home_path, 'config', 'priv_validator_key.json'), 'w') as file:
                json.dump(pv_data['Key'], file)
                return dict((k, v) for k, v in pv_data['Key'].items() if k in ('pub_key', 'address'))


def config_node(root_path, moniker, genesis, config):
    home_path = os.path.join(root_path, moniker)
    with open(os.path.join(home_path, 'config', 'genesis.json'), 'w') as file:
        json.dump(genesis, file, cls=JSONEncoder)
    with open(os.path.join(home_path, 'config', 'config.toml'), 'r') as file:
        config['moniker'] = moniker
        config = deep_update(pytoml.load(file), config)
    with open(os.path.join(home_path, 'config', 'config.toml'), 'w') as file:
        pytoml.dump(config, file)


def make_root_ca(root_path, distinguished_name, genesis, password=None):
    csp = CSProvider()
    key = csp.key_gen(ed25519.KeyOpts())
    csr = x509cert.create_csr(distinguished_name, key, x509cert.template.CA)
    cert = x509cert.apply_csr(csr, (csr, key), '2070-01-01')
    if 'app_state' not in genesis:
        genesis['app_state'] = dict(certificates=[])
    elif 'certificates' not in genesis['app_state']:
        genesis['app_state']['certificates'] = []
    genesis['app_state']['certificates'].append(cert.public_bytes(encoding=serialization.Encoding.PEM).decode('utf8'))
    encryption_algorithm = (serialization.BestAvailableEncryption(password)
                            if password else serialization.NoEncryption())
    with open(os.path.join(root_path, 'root_ca.key'), 'wb') as file:
        file.write(key.raw.private_bytes(encoding=serialization.Encoding.PEM,
                                         format=serialization.PrivateFormat.PKCS8,
                                         encryption_algorithm=encryption_algorithm))
    with open(os.path.join(root_path, 'root_ca.crt'), "wb") as file:
        file.write(cert.public_bytes(encoding=serialization.Encoding.PEM))
    return cert, key


def make_ca(root_path, distinguished_name, moniker, genesis, issuer_pair, password=None):
    csp = CSProvider()
    key = csp.key_gen(ed25519.KeyOpts())
    csr = x509cert.create_csr(distinguished_name, key, dpki.x509cert.template.CA, path_length=7)
    cert = x509cert.apply_csr(csr, issuer_pair, '2050-01-01')
    genesis['app_state']['certificates'].append(cert.public_bytes(encoding=serialization.Encoding.PEM).decode('utf8'))
    with open(os.path.join(root_path, moniker, 'config', 'ca_key.json'), 'w') as file:
        json.dump(dict(type='tendermint/PrivKeyEd25519',
                       value=b64encode(bytes(key) + bytes(key.public_key)).decode('utf8')), file)
    with open(os.path.join(root_path, moniker, 'config', 'config.toml'), 'r') as file:
        config = pytoml.load(file)
        config['ca'] = dict(ca_key_file='config/ca_key.json', allow_templates=['CA', 'Node', 'User'],
                            ca_valid_for='795d', host_valid_for='530d', user_valid_for='365d', next_path_length=3,
                            waiting_for_downstream='900s')
    with open(os.path.join(root_path, moniker, 'config', 'config.toml'), 'w') as file:
        pytoml.dump(config, file)

    return cert, key


def main():
    import argparse
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0], ), description='Testnet gen for DPKI')
    parser.add_argument('-o', '--output', help='Output files path', default=os.path.join(os.path.curdir, '.testnet'))
    args = parser.parse_args()
    root_path = args.output if args.output.endswith('.testnet') else os.path.join(args.output, '.testnet')
    if os.path.exists(root_path):
        shutil.rmtree(root_path, True)
    os.makedirs(root_path, exist_ok=True)

    genesis = {**make_node(root_path, 'node0000', tmpl=None), 'chain_id': 'test-chain-DPKI'}
    genesis['validators'][0]['name'] = 'node0000'
    for moniker in ('node00ca', 'node01ca'):
        pv_data = make_node(root_path, moniker, pv=True, tmpl='node0000')
        genesis['validators'].append({**pv_data, 'power': '10', 'name': moniker})

    for moniker in ('node0100',):
        make_node(root_path, moniker, tmpl='node0000')

    issuer_pair = make_root_ca(root_path, 'CN=Wonderland root CA, C=WN', genesis)
    issuer_pair = make_ca(root_path, "CN=Wonderland main CA, C=WN", 'node00ca', genesis, issuer_pair)
    make_ca(root_path, "CN=CA controlled by Cheshire Cat, STREET=Cat's house, L=Cheshire, C=WN",
            'node01ca', genesis, issuer_pair)

    for moniker in ('node0000', 'node00ca', 'node01ca', 'node0100'):
        config_node(root_path, moniker, genesis, {
            'consensus': {
                'create_empty_blocks': False
            }
        })


if __name__ == '__main__':
    main()
