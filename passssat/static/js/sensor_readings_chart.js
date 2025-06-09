// Globalne zmienne
let singleSensorChart = null; // Instancja dla pojedynczego, dużego wykresu
const multipleSensorCharts = {}; // Obiekt do przechowywania instancji wielu wykresów (key: sensorId)
let autoRefreshIntervalId = null; // ID interwału dla auto-odświeżania
const REFRESH_INTERVAL_MS = 10000; // Odświeżaj co 10 sekund (dla zakresu 1h)

// Elementy DOM
const vesselSelect = document.getElementById("vesselSelect");
const sensorSelect = document.getElementById("sensorSelect");
const timeRangeSelect = document.getElementById("timeRangeSelect");

const singleChartWrapper = document.getElementById("singleChartContainerWrapper");
const singleChartCanvas = document.getElementById("sensorReadingsChart");

const multipleChartsContainer = document.getElementById("multipleChartsContainer"); // NOWY

const chartErrorDiv = document.getElementById("chartError");
const noDataMessageDiv = document.getElementById("noDataMessage");

/**
 * Wyświetla komunikat błędu w dedykowanym div.
 * @param {string} message - Wiadomość błędu.
 */
function displayChartError(message) {
    if (chartErrorDiv) {
        chartErrorDiv.textContent = message;
        chartErrorDiv.classList.remove("hidden");
    }
    if (singleChartWrapper) singleChartWrapper.classList.add("hidden");
    if (multipleChartsContainer) multipleChartsContainer.classList.add("hidden");
    if (noDataMessageDiv) noDataMessageDiv.classList.add("hidden");
}

/**
 * Wyświetla komunikat o braku danych.
 */
function displayNoDataMessage(isForAllSensors = false) {
    if (noDataMessageDiv) {
        noDataMessageDiv.textContent = isForAllSensors ? 
            "Brak sensorów lub danych dla wybranego statku i zakresu czasu." :
            "Brak danych odczytów dla wybranego sensora i zakresu czasu.";
        noDataMessageDiv.classList.remove("hidden");
    }
    if (singleChartWrapper) singleChartWrapper.classList.add("hidden");
    if (!isForAllSensors && multipleChartsContainer) { // Jeśli nie ma danych dla pojedynczego, nie ukrywaj siatki
         // multipleChartsContainer.classList.add("hidden"); // Decyzja czy ukrywać całą siatkę
    } else if (isForAllSensors && multipleChartsContainer) {
        multipleChartsContainer.innerHTML = ''; // Wyczyść siatkę
        multipleChartsContainer.classList.remove("hidden"); // Pokaż kontener z wiadomością
    }
}

/**
 * Czyści komunikaty o błędach i braku danych, pokazuje canvas.
 */
function clearMessagesAndPrepareDisplay(isSingleChartView) {
    if (chartErrorDiv) chartErrorDiv.classList.add("hidden");
    if (noDataMessageDiv) noDataMessageDiv.classList.add("hidden");

    if (isSingleChartView) {
        if (singleChartWrapper) singleChartWrapper.classList.remove("hidden");
        if (multipleChartsContainer) multipleChartsContainer.classList.add("hidden");
    } else { // Widok wielu wykresów
        if (singleChartWrapper) singleChartWrapper.classList.add("hidden");
        if (multipleChartsContainer) {
            multipleChartsContainer.classList.remove("hidden");
            multipleChartsContainer.innerHTML = ''; // Wyczyść przed dodaniem nowych canvasów
        }
    }
}

/**
 * Pobiera listę statków i wypełnia dropdown.
 */
async function populateVesselSelect() {
  if (!vesselSelect) return;
    try {
        const response = await fetch("/sensors-overview/api/vessels");
        if (!response.ok) {
            const err = await response.json().catch(() => ({detail: "Błąd serwera"}));
            throw new Error(`Nie udało się pobrać listy statków: ${err.detail || response.statusText}`);
        }
        const vessels = await response.json();
        vesselSelect.innerHTML = '<option value="">-- Wybierz statek --</option>';
        if (vessels && vessels.length > 0) {
            vessels.forEach((vessel) => {
                const option = document.createElement("option");
                option.value = vessel.id;
                option.textContent = `${vessel.name} (ID: ${vessel.id})`;
                vesselSelect.appendChild(option);
            });
            if (PRESELECTED_VESSEL_ID) {
                vesselSelect.value = PRESELECTED_VESSEL_ID;
                await populateSensorSelect(PRESELECTED_VESSEL_ID); // To wywoła dalsze ładowanie
            } else {
                // Jeśli nie ma preselekcji statku, domyślnie nic nie rób lub wybierz pierwszy
                // handleVesselChange(); // Aby załadować sensory dla domyślnie wybranego (jeśli jest)
            }
        } else {
            vesselSelect.innerHTML = '<option value="">Brak dostępnych statków</option>';
        }
    } catch (error) {
        console.error("Błąd ładowania statków:", error);
        vesselSelect.innerHTML = `<option value="">Błąd: ${error.message}</option>`;
        displayChartError(`Błąd ładowania listy statków: ${error.message}`);
    }
}

