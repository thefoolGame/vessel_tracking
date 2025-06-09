// static/js/map_manager.js

// Globalne zmienne
let map;
const vesselMarkers = {};
let currentTraveledPath = null;
let currentPlannedRoutePolyline = null;
let selectedVesselId = null;
let allVesselsMapData = [];

// NOWE: Grupa warstw dla markerów historii lokalizacji i obiekt do ich przechowywania
const historicalLocationMarkersGroup = L.layerGroup();
// const historicalLocationMarkers = {}; // Opcjonalnie, jeśli potrzebujesz dostępu do konkretnych markerów po ID

// Ikony dla statków (bez zmian)
const mainVesselIconUrl = "/static/ship_selected.svg";
const otherVesselIconUrl = "/static/ship_other.svg";
const iconSize = [25, 25];

// Ikony dla punktów trasy (bez zmian)
const plannedRoutePointIcon = L.divIcon({
  html: '<div style="background-color: rgba(255, 165, 0, 0.7); width: 10px; height: 10px; border-radius: 50%; border: 1px solid white; box-shadow: 0 0 3px rgba(0,0,0,0.4);"></div>',
  className: "planned-route-point-marker",
  iconSize: [10, 10],
  iconAnchor: [5, 5],
});
const routePointMarkersLayerGroup = L.layerGroup();

// NOWA IKONA: dla markerów historii lokalizacji
const historyLocationPointIcon = L.divIcon({
    html: '<div style="background-color: #007bff; width: 8px; height: 8px; border-radius: 50%; border: 1px solid #fff; opacity: 0.7;"></div>',
    className: 'history-location-point-marker',
    iconSize: [8, 8],
    iconAnchor: [4, 4]
});


// parseWKTPosition, createVesselIcon, updateVesselInfoPanel, showVesselInfoPanel, hideVesselInfoPanel - bez zmian
function parseWKTPosition(wktPoint) {
    if (!wktPoint || !wktPoint.toUpperCase().startsWith("POINT (")) {
        console.warn("Invalid WKT point for parsing:", wktPoint);
        return null;
    }
    try {
        const coords = wktPoint.match(/\(([^)]+)\)/)[1].split(' ');
        return { lon: parseFloat(coords[0]), lat: parseFloat(coords[1]) };
    } catch (e) {
        console.error("Error parsing WKT point:", wktPoint, e);
        return null;
    }
}

function createVesselIcon(isMain, rotationAngle = 0) {
    return L.divIcon({
        html: `<img src="${isMain ? mainVesselIconUrl : otherVesselIconUrl}" style="transform: rotate(${rotationAngle}deg); width: ${iconSize[0]}px; height: ${iconSize[1]}px; transform-origin: center;">`,
        className: 'leaflet-custom-div-icon',
        iconSize: iconSize,
        iconAnchor: [iconSize[0] / 2, iconSize[1] / 2],
        popupAnchor: [0, -iconSize[1] / 2]
    });
}

function updateVesselInfoPanel(vesselAPIData) {
    const panel = document.getElementById('vessel-info-panel');
    const panelVesselName = document.getElementById('panel-vessel-name');
    const panelVesselDetails = document.getElementById('panel-vessel-details');
    if (!panel || !panelVesselName || !panelVesselDetails) return;
    panelVesselName.textContent = vesselAPIData.name || "Brak nazwy";
    let detailsHtml = '<ul class="space-y-2 text-sm">';
    const displayOrder = [
        { label: "Typ statku", value: vesselAPIData.vessel_type?.name },
        { label: "Operator", value: vesselAPIData.operator?.name },
        { label: "Flota", value: vesselAPIData.fleet?.name },
        { label: "Status", value: vesselAPIData.status, capitalize: true },
        { label: "Rok produkcji", value: vesselAPIData.production_year },
        { label: "Nr rejestracyjny", value: vesselAPIData.registration_number },
    ];
    displayOrder.forEach(item => {
        let valueToDisplay = item.value;
        if (valueToDisplay === null || valueToDisplay === undefined || valueToDisplay === "") {
            valueToDisplay = "Brak danych";
        }
        if (item.capitalize && typeof valueToDisplay === 'string' && valueToDisplay !== "Brak danych") {
            valueToDisplay = valueToDisplay.charAt(0).toUpperCase() + valueToDisplay.slice(1);
        }
        detailsHtml += `<li><strong class="font-semibold text-gray-400">${item.label}:</strong> <span class="text-gray-200">${valueToDisplay}</span></li>`;
    });
    detailsHtml += '</ul>';

    if (vesselAPIData.id) {
        const sensorsOverviewUrl = `/sensors-overview/vessel/${vesselAPIData.id}`;
        detailsHtml += `
            <div class="mt-4 pt-4 border-t border-gray-700">
                <a href="${sensorsOverviewUrl}" 
                   class="block w-full text-center bg-teal-600 hover:bg-teal-700 text-white font-semibold py-2 px-4 rounded text-sm transition duration-150 ease-in-out">
                    Zobacz Odczyty Sensorów
                </a>
            </div>
        `;
    }

    panelVesselDetails.innerHTML = detailsHtml;
    panel.classList.remove('translate-x-full');
    panel.classList.remove('opacity-0');
}

