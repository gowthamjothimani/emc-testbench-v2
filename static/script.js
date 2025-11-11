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
                        el.textContent = data.in_number || data.error || "--";
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

 function openQCModal(status) {
    const qcTitle = document.getElementById("qcTitle");
    qcTitle.innerText = status === "passed" ? "QC PASSED" : "QC FAILED";
    document.getElementById("qcResult").innerText = "";
    document.getElementById("qcModal").style.display = "block";
    document.getElementById("qcResult").setAttribute("data-status", status);

    // Fetch last test log first
    fetch('/get_last_log')
        .then(res => res.json())
        .then(logData => {
            // Then fetch live environment data
            fetch('/read_sensors')
                .then(res => res.json())
                .then(envData => {
                    const temperature = envData.temperature ?? logData["system-check"]["temperature"];
                    const humidity = envData.humidity ?? logData["system-check"]["humidity"];
                    const cpuUsage = logData["system-check"]["cpu-usage"] ?? "--";

                    let html = "<ul>";

                    // Display general system info (no checkmarks)
                    html += `<li><strong>CPU Usage:</strong> ${cpuUsage}%</li>`;
                    html += `<li><strong>Temperature:</strong> ${temperature ?? "--"} °C</li>`;
                    html += `<li><strong>Humidity:</strong> ${humidity ?? "--"} %</li>`;
                    html += `<li><strong>Timestamp:</strong> ${logData["system-check"]["timestamp"]}</li>`;

                    // Function to generate ✅ / ❌ mark
                    const makeMark = (val) => {
                        if (val === "working" || val === "Good" || val === "12V") return "✅";
                        if (val === "error" || val === "Error" || val === "0V") return "❌";
                        return "";
                    };

                    // Gas sensor
                    html += `<li><strong>Gas Sensor:</strong> ${makeMark(logData["gas-status"]["sensor-status"])} (${logData["gas-status"]["sensor-status"]})</li>`;

                    // eFuse ON states
                    for (const [key, val] of Object.entries(logData["efuse-turn-on-status"] || {})) {
                        html += `<li><strong>${key.replaceAll("_"," ")}:</strong> ${makeMark(val)} (${val})</li>`;
                    }

                    // eFuse OFF states
                    for (const [key, val] of Object.entries(logData["efuse-turn-off-status"] || {})) {
                        html += `<li><strong>${key.replaceAll("_"," ")}:</strong> ${makeMark(val)} (${val})</li>`;
                    }

                    // Card reader info — no tick/cross
                    html += `<li><strong>Card IN Reader:</strong> ${logData["card-reader-status"]["in-reader"] || "--"}</li>`;
                    html += `<li><strong>Card OUT Reader:</strong> ${logData["card-reader-status"]["out-reader"] || "--"}</li>`;

                    // Relay status
                    for (const [key, val] of Object.entries(logData["relay-status"] || {})) {
                        html += `<li><strong>${key.replaceAll("_"," ")}:</strong> ${makeMark(val)} (${val})</li>`;
                    }

                    // Alarm status
                    for (const [key, val] of Object.entries(logData["alarm-status"] || {})) {
                        html += `<li><strong>${key.replaceAll("_"," ")}:</strong> ${makeMark(val)} (${val})</li>`;
                    }

                    html += "</ul>";
                    document.getElementById("qcResultsList").innerHTML = html;
                    updateQCSummaryBanner();

                    // Store QC status for confirm step
                    document.getElementById("qcResult").setAttribute("data-status", status);
                })
                .catch(err => {
                    console.error("Error fetching live sensor data:", err);
                });
        })
        .catch(err => {
            console.error("Error loading QC log:", err);
            document.getElementById("qcResultsList").innerHTML = "<p>Failed to load test results.</p>";
        });
}

function updateQCSummaryBanner() {
    const listItems = Array.from(document.querySelectorAll("#qcResultsList li"));
    const banner = document.getElementById("qcSummaryBanner");
    if (!banner) return;

    const hasError = listItems.some(li =>
        li.textContent.includes("❌") || li.textContent.includes("error") || li.textContent.includes("--")
    );

    if (hasError) {
        banner.innerHTML = "❌ Some tests failed or incomplete — review before confirming.";
        banner.style.backgroundColor = "#ff4c4c";
        banner.style.color = "white";
    } else {
        banner.innerHTML = "✅ All tests passed successfully — ready to confirm QC.";
        banner.style.backgroundColor = "#00c853";
        banner.style.color = "white";
    }
    banner.style.padding = "10px";
    banner.style.borderRadius = "6px";
    banner.style.marginBottom = "10px";
    banner.style.textAlign = "center";
}