/**
 * Pobiera listę sensorów dla wybranego statku i wypełnia dropdown.
 * @param {string|number} vesselId - ID wybranego statku.
 */
async function populateSensorSelect(vesselId) {
    if (!sensorSelect || !vesselId) {
        if (sensorSelect) {
            sensorSelect.innerHTML = '<option value="">Najpierw wybierz statek...</option>';
            sensorSelect.disabled = true;
            timeRangeSelect.disabled = true;
        }
        clearAllChartsAndMessages();
        return;
    }
    sensorSelect.disabled = true;
    sensorSelect.innerHTML = '<option value="">Ładowanie sensorów...</option>';
    timeRangeSelect.disabled = true;

    try {
        const response = await fetch(`/sensors-overview/api/vessels/${vesselId}/sensors`);
        if (!response.ok) {
            const err = await response.json().catch(() => ({detail: "Błąd serwera"}));
            throw new Error(`Nie udało się pobrać listy sensorów: ${err.detail || response.statusText}`);
        }
        const sensors = await response.json();
        sensorSelect.innerHTML = ''; // Wyczyść

        // Dodaj opcję "Wszystkie Sensory" jako pierwszą
        const allSensorsOption = document.createElement("option");
        allSensorsOption.value = "all"; // Specjalna wartość
        allSensorsOption.textContent = "-- Wszystkie Sensory --";
        sensorSelect.appendChild(allSensorsOption);

        if (sensors && sensors.length > 0) {
            sensors.forEach((sensor) => {
                const option = document.createElement("option");
                option.value = sensor.id;
                option.textContent = `${sensor.name} (Typ: ${sensor.sensor_type.name}, Jedn.: ${sensor.measurement_unit || 'N/A'})`;
                sensorSelect.appendChild(option);
            });
            sensorSelect.disabled = false;
            
            if (PRESELECTED_SENSOR_ID && String(PRESELECTED_VESSEL_ID) === String(vesselId)) {
                sensorSelect.value = PRESELECTED_SENSOR_ID;
            } else {
                sensorSelect.value = "all"; // Domyślnie wybierz "Wszystkie Sensory"
            }
            await handleSensorOrTimeRangeChange(); // Załaduj dane
            
        } else {
            sensorSelect.innerHTML = '<option value="all">-- Wszystkie Sensory --</option><option value="" disabled>Brak sensorów dla tego statku</option>';
            await handleSensorOrTimeRangeChange(); // Spróbuj załadować (pokaże "brak danych")
        }
    } catch (error) {
        console.error("Błąd ładowania sensorów:", error);
        sensorSelect.innerHTML = `<option value="">Błąd: ${error.message}</option>`;
        displayChartError(`Błąd ładowania listy sensorów: ${error.message}`);
    }
}

/**
 * Oblicza datę początkową na podstawie wybranego zakresu czasu.
 * @param {string} range - Wartość z timeRangeSelect (np. "1h", "24h", "7d").
 * @returns {Date} Obiekt Date dla czasu początkowego.
 */
function getStartTimeForRange(range) {
    const now = new Date();
    let startTime = new Date(now);

    switch (range) {
        case "1h":
            startTime.setHours(now.getHours() - 1);
            break;
        case "6h":
            startTime.setHours(now.getHours() - 6);
            break;
        case "24h":
            startTime.setDate(now.getDate() - 1);
            break;
        case "7d":
            startTime.setDate(now.getDate() - 7);
            break;
        case "30d":
            startTime.setDate(now.getDate() - 30);
            break;
        default: // Domyślnie 24h
            startTime.setDate(now.getDate() - 1);
    }
    return startTime;
}

