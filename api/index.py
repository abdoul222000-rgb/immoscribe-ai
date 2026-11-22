import sys
import os
import json

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from server import app as flask_app

def app(environ, start_response):
    if 'debug' in environ.get('QUERY_STRING', ''):
        data = {k: str(v) for k, v in environ.items() if isinstance(v, (str, int, float, bool))}
        res = json.dumps(data, indent=2).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [res]
    
    return flask_app(environ, start_response)
