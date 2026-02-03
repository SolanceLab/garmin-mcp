# Garmin Connect MCP Server

Custom MCP server that connects your Garmin Connect account to Claude Code and Claude Desktop, exposing health and fitness data as tools.

Built for a Garmin Descent G1 but works with any Garmin device that supports health monitoring.

## Tools (13)

### Read
- **get_daily_summary** — Combined daily health overview
- **get_body_battery** — Energy level, charged/drained values
- **get_sleep_data** — Sleep score, bedtime, wake time, stages
- **get_heart_rate** — Daily HR: current, min, max, average
- **get_resting_heart_rate** — Baseline HR trend
- **get_stress** — Stress levels and zone breakdown
- **get_steps** — Step count and activity data
- **get_menstrual_cycle** — Cycle day, phase, predictions
- **get_hrv** — Heart rate variability
- **get_hydration** — Water intake for the day
- **get_activities** — Recent workouts and activities

### Write
- **add_hydration** — Log water intake in ml
- **update_menstrual_cycle** — Log/update period start and end dates

## Setup

### 1. Install dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.template .env
# Edit .env with your Garmin Connect email and password
```

### 3. Authenticate (one-time)

```bash
.venv/bin/python auth.py
```

If you have MFA enabled, you'll be prompted for the code. OAuth tokens are saved to `~/.garminconnect/` and reused automatically. Tokens last ~6 months.

### 4. Register in Claude Code

```bash
claude mcp add garmin -- /path/to/garmin-mcp/.venv/bin/python /path/to/garmin-mcp/server.py
```

### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
"garmin": {
  "command": "/path/to/garmin-mcp/.venv/bin/python",
  "args": ["/path/to/garmin-mcp/server.py"]
}
```

## Dependencies

- `garminconnect==0.2.38` — Garmin Connect API client (pinned)
- `mcp>=1.8.1` — Model Context Protocol framework
- `python-dotenv>=1.0.0` — Environment variable loading

## Notes

- All date parameters use `YYYY-MM-DD` format and default to today
- The menstrual cycle write endpoint was reverse-engineered from Garmin Connect web — it's not part of the garminconnect library
- Credentials are only used during initial authentication; after that, OAuth tokens handle everything
- `.env` is gitignored and never leaves your machine

## Disclaimer

This software is provided **as-is, without warranty or guarantee of any kind**. Use at your own risk.

- This project is **not affiliated with, endorsed by, or supported by Garmin Ltd.** or any of its subsidiaries
- It relies on unofficial, reverse-engineered API endpoints that **may break at any time** without notice if Garmin changes their backend
- The menstrual cycle write endpoint in particular is undocumented and was captured via browser network inspection — its behavior may change
- **You are responsible** for the security of your own Garmin credentials and OAuth tokens
- The authors are not liable for any data loss, account issues, or other consequences of using this software

See [LICENSE](LICENSE) for full terms.

## Support

If you find this useful, support us on Ko-fi:

[![Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/houseofsolance)

## Authors

Built by **Anne Solance** and **Chadrien Solance** at [House of Solance](https://ko-fi.com/houseofsolance).
