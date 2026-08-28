from common.config import MODULE1_OUTPUT_DIRECTORY
from common.csv_loader import CSVLoader
from production_line_a import ProductionLineADigitalTwin
from production_line_b import ProductionLineBDigitalTwin

from boiler import BoilerDigitalTwin
from solar import SolarDigitalTwin
from battery import BatteryDigitalTwin
from grid import GridDigitalTwin

from hvac import HVACDigitalTwin
from compressor import CompressorDigitalTwin


class SystemSync:
    """
    Synchronizes all Digital Twin modules.
    """

    def __init__(self):
        self.production_line_a = ProductionLineADigitalTwin()
        self.production_line_b = ProductionLineBDigitalTwin()

        self.boiler = BoilerDigitalTwin()
        self.solar = SolarDigitalTwin()
        self.battery = BatteryDigitalTwin()
        self.grid = GridDigitalTwin()

        self.hvac = HVACDigitalTwin()
        self.compressor = CompressorDigitalTwin()

        # CSV Loaders
        self.production_line_a_loader = CSVLoader(
            MODULE1_OUTPUT_DIRECTORY / "production_line_a_production.csv"
        )

        self.production_line_b_loader = CSVLoader(
            MODULE1_OUTPUT_DIRECTORY / "production_line_b_production.csv"
        )

        self.boiler_loader = CSVLoader(
            MODULE1_OUTPUT_DIRECTORY / "boiler.csv"
        )

        self.compressor_loader = CSVLoader(
            MODULE1_OUTPUT_DIRECTORY / "compressor.csv"
        )

        self.hvac_loader = CSVLoader(
            MODULE1_OUTPUT_DIRECTORY / "hvac.csv"
        )

        self.solar_loader = CSVLoader(
            MODULE1_OUTPUT_DIRECTORY / "solar_plant.csv"
        )

        self.battery_loader = CSVLoader(
            MODULE1_OUTPUT_DIRECTORY / "battery_storage.csv"
        )

        self.grid_loader = CSVLoader(
            MODULE1_OUTPUT_DIRECTORY / "grid.csv"
        )

    def sync_once(self):

        self.production_line_a.update(
            self.production_line_a_loader.get_next_row()
        )

        self.production_line_b.update(
            self.production_line_b_loader.get_next_row()
        )

        self.boiler.update(
            self.boiler_loader.get_next_row()
        )

        self.compressor.update(
            self.compressor_loader.get_next_row()
        )

        self.hvac.update(
            self.hvac_loader.get_next_row()
        )

        self.solar.update(
            self.solar_loader.get_next_row()
        )

        self.battery.update(
            self.battery_loader.get_next_row()
        )

        self.grid.update(
            self.grid_loader.get_next_row()
        )

        return {
            "production_line_a": self.production_line_a.state_manager.snapshot(),
            "production_line_b": self.production_line_b.state_manager.snapshot(),
            "boiler": self.boiler.state_manager.snapshot(),
            "compressor": self.compressor.state_manager.snapshot(),
            "hvac": self.hvac.state_manager.snapshot(),
            "solar": self.solar.state_manager.snapshot(),
            "battery": self.battery.state_manager.snapshot(),
            "grid": self.grid.state_manager.snapshot(),
        }