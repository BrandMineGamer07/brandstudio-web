import sys
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app

# Vercel WSGI Middleware to fix rewrites in Vercel CLI 65+
class VercelPathFixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = (
            environ.get('HTTP_X_MATCHED_PATH') or 
            environ.get('HTTP_X_FORWARDED_URI') or 
            environ.get('HTTP_X_ORIGINAL_URI') or
            environ.get('HTTP_X_VERCEL_MATCHED_PATH')
        )
        if matched_path:
            path_only = matched_path.split('?')[0]
            if path_only in ('', '/'):
                environ['PATH_INFO'] = '/'
            else:
                environ['PATH_INFO'] = path_only
        elif environ.get('PATH_INFO') == '/api/index':
            environ['PATH_INFO'] = '/'
            
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)
app.debug = False
