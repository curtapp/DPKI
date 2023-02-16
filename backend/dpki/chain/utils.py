import json
from datetime import date, datetime, timezone


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return (obj if obj.tzinfo else obj.replace(tzinfo=timezone.utc)).isoformat().replace('+00:00', 'Z')
        elif isinstance(obj, date):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