function showVesselInfoPanel() {
    const panel = document.getElementById('vessel-info-panel');
    if (panel) {
        panel.classList.remove('translate-x-full');
        panel.classList.remove('opacity-0');
    }
}
function hideVesselInfoPanel() {
    const panel = document.getElementById('vessel-info-panel');
    const panelVesselName = document.getElementById('panel-vessel-name');
    const panelVesselDetails = document.getElementById('panel-vessel-details');
    if (panel) {
        panel.classList.add('translate-x-full');
        panel.classList.add('opacity-0');
    }
    if(panelVesselName) panelVesselName.textContent = "Wybierz statek";
    if(panelVesselDetails) panelVesselDetails.innerHTML = '<p class="text-gray-400">Wybierz statek na mapie, aby zobaczyć szczegóły.</p>';
}


function clearCurrentTraveledPath() {
    if (currentTraveledPath) {
        map.removeLayer(currentTraveledPath);
        currentTraveledPath = null;
    }
    historicalLocationMarkersGroup.clearLayers(); // Wyczyść markery historii
}

function clearCurrentPlannedRoute() {
    if (currentPlannedRoutePolyline) {
        map.removeLayer(currentPlannedRoutePolyline);
        currentPlannedRoutePolyline = null;
    }
    routePointMarkersLayerGroup.clearLayers();
}

// displayVesselLocationHistory - bez zmian, nadal wypełnia tabelę
async function displayVesselLocationHistory(vesselId, vesselName) {
    const historyContainer = document.getElementById('selected-vessel-history-container');
    const historyTableName = document.getElementById('history-vessel-name');
    const historyTableBody = document.getElementById('selected-vessel-history-table-body');
    if (!historyContainer || !historyTableBody || !historyTableName) return;

    historyTableName.textContent = vesselName || "Wybrany statek";
    historyTableBody.innerHTML = '<tr><td colspan="4" class="p-4 text-gray-400">Ładowanie historii...</td></tr>';

    try {
        const response = await fetch(`/public/vessels/${vesselId}/locations?limit=50`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(`Nie udało się pobrać historii lokalizacji (status: ${response.status}) ${errorData ? errorData.detail : ''}`);
        }
        const locationHistory = await response.json();

        if (locationHistory && locationHistory.length > 0) {
            let rowsHtml = '';
            locationHistory.slice().reverse().forEach(loc => { // Najnowsze na górze tabeli
                const timestamp = loc.timestamp ? new Date(loc.timestamp).toLocaleString() : 'Brak danych';
                const positionWKT = loc.position || 'Brak danych';
                const coords = parseWKTPosition(positionWKT);
                const positionDisplay = coords ? `${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}` : positionWKT;
                const heading = loc.heading !== null && loc.heading !== undefined ? parseFloat(loc.heading).toFixed(2) : 'Brak';
                const source = loc.source || 'Brak';
                rowsHtml += `
                    <tr>
                        <td class="border p-2">${timestamp}</td>
                        <td class="border p-2">${positionDisplay}</td>
                        <td class="border p-2">${heading}°</td>
                        <td class="border p-2">${source}</td>
                    </tr>
                `;
            });
            historyTableBody.innerHTML = rowsHtml;
        } else {
            historyTableBody.innerHTML = '<tr><td colspan="4" class="p-4 text-gray-500">Brak historii pozycji dla tego statku.</td></tr>';
        }
    } catch (error) {
        console.error("Błąd podczas pobierania lub wyświetlania historii lokalizacji:", error);
        historyTableBody.innerHTML = `<tr><td colspan="4" class="p-4 text-red-400">Błąd ładowania historii: ${error.message}</td></tr>`;
    }
}


