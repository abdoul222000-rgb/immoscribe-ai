import sys
import os
import urllib.parse

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from server import app as flask_app

class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query = environ.get('QUERY_STRING', '')
        if '__path__=' in query:
            params = urllib.parse.parse_qs(query)
            if '__path__' in params:
                raw_path = params['__path__'][0]
                cleaned = '/' + raw_path.strip().lstrip('/')
                environ['PATH_INFO'] = cleaned
                clean_params = {k: v for k, v in params.items() if k != '__path__'}
                environ['QUERY_STRING'] = urllib.parse.urlencode(clean_params, doseq=True)
        elif environ.get('PATH_INFO', '') in ('/api/index.py', '/api/index', ''):
            environ['PATH_INFO'] = '/'
        return self.wsgi_app(environ, start_response)

flask_app.wsgi_app = VercelPathMiddleware(flask_app.wsgi_app)
app = flask_app
