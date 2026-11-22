import sys
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from server import app

class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched = environ.get('HTTP_X_MATCHED_PATH')
        if matched:
            environ['PATH_INFO'] = matched
        else:
            path = environ.get('PATH_INFO', '')
            if path.startswith('/api/index.py'):
                environ['PATH_INFO'] = path[len('/api/index.py'):] or '/'
            elif path.startswith('/api/index'):
                environ['PATH_INFO'] = path[len('/api/index'):] or '/'
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
