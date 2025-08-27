import paho.mqtt.client as mqtt
import pandas as pd
import json
import os
from datetime import datetime

# ===== MQTT CONFIG =====
MQTT_BROKER = "10.30.250.241"  
MQTT_PORT = 1883
MQTT_TOPIC = "emc_test"

# ===== CSV FILE =====
CSV_FILE = "emc_test_log.csv"

# ===== MQTT CALLBACKS =====
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        # Decode and parse JSON
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)

        # Flatten nested JSON into a single-level dict
        flat_data = flatten_json(data)
        
        # Add receive timestamp
        flat_data["received_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append to CSV
        save_to_csv(flat_data)

        print(f" Data logged: {flat_data}")

    except Exception as e:
        print(f"Error processing message: {e}")

# ===== FLATTEN JSON =====
def flatten_json(y):
    """Flatten nested JSON into a single dictionary."""
    out = {}

    def flatten(x, name=""):
        if isinstance(x, dict):
            for a in x:
                flatten(x[a], f"{name}{a}_")
        elif isinstance(x, list):
            i = 0
            for a in x:
                flatten(a, f"{name}{i}_")
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

# ===== SAVE TO CSV =====
def save_to_csv(row_dict):
    # Create DataFrame for one row
    df = pd.DataFrame([row_dict])

    if not os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE, index=False)
    else:
        df.to_csv(CSV_FILE, mode="a", header=False, index=False)

# ===== MAIN =====
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to broker
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

    # Loop forever
    client.loop_forever()

if __name__ == "__main__":
    main()
