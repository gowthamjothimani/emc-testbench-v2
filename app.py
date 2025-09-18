from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
import minimalmodbus
import threading
from eeprom import EEPROM
import json
from datetime import datetime
import time
import psutil
from emc_board import EMC_Board
from card_reader import CardReader
from mqtt_client import MQTTClient
from gas_sensor import GasSensor
from log_exporter import LogExporter  
from sensor_reader import get_temp_hum

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize components
controller = EMC_Board()
eeprom = EEPROM()
mqtt_client = MQTTClient(socketio)
tester_info_submitted = False
fuse_check_running = True
log_exporter = LogExporter(controller, mqtt_client)
log_exporter = LogExporter(controller, mqtt_client)
card_reader = CardReader(socketio, log_exporter)


# ========== GAS SENSOR CONFIGURATION ==========
gas_test_running = False
selected_sensor = None 
last_sensor_reading = None

def gas_test():
    global gas_test_running, selected_sensor
    while gas_test_running:
        if selected_sensor:
            value = selected_sensor.read_sensor()
            last_sensor_reading = value
            log_exporter.update_sensor_status(selected_sensor, last_sensor_reading) 

            if value:
                if isinstance(value, list) and len(value) > 2 and 0 < value[2] < 1024:
                    socketio.emit('sensor_status', {'state': 'working', 'color': 'lightgreen'})
                elif isinstance(value, int) and value > 0:
                    socketio.emit('sensor_status', {'state': 'working', 'color': 'lightgreen'})
                else:
                    socketio.emit('sensor_status', {'state': 'error', 'color': 'lightcoral'})
            else:
                socketio.emit('sensor_status', {'state': 'error', 'color': 'lightcoral'})
        time.sleep(1)

def monitor_fuse_and_gas_n():
    global fuse_check_running
    while fuse_check_running:
        try:
            gas_fault = controller.read_gas_efuse()
            badge_fault = controller.read_badge_efuse()
            alarm_fault = controller.read_alarm_efuse()
            gas_in = controller.read_gas_power_in()

            socketio.emit('gas_fault', {'status': gas_fault, 'color': 'lightgreen'})
            socketio.emit('badge_fault', {'status': badge_fault, 'color': 'lightgreen'})
            socketio.emit('alarm_fault', {'status': alarm_fault, 'color': 'lightgreen'})
            socketio.emit('gas_in', {'status': gas_in, 'color': 'lightgreen'})
        except Exception as e:
            print(f"Error reading values: {e}")
        time.sleep(1)

def system_status():
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        try:
            from sensor_reader import get_temp_hum
            temp_data = get_temp_hum()
            temp = temp_data.get("temperature")
            hum = temp_data.get("humidity")
        except:
            temp, hum = None, None

        log_exporter.set_environment_data(temp, hum, cpu_usage)
        socketio.emit('update_status', {'cpu': cpu_usage})
        time.sleep(10)


# ========== TEMP & HUM SENSOR DATA =========
@app.route('/read_sensors')
def read_sensors():
    return get_temp_hum()

# ========== FLASK ROUTES ==========
@app.route('/')
def home():
    if not tester_info_submitted:
        return redirect(url_for('tester_info'))
    return render_template('index.html')

@app.route('/tester_info')
def tester_info():
    return render_template('tester_info.html')

def submit_test_info():
    global tester_info_submitted
    tester_name = request.form['tester_name']
    pcb_serial = request.form['pcb_serial']
    hardware_provider = request.form['hardware_provider']
    hardware_type = request.form['hardware_type']

    log_exporter.set_test_details(
        tester_name, 
        pcb_serial, 
        hardware_provider, 
        hardware_type
    )
    tester_info_submitted = True
    return redirect(url_for('home'))

# ========== SENSOR SELECTION ==========
@socketio.on('select_gas_sensor')
def select_gas_sensor(data):
    global selected_sensor
    sensor_type = data.get("sensor_type")

    if sensor_type and sensor_type in ["Blackline EXO", "Drager X-Zone"]:
        selected_sensor = GasSensor(sensor_type)
        print(f"Selected Gas Sensor: {sensor_type}")
        socketio.emit('sensor_selected', {"sensor": sensor_type, "message": f"Sensor {sensor_type} selected!"})
    else:
        selected_sensor = None
        socketio.emit('sensor_selected', {"sensor": None, "message": "No sensor selected!"})


# ========== START/STOP TESTS ==========
@socketio.on('start_all_tests')
def start_all_tests():
    global gas_test_running
    if not gas_test_running:
        gas_test_running = True
        threading.Thread(target=gas_test, daemon=True).start()

    card_reader.start_card_test()

@socketio.on('stop_all_tests')
def stop_all_tests():
    """Stops all active test threads."""
    global gas_test_running
    gas_test_running = False
    card_reader.stop_card_test()


# ========== EMC BOARD CONTROL ==========
@app.route('/control/efuse_gas_on')
def efuse_gas_on():
    controller.turn_on_efuse_gas()
    return 'Gas eFuse On'

@app.route('/control/efuse_gas_off')
def efuse_gas_off():
    controller.turn_off_efuse_gas()
    return 'Gas eFuse Off'

@app.route('/control/efuse_badge_on')
def efuse_badge_on():
    controller.turn_on_efuse_badge()
    return 'Badge eFuse On'

