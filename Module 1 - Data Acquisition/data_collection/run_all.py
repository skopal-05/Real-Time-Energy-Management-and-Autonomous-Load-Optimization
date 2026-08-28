from __future__ import annotations

from battery import generate_battery
from boiler import generate_boiler
from grid import generate_grid
from production import generate_production_line
from solar import generate_solar
from weather import generate_weather
from compressor import generate_compressor
from hvac import generate_hvac    # <-- ADD THIS


def main() -> None:
    outputs = [
        generate_production_line("production_line_a"),
        generate_production_line("production_line_b"),
        generate_boiler(),
        generate_compressor(),
        generate_hvac(),          # <-- ADD THIS
        generate_solar(),
        generate_battery(),
        generate_grid(),
        generate_weather(),
    ]

    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()