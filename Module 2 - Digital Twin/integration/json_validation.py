import json


class JSONValidator:
    """
    Validates Digital Twin outputs before integration.
    """

    @staticmethod
    def is_valid(data):
        """
        Check whether the given data is JSON serializable.

        Args:
            data (dict): Output from Digital Twin modules.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            json.dumps(data)
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def validate_required_keys(data, required_keys):
        """
        Check if all required keys exist in the data.

        Args:
            data (dict): JSON data.
            required_keys (list): List of required keys.

        Returns:
            bool: True if all keys exist, False otherwise.
        """
        return all(key in data for key in required_keys)