@app.route('/control/efuse_badge_off')
def efuse_badge_off():
    controller.turn_off_efuse_badge()
    return 'Badge eFuse Off'

@app.route('/control/efuse_alarm_on')
def efuse_alarm_on():
    controller.turn_on_efuse_alarm()
    return 'Alarm eFuse On'

@app.route('/control/efuse_alarm_off')
def efuse_alarm_off():
    controller.turn_off_efuse_alarm()
    return 'Alarm eFuse Off'

@app.route('/control/lamp_badge_on')
def lamp_badge_on():
    controller.turn_on_badge_lamp()
    return 'Badge Lamp On'

@app.route('/control/lamp_badge_off')
def lamp_badge_off():
    controller.turn_off_badge_lamp()
    return 'Badge Lamp Off'

@app.route('/control/lamp_alarm_red_on')
def lamp_alarm_red_on():
    controller.turn_on_alarm_red_lamp()
    return 'Alarm Red Lamp On'

@app.route('/control/lamp_alarm_red_off')
def lamp_alarm_red_off():
    controller.turn_off_alarm_red_lamp()
    return 'Alarm Red Lamp Off'

@app.route('/control/lamp_alarm_green_on')
def lamp_alarm_green_on():
    controller.turn_on_alarm_green_lamp()
    return 'Alarm Green Lamp On'

@app.route('/control/lamp_alarm_green_off')
def lamp_alarm_green_off():
    controller.turn_off_alarm_green_lamp()
    return 'Alarm Green Lamp Off'

@app.route('/control/alarm_sound_on')
def alarm_sound_on():
    controller.turn_on_alarm_sound()
    return 'Alarm Sound On'

@app.route('/control/alarm_sound_off')
def alarm_sound_off():
    controller.turn_off_alarm_sound()
    return 'Alarm Sound Off'

# ========== MQTT CONFIGURATION ==========
@app.route('/get_mqtt_config', methods=['GET'])
def get_mqtt_config():
    return jsonify(mqtt_client.mqtt_config)

@app.route('/update_mqtt', methods=['POST'])
def update_mqtt():
    config = request.json
    mqtt_client.update_config(config)
    return jsonify({"message": "MQTT configuration updated!"})

# ========== MQTT PUBLISH ==========
@socketio.on('export_log')
def export_log():
    temp_hum = get_temp_hum()
    if isinstance(temp_hum, str):
        try:
            import json
            temp_hum = json.loads(temp_hum)
        except Exception as e:
            print(f"Failed to parse temp_hum JSON: {e}")
            temp_hum = {}

    temperature = temp_hum.get("temperature")
    humidity = temp_hum.get("humidity")
    cpu_usage = psutil.cpu_percent()
    log_exporter.set_environment_data(temperature, humidity, cpu_usage)
    log_exporter.export_log()

# ========== STATUS UPDATE ==============
@socketio.on('efuse_status_update')
def handle_efuse_update(data):
    action = data.get('action', '')
    status = data.get('status', '')
    if "on" in action:
        log_exporter.set_state("on", action, status)
    elif "off" in action:
        log_exporter.set_state("off", action, status)

@socketio.on('relay_status_update')
def handle_relay_update(data):
    action = data.get('action', '')
    status = data.get('status', '')
    log_exporter.set_state("relay", action, status)

@socketio.on('alarm_status_update')
def handle_relay_update(data):
    action = data.get('action', '')
    status = data.get('status', '')
    log_exporter.set_state("alarm", action, status)

    
# ========== QC STATUS ==============
@app.route('/qc_status', methods=['POST'])
def qc_status():
    try:
        data = request.json
        qc_status = data.get("qc_status") 
        hardware_provider = data.get("hardware_provider", "unknown")
        hardware_type = data.get("hardware_type", "unknown")
        serial_num = data.get("serial_number", "0000")

        provider_map = {
            "VISICS": "VIS",
            "Total Safety": "ORION"
        }
        provider_prefix = provider_map.get(hardware_provider, hardware_provider.upper())

        final_serial = f"{provider_prefix}-{hardware_type}-{serial_num}"

        device_info = {
            "serial_number": final_serial,
            "qc_status": qc_status,
            "tested_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        eeprom.write_protect(True)
        eeprom.write_eeprom(0x0000, [0xFF] * 250)

        json_bytes = json.dumps(device_info).encode("utf-8")
        eeprom.write_eeprom(0x0000, list(json_bytes))

        eeprom.write_protect(False)

        return jsonify({"status": "success", "data": device_info})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    
@app.route('/device_info', methods=['GET'])
def device_info():
    try:
        raw_data = eeprom.read_eeprom(0x0000, 250)
        # Strip trailing 0xFF
        clean_bytes = bytes([b for b in raw_data if b != 0xFF])
        if not clean_bytes:
            return jsonify({"status": "empty", "message": "No data in EEPROM"})

        # Decode JSON
        device_info = json.loads(clean_bytes.decode("utf-8"))
        return jsonify({"status": "success", "data": device_info})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== BACKGROUND THREADS ==========
def start_monitoring():
    threading.Thread(target=monitor_fuse_and_gas_n, daemon=True).start()
    threading.Thread(target=system_status, daemon=True).start()

if __name__ == '__main__':
    start_monitoring()
    mqtt_client.connect_mqtt()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
