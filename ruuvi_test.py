import os
import asyncio
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

async def main():
    async for found_data in RuuviTagSensor.get_data_async():
        print(f"MAC: {found_data[0]}")
        print(f"Data: {found_data[1]}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())