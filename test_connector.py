import asyncio
from datetime import date, timedelta
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from analytics import summarize
import server
from config import data_dir, read_key, save_secret
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class Tests(unittest.TestCase):
    def test_nonoverlapping_windows(self):
        end = date(2026, 11, 14)
        rows = [{'date': str(end-timedelta(days=i)), 'value': 60 if i < 7 else 50} for i in range(35)]
        result = summarize(rows, str(end))
        self.assertEqual(result['difference'], 10)
        self.assertEqual(result['difference_percent'], 20)
        self.assertEqual(result['baseline']['observed_days'], 28)

    def test_missing_not_zero(self):
        result = summarize([{'date': '2026-11-14', 'value': None}], '2026-11-14')
        self.assertIsNone(result['recent']['mean'])
        self.assertIsNone(result['difference'])
        self.assertFalse(result['coverage_sufficient'])

    def test_invalid_observations(self):
        for value in [True, float('nan'), float('inf'), '50']:
            with self.assertRaises(ValueError):
                summarize([{'date': '2026-11-14', 'value': value}], '2026-11-14')
        with self.assertRaises(ValueError):
            summarize([{'date': '2026-11-14', 'value': 50}]*2, '2026-11-14')

    def test_ranges(self):
        for a, b in [('2026-01-02', '2026-01-01'), ('2026-01-01', '2026-02-01'), ('2099-01-01', '2099-01-01')]:
            with self.assertRaises(ValueError):
                server.validate_range(a, b)

    def test_error_redaction(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {'GARMIN_HEALTH_DATA_DIR': root, 'GARMIN_PERSONAL_API_KEY': 'synthetic-example'}), patch.object(server, 'PersonalApiAuthenticator', side_effect=RuntimeError('synthetic-example')):
            with self.assertRaises(ValueError) as caught:
                server.query('get_daily_hrv', '2026-11-14')
            self.assertNotIn('synthetic-example', str(caught.exception))

    def test_independent_user_stores(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            with patch.dict(os.environ, {'GARMIN_HEALTH_DATA_DIR': first}):
                with patch.dict(os.environ):
                    os.environ.pop('GARMIN_PERSONAL_API_KEY', None)
                    save_secret('api-key', 'synthetic-user-one')
                    self.assertEqual(read_key(), 'synthetic-user-one')
                    if os.name == 'posix':
                        self.assertEqual((Path(first)/'api-key').stat().st_mode & 0o777, 0o600)
            with patch.dict(os.environ, {'GARMIN_HEALTH_DATA_DIR': second, 'GARMIN_PERSONAL_API_KEY': ''}):
                with self.assertRaises(ValueError):
                    read_key()
                save_secret('api-key', 'synthetic-user-two')
                # Explicit empty environment must not fall back to a saved key.
                with self.assertRaises(ValueError):
                    read_key()
                os.environ.pop('GARMIN_PERSONAL_API_KEY')
                self.assertEqual(read_key(), 'synthetic-user-two')

    def test_no_key_config_output(self):
        import subprocess
        env = dict(os.environ, GARMIN_PERSONAL_API_KEY='synthetic-hidden-value')
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('configure.py')), '--claude-config'], capture_output=True, text=True, env=env, check=True)
        self.assertNotIn('synthetic-hidden-value', result.stdout)
        import json
        config = json.loads(result.stdout)['mcpServers']['garmin-health']
        self.assertTrue(Path(config['command']).is_absolute())
        self.assertTrue(Path(config['args'][0]).is_absolute())

    def test_mcp_protocol(self):
        async def check():
            params = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name('server.py'))], env={'GARMIN_PERSONAL_API_KEY': ''})
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    names = {t.name for t in (await session.list_tools()).tools}
                    self.assertEqual(names, {'get_health_day', 'get_health_history', 'compare_observations'})
                    result = await session.call_tool('compare_observations', {'metric': 'test', 'unit': 'bpm', 'source_field': 'test', 'observations': [], 'end_date': '2026-11-14'})
                    self.assertFalse(result.isError)
                    missing = await session.call_tool('get_health_day', {'metric': 'hrv', 'calendar_date': '2026-11-14'})
                    self.assertTrue(missing.isError)
        asyncio.run(check())


if __name__ == '__main__':
    unittest.main()
