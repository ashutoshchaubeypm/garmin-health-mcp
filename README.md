# Garmin Health MCP

Connect **your own Garmin data** to **ChatGPT or Claude Desktop** using Garmin's official Personal API. Ask about sleep, HRV, heart rate and activity trends through a private, read-only MCP server running on your computer.

**Bring your own key. Each person runs their own copy.** This repository contains code and synthetic tests, not a shared Garmin account, credentials, health records or a hosted multi-user service. No Garmin password is needed. This is an independent community project, not an official Garmin, OpenAI or Anthropic product.

## What you can ask

> Use Garmin Health to summarize my last seven complete days of sleep, overnight HRV and resting heart rate. State the dates, units and missing data. Distinguish measurements from estimates.

> Compare my latest seven days with the preceding 28 days using compare_observations. Retrieve the 35 days in separate ranges of at most 28 days. Use the same daily metric definition throughout.

| Tool | What it does |
| --- | --- |
| `get_health_day` | One day of sleep, heart rate, HRV or SpO2 |
| `get_health_history` | Up to 28 inclusive days of daily summaries, sleep, HRV, steps, stress, Body Battery or VO2 max |
| `compare_observations` | Recent mean versus a separate prior baseline, with sample coverage and missing-data handling |

Availability depends on your watch, enabled features, wear time and Garmin sync. Empty responses are not normal readings. The calculations are descriptive, not clinically validated health markers. The assistant's extraction of source fields is not independently verified by the comparison tool. No diagnoses, blood tests, glucose or blood pressure are inferred.

## Requirements