function formatResult(label, value) {
    let icon = (value && value.toString().toLowerCase() === "working") ? "✅" : "❌";
    return `<li>${label}: ${icon} (${value})</li>`;
}


    function closeQCModal() {
        document.getElementById("qcModal").style.display = "none";
    }

   function confirmQC() {
    const qcStatus = document.getElementById("qcResult").getAttribute("data-status");
    const listElement = document.getElementById("qcResultsList");
    if (!listElement) {
        alert("No test results available to validate.");
        return;
    }

    // Gather all test items
    const listItems = Array.from(listElement.querySelectorAll("li"));
    const items = listItems.map(li => li.textContent);

    // Define mandatory checks
    const requiredChecks = [
        "CPU Usage",
        "Temperature",
        "Humidity",
        "Timestamp",
        "Gas Sensor",
        "efuse alarm on",
        "efuse badge on",
        "efuse gas on",
        "efuse alarm off",
        "efuse badge off",
        "efuse gas off",
        "Card IN Reader",
        "Card OUT Reader",
        "alarm sound off",
        "alarm sound on",
        "lamp alarm green off",
        "lamp alarm green on",
        "lamp alarm red off",
        "lamp alarm red on",
        "lamp badge off",
        "lamp badge on"
    ];

    // Reset any previous highlights
    listItems.forEach(li => li.style.color = "");

    // Identify missing and failed
    const missing = requiredChecks.filter(check => 
        !items.some(i => i.toLowerCase().includes(check.toLowerCase()))
    );

    const failed = listItems.filter(li =>
        li.textContent.includes("❌") || li.textContent.includes("error") || li.textContent.includes("--")
    );

    // Highlight missing and failed
    missing.forEach(check => {
        const li = document.createElement("li");
        li.textContent = check + " — missing";
        li.style.color = "red";
        listElement.appendChild(li);
    });
    failed.forEach(li => li.style.color = "red");
     updateQCSummaryBanner();
    const hasMissing = missing.length > 0;
    const hasFailed = failed.length > 0;

    // Validation logic
    if (qcStatus === "passed") {
        if (hasMissing || hasFailed) {
            const msg = [
                "⚠️ QC PASS not allowed — some tests are incomplete or failed.",
                hasMissing ? `\n🟥 Missing: ${missing.join(", ")}` : "",
                hasFailed ? `\n🟥 Failed: ${failed.length} item(s)` : ""
            ].join("");
            alert(msg);
            return;
        }
    } else if (qcStatus === "failed") {
        // If everything looks good but user clicked fail, block it
        if (!hasMissing && !hasFailed) {
            alert("⚠️ QC FAIL not allowed — all tests passed successfully.");
            return;
        }
    }

    // ✅ Validation passed — proceed with EEPROM write
    fetch("/get_test_info")
        .then(res => res.json())
        .then(testInfo => {
            const payload = {
                qc_status: qcStatus.toUpperCase(),
                hardware_provider: testInfo.hardware_provider,
                hardware_type: testInfo.hardware_type,
                serial_number: testInfo.pcb_serial
            };

            return fetch("/qc_status", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        })
        .then(res => res.json())
        .then(response => {
            if (response.status === "success") {
                alert("✅ QC " + qcStatus.toUpperCase() + " successfully recorded!");
                closeQCModal();
            } else {
                alert("❌ Error saving QC status: " + (response.message || "Unknown error"));
            }
        })
        .catch(err => {
            console.error("QC confirm error:", err);
            alert("❌ Failed to confirm QC: " + err);
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

    function confirmQCStatus(qcStatus) {
    fetch('/get_test_info')
        .then(response => response.json())
        .then(testInfo => {
            // Build final serial number dynamically
            let providerCode = testInfo.hardware_provider === "Visics" ? "VIS" : "ORION";
            let serial_number = `${providerCode}-${testInfo.hardware_type}-${testInfo.pcb_serial}`;

            let qcData = {
                serial_number: serial_number,
                qc_status: qcStatus,
                tested_date: new Date().toISOString().slice(0, 19).replace('T', ' ')
            };

            // Send to backend to write EEPROM
            fetch('/qc_status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(qcData)
            })
            .then(r => r.json())
            .then(res => alert(res.message))
            .catch(err => console.error("QC update failed:", err));
        });
}