async function handleVesselClick(vesselId) {
    if (selectedVesselId === vesselId) return;

    if (selectedVesselId && vesselMarkers[selectedVesselId]) {
        const oldMarker = vesselMarkers[selectedVesselId];
        oldMarker.setIcon(createVesselIcon(false, oldMarker.options.rotationAngle || 0));
    }

    clearCurrentTraveledPath();
    clearCurrentPlannedRoute();

    selectedVesselId = vesselId;
    const clickedMarker = vesselMarkers[vesselId];

    if (clickedMarker) {
        const currentRotation = clickedMarker.options.rotationAngle || 0;
        clickedMarker.setIcon(createVesselIcon(true, currentRotation));
        showVesselInfoPanel();

        try {
            const detailsResponse = await fetch(`/public/vessels/${selectedVesselId}`);
            if (!detailsResponse.ok) throw new Error('Nie udało się pobrać szczegółów statku');
            const vesselDetailsData = await detailsResponse.json();
            updateVesselInfoPanel(vesselDetailsData);

            await displayVesselLocationHistory(selectedVesselId, vesselDetailsData.name); // Wypełnia tabelę

            // Pobierz historię lokalizacji dla mapy (więcej punktów) i narysuj trasę oraz markery
            const historyResponse = await fetch(`/public/vessels/${selectedVesselId}/locations?limit=200`);
            if (!historyResponse.ok) {
                console.warn('Nie udało się pobrać pełnej historii lokalizacji dla trasy na mapie');
            } else {
                const locationHistory = await historyResponse.json();
                if (locationHistory && locationHistory.length > 0) {
                    const latLngsForPath = [];

                    const currentVesselData = allVesselsMapData.find(v => v.vessel_id === selectedVesselId);
                    const latestPositionTimestampFromInitial = currentVesselData ? currentVesselData.latest_timestamp : null;

                    locationHistory.forEach(loc => {
                        const coords = parseWKTPosition(loc.position);
                        if (coords) {
                            const latLng = [coords.lat, coords.lon];
                            latLngsForPath.push(latLng);

                            let isLatestPoint = false;
                            if (latestPositionTimestampFromInitial && loc.timestamp) {
                                if (loc.timestamp === latestPositionTimestampFromInitial) {
                                    isLatestPoint = true;
                                }
                            }

                            if (!isLatestPoint) {
                                const historyMarker = L.marker(latLng, {
                                    icon: historyLocationPointIcon,
                                })
                                .addTo(historicalLocationMarkersGroup);
                                
                                historyMarker.bindTooltip(
                                    `<b>Historia</b><br>Czas: ${new Date(loc.timestamp).toLocaleString()}<br>Kurs: ${parseFloat(loc.heading).toFixed(1)}°<br>Źródło: ${loc.source}`
                                );
                            }
                        }
                    });
                    historicalLocationMarkersGroup.addTo(map); // Dodaj grupę do mapy

                    if (latLngsForPath.length > 1) {
                        currentTraveledPath = L.polyline(latLngsForPath.slice().reverse(), {
                            color: '#007bff',
                            weight: 3,
                            opacity: 0.6
                        }).addTo(map);
                    }
                }
            }

            // Narysuj planowaną trasę (RoutePoint)
            const vesselData = allVesselsMapData.find(v => v.vessel_id === selectedVesselId);
            if (vesselData && vesselData.planned_route && vesselData.planned_route.length > 0) {
                const vesselCurrentPosition = parseWKTPosition(vesselData.latest_position_wkt);
                drawPlannedRouteOnMainMap(vesselData.planned_route, vesselCurrentPosition ? [vesselCurrentPosition.lat, vesselCurrentPosition.lon] : null);
            }

        } catch (error) {
            console.error(`Błąd podczas pobierania danych dla statku ${selectedVesselId}:`, error);
            const panelVesselDetails = document.getElementById('panel-vessel-details');
            if(panelVesselDetails) panelVesselDetails.innerHTML = `<p class="text-red-400">Nie udało się załadować danych: ${error.message}</p>`;
        }
    }
}

