import psutil
import time
from sensor_reader import get_temp_hum

class LogExporter:
    def __init__(self, controller, mqtt_client):
        self.controller = controller
        self.mqtt_client = mqtt_client
        self.tester_name = ""
        self.pcb_serial_number = ""
        self.sensor_status = "No sensor selected"
        self.sensor_type = "Unknown"
        self.efuse_on_states = {}
        self.efuse_off_states = {}
        self.relay_states = {}
        self.alarm_states = {}
        self.card_reader_data = {"in-reader": "--", "out-reader": "--"}
        self.env_data = {"temperature": None, "humidity": None, "cpu": None}

    def update_sensor_status(self, sensor, last_reading):
        if sensor:
            self.sensor_type = sensor.sensor_type
            value = last_reading
            if value and isinstance(value, (list, int)) and (
                (isinstance(value, list) and len(value) > 2 and 0 < value[2] < 1024)
                or (isinstance(value, int) and value > 0)
            ):
                self.sensor_status = "working"
            else:
                self.sensor_status = "error"
        else:
            self.sensor_status = "No sensor selected"
            self.sensor_type = "Unknown"

    def set_state(self, category, key, value):
        if category == "on":
            self.efuse_on_states[key] = value
        elif category == "off":
            self.efuse_off_states[key] = value
        elif category == "relay":
            self.relay_states[key] = value
        elif category =="alarm":
            self.alarm_states[key] = value


    def set_card_data(self, in_reader, out_reader):
        self.card_reader_data["in-reader"] = in_reader
        self.card_reader_data["out-reader"] = out_reader

    def set_environment_data(self, temperature, humidity, cpu):
        self.env_data["temperature"] = temperature
        self.env_data["humidity"] = humidity
        self.env_data["cpu"] = cpu

    def set_test_details(self, tester_name, pcb_serial, hardware_provider, hardware_type):
        self.test_details = {
            "tester_name": tester_name,
            "pcb_serial": pcb_serial,
            "hardware_provider": hardware_provider,
            "hardware_type": hardware_type
        }

    def export_log(self):
        data = {
                "test_details": self.test_details,
            "system-check": {
                "cpu-usage": self.env_data["cpu"],
                "temperature": self.env_data["temperature"],
                "humidity": self.env_data["humidity"],
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            },
            "gas-status": {
                "gas-type": self.sensor_type,
                "sensor-status": self.sensor_status
            },
            "efuse-turn-on-status": self.efuse_on_states,
            "efuse-turn-off-status": self.efuse_off_states,
            "card-reader-status": self.card_reader_data,
            "relay-status": self.relay_states,
            "alarm-status":self.alarm_states
        }
        self.mqtt_client.publish_data(data)
        
