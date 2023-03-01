import json
import os.path
import re
from base64 import b64decode
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

import pytoml

from csp import ed25519
from csp.base import Key
from csp.provider import CSProvider

if TYPE_CHECKING:
    from typing import Any, Dict, Union

    Config = Dict[str, Union[Dict[str, Any], Any]]


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return (obj if obj.tzinfo else obj.replace(tzinfo=timezone.utc)).isoformat().replace('+00:00', 'Z')
        elif isinstance(obj, date):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def load_config(home_path: str) -> 'Config':
    with open(os.path.join(home_path, 'config', 'config.toml'), 'r') as file:
        return pytoml.load(file)


def normalize_config(config: 'Config'):
    result = dict()
    for key, value in config.items():
        if isinstance(value, str):
            if match := re.search(r'(\d+)s', value):
                value = float(match.group(1))
            elif match := re.search(r'(\d+)ms', value):
                value = float(match.group(1)) / 1000
            elif match := re.search(r'(\d+)d', value):
                value = int(match.group(1))
        result[key] = value
    return result


def load_from_key_file(key_file: str) -> 'Key':
    with open(key_file, 'r') as file:
        obj = json.load(file)
        assert obj['type'].startswith('tendermint/PrivKey')
        if obj['type'].endswith('PrivKeyEd25519'):
            csp = CSProvider()
            return csp.key_import(b64decode(obj['value'])[:32], ed25519.KeyOpts())
        raise NotImplementedError(f"Key loader for {obj['type']} not yet implemented")
