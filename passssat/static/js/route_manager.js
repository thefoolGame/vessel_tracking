let routeMap;
const routePointMarkers = {};
let plannedRoutePolyline = null;
let vesselMarker = null; // Marker dla aktualnej pozycji statku
let temporaryNewPointMarker = null;

// Dostęp do zmiennych globalnych zdefiniowanych w szablonie HTML
// const CURRENT_VESSEL_ID (już zdefiniowane w HTML)

// Ikony 
const routePointIconDefault = L.divIcon({
  html: '<div style="background-color: blue; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.5);"></div>',
  className: "route-point-marker-default",
  iconSize: [12, 12],
  iconAnchor: [6, 6],
});
const routePointIconPlanned = L.divIcon({
  html: '<div style="background-color: orange; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.5);"></div>',
  className: "route-point-marker-planned",
  iconSize: [12, 12],
  iconAnchor: [6, 6],
});
const routePointIconReached = L.divIcon({
  html: '<div style="background-color: green; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.5);"></div>',
  className: "route-point-marker-reached",
  iconSize: [12, 12],
  iconAnchor: [6, 6],
});
const currentVesselPositionIcon = L.divIcon({ // Ikona dla aktualnej pozycji statku
    html: '<img src="/static/ship_selected.svg" style="width: 25px; height: 25px; transform-origin: center;">', // Możesz dostosować
    className: 'current-vessel-marker',
    iconSize: [25, 25],
    iconAnchor: [12.5, 12.5],
});
const tempNewPointIcon = L.divIcon({ // NOWA IKONA dla tymczasowego punktu
    html: '<div style="background-color: rgba(220, 220, 0, 0.7); width: 14px; height: 14px; border-radius: 50%; border: 2px dashed #333; box-shadow: 0 0 5px rgba(0,0,0,0.3);"></div>',
    className: "temp-new-point-marker",
    iconSize: [14, 14],
    iconAnchor: [7, 7],
});

const vesselIconUrl = "/static/ship_selected.svg"; 
const vesselIconSize = [25, 25];

function createCurrentVesselIcon(rotationAngle = 0) {
    return L.divIcon({
        html: `<img src="${vesselIconUrl}" style="transform: rotate(${rotationAngle}deg); width: ${vesselIconSize[0]}px; height: ${vesselIconSize[1]}px; transform-origin: center;">`,
        className: 'current-vessel-marker leaflet-custom-div-icon', // Dodajmy wspólną klasę
        iconSize: vesselIconSize,
        iconAnchor: [vesselIconSize[0] / 2, vesselIconSize[1] / 2],
    });
}

// Elementy DOM
const routePointForm = document.getElementById("routePointForm");
const routePointFormTitle = document.getElementById("route-point-form-title");
const submitRoutePointFormBtn = document.getElementById(
  "submitRoutePointFormBtn",
);
const cancelRoutePointFormBtn = document.getElementById(
  "cancelRoutePointFormBtn",
);
const routePointsListContainer = document.getElementById(
  "route-points-list-container",
);
const routePointItemTemplate = document.getElementById(
  "route-point-item-template",
);
const routePointFormError = document.getElementById("route-point-form-error");
const saveRouteOrderBtn = document.getElementById("saveRouteOrderBtn");


function initRouteMap() {
routeMap = L.map("route-map").setView([54.5, 18.5], 7);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
    minZoom: 3,
  }).addTo(routeMap);

  routeMap.on("click", handleMapClick);
  loadAndDisplayCurrentVesselPosition();
}

async function fetchRoutePoints() {
  try {
    const response = await fetch(
      `/admin/vessels/${CURRENT_VESSEL_ID}/route-management/points/`,
    );
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({detail: "Błąd serwera"}));
      throw new Error(
        `Nie udało się pobrać punktów trasy: ${errorData.detail || response.statusText}`,
      );
    }
    const routePoints = await response.json();
    return routePoints;
  } catch (error) {
    console.error("Błąd podczas pobierania punktów trasy:", error);
    if (routePointsListContainer)
      routePointsListContainer.innerHTML = `<p class="text-red-400 text-sm">Błąd ładowania punktów trasy: ${error.message}</p>`;
    return [];
  }
}

