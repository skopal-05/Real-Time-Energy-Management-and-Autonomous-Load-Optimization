"""
Run the Digital Twin continuously in realtime.
"""

import json
import time

from integration.system_sync import SystemSync
from common.config import SAMPLING_INTERVAL


def main():
    system = SystemSync()

    print("Starting Realtime Digital Twin...")
    print("Press Ctrl + C to stop.\n")

    try:
        while True:
            output = system.sync_once()

            print(json.dumps(output, indent=4))

            time.sleep(SAMPLING_INTERVAL)

    except KeyboardInterrupt:
        print("\nRealtime simulation stopped.")


if __name__ == "__main__":
    main()