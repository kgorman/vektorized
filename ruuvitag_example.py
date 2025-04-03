import os
from pymongo import MongoClient
import asyncio
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get the MongoDB credentials from environment variables
MONGO_USERNAME = os.getenv('MONGO_USERNAME')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_CLUSTER = os.getenv('MONGO_CLUSTER')
MONGO_DB = os.getenv('MONGO_DB', 'ruuvi_data')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'sensor_data')

# Check if the credentials were loaded successfully
if not MONGO_USERNAME or not MONGO_PASSWORD:
    raise ValueError(
        "Missing MongoDB connection credentials in environment variables")

# Construct the MongoDB URI
MONGO_URI = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/{MONGO_DB}?retryWrites=true&w=majority"

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

# store data into mongodb
def store_data_in_mongo(mac_address, sensor_data):
    utc_datetime = datetime.now(tz=timezone.utc)
    document = {
        'time': utc_datetime,
        'mac_address': mac_address,
        'data': sensor_data
    }
    print(document)
    try:
        collection.insert_one(document)
        print(f"Inserted sensor data from {mac_address} into MongoDB")
    except Exception as e:
        print(f"Error inserting data into MongoDB: {e}")

async def main():
    async for found_data in RuuviTagSensor.get_data_async():
        print(f"MAC: {found_data[0]}")
        print(f"Data: {found_data[1]}")
        store_data_in_mongo(found_data[0], found_data[1])

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())