function renderRoutePointsList(routePoints) {
  if (!routePointsListContainer || !routePointItemTemplate) return;

  routePointsListContainer.innerHTML = ""; 

  if (!routePoints || routePoints.length === 0) {
    routePointsListContainer.innerHTML =
      '<p class="text-gray-400 text-sm">Brak zdefiniowanych punktów trasy dla tego statku.</p>';
    if (saveRouteOrderBtn) saveRouteOrderBtn.classList.add("hidden");
    return;
  }

  routePoints.forEach((rp) => {
    const templateClone = routePointItemTemplate.content.cloneNode(true);
    const listItem = templateClone.querySelector(".route-point-item");

    listItem.dataset.routePointId = rp.route_point_id;
    listItem.dataset.sequenceNumber = rp.sequence_number; 

    templateClone.querySelector(".sequence-display").textContent =
      rp.sequence_number;
    const coords = parseWKTPointForDisplay(rp.planned_position);
    templateClone.querySelector(".position-display").textContent = coords
      ? `${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}`
      : "Błędna pozycja";
    templateClone.querySelector(".status-display").textContent =
      rp.status || "N/A";
    templateClone.querySelector(".arrival-display").textContent = rp.planned_arrival_time
      ? new Date(rp.planned_arrival_time).toLocaleString() // Zakładamy UTC z backendu
      : "N/A";

    const editBtn = templateClone.querySelector(".edit-route-point-btn");
    editBtn.addEventListener("click", () => populateFormForEdit(rp));

    const deleteBtn = templateClone.querySelector(".delete-route-point-btn");
    deleteBtn.addEventListener("click", () =>
      handleDeleteRoutePoint(rp.route_point_id),
    );

    routePointsListContainer.appendChild(templateClone);
  });

  if (typeof Sortable !== "undefined") {
    new Sortable(routePointsListContainer, {
      animation: 150,
      handle: ".drag-handle",
      ghostClass: "bg-gray-600",
      onEnd: handleRouteOrderChange,
    });
    // Pokaż przycisk zapisu kolejności tylko jeśli są punkty
    if (saveRouteOrderBtn && routePoints.length > 0) saveRouteOrderBtn.classList.remove("hidden");
    else if (saveRouteOrderBtn) saveRouteOrderBtn.classList.add("hidden");

  } else {
    if (saveRouteOrderBtn) saveRouteOrderBtn.classList.add("hidden");
  }
}

function parseWKTPointForDisplay(wktPoint) {
  if (!wktPoint || !wktPoint.toUpperCase().startsWith("POINT (")) return null;
  try {
    const match = wktPoint.match(/\(([^)]+)\)/);
    if (!match || !match[1]) return null;
    const parts = match[1].split(" ");
    return { lon: parseFloat(parts[0]), lat: parseFloat(parts[1]) };
  } catch (e) {
    console.error("Błąd parsowania WKT dla wyświetlania:", wktPoint, e);
    return null;
  }
}


function updateRoutePointMarkers(routePoints) {
  Object.values(routePointMarkers).forEach((marker) => routeMap.removeLayer(marker));
  for (const id in routePointMarkers) {
      delete routePointMarkers[id];
  }

  routePoints.forEach((rp) => {
    const coords = parseWKTPointForDisplay(rp.planned_position);
    if (coords) {
      const latLng = [coords.lat, coords.lon];
      let icon = routePointIconDefault;
      if (rp.status === "planned") icon = routePointIconPlanned;
      else if (rp.status === "reached") icon = routePointIconReached;

      let popupContent = `<b>Punkt ${rp.sequence_number}</b><br>Status: ${rp.status}`;
      if (rp.planned_arrival_time) {
        popupContent += `<br>Plan. przybycie: ${new Date(rp.planned_arrival_time).toLocaleString()}`;
      }
      if (rp.planned_departure_time) {
        popupContent += `<br>Plan. odjazd: ${new Date(rp.planned_departure_time).toLocaleString()}`;
      }
      if (rp.status === "reached" && rp.actual_arrival_time) {
        popupContent += `<br><strong class="text-green-400">Fakt. przybycie: ${new Date(rp.actual_arrival_time).toLocaleString()}</strong>`;
      }
      popupContent += `<br><button class="text-blue-500 hover:underline" onclick="populateFormForEditById(${rp.route_point_id})">Edytuj</button>`;
      popupContent += ` | <button class="text-red-500 hover:underline" onclick="handleDeleteRoutePoint(${rp.route_point_id})">Usuń</button>`; // NOWY PRZYCISK USUŃ

      const marker = L.marker(latLng, {
        icon: icon,
        draggable: true,
        routePointId: rp.route_point_id,
      })
        .addTo(routeMap)
        .bindPopup(popupContent);

      marker.on("dragend", function (event) {
        const newLatLng = event.target.getLatLng();
        handleMarkerDragEnd(rp.route_point_id, newLatLng);
      });

      routePointMarkers[rp.route_point_id] = marker;
    }
  });

  drawPlannedRoute(routePoints);
}

