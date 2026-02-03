"""
One-time authentication script for Garmin Connect.
Run this interactively to authenticate and save OAuth tokens.
After this, the MCP server can start without credentials.
"""

from garminconnect import Garmin
from dotenv import load_dotenv
import os
import sys

TOKENSTORE = os.path.expanduser("~/.garminconnect")


def authenticate():
    load_dotenv()

    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not email or not password:
        print("GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env")
        print("Copy .env.template to .env and fill in your credentials.")
        sys.exit(1)

    print(f"Authenticating as {email}...")

    try:
        client = Garmin(
            email=email,
            password=password,
            prompt_mfa=lambda: input("Enter MFA code: "),
        )
        client.login()
        client.garth.dump(TOKENSTORE)

        print(f"\nAuthentication successful!")
        print(f"Display name: {client.display_name}")
        print(f"Tokens saved to: {TOKENSTORE}")
        print(f"\nThe MCP server can now start using saved tokens.")

    except Exception as e:
        print(f"\nAuthentication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    authenticate()
