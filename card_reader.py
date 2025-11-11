import threading
import time
import Adafruit_BBIO.GPIO as GPIO
from flask_socketio import SocketIO
from log_exporter import LogExporter  

class CardReader:
    def __init__(self, socketio: SocketIO, log_exporter: LogExporter):
        self.socketio = socketio
        self.log_exporter = log_exporter
        self.card_test_running = False
        self.in_value_lock = threading.Lock()
        self.out_value_lock = threading.Lock()
        self.in_value = ""
        self.out_value = ""
        self.start_time_in = 0
        self.start_time_out = 0

        # IN Reader GPIOs
        self.in_first_gpio = "P8_14"
        self.in_second_gpio = "P8_16"
        GPIO.setup(self.in_first_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.in_second_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # OUT Reader GPIOs
        self.out_first_gpio = "P8_18"
        self.out_second_gpio = "P8_26"
        GPIO.setup(self.out_first_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.out_second_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Attach event listeners
        GPIO.add_event_detect(self.in_first_gpio, GPIO.RISING, callback=self.in_first_gpio_callback)
        GPIO.add_event_detect(self.in_second_gpio, GPIO.RISING, callback=self.in_second_gpio_callback)
        GPIO.add_event_detect(self.out_first_gpio, GPIO.RISING, callback=self.out_first_gpio_callback)
        GPIO.add_event_detect(self.out_second_gpio, GPIO.RISING, callback=self.out_second_gpio_callback)

    def decode_wiegand(self, bits):
        try:
            if len(bits) != 26:
                return None
            facility_code = str(int(bits[1:9], 2)).zfill(3)
            card_number = str(int(bits[9:25], 2)).zfill(5)
            return facility_code, card_number
        except Exception as e:
            print(f"Wiegand Decode Error: {e}")
            return None

    # Callback functions
    def in_second_gpio_callback(self, *args):
        with self.in_value_lock:
            if not self.in_value:
                self.start_time_in = time.monotonic_ns()
            self.in_value += "0"

    def in_first_gpio_callback(self, *args):
        with self.in_value_lock:
            if not self.in_value:
                self.start_time_in = time.monotonic_ns()
            self.in_value += "1"

    def out_second_gpio_callback(self, *args):
        with self.out_value_lock:
            if not self.out_value:
                self.start_time_out = time.monotonic_ns()
            self.out_value += "0"

    def out_first_gpio_callback(self, *args):
        with self.out_value_lock:
            if not self.out_value:
                self.start_time_out = time.monotonic_ns()
            self.out_value += "1"

def card_test(self):
    while self.card_test_running:
        time.sleep(0.1)

        # ---- IN Reader ----
        with self.in_value_lock:
            if self.in_value and (time.monotonic_ns() - self.start_time_in > 500_000_000):
                bit_count = len(self.in_value)
                if bit_count == 26:
                    result = self.decode_wiegand(self.in_value)
                    if result:
                        _, card_number = result
                        # ✅ UI update: show number, green background
                        self.socketio.emit('in_data', {
                            'in_number': card_number,
                            'status': 'working'
                        })
                        # ✅ Log only status
                        self.log_exporter.set_card_data(
                            in_reader="working",
                            out_reader=self.log_exporter.card_reader_data["out-reader"]
                        )
                    else:
                        self.socketio.emit('in_data', {'error': 'Decode error', 'status': 'error'})
                        self.log_exporter.set_card_data(in_reader="error", out_reader=self.log_exporter.card_reader_data["out-reader"])
                elif bit_count > 26:
                    # Too many bits = invalid
                    self.socketio.emit('in_data', {'error': 'Invalid length', 'status': 'error'})
                    self.log_exporter.set_card_data(in_reader="error", out_reader=self.log_exporter.card_reader_data["out-reader"])

                # Reset buffer
                self.in_value = ""

        # ---- OUT Reader ----
        with self.out_value_lock:
            if self.out_value and (time.monotonic_ns() - self.start_time_out > 500_000_000):
                bit_count = len(self.out_value)
                if bit_count == 26:
                    result = self.decode_wiegand(self.out_value)
                    if result:
                        _, card_number = result
                        self.socketio.emit('out_data', {
                            'out_number': card_number,
                            'status': 'working'
                        })
                        self.log_exporter.set_card_data(
                            in_reader=self.log_exporter.card_reader_data["in-reader"],
                            out_reader="working"
                        )
                    else:
                        self.socketio.emit('out_data', {'error': 'Decode error', 'status': 'error'})
                        self.log_exporter.set_card_data(in_reader=self.log_exporter.card_reader_data["in-reader"], out_reader="error")
                elif bit_count > 26:
                    self.socketio.emit('out_data', {'error': 'Invalid length', 'status': 'error'})
                    self.log_exporter.set_card_data(in_reader=self.log_exporter.card_reader_data["in-reader"], out_reader="error")

                # Reset buffer
                self.out_value = ""



    def start_card_test(self):
        if not self.card_test_running:
            self.card_test_running = True
            threading.Thread(target=self.card_test, daemon=True).start()

    def stop_card_test(self):
        self.card_test_running = False
