import os
import asyncio
import requests
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from datetime import datetime, timezone
from dotenv import load_dotenv

# Static threshold value
THRESHOLD = 1000

async def main():
    async for found_data in RuuviTagSensor.get_data_async():
        mac = found_data[0]
        data = found_data[1]
        
        # Use the "acceleration" key from the data.
        acceleration = data.get('acceleration')
        # Ensure acceleration is a number; if not, default to 0.
        if acceleration is None:
            acceleration = 0
        
        # Determine state based on static threshold.
        if acceleration > THRESHOLD:
            state = "running"
        else:
            state = "idle"
        
        payload = {"ruuvi_id": mac, "state": state, "payload": data}
        
        # Try to send the payload to the server running on localhost.
        try:
            response = await asyncio.to_thread(requests.post, "http://localhost:5100/update_status", json=payload)
            html_code = response.text
            status_code = response.status_code
        except Exception as e:
            html_code = f"Error connecting to server: {e}"
            status_code = "N/A"
        
        print(f"Sent payload for {mac}: {payload}, HTTP {status_code}, Response HTML: {html_code}", flush=True)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())