"""Same-origin desktop demo server. Local development keeps backend.main unchanged.

Credentials come only from process environment. Never initializes a usage ledger.
Run with python -m backend.deployment; exactly one Uvicorn worker.
"""
import base64
import binascii
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.integrations.jev_live import configuration
from backend.integrations.usage import UsageLedger
from backend.main import app as api_app

DIST = Path(__file__).resolve().parents[1] / 'frontend' / 'dist'


def validate_live_storage():
    """Require an existing, unblocked ledger and persistent paths on Railway."""
    configuration()  # Validates endpoint/key/model; sends no provider request.
    paths = []
    for key in ('TYPESAFE_USAGE_DB', 'DEALCOMPASS_ANALYSIS_CACHE_DB'):
        value = os.environ.get(key, '')
        if not value or not Path(value).is_absolute():
            raise RuntimeError(f'{key} must be an explicit absolute path.')
        paths.append(Path(value).resolve())
    if paths[0] == paths[1]:
        raise RuntimeError('Usage ledger and analysis cache must use separate files.')
    if os.environ.get('RAILWAY_PROJECT_ID'):
        mount = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
        if not mount or not Path(mount).is_dir():
            raise RuntimeError('Attach a Railway volume before enabling Jev.')
        for path in paths:
            if not path.is_relative_to(Path(mount).resolve()):
                raise RuntimeError('Ledger and cache must both be inside the Railway volume.')
    for path in paths:
        if not path.parent.is_dir() or not os.access(path.parent, os.W_OK):
            raise RuntimeError('Ledger/cache directory must already exist and be writable.')
    if UsageLedger(paths[0]).summary()['blocked']:
        raise RuntimeError('Usage ledger is blocked. Resolve receipts; never reset the budget.')


def create_app(dist: Path = DIST):
    username = os.environ.get('DEALCOMPASS_DEMO_USER', 'team')
    password = os.environ.get('DEALCOMPASS_DEMO_PASSWORD', '')
    if not username or ':' in username or len(password) < 16:
        raise RuntimeError('Set a demo username and a password of at least 16 characters.')
    mode = os.environ.setdefault('DEALCOMPASS_ENGINE_MODE', 'rules')
    if mode not in ('rules', 'jev'):
        raise RuntimeError('Deployment mode must be explicitly rules or jev.')
    if mode == 'jev':
        validate_live_storage()
    if not (dist / 'index.html').is_file() or not (dist / 'assets').is_dir():
        raise RuntimeError('Frontend build missing. Run npm --prefix frontend run build.')

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware('http')
    async def protect_demo(request: Request, call_next):
        # Railway health probes do not receive passwords. No paid calls here.
        if request.url.path == '/health' and request.method == 'GET':
            return await call_next(request)
        header = request.headers.get('authorization', '')
        supplied_user = supplied_password = ''
        try:
            scheme, payload = header.split(' ', 1)
            if scheme.lower() == 'basic':
                decoded = base64.b64decode(payload, validate=True).decode('utf-8')
                supplied_user, supplied_password = decoded.split(':', 1)
        except (ValueError, UnicodeError, binascii.Error):
            pass
        valid_user = secrets.compare_digest(supplied_user.encode(), username.encode())
        valid_password = secrets.compare_digest(supplied_password.encode(), password.encode())
        if not (valid_user and valid_password):
            return JSONResponse({'detail': 'Demo login required.'}, status_code=401,
                                headers={'WWW-Authenticate': 'Basic realm="DealCompass", charset="UTF-8"',
                                         'Cache-Control': 'no-store'})
        # Browser Basic credentials are automatic: reject cross-origin paid POSTs.
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('origin')
            if (request.headers.get('sec-fetch-site') == 'cross-site' or
                    (origin is not None and origin != str(request.base_url).rstrip('/'))):
                return JSONResponse({'detail': 'Cross-origin request rejected.'}, status_code=403)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        return response

    @app.get('/', include_in_schema=False)
    def dashboard():
        return FileResponse(dist / 'index.html')

    app.mount('/assets', StaticFiles(directory=dist / 'assets'), name='assets')
    # API and docs remain behind the same auth. Unknown routes keep JSON 404s,
    # never a successful HTML response that disguises a missing API route.
    app.mount('/', api_app)
    return app


if __name__ == '__main__':
    import uvicorn
    os.umask(0o077)
    uvicorn.run(create_app(), host='0.0.0.0', port=int(os.environ.get('PORT', '8080')),
                workers=1, proxy_headers=True, forwarded_allow_ips='*')
