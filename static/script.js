var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

var selectedSensor = null;
document.addEventListener("DOMContentLoaded", function () {
    const sensorDropdown = document.getElementById("sensorSelect");
    sensorDropdown.innerHTML = `
        <option value="" disabled selected>Select a Sensor</option>
        <option value="Blackline EXO">Blackline EXO</option>
        <option value="Drager X-Zone">Drager X-Zone</option>
    `;
});

// Handle sensor selection
function selectSensor() {
    let sensorDropdown = document.getElementById("sensorSelect");
    let selectedOption = sensorDropdown.value;

    if (!selectedOption) {
        alert("Please select a valid sensor.");
        return;
    }

    let confirmSelection = confirm(`Confirm selection: ${selectedOption}?`);
    if (confirmSelection) {
        selectedSensor = selectedOption;
        socket.emit('select_gas_sensor', { sensor_type: selectedSensor });
    }
}

// Listen for sensor selection confirmation from backend
socket.on('sensor_selected', function (data) {
    alert(data.message);
    if (data.sensor) {
        document.getElementById("selectedSensorText").innerText = `Selected Sensor: ${data.sensor}`;
        document.getElementById("selectedSensorText").style.color = "green";
    } else {
        document.getElementById("selectedSensorText").innerText = "No Sensor Selected";
        document.getElementById("selectedSensorText").style.color = "red";
    }
});

        function showTab(tabId) {
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
        }

        function startGasTest() {
            socket.emit('start_gas_test');
        }

        function stopGasTest() {
            socket.emit('stop_gas_test');
        }

        function startCardTest() {
            socket.emit('start_card_test');
        }

        function stopCardTest() {
            socket.emit('stop_card_test');
        }

            // Card test data update
            socket.on('in_data', data => {
                    const el = document.getElementById('inData');
                    if (data.status === 'working') {
                        el.style.backgroundColor = 'lightgreen';
                    } else if (data.status === 'error') {
                        el.style.backgroundColor = 'lightcoral';
                    }
                    el.textContent = data.in_number || data.error || "--";
                });

                // Card test data update
                socket.on('out_data', data => {
                        const el = document.getElementById('outData');
                        if (data.status === 'working') {
                            el.style.backgroundColor = 'lightgreen';
                        } else if (data.status === 'error') {
                            el.style.backgroundColor = 'lightcoral';
                        }
                        el.textContent = data.out_number || data.error || "--";
                    });

                function controlEfuse(action) {
                    // Step 1: Actually perform the ON/OFF action first
                    fetch(`/control/${action}`)
                        .then(response => response.text())
                        .then(data => {
                            // Step 2: Now ask the user if it worked
                            let confirmMsg = `${action.replaceAll("_", " ")} is now done. Is it working?`;
                            let confirmed = confirm(confirmMsg);
                            let status = confirmed ? "working" : "error";

                            // Step 3: Emit status to backend
                            socket.emit('efuse_status_update', { action: action, status: status });
                        })
                        .catch(error => {
                            alert('Error controlling eFuse: ' + error);
                        });
                }

                function controlLamp(action) {
                    fetch(`/control/${action}`)
                        .then(response => response.text())
                        .then(data => {
                            let confirmMsg = `${action.replaceAll("_", " ")} is now done. Is it working?`;
                            let confirmed = confirm(confirmMsg);
                            let status = confirmed ? "working" : "error";
                            socket.emit('relay_status_update', { action: action, status: status });
                        })
                        .catch(error => {
                            alert('Error controlling Lamp: ' + error);
                        });
                }

                function controlAlarm(action) {
                    fetch(`/control/${action}`)
                        .then(response => response.text())
                        .then(data => {
                            let confirmMsg = `${action.replaceAll("_", " ")} is now done. Is it working?`;
                            let confirmed = confirm(confirmMsg);
                            let status = confirmed ? "working" : "error";
                            socket.emit('alarm_status_update', { action: action, status: status });
                        })
                        .catch(error => {
                            alert('Error controlling sound: ' + error);
                        });
                }


            socket.on('sensor_status', function(data) {
            document.getElementById("gasData").innerText = data.state;
            document.getElementById("gasData").style.backgroundColor = data.color;
        });

        socket.on('gas_fault', function(data) {
            document.getElementById("gasState").innerText = data.status;
            document.getElementById("gasState").style.backgroundColor = data.color;
        });
        socket.on('badge_fault', function(data) {
            document.getElementById("badgeState").innerText = data.status;
            document.getElementById("badgeState").style.backgroundColor = data.color;
        });
        socket.on('alarm_fault', function(data) {
            document.getElementById("alarmState").innerText = data.status;
            document.getElementById("alarmState").style.backgroundColor = data.color;
        });
        socket.on('gas_in', function(data) {
            document.getElementById("gasIn").innerText = data.status;
            document.getElementById("gasIn").style.backgroundColor = data.color;
        });

        socket.on("update_status", function (data) {
        document.getElementById("cpu_usage").innerText = data.cpu + "%";
       });

       function startTest() {
        socket.emit('start_all_tests');
    }

    function stopTest() {
        socket.emit('stop_all_tests');
    }

    socket.on('mqtt_status', function(data) {
        document.getElementById('networkIcon').style.color = data.color;
    });

  function openMQTTConfig() {
    fetch('/get_mqtt_config')
        .then(response => response.json())
        .then(config => {
            document.getElementById('mqtt_hostname').value = config.hostname || '';
            document.getElementById('mqtt_port').value = config.port || '';
            document.getElementById('mqtt_topic').value = config.topic || '';
            document.getElementById('mqtt_username').value = config.username || '';
            document.getElementById('mqtt_password').value = config.password || '';
        })
        .catch(error => {
            console.error("Failed to load MQTT config:", error);
        });

    document.getElementById('mqttConfigModal').style.display = "block";
}


    function closeMQTTConfig() {
        document.getElementById('mqttConfigModal').style.display = "none";
    }

    function saveMQTTConfig() {
        let config = {
            hostname: document.getElementById('mqtt_hostname').value,
            port: parseInt(document.getElementById('mqtt_port').value),
            topic: document.getElementById('mqtt_topic').value,
            username: document.getElementById('mqtt_username').value,
            password: document.getElementById('mqtt_password').value
        };
        fetch('/update_mqtt', { method: 'POST', body: JSON.stringify(config), headers: {'Content-Type': 'application/json'}})
            .then(response => response.json())
            .then(data => console.log(data));
        closeMQTTConfig();
    }

    function exportLog() {
        socket.emit('export_log');
    }

    function updateTempHum() {
        fetch('/read_sensors')
            .then(response => response.json())
            .then(data => {
                if (data.temperature && data.humidity) {
                    document.getElementById("temp_display").textContent = data.temperature + " °C";
                    document.getElementById("hum_display").textContent = data.humidity + " %";
                } else {
                    document.getElementById("temp_display").textContent = "Err";
                    document.getElementById("hum_display").textContent = "Err";
                }
            })
            .catch(error => {
                document.getElementById("temp_display").textContent = "Fail";
                document.getElementById("hum_display").textContent = "Fail";
            });
    }
    updateTempHum();
    setInterval(updateTempHum, 10000);

    let qcStatus = null;