async function loadAndDisplayCurrentVesselPosition() {
    try {
        const response = await fetch(`/admin/vessels/${CURRENT_VESSEL_ID}/route-management/current-position/`);
        if (!response.ok) {
            console.warn("Nie udało się pobrać aktualnej pozycji statku.");
            return null;
        }
        const locationData = await response.json();

        if (locationData && locationData.position) {
            const coords = parseWKTPointForDisplay(locationData.position);
            if (coords) {
                const latLng = [coords.lat, coords.lon];
                const heading = parseFloat(locationData.heading) || 0;

                if (vesselMarker) {
                    vesselMarker.setLatLng(latLng);
                    vesselMarker.setIcon(createCurrentVesselIcon(heading));
                } else {
                    const icon = createCurrentVesselIcon(heading);
                    vesselMarker = L.marker(latLng, {
                        icon: icon,
                        currentHeading: heading 
                    }).addTo(routeMap);
                }
                return latLng;
            }
        }
    } catch (error) {
        console.warn("Błąd ładowania aktualnej pozycji statku:", error);
    }
    return null;
}


function drawPlannedRoute(allRoutePoints) {
  if (plannedRoutePolyline) {
    routeMap.removeLayer(plannedRoutePolyline);
    plannedRoutePolyline = null;
  }

  const plannedPointsCoords = allRoutePoints
    .filter(rp => rp.status === 'planned')
    // Sortuj po sequence_number, aby linia była w poprawnej kolejności
    .sort((a, b) => a.sequence_number - b.sequence_number)
    .map(rp => parseWKTPointForDisplay(rp.planned_position))
    .filter(Boolean) // Usuń null jeśli parsowanie się nie udało
    .map(coords => [coords.lat, coords.lon]);

  let finalPathCoords = [];
  if (vesselMarker) { 
      const vesselLatLng = vesselMarker.getLatLng();
      if (vesselLatLng) {
        finalPathCoords.push(vesselLatLng);
      }
  }
  finalPathCoords = finalPathCoords.concat(plannedPointsCoords);


  if (finalPathCoords.length > 1) {
    plannedRoutePolyline = L.polyline(finalPathCoords, {
      color: "orange",
      weight: 3,
      opacity: 0.8,
    }).addTo(routeMap);
  }
}


async function initializeRouteManagement() {
  initRouteMap(); // Inicjalizuje mapę i ładuje pozycję statku
  const routePoints = await fetchRoutePoints();
  renderRoutePointsList(routePoints);
  updateRoutePointMarkers(routePoints); // To wywoła drawPlannedRoute z aktualnymi punktami

  if (routePoints.length > 0) {
    const validCoords = routePoints
        .map((rp) => parseWKTPointForDisplay(rp.planned_position))
        .filter(Boolean)
        .map((coords) => [coords.lat, coords.lon]);
    
    if (vesselMarker && vesselMarker.getLatLng()) {
        validCoords.push(vesselMarker.getLatLng());
    }

    if (validCoords.length > 0) {
        const bounds = L.latLngBounds(validCoords);
        if (bounds.isValid()) {
            routeMap.fitBounds(bounds, { padding: [50, 50] });
        }
    }
  } else if (vesselMarker) { // Jeśli nie ma punktów trasy, ale jest statek
      routeMap.setView(vesselMarker.getLatLng(), 10); // Ustaw widok na statek
  }
}

