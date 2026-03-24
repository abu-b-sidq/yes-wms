#!/usr/bin/env python
import os
import sys

from dotenv import load_dotenv

# Load .env so FIREBASE_SERVICE_ACCOUNT_PATH etc. are available
if os.path.isfile("/app/.env"):
    load_dotenv("/app/.env")
else:
    load_dotenv()


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wms_middleware.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