function openQCModal() {
    document.getElementById("qcResult").innerText = "";
    document.getElementById("qcModal").style.display = "block";
    document.getElementById("qcResultsList").innerHTML = "<p>Loading...</p>";
    document.getElementById("qcSummaryBanner")?.remove();

    // Fetch last test log & live env data
    Promise.all([
        fetch('/get_last_log').then(r => r.json()),
        fetch('/read_sensors').then(r => r.json())
    ]).then(([logData, envData]) => {
        // normalize values
        const cpu = logData["system-check"]["cpu-usage"] ?? "--";
        const temp = envData.temperature ?? logData["system-check"]["temperature"] ?? "--";
        const hum  = envData.humidity ?? logData["system-check"]["humidity"] ?? "--";

        const items = [];

        // Required checks - align with your list
        items.push({ key: "system-check-cpu", label: `CPU Usage: ${cpu}`, ok: cpu !== null && cpu !== "--" });
        items.push({ key: "system-check-temp", label: `Temperature: ${temp}`, ok: temp !== null && temp !== "--" });
        items.push({ key: "system-check-hum",  label: `Humidity: ${hum}`, ok: hum !== null && hum !== "--" });

        // Board inspections
        const board = logData["board-inspection-status"] || {};
        items.push({ key: "visual", label: `Visual Inspection: ${board.visual}`, ok: board.visual === "yes" });
        items.push({ key: "electrical", label: `Electrical Inspection: ${board.electrical}`, ok: board.electrical === "yes" });

        // Gas sensor
        const gas = (logData["gas-status"] && logData["gas-status"]["sensor-status"]) || "error";
        items.push({ key: "gas", label: `Gas Sensor: ${gas}`, ok: gas === "working" });

        // eFuse ON states - require at least to have been toggled and "working"
        const onStates = logData["efuse-turn-on-status"] || {};
        for (const k in onStates) {
            items.push({ key: `efuse_on_${k}`, label: `${k.replaceAll("_"," ")} (ON): ${onStates[k]}`, ok: onStates[k] === "working" });
        }
        const offStates = logData["efuse-turn-off-status"] || {};
        for (const k in offStates) {
            items.push({ key: `efuse_off_${k}`, label: `${k.replaceAll("_"," ")} (OFF): ${offStates[k]}`, ok: offStates[k] === "working" });
        }

        // Card readers
        const inReader = (logData["card-reader-status"] && logData["card-reader-status"]["in-reader"]) || "--";
        const outReader = (logData["card-reader-status"] && logData["card-reader-status"]["out-reader"]) || "--";
        items.push({ key: "card_in", label: `Card IN Reader: ${inReader}`, ok: inReader && inReader !== "--" });
        items.push({ key: "card_out", label: `Card OUT Reader: ${outReader}`, ok: outReader && outReader !== "--" });

        // Relay & Alarm states (lamp on/off)
        const relays = logData["relay-status"] || {};
        for (const k in relays) {
            items.push({ key: `relay_${k}`, label: `${k.replaceAll("_"," ")}: ${relays[k]}`, ok: relays[k] === "working" });
        }
        const alarms = logData["alarm-status"] || {};
        for (const k in alarms) {
            items.push({ key: `alarm_${k}`, label: `${k.replaceAll("_"," ")}: ${alarms[k]}`, ok: alarms[k] === "working" });
        }

        // Build HTML list and determine pass/fail
        let html = "<ul>";
        const missing = [];
        const failed = [];
        items.forEach(it => {
            const mark = it.ok ? "✅" : "❌";
            html += `<li><strong>${it.label}</strong> ${mark}</li>`;
            if (!it.ok) {
                // decide if missing or failed
                if (it.label.includes("--") || it.label.toLowerCase().includes("undefined")) {
                    missing.push(it.label);
                } else {
                    failed.push(it.label);
                }
            }
        });
        html += "</ul>";

        // QC decision:
        const allOk = failed.length === 0 && missing.length === 0;
        const banner = document.createElement("div");
        banner.id = "qcSummaryBanner";
        banner.style.padding = "10px";
        banner.style.borderRadius = "6px";
        banner.style.marginBottom = "10px";
        banner.style.textAlign = "center";

        if (allOk) {
            banner.innerText = "✅ All tests passed successfully — ready to confirm QC.";
            banner.style.backgroundColor = "#00c853";
            banner.style.color = "white";
            document.getElementById("qcTitle").innerText = "QC PASSED";
            document.getElementById("qcResult").setAttribute("data-status", "passed");
        } else {
            banner.innerText = "❌ Some tests failed or incomplete — review before confirming.";
            banner.style.backgroundColor = "#ff4c4c";
            banner.style.color = "white";
            document.getElementById("qcTitle").innerText = "QC FAILED";
            document.getElementById("qcResult").setAttribute("data-status", "failed");
        }

        document.getElementById("qcResultsList").innerHTML = html;
        document.getElementById("qcModal").querySelector(".modal-content").prepend(banner);
        // store failure lists on element for confirm step
        document.getElementById("qcModal").dataset.failed = JSON.stringify(failed);
        document.getElementById("qcModal").dataset.missing = JSON.stringify(missing);

    }).catch(err => {
        console.error("QC load error:", err);
        document.getElementById("qcResultsList").innerHTML = "<p style='color:red;'>Failed to load test results.</p>";
    });
}


