"""
CSV Loader for streaming Module 1 sensor data into Module 2.
"""

from pathlib import Path
import csv


class CSVLoader:
    """
    Streams one CSV row at a time.

    Each call to get_next_row() returns the next sensor reading.
    When the end of the file is reached, it automatically
    starts again from the beginning.
    """

    def __init__(self, csv_path):
        self.csv_path = Path(csv_path)

        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")

        self._open_file()

    def _open_file(self):
        """Open the CSV file and initialize the reader."""
        self.file = open(
            self.csv_path,
            mode="r",
            newline="",
            encoding="utf-8",
        )
        self.reader = csv.DictReader(self.file)

    def get_next_row(self):
        """
        Return the next row from the CSV.

        If EOF is reached, restart from the beginning.
        """

        try:
            return next(self.reader)

        except StopIteration:
            self.file.seek(0)
            self.reader = csv.DictReader(self.file)
            return next(self.reader)

    def reset(self):
        """
        Restart reading from the beginning.
        """
        self.file.seek(0)
        self.reader = csv.DictReader(self.file)

    def close(self):
        """
        Close the CSV file.
        """
        if hasattr(self, "file") and not self.file.closed:
            self.file.close()

    def __del__(self):
        self.close()