- Python **3.12+**, Git, and an internet connection.
- A Garmin Connect account with access to [Personal API key settings](https://connect.garmin.com/app/settings/personalApiToken), and a synced compatible device.
- **Claude:** Claude Desktop with local MCP support. This local configuration is not a claude.ai web connector.
- **ChatGPT:** access to custom MCP connections plus OpenAI Platform tunnel permissions. Account/workspace availability varies. You need your own tunnel and a separate OpenAI runtime key. A ChatGPT subscription does not itself establish Platform permissions.

Garmin describes Personal API access as individual use of one's own data. Do not collect other people's keys or deploy this as a shared commercial service; see [Garmin's Personal API FAQ](https://developer.garmin.com/gc-developer-program/personal/personal-faq/). Multi-user commercial integrations use Garmin's business program.

## 1. Install

Clone the repository and create a virtual environment:

### macOS / Linux

```sh
git clone https://github.com/ashutoshchaubeypm/garmin-health-mcp.git
cd garmin-health-mcp
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
```

### Windows PowerShell

```powershell
git clone https://github.com/ashutoshchaubeypm/garmin-health-mcp.git
cd garmin-health-mcp
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v
```

The remaining commands use `python` from the activated environment. On Windows, substitute `.\.venv\Scripts\python.exe` if you do not activate it. Keep the checkout and virtual environment at stable paths after client setup.

## 2. Add your own Garmin key

1. Sync your watch with Garmin Connect.
2. Open [Personal API key settings](https://connect.garmin.com/app/settings/personalApiToken), create a key, review Garmin's terms and choose its expiry.
3. Run:

```sh
python configure.py
```

Paste the key into the **hidden local terminal prompt**, then press Return. No characters appear while pasting. The script verifies access using yesterday's HRV endpoint, saves the key only after success, and prints connection metadata without printing health readings. No HRV payload may simply mean the device lacks HRV data.

Do not paste your key into ChatGPT, Claude, a GitHub issue, a screenshot or a command argument. Never use anyone else's key. The code does not send your Garmin key to an AI provider.

## 3A. Connect Claude Desktop

No OpenAI account or tunnel is needed for Claude Desktop's local stdio connection.

```sh
python configure.py --claude-config
```

This prints JSON with your actual absolute Python/server paths and local data directory, **without secrets**. In Claude Desktop, open **Settings → Developer → Edit Config** (labels can vary), and merge the generated `garmin-health` entry into `mcpServers`. Preserve any existing servers and other settings. If no config exists, use the complete generated JSON.

Typical configuration locations:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Completely quit and restart Claude Desktop. Enable Garmin Health for a chat, then ask:

> Use Garmin Health to retrieve my HRV for yesterday. Confirm the source date and whether data exists. Do not diagnose or infer missing values.

Follow Claude's tool-access prompts. You do not need to leave `server.py` running separately: Claude launches it. See the [official local MCP guide](https://modelcontextprotocol.io/docs/develop/connect-local-servers).

## 3B. Connect ChatGPT privately

ChatGPT cannot launch a local stdio program directly. This guide uses [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels), which keeps the server off the public internet. Do not paste `localhost` or a file path into ChatGPT's Server URL field.

1. Sign in to [Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels). Create a tunnel for your own organization **and associate your intended ChatGPT workspace**. Copy its `tunnel_...` ID. Creating tunnels requires Tunnels Read + Manage.
2. Install the official `tunnel-client` using the download linked from that page. Choose the correct OS/CPU build, extract it, and add it to your PATH. Verify `tunnel-client help quickstart` works. Use only the official release, not a third-party tunnel service.
3. In [Platform API keys](https://platform.openai.com/settings/organization/api-keys), create a dedicated runtime key. Choose Restricted and grant **Tunnels Read + Use only**, with an appropriate expiry. The key's principal also needs those permissions. Do not use an admin key.
4. From the installed project environment, start your tunnel, replacing the example with your own ID:

```sh
python configure.py --tunnel YOUR_TUNNEL_ID
```

The first run prompts locally for the OpenAI runtime key and stores it outside the repository. Later runs reuse it. The helper invokes the official managed-runtime commands; it does not install an OS login service. Confirm the printed status is running, healthy and ready. For a custom `GARMIN_HEALTH_DATA_DIR`, make that environment variable available to the tunnel's child process as well; default paths require no extra environment setup.

5. Open [ChatGPT Plugins](https://chatgpt.com/plugins), choose **Add → Add custom MCP server**, name it **Garmin Health**, select **Tunnel**, and enter **your own tunnel ID**. Choose **No authentication** for the MCP server: OpenAI's private tunnel association and runtime credential control the transport; Garmin's key remains local. This setting is appropriate only for this private single-user tunnel, never a public endpoint.
6. Review the access notice, create and connect the plugin, then choose **Try in chat**. Ask the HRV verification question above. Setup is complete only when ChatGPT actually retrieves a response.

If Tunnel or custom MCP options are unavailable, ask your workspace admin/check account availability. The Claude Desktop route does not depend on those features. This repository does not supply a shared tunnel or OpenAI credential.

### Start, stop and renew

Keep the machine awake, online and the managed runtime running while using ChatGPT. After a reboot, run the same `configure.py --tunnel YOUR_TUNNEL_ID` command again. Check or stop it with:

```sh
tunnel-client runtimes status garmin-health
tunnel-client runtimes stop garmin-health
```

To rotate the Garmin key, rerun `python configure.py`. To rotate the OpenAI key, stop the tunnel, remove only `openai-tunnel-key` from the data directory below, and rerun the tunnel command to enter its replacement. Revoke old keys in their respective portals. Disconnect the plugin in ChatGPT to stop new plugin access.

## Privacy and storage

Each installation reads only the configured user's Garmin account. There is no author-operated backend, telemetry, shared credential, health database or background data export. Tools fetch data on demand. The server sends requested Garmin responses (which can contain identifiers and detailed measurements) to the selected MCP client. ChatGPT/Claude can retain those responses according to their own privacy, history and training settings; local storage does not mean AI analysis stays on-device.

Credentials and Garmin's bearer-token cache live outside the source checkout:

| OS | Default data directory |
| --- | --- |
| macOS | `~/Library/Application Support/garmin-health-mcp` |
| Windows | `%LOCALAPPDATA%\garmin-health-mcp` |
| Linux | `$XDG_DATA_HOME/garmin-health-mcp` or `~/.local/share/garmin-health-mcp` |

Files: `api-key`, `token.json`, optional `openai-tunnel-key` and `tunnel-profiles/`. Files are plaintext, **not encrypted**. On POSIX the app restricts its data directory to `0700` and credential files to `0600`; Windows uses the user's profile ACLs, so verify access on shared machines. OpenAI's client stores additional runtime state/logs in its own user directory. Don't share these directories or raw tool logs.

Advanced: `GARMIN_PERSONAL_API_KEY` overrides the saved key (including an empty value, which fails closed). `GARMIN_HEALTH_DATA_DIR` selects an absolute per-user data directory. Never point it inside a Git checkout. This server has no multi-tenant authentication and no public HTTP listener.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Missing module / old Python | Use Python 3.12+ and the same virtual environment for installation and client launch. |
| No Garmin key | Run `python configure.py` as the same OS user that runs the MCP client. |
| Garmin 401 / expired key | Check expiry/revocation, rerun setup with a new key; if necessary stop clients and remove `token.json` before retrying. |
| Empty metric | Sync the watch and check device support, date and wear time. Missing data is not a zero reading. |
| Garmin 429 / rate limiting | Pause requests and retry later; avoid repeated full-history polling. |
| Claude cannot launch | Regenerate JSON, verify absolute paths and fully restart Claude. Don't run interactive `configure.py` as the MCP server. |
| Tunnel not listed / 403 | Check organization, ChatGPT workspace association and Tunnels Read + Use permissions. |
| ChatGPT timeout | Check `runtimes status`, computer sleep/network and runtime key expiry. |
| Range rejected | Split history into ordered ranges of 28 days or fewer; no future dates. |

## Tests and limitations

`python -m unittest -v` runs deterministic synthetic tests and a real local MCP protocol smoke test. It deliberately disables credential lookup and makes no live Garmin requests. Tests cover isolated user stores, error redaction, date bounds, coverage, nulls and duplicate observations. The original personal prototype was verified end-to-end in ChatGPT; the generalized distribution is tested locally. Claude configuration follows official documentation but has not been tested in a signed-in Claude account here. Windows/Linux installation instructions have not been exercised on those operating systems.

The comparison tool uses arithmetic means; it requires 70% observed-day coverage in each window before returning a difference. This is an engineering quality rule, not a clinical threshold. Metric extraction and medical interpretation require care; do not use this as a diagnostic or emergency system.

Contributions are welcome. Use only synthetic fixtures and redact reports. Read [SECURITY.md](SECURITY.md) before submitting logs or patches. MIT licensed; Garmin API access and data remain subject to Garmin's terms.