async function handleSensorOrTimeRangeChange() {
    const selectedVesselId = vesselSelect.value;
    const selectedSensorValue = sensorSelect.value; // Może być ID sensora lub "all"

    if (!selectedVesselId) {
        clearAllChartsAndMessages();
        displayNoDataMessage(true);
        return;
    }
    
    timeRangeSelect.disabled = false; // Odblokuj wybór czasu, gdy statek jest wybrany

    if (selectedSensorValue && selectedSensorValue !== "all") {
        // Widok pojedynczego sensora
        await loadAndDrawSingleChart(selectedSensorValue);
    } else if (selectedSensorValue === "all") {
        // Widok wszystkich sensorów dla statku
        await loadAndDrawMultipleCharts(selectedVesselId);
    } else {
        // Żaden sensor nie wybrany (np. po zmianie statku, przed załadowaniem sensorów)
        clearAllChartsAndMessages();
        // displayNoDataMessage(true); // Komunikat o braku wyboru sensora
    }
    setupAutoRefresh(); // Ustaw/zresetuj auto-odświeżanie
}

function clearAllChartsAndMessages() {
    if (singleSensorChart) {
        singleSensorChart.destroy();
        singleSensorChart = null;
    }
    Object.values(multipleSensorCharts).forEach(chart => chart.destroy());
    for (const key in multipleSensorCharts) delete multipleSensorCharts[key];
    
    if (multipleChartsContainer) multipleChartsContainer.innerHTML = ''; 
    if (chartErrorDiv) chartErrorDiv.classList.add("hidden");
    if (noDataMessageDiv) noDataMessageDiv.classList.add("hidden");
    if (singleChartWrapper) singleChartWrapper.classList.add("hidden"); 
    if (multipleChartsContainer) multipleChartsContainer.classList.add("hidden");
}

/**
 * Pobiera odczyty dla wybranego sensora i zakresu czasu, a następnie rysuje wykres.
 */
async function loadAndDrawSingleChart(sensorId) {
    clearMessagesAndPrepareDisplay(true); // Pokaż kontener na pojedynczy wykres
    const selectedTimeRange = timeRangeSelect.value;
    const startTime = getStartTimeForRange(selectedTimeRange);
    const endTime = new Date();

    try {
        const params = new URLSearchParams({
            start_time: startTime.toISOString(),
            end_time: endTime.toISOString(),
            limit: 5000
        });
        const response = await fetch(`/sensors-overview/api/sensors/${sensorId}/readings?${params.toString()}`);
        if (!response.ok) {
            const err = await response.json().catch(() => ({detail: "Błąd serwera"}));
            throw new Error(`Nie udało się pobrać odczytów: ${err.detail || response.statusText}`);
        }
        const readings = await response.json();
        if (readings && readings.length > 0) {
            drawSingleChart(readings, sensorId);
        } else {
            if (singleSensorChart) singleSensorChart.destroy();
            singleSensorChart = null;
            displayNoDataMessage(false);
        }
    } catch (error) {
        console.error("Błąd ładowania danych dla pojedynczego wykresu:", error);
        if (singleSensorChart) singleSensorChart.destroy();
        singleSensorChart = null;
        displayChartError(`Błąd ładowania danych: ${error.message}`);
    }
}

async function loadAndDrawMultipleCharts(vesselId) {
    clearMessagesAndPrepareDisplay(false); // Pokaż kontener na wiele wykresów
    const selectedTimeRange = timeRangeSelect.value;
    const startTime = getStartTimeForRange(selectedTimeRange);
    const endTime = new Date();

    // Najpierw pobierz listę sensorów dla statku
    let sensorsOnVessel = [];
    try {
        const sensorsResponse = await fetch(`/sensors-overview/api/vessels/${vesselId}/sensors`);
        if (!sensorsResponse.ok) throw new Error("Nie udało się pobrać listy sensorów dla statku.");
        sensorsOnVessel = await sensorsResponse.json();
    } catch (error) {
        console.error(error);
        displayChartError(error.message);
        return;
    }

    if (!sensorsOnVessel || sensorsOnVessel.length === 0) {
        displayNoDataMessage(true);
        return;
    }

    // Usuń stare wykresy
    Object.values(multipleSensorCharts).forEach(chart => chart.destroy());
    for (const key in multipleSensorCharts) delete multipleSensorCharts[key];
    multipleChartsContainer.innerHTML = ''; // Wyczyść kontener

    let chartsRendered = 0;
    for (const sensor of sensorsOnVessel) {
        try {
            const params = new URLSearchParams({
                start_time: startTime.toISOString(),
                end_time: endTime.toISOString(),
                limit: 1000 // Mniejszy limit dla wielu wykresów
            });
            const readingsResponse = await fetch(`/sensors-overview/api/sensors/${sensor.id}/readings?${params.toString()}`);
            if (!readingsResponse.ok) {
                console.warn(`Nie udało się pobrać odczytów dla sensora ${sensor.name} (ID: ${sensor.id})`);
                continue; // Przejdź do następnego sensora
            }
            const readings = await readingsResponse.json();

            if (readings && readings.length > 0) {
                const canvasId = `sensorChart-${sensor.id}`;
                const chartDiv = document.createElement('div');
                chartDiv.className = 'chart-container-multiple'; // Styl dla kontenera wykresu
                const canvas = document.createElement('canvas');
                canvas.id = canvasId;
                chartDiv.appendChild(canvas);
                multipleChartsContainer.appendChild(chartDiv);
                
                drawIndividualChart(readings, sensor, canvasId, true); // true dla isMultipleView
                chartsRendered++;
            }
        } catch (error) {
            console.error(`Błąd ładowania odczytów dla sensora ${sensor.name}:`, error);
            // Można dodać komunikat błędu dla tego konkretnego wykresu
            const errorP = document.createElement('p');
            errorP.className = 'text-red-400 text-xs p-2';
            errorP.textContent = `Błąd ładowania danych dla ${sensor.name}.`;
            const chartDiv = document.createElement('div');
            chartDiv.className = 'chart-container-multiple flex items-center justify-center';
            chartDiv.appendChild(errorP);
            multipleChartsContainer.appendChild(chartDiv);
        }
    }
    if (chartsRendered === 0 && sensorsOnVessel.length > 0) {
        displayNoDataMessage(true); // Jeśli były sensory, ale żaden nie miał danych
    }
}

