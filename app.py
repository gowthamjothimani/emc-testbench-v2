from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
import minimalmodbus
import threading
from eeprom import EEPROM
import json
from datetime import datetime
import time
import math
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
log_exporter = LogExporter(controller, mqtt_client, socketio)
card_reader = CardReader(socketio, log_exporter)


# ========== GAS SENSOR CONFIGURATION ==========
gas_test_running = False
selected_sensor = None
last_sensor_reading = None

def gas_test():
    global gas_test_running, selected_sensor, last_sensor_reading
    while gas_test_running:
        if selected_sensor:
            value = selected_sensor.read_sensor()
            last_sensor_reading = value
            log_exporter.update_sensor_status(selected_sensor, last_sensor_reading)

            if value is not None:
                if isinstance(value, list) and len(value) > 2:
                    if 0 < value[2] < 1024:
                        socketio.emit('sensor_status', {'state': 'working', 'color': 'lightgreen'})
                    else:
                        socketio.emit('sensor_status', {'state': 'error', 'color': 'lightcoral'})
                elif isinstance(value, int):
                    if selected_sensor.sensor_type == "Drager X-Zone":
                        if value == 0:
                            socketio.emit('sensor_status', {'state': 'working', 'color': 'lightgreen'})
                        else:
                            socketio.emit('sensor_status', {'state': 'error', 'color': 'lightcoral'})
                    else:
                        if value > 0:
                            socketio.emit('sensor_status', {'state': 'working', 'color': 'lightgreen'})
                        else:
                            socketio.emit('sensor_status', {'state': 'error', 'color': 'lightcoral'})
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
        socketio.emit('update_status', {
            'cpu': cpu_usage,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        time.sleep(1)

def safe_clean(raw):
    if not raw:
        return b""
    arr = bytearray(raw)

    while arr and (arr[-1] == 0xFF or arr[-1] == 0x00):
        arr.pop()

    return bytes(arr)



def _clear_eeprom_range(start_addr, end_addr, block_size=64):
    length = end_addr - start_addr
    if length <= 0:
        return

    blank = [0xFF] * block_size
    addr = start_addr

    while addr < end_addr:
        eeprom.write_protect(False)     # allow write
        eeprom.write_eeprom(addr, blank)
        time.sleep(0.007)               # mandatory delay
        eeprom.write_protect(True)      # protect after
        addr += block_size




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

@app.route('/submittestinfo', methods=['POST'])
def submittestinfo():
    global tester_info_submitted,testername,pcbserial,modelnumber,projectdetail
    testername = request.form.get('testername')
    pcbserial = request.form.get('serialnumber')
    modelnumber = request.form.get('modelnumber')
    projectdetail = request.form.get('projectdetail')

    # Update LogExporter test details accordingly
    log_exporter.set_test_details(
        testername=testername,
        pcbserial=pcbserial,
        modelnumber=modelnumber,
        projectdetail=projectdetail
    )
    # Store in global state if needed
    tester_info_submitted = True
    # Redirect to main app page to start tests
    return redirect(url_for('home'))


@app.route('/write_eeprom_full', methods=['POST'])
def write_eeprom_full():
    try:
        payload = request.get_json() or {}
        uuid = payload.get("uuid", "UNKNOWN")
        hw = payload.get("hw", "UNKNOWN")
        timestamp = payload.get("timestamp") or datetime.now().isoformat()
        qc_status = payload.get("qc_status", "FAILED")
        qc_reasons = payload.get("qc_fail_reasons", [])
        full_log = payload.get("full_log")
        try:
            env = get_temp_hum()
            cpu_now = psutil.cpu_percent()

            # If get_temp_hum returns a string, try parsing it
            if isinstance(env, str):
                try:
                    env = json.loads(env)
                except:
                    env = {}

            temperature = env.get("temperature")
            humidity = env.get("humidity")

            log_exporter.set_environment_data(temperature, humidity, cpu_now)

        except Exception as e:
            print("Env update failed:", e)


        # ----------- Build Device Info -----------
        device_info = {
            "UUID": uuid,
            "HW": hw,
            "timestamp": timestamp,
            "qc_status": qc_status
        }

        # ----------- Build Log -----------
        if not full_log:
            full_log = log_exporter.get_last_log()

        full_log["qc_status"] = qc_status
        if qc_reasons:
            full_log["qc_fail_reasons"] = qc_reasons

        # ----------- Combine Into Single JSON -----------
        combined = {
            "device_info": device_info,
            "log_report": full_log
        }

        combined_bytes = json.dumps(combined, default=str).encode("utf-8")

        # EEPROM region for combined data
        EEPROM_START = 0x0200
        EEPROM_END   = 0x0900
        EEPROM_SIZE  = EEPROM_END - EEPROM_START

        # ------------- CLEAR EEPROM BLOCK -------------
        _clear_eeprom_range(EEPROM_START, EEPROM_END)

        # ------------- PAGE-SAFE WRITE -------------
        PAGE = 32
        addr = EEPROM_START
        idx = 0

        while idx < len(combined_bytes):
            chunk = list(combined_bytes[idx : idx + PAGE])
            eeprom.write_protect(False)
            eeprom.write_eeprom(addr, chunk)
            time.sleep(0.007)  # 7ms write cycle
            eeprom.write_protect(True)

            addr += len(chunk)
            idx += PAGE


        # ----------- Pad Remaining Space -----------
        written_len = len(combined_bytes)
        if written_len < EEPROM_SIZE:
            pad_len = EEPROM_SIZE - written_len
            eeprom.write_protect(True)
            eeprom.write_eeprom(EEPROM_START + written_len, [0xFF] * pad_len)
            eeprom.write_protect(False)

        # ----------- DEBUG READBACK -----------
        raw = eeprom.read_eeprom(EEPROM_START, EEPROM_SIZE)
        cleaned = bytes([b for b in raw if b not in (0x00, 0xFF)])

        print("\n========== EEPROM COMBINED JSON DEBUG ==========")
        print("RAW:", list(raw[:200]))
        try:
            print("CLEAN:", cleaned.decode())
        except:
            print("CLEAN: <Decode Error>")
        print("================================================\n")

        return jsonify({
            "status": "success",
            "message": "Single-block EEPROM written successfully",
            "device_info": device_info
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



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

@app.route('/save_board_inspection', methods=['POST'])
def save_board_inspection():
    data = request.get_json()
    visual = data.get("visual", "error")
    electrical = data.get("electrical", "error")
    board_log = {
        "visual": visual,
        "electrical": electrical
    }
    try:
        log_exporter.set_board_inspection(board_log)
        return jsonify({
            "status": "success",
            "message": "Board inspection results saved successfully."
        })
    except Exception as e:
        print("Error saving board inspection log:", e)
        return jsonify({
            "status": "error",
            "message": f"Failed to save board inspection log: {e}"
        })


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
        qc_status = data.get("qc_status", "FAILED")

        # Just record inside log_exporter, nothing else
        log_exporter.set_state("qc", "qc_status", qc_status)

        return jsonify({
            "status": "success",
            "message": "QC status recorded (no EEPROM writes)",
            "qc_status": qc_status
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route('/device_info', methods=['GET'])
def device_info():
    try:
        EEPROM_START = 0x0200
        EEPROM_END   = 0x0900
        EEPROM_SIZE  = EEPROM_END - EEPROM_START

        raw = eeprom.read_eeprom(EEPROM_START, EEPROM_SIZE)
        cleaned = safe_clean(raw)

        if not cleaned:
            return jsonify({"status": "success", "device_info": {}, "log_report": {}})

        try:
            combined = json.loads(cleaned.decode("utf-8"))
        except Exception as e:
            return jsonify({
                "status": "success",
                "device_info": {"error": f"Invalid JSON: {e}"},
                "log_report": {}
            })

        return jsonify({
            "status": "success",
            "device_info": combined.get("device_info", {}),
            "log_report": combined.get("log_report", {})
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})



@app.route('/get_test_info', methods=['GET'])
def get_test_info():
    return jsonify(log_exporter.test_details)

@app.route('/get_last_log')
def get_last_log():
    return jsonify(log_exporter.get_last_log())


# ========== BACKGROUND THREADS ==========
def start_monitoring():
    threading.Thread(target=monitor_fuse_and_gas_n, daemon=True).start()
    threading.Thread(target=system_status, daemon=True).start()

if __name__ == '__main__':
    start_monitoring()
    mqtt_client.connect_mqtt()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)