function formatResult(label, value) {
    let icon = (value && value.toString().toLowerCase() === "working") ? "✅" : "❌";
    return `<li>${label}: ${icon} (${value})</li>`;
}


    function closeQCModal() {
        document.getElementById("qcModal").style.display = "none";
    }

function confirmQC() {
    const status = document.getElementById("qcResult").getAttribute("data-status") || "failed";
    const failed = JSON.parse(document.getElementById("qcModal").dataset.failed || "[]");
    const missing = JSON.parse(document.getElementById("qcModal").dataset.missing || "[]");

    // If QC is passed but we have problems, block
    if (status === "passed" && (failed.length > 0 || missing.length > 0)) {
        alert("⚠ Cannot mark QC as PASSED — some tests failed or are missing.");
        return;
    }

    // If QC is failed but no failed or missing items reported, warn operator
    if (status === "failed" && failed.length === 0 && missing.length === 0) {
        if (!confirm("QC is marked FAILED but no failing items were detected. Proceed to write FAILED QC anyway?")) {
            return;
        }
    }

    // If failed/missing items exist, show them and ask for operator confirmation to proceed as failed
    if (status === "failed" && (failed.length > 0 || missing.length > 0)) {
        const reasons = failed.concat(missing);
        if (!confirm("QC failures detected:\n\n" + reasons.join("\n") + "\n\nProceed to save QC as FAILED?")) {
            return;
        }
    }

    // Fetch tester info for EEPROM fields
    fetch("/get_test_info")
        .then(r => r.json())
        .then(info => {
            const payload = {
                uuid: info.pcbserial || info.pcb_serial || "UNKNOWN",
                hw: info.modelnumber || info.model_number || "UNKNOWN",
                timestamp: new Date().toISOString(),
                qc_status: (status === "passed") ? "PASSED" : "FAILED",
                qc_fail_reasons: failed.concat(missing),
                full_log: null // server will fetch via log_exporter if not provided
            };

            return fetch("/write_eeprom_full", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });
        })
        .then(r => r.json())
        .then(res => {
            if (res.status === "success") {
                alert("QC recorded to EEPROM: " + res.device_info.qc_status);
                closeQCModal();
            } else {
                alert("Failed to write EEPROM: " + (res.message || JSON.stringify(res)));
            }
        })
        .catch(err => {
            alert("Error while confirming QC: " + err);
        });
}

    function showDeviceInfo() {
    fetch("/device_info")
        .then(res => res.json())
        .then(data => {
            const modal = document.getElementById("deviceInfoModal");
            const content = document.getElementById("deviceInfoData");

            if (data.status === "success" && data.data) {
                const info = data.data;
                let html = `
                    <div class="device-info-table">
                        <div><strong>Serial Number:</strong> ${info.serial_number}</div>
                        <div><strong>QC Status:</strong> 
                            <span class="${info.qc_status === 'PASSED' ? 'qc-pass' : 'qc-fail'}">
                                ${info.qc_status}
                            </span>
                        </div>
                        <div><strong>Tested Date:</strong> ${info.tested_date}</div>
                    </div>
                `;
                content.innerHTML = html;
            } else {
                content.innerHTML = `<p style="color:red;">No valid data found in device memory.</p>`;
            }

            modal.style.display = "block";
        })
        .catch(err => {
            console.error("Device Info Fetch Error:", err);
            document.getElementById("deviceInfoData").innerHTML =
                "<p style='color:red;'>Error fetching device info.</p>";
            document.getElementById("deviceInfoModal").style.display = "block";
        });
}

    function closeDeviceInfo() {
        document.getElementById("deviceInfoModal").style.display = "none";
    }

    
function saveBoardInspection() {
    const visual = document.querySelector('input[name="visual"]:checked');
    const electrical = document.querySelector('input[name="electrical"]:checked');

    if (!visual || !electrical) {
        alert("Please answer both inspection questions before saving.");
        return;
    }

    const payload = {
        visual: visual.value === "yes" ? "yes" : "no",
        electrical: electrical.value === "yes" ? "yes" : "no"
    };

    fetch("/save_board_inspection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            alert("✅ Board inspection saved successfully!");
        } else {
            alert("❌ Error saving inspection: " + data.message);
        }
    })
    .catch(err => {
        alert("Error: " + err.message);
    });
}