/**
 * Rysuje pojedynczy duży wykres.
 */
function drawSingleChart(readings, sensorId) {
    const sensorData = sensorSelect.options[sensorSelect.selectedIndex];
    const sensorName = sensorData ? sensorData.textContent : `Sensor ID: ${sensorId}`;
    drawIndividualChart(readings, {id: sensorId, name: sensorName}, "sensorReadingsChart", false);
}

/**
 * Rysuje wykres (używane zarówno dla pojedynczego, jak i wielu).
 * @param {Array<Object>} readings
 * @param {Object} sensor - Obiekt sensora (id, name, measurement_unit)
 * @param {string} canvasId - ID elementu canvas
 * @param {boolean} isMultipleView - Czy to widok wielu wykresów (wpływa na tooltipy)
 */
function drawIndividualChart(readings, sensor, canvasId, isMultipleView) {
    const canvasElement = document.getElementById(canvasId);
    if (!canvasElement) {
        console.error(`Canvas element with ID ${canvasId} not found.`);
        return;
    }

    if (isMultipleView) {
        if (multipleSensorCharts[sensor.id]) {
            multipleSensorCharts[sensor.id].destroy();
            delete multipleSensorCharts[sensor.id]; // Usuń referencję
        }
    } else { // Widok pojedynczego wykresu
        if (singleSensorChart && singleSensorChart.canvas.id === canvasId) { // Upewnij się, że to ten sam canvas
            singleSensorChart.destroy();
            singleSensorChart = null; // Usuń referencję
        }
    }

    const labels = readings.map(r => new Date(r.timestamp));
    const dataValues = readings.map(r => parseFloat(r.value));

    let pointColors, pointRadii;

    if (isMultipleView) {
        // Dla widoku wielu, punkty 'normal' mają być przezroczyste i małe (lub promień 0)
        pointColors = readings.map(r => {
            switch (r.status) {
                case 'warning': return 'rgba(255, 193, 7, 0.9)';
                case 'critical': return 'rgba(244, 67, 54, 0.9)';
                case 'error': return 'rgba(176, 0, 32, 0.9)';
                default: return 'rgba(0, 0, 0, 0)'; // Przezroczysty dla normal
            }
        });
        pointRadii = readings.map(r => {
            switch (r.status) {
                case 'warning': return 5;
                case 'critical': return 6;
                case 'error': return 6;
                default: return 0; // Promień 0 dla normal, aby były niewidoczne
            }
        });
    } else {
        // Dla widoku pojedynczego, normalne punkty są widoczne
        pointColors = readings.map(r => {
            switch (r.status) {
                case 'warning': return 'rgba(255, 193, 7, 0.9)';
                case 'critical': return 'rgba(244, 67, 54, 0.9)';
                case 'error': return 'rgba(176, 0, 32, 0.9)';
                default: return 'rgba(54, 162, 235, 0.8)';
            }
        });
        pointRadii = readings.map(r => (r.status !== 'normal' ? 5 : 3));
    }

    const chartInstance = multipleSensorCharts[sensor.id] || singleSensorChart;
    if (chartInstance) {
        chartInstance.destroy();
    }
    
    const unitMatch = sensor.name.match(/Jedn\.:\s*([^)]+)/); // Spróbuj wyciągnąć jednostkę z nazwy w dropdownie
    const unit = unitMatch ? unitMatch[1] : '';

    const newChart = new Chart(canvasElement, {
    type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `Wartość ${unit ? '('+unit+')' : ''}`,
                data: dataValues,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                tension: 0.2,
                fill: true,
                pointBackgroundColor: pointColors,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: pointColors,
                pointHoverBorderColor: '#fff',
                pointRadius: pointRadii,
                pointHoverRadius: pointRadii.map(r => r > 0 ? r + 2 : 0), // Hover tylko dla widocznych punktów
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: isMultipleView ? sensor.name.split(' (Typ:')[0] : sensor.name,
                    font: { size: isMultipleView ? 12 : 16 },
                    color: '#e5e7eb'
                },
                legend: { display: !isMultipleView, labels: { color: '#d1d5db' } },
                tooltip: {
                    enabled: true,
                    filter: function(tooltipItem) {
                        if (isMultipleView) {
                            const readingIndex = tooltipItem.dataIndex;
                            const currentReading = readings[readingIndex];
                            return currentReading && 
                                   (currentReading.status === 'warning' || 
                                    currentReading.status === 'critical' ||
                                    currentReading.status === 'error');
                        }
                        return true; // Pokaż wszystkie tooltipy dla widoku pojedynczego
                    },
                    callbacks: {
                        label: function(context) {
                            const readingIndex = context.dataIndex;
                            const currentReading = readings[readingIndex];
                            if (!currentReading) return '';
                            
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.parsed.y !== null) label += context.parsed.y.toFixed(2);
                            label += ` (Status: ${currentReading.status})`;
                            return label;
                        },
                        title: function(context) {
                            if (context.length > 0 && context[0].parsed) {
                                return new Date(context[0].parsed.x).toLocaleString();
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                x: { type: 'time', time: { unit: 'hour', tooltipFormat: 'PP H:mm:ss' }, ticks: { color: '#d1d5db', maxTicksLimit: isMultipleView ? 5 : 10 }, grid: { color: 'rgba(255,255,255,0.1)'} },
                y: { beginAtZero: false, ticks: { color: '#d1d5db', maxTicksLimit: isMultipleView ? 4 : 8 }, grid: { color: 'rgba(255,255,255,0.1)'} }
            },
            interaction: { // Dla lepszej obsługi tooltipów
                intersect: false,
                mode: 'index',
            },
        }
    });

    if (isMultipleView) {
        multipleSensorCharts[sensor.id] = newChart;
    } else {
        singleSensorChart = newChart;
    }
}

