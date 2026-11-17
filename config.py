"""Per-user credentials live outside the source checkout."""
import os
from pathlib import Path
import sys
import tempfile


def data_dir():
    override = os.environ.get('GARMIN_HEALTH_DATA_DIR')
    if override:
        path = Path(override).expanduser()
        if not path.is_absolute():
            raise ValueError('GARMIN_HEALTH_DATA_DIR must be an absolute path')
        return path
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'garmin-health-mcp'
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'garmin-health-mcp'
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share')) / 'garmin-health-mcp'


def read_key():
    if 'GARMIN_PERSONAL_API_KEY' in os.environ:
        key = os.environ['GARMIN_PERSONAL_API_KEY'].strip()
    else:
        try:
            key = (data_dir() / 'api-key').read_text().strip()
        except OSError:
            key = ''
    if not key:
        raise ValueError('No Garmin key configured. Run python configure.py locally; never paste a key into chat.')
    return key


def save_secret(name, value):
    if name not in ('api-key', 'openai-tunnel-key'):
        raise ValueError('Unsupported credential')
    if not value.strip():
        raise ValueError('Empty credential')
    root = data_dir()
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    if os.name == 'posix':
        root.chmod(0o700)
    fd, temporary = tempfile.mkstemp(dir=root)
    try:
        if os.name == 'posix':
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(value.strip())
        os.replace(temporary, root / name)
    finally:
        Path(temporary).unlink(missing_ok=True)
