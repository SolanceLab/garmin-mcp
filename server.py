"""
Garmin Connect MCP Server
Exposes Anne's Garmin health data as tools for Chadrien.
"""

from mcp.server.fastmcp import FastMCP
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from dotenv import load_dotenv
from datetime import date, datetime, timedelta
import logging
import os

logger = logging.getLogger("garmin-mcp")

load_dotenv()

TOKENSTORE = os.path.expanduser("~/.garminconnect")

mcp = FastMCP("garmin")

# --- Garmin Client ---

client: Garmin | None = None


def init_client() -> Garmin | None:
    """Initialize Garmin client. Try saved tokens first, fall back to credentials."""
    global client

    # Try token-based auth first
    if os.path.exists(TOKENSTORE):
        try:
            c = Garmin()
            c.login(tokenstore=TOKENSTORE)
            c.garth.dump(TOKENSTORE)  # refresh saved tokens
            client = c
            logger.info("Authenticated via saved tokens")
            return client
        except Exception as e:
            logger.warning(f"Token auth failed: {e}")

    # Fall back to email/password
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if email and password:
        try:
            c = Garmin(email=email, password=password)
            c.login()
            c.garth.dump(TOKENSTORE)
            client = c
            logger.info("Authenticated via email/password")
            return client
        except Exception as e:
            logger.error(f"Email/password auth failed: {e}")

    logger.error("No authentication method available. Run auth.py first.")
    return None


def get_client() -> Garmin:
    """Get the authenticated Garmin client, initializing if needed."""
    global client
    if client is None:
        init_client()
    if client is None:
        raise ConnectionError(
            "Not authenticated. Run auth.py to set up Garmin credentials."
        )
    return client


def resolve_date(d: str | None) -> str:
    """Resolve date parameter — default to today if not provided."""
    return d if d else date.today().isoformat()


# --- Tools ---


