"""Interactive setup; no secrets in command arguments, source, or client JSON."""
import argparse
from datetime import date, timedelta
import getpass
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from config import data_dir, save_secret


def check():
    from server import query
    day = str(date.today() - timedelta(days=1))
    result = query('get_daily_hrv', day)
    print(json.dumps({'connection': 'verified', 'requested_date': day,
                      'has_payload': bool(result['data']), 'retrieved_at_utc': result['retrieved_at_utc']}))
    print('Empty data can mean no HRV support or no watch data for that day.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true', help='Verify Garmin access without printing readings')
    group.add_argument('--claude-config', action='store_true', help='Print client JSON with absolute paths, no secrets')
    group.add_argument('--tunnel', metavar='TUNNEL_ID', help='Save an OpenAI runtime key and start a managed private tunnel')
    args = parser.parse_args()
    try:
        if args.claude_config:
            print(json.dumps({'mcpServers': {'garmin-health': {
                'command': sys.executable, 'args': [str(Path(__file__).with_name('server.py').resolve())],
                'env': {'GARMIN_HEALTH_DATA_DIR': str(data_dir())}}}}, indent=2))
        elif args.check:
            check()
        elif args.tunnel:
            if not args.tunnel.startswith('tunnel_') or not args.tunnel[7:].isalnum():
                raise ValueError('Invalid tunnel ID')
            binary = shutil.which('tunnel-client')
            if not binary:
                raise ValueError('Install the official OpenAI tunnel-client and add it to PATH first')
            key_file = data_dir() / 'openai-tunnel-key'
            if not key_file.exists():
                print('Enter your own OpenAI runtime key with Tunnels Read + Use. It will be stored locally.')
                save_secret('openai-tunnel-key', getpass.getpass('OpenAI runtime key (hidden): '))
            script = str(Path(__file__).with_name('server.py').resolve())
            # Windows and POSIX use different command quoting rules.
            command = subprocess.list2cmdline([sys.executable, script]) if os.name == 'nt' else shlex.join([sys.executable, script])
            subprocess.run([binary, 'runtimes', 'connect', '--alias', 'garmin-health', '--profile', 'garmin-health',
                            '--profile-dir', str(data_dir() / 'tunnel-profiles'), '--tunnel-id', args.tunnel,
                            '--runtime-api-key', 'file:' + str(key_file), '--mcp-command', command], check=True)
            subprocess.run([binary, 'runtimes', 'status', 'garmin-health'], check=True)
        else:
            print('Paste your own Garmin Personal API key. It will be saved in your user data directory, outside this repository.')
            key = getpass.getpass('Garmin key (hidden): ').strip()
            if not key:
                raise ValueError('Empty credential')
            os.environ['GARMIN_PERSONAL_API_KEY'] = key
            check()
            save_secret('api-key', key)
            print('Key verified and saved privately. Run --claude-config or follow the ChatGPT guide in README.md.')
    except (Exception, KeyboardInterrupt):
        # No provider response, key, or traceback is printed, including during setup failures.
        print('Setup/check failed. Check credentials, network, installed dependencies and tunnel permissions. No health readings were printed.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