// drawPlannedRouteOnMainMap, addVesselMarker, loadInitialMapData - bez zmian
function drawPlannedRouteOnMainMap(plannedRoutePoints, vesselCurrentLatLng) {
    clearCurrentPlannedRoute();
    if (!plannedRoutePoints || plannedRoutePoints.length === 0) return;
    const routeLatLngs = plannedRoutePoints
        .filter(rp => rp.status === 'planned')
        .sort((a,b) => a.sequence_number - b.sequence_number)
        .map(rp => parseWKTPosition(rp.planned_position))
        .filter(p => p !== null)
        .map(coords => [coords.lat, coords.lon]);
    let fullPath = [];
    if (vesselCurrentLatLng) {
        fullPath.push(vesselCurrentLatLng);
    }
    fullPath = fullPath.concat(routeLatLngs);
    if (fullPath.length > 1) {
        currentPlannedRoutePolyline = L.polyline(fullPath, {
            color: 'orange',
            weight: 3,
            dashArray: '5, 5',
            opacity: 0.9
        }).addTo(map);
    }
    routeLatLngs.forEach((latLng, index) => {
        const rpData = plannedRoutePoints.find(rp => {
            const coords = parseWKTPosition(rp.planned_position);
            return coords && coords.lat === latLng[0] && coords.lon === latLng[1];
        });
        if (rpData) {
            L.marker(latLng, { icon: plannedRoutePointIcon })
            .addTo(routePointMarkersLayerGroup)
            .bindTooltip(`Planowany pkt ${rpData.sequence_number}<br>Status: ${rpData.status}`);
        }
    });
    routePointMarkersLayerGroup.addTo(map);
}

function addVesselMarker(vesselMapData) {
    const { vessel_id, name, latest_position_wkt, latest_heading } = vesselMapData;
    if (!latest_position_wkt) {
        console.warn(`Brak najnowszej pozycji dla statku ${name} (ID: ${vessel_id})`);
        return;
    }
    const coords = parseWKTPosition(latest_position_wkt);
    if (!coords) return;
    const latLng = [coords.lat, coords.lon];
    const rotation = parseFloat(latest_heading) || 0;
    if (vesselMarkers[vessel_id]) {
        vesselMarkers[vessel_id].setLatLng(latLng);
        vesselMarkers[vessel_id].setIcon(createVesselIcon(selectedVesselId === vessel_id, rotation));
        vesselMarkers[vessel_id].options.rotationAngle = rotation;
    } else {
        const icon = createVesselIcon(selectedVesselId === vessel_id, rotation);
        vesselMarkers[vessel_id] = L.marker(latLng, { icon: icon, rotationAngle: rotation })
            .addTo(map)
            .on('click', () => handleVesselClick(vessel_id));
        if (name) {
            vesselMarkers[vessel_id].bindTooltip(name);
        }
    }
}

async function loadInitialMapData() {
    try {
        const panelVesselName = document.getElementById('panel-vessel-name');
        const panelVesselDetails = document.getElementById('panel-vessel-details');
        if(panelVesselName) panelVesselName.textContent = "Ładowanie...";
        if(panelVesselDetails) panelVesselDetails.innerHTML = '<p class="text-gray-400">Ładowanie mapy...</p>';
        const response = await fetch('/map-data/initial-vessels-public');
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(`Nie udało się pobrać danych inicjalnych mapy: ${errorData ? errorData.detail : response.statusText}`);
        }
        allVesselsMapData = await response.json();
        console.log("Pobrano publiczne dane inicjalne mapy:", allVesselsMapData);
        if (!allVesselsMapData || allVesselsMapData.length === 0) {
            hideVesselInfoPanel();
            return;
        }
        allVesselsMapData.forEach(vesselData => {
            addVesselMarker(vesselData);
        });
        const firstVesselWithPosition = allVesselsMapData.find(v => v.latest_position_wkt);
        if (firstVesselWithPosition) {
            const firstPosCoords = parseWKTPosition(firstVesselWithPosition.latest_position_wkt);
            if (firstPosCoords) map.setView([firstPosCoords.lat, firstPosCoords.lon], 7);
            selectedVesselId = null;
            await handleVesselClick(firstVesselWithPosition.vessel_id);
        } else {
            hideVesselInfoPanel();
        }
    } catch (error) {
        console.error("Błąd podczas ładowania danych inicjalnych mapy:", error);
        hideVesselInfoPanel();
    }
}


// Inicjalizacja
document.addEventListener('DOMContentLoaded', () => {
    map = L.map('map', {
        center: [28.5, -16.5],
        zoom: 7,
        renderer: L.canvas() // Użyj L.canvas() dla potencjalnie lepszej wydajności z wieloma markerami
    });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18, minZoom: 3
    }).addTo(map);

    loadInitialMapData();
});
