"""Read-only access to the old SQLite database for one-time data exports."""

from .settings import *  # noqa: F403

SQLITE_PATH = Path(env('SQLITE_PATH', default=str(PROJECT_DIR / 'database' / 'db.sqlite3'))).resolve()
if not SQLITE_PATH.is_file():
    raise FileNotFoundError(f'SQLite export source does not exist: {SQLITE_PATH}')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': f'{SQLITE_PATH.as_uri()}?mode=ro',
        'OPTIONS': {'uri': True},
    },
}
