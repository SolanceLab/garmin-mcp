# Garmin MCP Server — Dev Log

## Overview
Custom MCP server connecting Anne's Garmin Connect account (Descent G1) to Claude Code and Claude Desktop. Built from scratch — no third-party server code, only the `garminconnect` PyPI library as a dependency.

**Created:** 2026-02-03
**Location:** `~/Documents/Chadrien_Workspace/garmin-mcp/`
**Stack:** Python 3.14 + FastMCP + garminconnect 0.2.38
**Transport:** stdio
**Auth:** OAuth tokens via garth, saved to `~/.garminconnect/`

## Files

| File | Purpose |
|---|---|
| `server.py` | Main MCP server — all 13 tools |
| `auth.py` | One-time interactive authentication script |
| `.env` | Garmin credentials (gitignored) |
| `.env.template` | Credential template |
| `requirements.txt` | Pinned dependencies |
| `.gitignore` | Excludes .env, .venv, __pycache__ |

## Dependencies (pinned)

```
garminconnect==0.2.38
mcp>=1.8.1
python-dotenv>=1.0.0
```

## Tools — 13 Total

### Read Tools (11)
| Tool | Garmin Method | Purpose |
|---|---|---|
| `get_daily_summary` | `get_user_summary(cdate)` | Morning check-in — all key metrics |
| `get_body_battery` | `get_body_battery(startdate)` + `get_body_battery_events(cdate)` | Energy level monitoring |
| `get_sleep_data` | `get_sleep_data(cdate)` | Sleep score, bedtime, wake time, stages |
| `get_heart_rate` | `get_heart_rates(cdate)` | Daily HR: current, min, max, avg |
| `get_resting_heart_rate` | `get_rhr_day(cdate)` | Baseline HR trend |
| `get_stress` | `get_stress_data(cdate)` | Stress levels and zone breakdown |
| `get_steps` | `get_steps_data(cdate)` | Step count and activity data |
| `get_menstrual_cycle` | `get_menstrual_data_for_date(fordate)` | Cycle day, phase, predictions |
| `get_hrv` | `get_hrv_data(cdate)` | Heart rate variability |
| `get_hydration` | `get_hydration_data(cdate)` | Water intake for the day |
| `get_activities` | `get_activities(start, limit)` | Recent workouts/dives/walks |

### Write Tools (2)
| Tool | Method | Purpose |
|---|---|---|
| `add_hydration` | `add_hydration_data(value_in_ml)` | Log water intake in ml |
| `update_menstrual_cycle` | Reverse-engineered POST (see below) | Log/update period dates |

## Reverse-Engineered Endpoint: Menstrual Cycle Write

The `garminconnect` library has no write support for menstrual data. We captured the browser request via Chrome DevTools.

**Endpoint:** `POST /periodichealth-service/menstrualcycle/calendarupdates`
**Response:** `204 No Content` on success

**Payload structure:**
```json
{
  "userProfilePk": YOUR_PROFILE_PK,
  "todayCalendarDate": "YYYY-MM-DD",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "futureEditsByFE": true,
  "reportTimestamp": "YYYY-MM-DDThh:mm:ss.ms",
  "cycleDatesLists": [["YYYY-MM-DD", "YYYY-MM-DD", ...]]
}
```

**Key findings:**
- No separate delete endpoint exists
- All operations (add/update/delete) use the same POST
- Garmin treats every POST as idempotent overwrite — latest state wins
- `cycleDatesLists` contains an array of every individual date in the period
- To "delete" a period, overwrite with corrected dates excluding the ones to remove

**Accessed via:** `garmin.connectapi(path, method="POST", json=payload)` which uses garth's authenticated HTTP client internally.

## Auth Flow

### First-time setup
```bash
# 1. Fill in .env with Garmin credentials
cp .env.template .env

# 2. Run auth script (handles MFA if enabled)
.venv/bin/python auth.py

# 3. Tokens saved to ~/.garminconnect/
```

### Server startup
1. Try token-based auth from `~/.garminconnect/`
2. If tokens expired → fall back to email/password from `.env`
3. If both fail → tools return auth error messages
4. Tokens auto-refresh on successful login

### Token expiry
Tokens last ~6 months. Re-authenticate:
```bash
.venv/bin/python auth.py
```

## Registration

**Claude Code** — registered via `claude mcp add`, config in `~/.claude.json`
**Claude Desktop** — manually added to `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
"garmin": {
  "command": "/path/to/garmin-mcp/.venv/bin/python",
  "args": ["/path/to/garmin-mcp/server.py"]
}
```

## Date Format

All date parameters: `YYYY-MM-DD` (e.g. `2026-02-03`). All tools default to today if no date provided.

## Garmin User Profile

- **User Profile PK:** (set in server.py — obtain from Garmin Connect)
- **Hydration goal:** 2,100ml/day
- **Device:** Garmin Descent G1 (Instinct 2 platform)
- **Cycle type:** Regular, predicted length 26 days