/**
 * Ustawia lub czyści interwał automatycznego odświeżania.
 */
function setupAutoRefresh() {
    if (autoRefreshIntervalId) {
        clearInterval(autoRefreshIntervalId);
        autoRefreshIntervalId = null;
    }

    const selectedTimeRange = timeRangeSelect.value;
    const selectedSensorValue = sensorSelect.value;
    const selectedVesselId = vesselSelect.value;

    if (selectedTimeRange === "1h" && selectedVesselId) { // Odświeżaj tylko dla zakresu 1h i gdy statek jest wybrany
        console.log("Ustawiam auto-odświeżanie co", REFRESH_INTERVAL_MS / 1000, "s");
        autoRefreshIntervalId = setInterval(async () => {
            console.log("Automatyczne odświeżanie danych...");
            if (selectedSensorValue && selectedSensorValue !== "all") {
                await loadAndDrawSingleChart(selectedSensorValue);
            } else if (selectedSensorValue === "all") {
                await loadAndDrawMultipleCharts(selectedVesselId);
            }
        }, REFRESH_INTERVAL_MS);
    } else {
        console.log("Auto-odświeżanie nieaktywne (zakres inny niż 1h lub brak statku).");
    }
}

// Event Listeners
document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("sensorReadingsChart") || document.getElementById("multipleChartsContainer")) {
        populateVesselSelect(); // Wypełnij statki na starcie

        vesselSelect.addEventListener("change", async (event) => {
            const vesselId = event.target.value;
            clearAllChartsAndMessages(); // Wyczyść wszystko przy zmianie statku
            if (vesselId) {
                await populateSensorSelect(vesselId); // To wywoła handleSensorOrTimeRangeChange
            } else {
                sensorSelect.innerHTML = '<option value="">Najpierw wybierz statek...</option>';
                sensorSelect.disabled = true;
                timeRangeSelect.disabled = true;
                displayNoDataMessage(true);
            }
            setupAutoRefresh(); // Zresetuj odświeżanie
        });

        sensorSelect.addEventListener("change", handleSensorOrTimeRangeChange);
        timeRangeSelect.addEventListener("change", handleSensorOrTimeRangeChange);
    }
});