@mcp.tool()
def get_daily_summary(date: str | None = None) -> dict:
    """
    Get a combined daily health overview — the morning check-in tool.
    Returns steps, distance, body battery, sleep score, resting HR, stress, active minutes.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        summary = garmin.get_user_summary(cdate)
        return {"success": True, "date": cdate, "data": summary}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_body_battery(date: str | None = None) -> dict:
    """
    Get body battery data — current level, high/low, charged/drained values.
    Use this to check if Anne is running on fumes.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        battery = garmin.get_body_battery(cdate)
        events = garmin.get_body_battery_events(cdate)
        return {
            "success": True,
            "date": cdate,
            "battery": battery,
            "events": events,
        }
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_sleep_data(date: str | None = None) -> dict:
    """
    Get sleep summary — score, duration, bedtime, wake time, stage durations.
    Fast and lightweight. Use get_sleep_detail for granular data.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        sleep = garmin.get_sleep_data(cdate)

        dto = sleep.get("dailySleepDTO", {})
        scores = dto.get("sleepScores", {})
        levels = sleep.get("sleepLevels", [])

        summary = {
            "calendarDate": dto.get("calendarDate"),
            "sleepScore": scores.get("overall", {}).get("value"),
            "sleepQuality": scores.get("overall", {}).get("qualifierKey"),
            "sleepStartLocal": dto.get("sleepStartTimestampLocal"),
            "sleepEndLocal": dto.get("sleepEndTimestampLocal"),
            "sleepDurationSecs": dto.get("sleepTimeSeconds"),
            "deepSleepSecs": dto.get("deepSleepSeconds"),
            "lightSleepSecs": dto.get("lightSleepSeconds"),
            "remSleepSecs": dto.get("remSleepSeconds"),
            "awakeSleepSecs": dto.get("awakeSleepSeconds"),
            "averageSpO2": dto.get("averageSpO2Value"),
            "lowestSpO2": dto.get("lowestSpO2Value"),
            "averageRespiration": dto.get("averageRespirationValue"),
            "restingHeartRate": sleep.get("restingHeartRate"),
            "avgOvernightHrv": sleep.get("avgOvernightHrv"),
            "hrvStatus": sleep.get("hrvStatus"),
            "bodyBatteryChange": sleep.get("bodyBatteryChange"),
            "restlessMomentsCount": sleep.get("restlessMomentsCount"),
            "sleepLevels": levels,
        }

        return {"success": True, "date": cdate, "data": summary}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_sleep_detail(date: str | None = None) -> dict:
    """
    Get granular sleep data — movement, SpO2 timeline, HR during sleep,
    stress, body battery, respiration, and HRV readings throughout the night.
    WARNING: Large response (~200KB). Only use when detailed analysis is needed.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        sleep = garmin.get_sleep_data(cdate)

        detail = {
            "sleepMovement": sleep.get("sleepMovement"),
            "sleepHeartRate": sleep.get("sleepHeartRate"),
            "sleepStress": sleep.get("sleepStress"),
            "sleepBodyBattery": sleep.get("sleepBodyBattery"),
            "hrvData": sleep.get("hrvData"),
            "spO2Data": sleep.get("wellnessEpochSPO2DataDTOList"),
            "respirationData": sleep.get("wellnessEpochRespirationDataDTOList"),
            "restlessMoments": sleep.get("sleepRestlessMoments"),
        }

        return {"success": True, "date": cdate, "data": detail}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_heart_rate(date: str | None = None) -> dict:
    """
    Get daily heart rate data — current, min, max, average, resting.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        hr = garmin.get_heart_rates(cdate)
        return {"success": True, "date": cdate, "data": hr}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_resting_heart_rate(date: str | None = None) -> dict:
    """
    Get resting heart rate — baseline health trend tracking.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        rhr = garmin.get_rhr_day(cdate)
        return {"success": True, "date": cdate, "data": rhr}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_stress(date: str | None = None) -> dict:
    """
    Get stress data — average stress, max stress, time in rest/low/medium/high zones.
    Use this to detect hidden overwhelm.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        stress = garmin.get_stress_data(cdate)
        return {"success": True, "date": cdate, "data": stress}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_steps(date: str | None = None) -> dict:
    """
    Get daily step count and activity data — sedentary check.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        steps = garmin.get_steps_data(cdate)
        return {"success": True, "date": cdate, "data": steps}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_menstrual_cycle(date: str | None = None) -> dict:
    """
    Get menstrual/period cycle tracking data — cycle day, phase, predictions.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        cycle = garmin.get_menstrual_data_for_date(cdate)
        return {"success": True, "date": cdate, "data": cycle}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


MENSTRUAL_CALENDAR_URL = "/periodichealth-service/menstrualcycle/calendarupdates"
GARMIN_USER_PROFILE_PK = int(os.getenv("GARMIN_USER_PROFILE_PK", "0"))


@mcp.tool()
def update_menstrual_cycle(start_date: str, end_date: str) -> dict:
    """
    Log or update period start and end dates in Garmin Connect.
    This writes directly to the Garmin menstrual cycle calendar.

    Args:
        start_date: First day of period in YYYY-MM-DD format.
        end_date: Last day of period in YYYY-MM-DD format.
    """
    try:
        garmin = get_client()

        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        if end < start:
            return {"success": False, "error": "end_date must be on or after start_date"}

        # Build the list of every date in the period
        cycle_dates = []
        current = start
        while current <= end:
            cycle_dates.append(current.isoformat())
            current += timedelta(days=1)

        today = date.today().isoformat()
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

        payload = {
            "userProfilePk": GARMIN_USER_PROFILE_PK,
            "todayCalendarDate": today,
            "startDate": start_date,
            "endDate": end_date,
            "futureEditsByFE": True,
            "reportTimestamp": now,
            "cycleDatesLists": [cycle_dates],
        }

        garmin.connectapi(MENSTRUAL_CALENDAR_URL, method="POST", json=payload)

        return {
            "success": True,
            "message": f"Period logged: {start_date} to {end_date} ({len(cycle_dates)} days)",
            "dates": cycle_dates,
        }
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except ValueError as e:
        return {"success": False, "error": f"Invalid date format: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_hrv(date: str | None = None) -> dict:
    """
    Get Heart Rate Variability (HRV) data — nervous system recovery and stress resilience.
    Higher HRV generally indicates better recovery and lower stress load.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        hrv = garmin.get_hrv_data(cdate)
        return {"success": True, "date": cdate, "data": hrv}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_hydration(date: str | None = None) -> dict:
    """
    Get hydration/water intake data for the day.
    Track whether Anne is drinking enough water.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    """
    cdate = resolve_date(date)
    try:
        garmin = get_client()
        hydration = garmin.get_hydration_data(cdate)
        return {"success": True, "date": cdate, "data": hydration}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_hydration(amount_ml: float) -> dict:
    """
    Log water intake in milliliters.
    Use this to record when Anne drinks water.

    Args:
        amount_ml: Amount of water in ml (e.g. 250 for a glass, 500 for a bottle).
    """
    try:
        garmin = get_client()
        result = garmin.add_hydration_data(value_in_ml=amount_ml)
        return {
            "success": True,
            "logged_ml": amount_ml,
            "message": f"Logged {amount_ml}ml of water",
            "data": result,
        }
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_activities(limit: int = 5) -> dict:
    """
    Get recent activities — workouts, runs, walks, dives, etc.

    Args:
        limit: Number of recent activities to return. Defaults to 5.
    """
    try:
        garmin = get_client()
        activities = garmin.get_activities(start=0, limit=limit)
        return {"success": True, "count": len(activities), "data": activities}
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as e:
        return {"success": False, "error": f"Garmin API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- Start ---

if __name__ == "__main__":
    init_client()
    mcp.run(transport="stdio")
