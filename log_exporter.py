import psutil
import time
from sensor_reader import get_temp_hum

class LogExporter:
    def __init__(self, controller, mqtt_client,socketio):
        self.controller = controller
        self.mqtt_client = mqtt_client
        self.socketio = socketio
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
        self.test_details = {}
        self.board_inspection = {"visual": "not tested", "electrical": "not tested"}
        self.qc_status = "NOT_RUN"
        self.qc_fail_reasons = []

    def update_sensor_status(self, sensor, last_reading):
        if sensor:
            self.sensor_type = sensor.sensor_type
            value = last_reading

            if isinstance(value, list) and len(value) > 2:
                if 0 < value[2] < 1024:
                    self.sensor_status = "working"
                else:
                    self.sensor_status = "error"

            elif isinstance(value, int):
                if self.sensor_type == "Drager X-Zone":
                    self.sensor_status = "working" if value == 0 else "error"
                else:
                    self.sensor_status = "working" if value > 0 else "error"

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
        elif category == "alarm":
            self.alarm_states[key] = value

    def set_card_data(self, in_reader, out_reader):
        self.card_reader_data["in-reader"] = in_reader
        self.card_reader_data["out-reader"] = out_reader

    def set_qc_status(self, status, reasons=None):
        self.qc_status = status
        self.qc_fail_reasons = reasons or []


    def set_environment_data(self, temperature, humidity, cpu):
        self.env_data["temperature"] = temperature
        self.env_data["humidity"] = humidity
        self.env_data["cpu"] = cpu

    def set_test_details(self, testername, pcbserial, modelnumber=None, projectdetail=None):
        self.test_details = {
            "testername": testername,
            "pcbserial": pcbserial,
            "modelnumber": modelnumber,
            "projectdetail": projectdetail
        }

    def set_board_inspection(self, board_log):
            """Save board inspection results into the current log session."""
            self.board_inspection["visual"] = board_log.get("visual", "no")
            self.board_inspection["electrical"] = board_log.get("electrical", "no")
            print("Board inspection saved:", self.board_inspection)

    def get_last_log(self):
        return {
            "system-check": {
                "cpu-usage": self.env_data["cpu"],
                "temperature": self.env_data["temperature"],
                "humidity": self.env_data["humidity"],
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            },
            "board-inspection-status": self.board_inspection, 
            "gas-status": {
                "gas-type": self.sensor_type,
                "sensor-status": self.sensor_status
            },
            "efuse-turn-on-status": self.efuse_on_states,
            "efuse-turn-off-status": self.efuse_off_states,
            "card-reader-status": self.card_reader_data,
            "relay-status": self.relay_states,
            "alarm-status": self.alarm_states,
             "qc_status": self.qc_status,
             "qc_fail_reasons": self.qc_fail_reasons
        }

    def export_log(self):
        try:
            data = {
                "test_details": self.test_details,
                "system-check": {
                    "cpu-usage": self.env_data["cpu"],  
                    "temperature": self.env_data["temperature"],
                    "humidity": self.env_data["humidity"],
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }, 
                "board-inspection-status": self.board_inspection, 
                "gas-status": {
                    "gas-type": self.sensor_type,
                    "sensor-status": self.sensor_status
                },
                "efuse-turn-on-status": self.efuse_on_states,
                "efuse-turn-off-status": self.efuse_off_states,
                "card-reader-status": self.card_reader_data,
                "relay-status": self.relay_states,
                "alarm-status": self.alarm_states,
                "qc_status": self.qc_status,
            "qc_fail_reasons": self.qc_fail_reasons
            }
            self.mqtt_client.publish_data(data)
            self.socketio.emit("mqtt_publish_result", {
                "success": True,
                "message": "Log published successfully!"
            })

        except Exception as e:
            print("Export log failed:", e)
            self.socketio.emit("mqtt_publish_result", {
                "success": False,
                "message": "MQTT publish failed!"
            })

