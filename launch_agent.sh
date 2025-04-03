#!/bin/bash

# Set the BLE adapter to use macOS CoreBluetooth
export RUUVI_BLE_ADAPTER="bluez"

# (Optional) Set other environment variables if needed
# export SOME_OTHER_VAR=value

# Run the agent
python3 agent.py