function handleMapClick(e) {
  console.log("Kliknięto na mapie:", e.latlng);

  if (temporaryNewPointMarker) {
    temporaryNewPointMarker.setLatLng(e.latlng);
  } else {
    temporaryNewPointMarker = L.marker(e.latlng, {
      icon: tempNewPointIcon,
      zIndexOffset: 900, // Aby był pod innymi markerami, jeśli się nałożą
    }).addTo(routeMap);
  }

  if (routePointForm) {
    routePointForm.elements["planned_lat"].value = e.latlng.lat.toFixed(6);
    routePointForm.elements["planned_lon"].value = e.latlng.lng.toFixed(6);

    const existingPoints = Array.from(
      routePointsListContainer.querySelectorAll(".route-point-item"),
    );
    let nextSequence = 1;
    if (existingPoints.length > 0) {
        const maxSequence = Math.max(...existingPoints.map(item => parseInt(item.dataset.sequenceNumber) || 0));
        nextSequence = maxSequence + 1;
    }
    routePointForm.elements["sequence_number"].value = nextSequence;

    if (routePointForm.elements["route_point_id_form_field"].value !== "") {
        resetAndPrepareFormForAdd(); // To również usunie tymczasowy marker, jeśli jest
    } else {
        // Jeśli formularz był już pusty (tryb dodawania), tylko aktualizujemy pozycję
        // i upewniamy się, że tymczasowy marker jest widoczny.
    }
    routePointForm.elements["sequence_number"].focus();
  }
}

function populateFormForEdit(routePointData) {
  if (!routePointForm) return;
  resetRoutePointFormError();
  removeTemporaryNewPointMarker(); 

  routePointForm.elements["route_point_id_form_field"].value =
    routePointData.route_point_id;
  routePointForm.elements["sequence_number"].value =
    routePointData.sequence_number;

  const coords = parseWKTPointForDisplay(routePointData.planned_position);
  if (coords) {
    routePointForm.elements["planned_lat"].value = coords.lat.toFixed(6);
    routePointForm.elements["planned_lon"].value = coords.lon.toFixed(6);
  } else {
    routePointForm.elements["planned_lat"].value = "";
    routePointForm.elements["planned_lon"].value = "";
  }

  routePointForm.elements["planned_arrival_time"].value = routePointData.planned_arrival_time
    ? datetimeLocalInputFormat(new Date(routePointData.planned_arrival_time))
    : "";
  routePointForm.elements["planned_departure_time"].value = routePointData.planned_departure_time
    ? datetimeLocalInputFormat(new Date(routePointData.planned_departure_time)) 
    : "";
  routePointForm.elements["status"].value = routePointData.status;

  if (routePointFormTitle)
    routePointFormTitle.textContent = "Edytuj Punkt Trasy";
  if (submitRoutePointFormBtn)
    submitRoutePointFormBtn.textContent = "Zapisz Zmiany";
}

async function populateFormForEditById(routePointId) {
    try {
        // Użyj nowego endpointu proxy do pobrania danych pojedynczego punktu
        const response = await fetch(`/admin/vessels/${CURRENT_VESSEL_ID}/route-management/points/${routePointId}`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({detail: "Błąd serwera"}));
            throw new Error(`Nie udało się pobrać danych punktu: ${errorData.detail || response.statusText}`);
        }
        const rpData = await response.json();
        populateFormForEdit(rpData);
        if (routeMap.closePopup) routeMap.closePopup();
    } catch (error) {
        console.error("Błąd pobierania danych punktu do edycji:", error);
        setRoutePointFormError("Nie udało się załadować danych punktu do edycji.");
    }
}

function resetAndPrepareFormForAdd() {
  if (!routePointForm) return;
  routePointForm.reset();
  routePointForm.elements["route_point_id_form_field"].value = "";
  if (routePointFormTitle) routePointFormTitle.textContent = "Dodaj Punkt Trasy";
  if (submitRoutePointFormBtn)
    submitRoutePointFormBtn.textContent = "Dodaj Punkt";
  resetRoutePointFormError();
  removeTemporaryNewPointMarker();
}

