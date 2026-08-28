"""
Integration Test for the Complete Digital Twin System.
"""

import json

from integration.system_sync import SystemSync
from integration.json_validation import JSONValidator


def run_integration_test():
    """
    Runs one complete integration cycle.
    """

    system = SystemSync()

    # Synchronize all digital twins
    output = system.sync_once()

    # Validate JSON
    if JSONValidator.is_valid(output):
        print("Integration Successful")
        print(json.dumps(output, indent=4))
    else:
        print("Integration Failed: Invalid JSON")


if __name__ == "__main__":
    run_integration_test()