function removeTemporaryNewPointMarker() {
    if (temporaryNewPointMarker) {
        routeMap.removeLayer(temporaryNewPointMarker);
        temporaryNewPointMarker = null;
    }
}

async function handleMarkerDragEnd(routePointId, newLatLng) {
  removeTemporaryNewPointMarker();
  console.log(
    `Marker ${routePointId} przeciągnięty do: ${newLatLng.lat}, ${newLatLng.lng}`,
  );
  const wktPosition = `POINT(${newLatLng.lng.toFixed(6)} ${newLatLng.lat.toFixed(6)})`;
  try {
    const response = await fetch(
      `/admin/vessels/${CURRENT_VESSEL_ID}/route-management/points/${routePointId}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ planned_position: wktPosition }), // Wysyłamy tylko zmienioną pozycję
      },
    );
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({detail: "Błąd serwera"}));
      throw new Error(
        `Nie udało się zaktualizować pozycji punktu: ${errorData.detail || response.statusText}`,
      );
    }
    const updatedPoints = await fetchRoutePoints();
    renderRoutePointsList(updatedPoints);
    updateRoutePointMarkers(updatedPoints);
    console.log(`Pozycja punktu ${routePointId} zaktualizowana.`);
  } catch (error) {
    console.error("Błąd aktualizacji pozycji po przeciągnięciu:", error);
    setRoutePointFormError(`Błąd aktualizacji pozycji: ${error.message}`);
    const updatedPoints = await fetchRoutePoints(); // Przywróć stan z serwera
    updateRoutePointMarkers(updatedPoints);
  }
}

async function handleRoutePointFormSubmit(event) {
  event.preventDefault();
  resetRoutePointFormError();
  removeTemporaryNewPointMarker();

  const formData = new FormData(routePointForm);
  const routePointId = formData.get("route_point_id_form");

  const plannedLat = parseFloat(formData.get("planned_lat"));
  const plannedLon = parseFloat(formData.get("planned_lon"));

  if (isNaN(plannedLat) || isNaN(plannedLon)) {
    setRoutePointFormError("Nieprawidłowe współrzędne geograficzne.");
    return;
  }

  // Obsługa czasu - konwersja z datetime-local na UTC ISO string
  const arrivalTimeString = formData.get("planned_arrival_time");
  const departureTimeString = formData.get("planned_departure_time");

  const payload = {
    sequence_number: parseInt(formData.get("sequence_number")),
    planned_position: `POINT (${plannedLon.toFixed(6)} ${plannedLat.toFixed(6)})`, // Poprawiony WKT
    planned_arrival_time: arrivalTimeString ? new Date(arrivalTimeString).toISOString() : null,
    planned_departure_time: departureTimeString ? new Date(departureTimeString).toISOString() : null,
    status: formData.get("status"),
  };
  // Usuń klucze z null, jeśli backend tego nie lubi (Pydantic z Optional powinien obsłużyć null)
  if (!payload.planned_arrival_time) delete payload.planned_arrival_time;
  if (!payload.planned_departure_time) delete payload.planned_departure_time;

  console.log("Wysyłany payload (RoutePoint):", JSON.stringify(payload, null, 2));

  let url, method;
  if (routePointId) {
    url = `/admin/vessels/${CURRENT_VESSEL_ID}/route-management/points/${routePointId}`;
    method = "PUT";
  } else {
    url = `/admin/vessels/${CURRENT_VESSEL_ID}/route-management/points/`;
    method = "POST";
  }

  try {
    const response = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      let errorDetail = "Nieznany błąd serwera.";
      try {
        const errorData = await response.json();
        if (Array.isArray(errorData.detail)) {
          errorDetail = errorData.detail.map(err => `${err.loc && err.loc.length > 1 ? err.loc[1] : 'body'}: ${err.msg}`).join("; ");
        } else if (errorData.detail) { errorDetail = errorData.detail; }
        else { errorDetail = JSON.stringify(errorData); }
      } catch (e) { errorDetail = await response.text(); }
      throw new Error(`Operacja nie powiodła się (status: ${response.status}): ${errorDetail}`);
    }
    const updatedPoints = await fetchRoutePoints();
    renderRoutePointsList(updatedPoints);
    updateRoutePointMarkers(updatedPoints);
    resetAndPrepareFormForAdd();
  } catch (error) {
    console.error("Błąd zapisu punktu trasy:", error);
    setRoutePointFormError(error.message);
  }
}

async function handleDeleteRoutePoint(routePointId) {
  if (!confirm("Czy na pewno chcesz usunąć ten punkt trasy?")) return;
  resetRoutePointFormError();

  try {
    const response = await fetch(
      `/admin/vessels/${CURRENT_VESSEL_ID}/route-management/points/${routePointId}`,
      {
        method: "DELETE",
      },
    );
    if (!response.ok && response.status !== 204) {
      const errorData = await response.json().catch(() => ({detail: "Błąd serwera"}));
      throw new Error(
        `Nie udało się usunąć punktu: ${errorData.detail || response.statusText}`,
      );
    }
    const updatedPoints = await fetchRoutePoints();
    renderRoutePointsList(updatedPoints);
    updateRoutePointMarkers(updatedPoints);
    // resetAndPrepareFormForAdd();
  } catch (error) {
    console.error("Błąd usuwania punktu trasy:", error);
    alert(`Błąd usuwania: ${error.message}`);
  }
}

function handleRouteOrderChange(evt) {
    if (saveRouteOrderBtn) saveRouteOrderBtn.classList.remove("hidden");
}

async function saveNewRouteOrder() {
    if (!saveRouteOrderBtn || saveRouteOrderBtn.classList.contains("hidden")) return;
    resetRoutePointFormError();

    const items = Array.from(routePointsListContainer.children);
    const orderedRoutePointIds = items.map(item => parseInt(item.dataset.routePointId));

    if (orderedRoutePointIds.length === 0 && items.length > 0) { // Sprawdź czy są itemy, ale ID nie udało się sparsować
        setRoutePointFormError("Błąd odczytu kolejności punktów. Upewnij się, że ID są poprawnie ustawione.");
        return;
    }
    
    // Jeśli nie ma punktów, nie ma co zapisywać
    if (orderedRoutePointIds.length === 0) {
        saveRouteOrderBtn.classList.add("hidden");
        return;
    }


    try {
        const response = await fetch(`/admin/vessels/${CURRENT_VESSEL_ID}/route-management/points/reorder`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(orderedRoutePointIds),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({detail: "Błąd serwera"}));
            throw new Error(`Nie udało się zapisać nowej kolejności: ${errorData.detail || response.statusText}`);
        }
        
        const updatedPoints = await fetchRoutePoints(); // Pobierz zaktualizowane dane z serwera
        renderRoutePointsList(updatedPoints);       // Odśwież listę (z nowymi sequence_number)
        updateRoutePointMarkers(updatedPoints);     // Odśwież markery
        saveRouteOrderBtn.classList.add("hidden");
        alert("Nowa kolejność punktów trasy została zapisana.");

    } catch (error) {
        console.error("Błąd zapisu kolejności punktów:", error);
        setRoutePointFormError(`Błąd zapisu kolejności: ${error.message}`);
    }
}

function setRoutePointFormError(message) {
    if (routePointFormError) {
        routePointFormError.textContent = message;
        routePointFormError.classList.remove("hidden");
    }
}
function resetRoutePointFormError() {
    if (routePointFormError) {
        routePointFormError.textContent = "";
        routePointFormError.classList.add("hidden");
    }
}

function datetimeLocalInputFormat(date) {
  if (!(date instanceof Date) || isNaN(date)) return "";
  const YYYY = date.getFullYear();
  const MM = String(date.getMonth() + 1).padStart(2, "0");
  const DD = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return `${YYYY}-${MM}-${DD}T${hh}:${mm}`;
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("route-map")) {
    initializeRouteManagement();

    if (routePointForm) {
      routePointForm.addEventListener("submit", handleRoutePointFormSubmit);
    }
    if (cancelRoutePointFormBtn) {
      cancelRoutePointFormBtn.addEventListener("click", () => {
          resetAndPrepareFormForAdd(); 
      });
    }
    if (saveRouteOrderBtn) {
        saveRouteOrderBtn.addEventListener("click", saveNewRouteOrder);
    }
  }
});
