let locationMap;
const locationMarkers = {}; // Obiekt do przechowywania markerów wpisów lokalizacji
let traveledPathPolyline = null; // Linia łącząca historyczne punkty
let temporaryLocationMarker = null

// Dostęp do zmiennej globalnej zdefiniowanej w szablonie HTML
// const CURRENT_VESSEL_ID_LOC (zdefiniowane w HTML)

// Ikony (możesz dostosować)
const locationMarkerIcon = L.divIcon({
  html: '<div style="background-color: red; width: 10px; height: 10px; border-radius: 50%; border: 1px solid white; box-shadow: 0 0 3px rgba(0,0,0,0.5);"></div>',
  className: "location-history-marker",
  iconSize: [10, 10],
  iconAnchor: [5, 5],
});
const tempLocationIcon = L.divIcon({ // Ikona dla tymczasowego punktu lokalizacji
    html: '<div style="background-color: rgba(255, 0, 0, 0.5); width: 12px; height: 12px; border-radius: 50%; border: 2px dashed #cc0000; box-shadow: 0 0 5px rgba(0,0,0,0.3);"></div>',
    className: "temp-location-marker",
    iconSize: [12, 12],
    iconAnchor: [6, 6],
});

// Elementy DOM
const locationEntryForm = document.getElementById("locationEntryForm");
const locationEntryFormTitle = document.getElementById(
  "location-entry-form-title",
);
const submitLocationEntryFormBtn = document.getElementById(
  "submitLocationEntryFormBtn",
);
const cancelLocationEntryFormBtn = document.getElementById(
  "cancelLocationEntryFormBtn",
);
const locationEntriesListContainer = document.getElementById(
  "location-entries-list-container",
);
const locationEntryItemTemplate = document.getElementById(
  "location-entry-item-template",
);
const locationEntryFormError = document.getElementById(
  "location-entry-form-error",
);

/**
 * Inicjalizuje mapę Leaflet.
 */
function initLocationHistoryMap() {
  locationMap = L.map("location-history-map").setView([54.5, 18.5], 6); // Domyślne centrum

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
    minZoom: 3,
  }).addTo(locationMap);

  locationMap.on("click", handleLocationMapClick);
}

/**
 * Pobiera wpisy lokalizacji dla aktualnego statku z API (przez proxy).
 */
async function fetchLocationEntries() {
  try {
    // Endpoint proxy do listowania lokalizacji
    const response = await fetch(
      `/admin/vessels/${CURRENT_VESSEL_ID_LOC}/location-history-management/locations/`, // Zaktualizowana ścieżka
    );
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({detail: "Błąd serwera"}));
      throw new Error(
        `Nie udało się pobrać historii lokalizacji: ${errorData.detail || response.statusText}`,
      );
    }
    const locations = await response.json();
    return locations; // Oczekujemy List[LocationResponse]
  } catch (error) {
    console.error("Błąd podczas pobierania historii lokalizacji:", error);
    if (locationEntriesListContainer)
      locationEntriesListContainer.innerHTML = `<p class="text-red-400 text-sm">Błąd ładowania historii: ${error.message}</p>`;
    return [];
  }
}

/**
 * Renderuje listę wpisów lokalizacji w kontenerze.
 * @param {Array<Object>} locations - Lista obiektów lokalizacji.
 */
function renderLocationEntriesList(locations) {
  if (!locationEntriesListContainer || !locationEntryItemTemplate) return;

  locationEntriesListContainer.innerHTML = ""; // Wyczyść

  if (!locations || locations.length === 0) {
    locationEntriesListContainer.innerHTML =
      '<p class="text-gray-400 text-sm">Brak zapisanych pozycji dla tego statku.</p>';
    return;
  }

  // Sortuj po timestamp malejąco (najnowsze pierwsze), jeśli API tego nie robi
  // locations.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  locations.forEach((loc) => {
    const templateClone = locationEntryItemTemplate.content.cloneNode(true);
    const listItem = templateClone.querySelector(".location-entry-item");

    listItem.dataset.locationId = loc.location_id;

    templateClone.querySelector(".timestamp-display").textContent = new Date(
      loc.timestamp, 
    ).toLocaleString();
    templateClone.querySelector(".source-display").textContent =
      loc.source || "N/A";

    const coords = parseWKTPointForDisplayLoc(loc.position); // Użyj dedykowanej funkcji parsowania
    templateClone.querySelector(".position-display").textContent = coords
      ? `${coords.lat.toFixed(5)}, ${coords.lon.toFixed(5)}`
      : "Błędna pozycja";
    templateClone.querySelector(".heading-display").textContent =
      parseFloat(loc.heading).toFixed(2);
    
const accuracyDisplay = templateClone.querySelector(".accuracy-display");
    const accuracyContainer = templateClone.querySelector(".accuracy-container"); // Zakładamy, że szablon ma <span class="accuracy-container">...</span>

    if (loc.accuracy_meters !== null && loc.accuracy_meters !== undefined) {
        if (accuracyDisplay) accuracyDisplay.textContent = parseFloat(loc.accuracy_meters).toFixed(1);
        if (accuracyContainer) accuracyContainer.style.display = 'inline';
    } else {
        if (accuracyContainer) accuracyContainer.style.display = 'none';
        else if (accuracyDisplay) accuracyDisplay.textContent = "N/A";
    }


    const editBtn = templateClone.querySelector(".edit-location-entry-btn");
    editBtn.addEventListener("click", () => populateLocationFormForEdit(loc));

    const deleteBtn = templateClone.querySelector(
      ".delete-location-entry-btn",
    );
    deleteBtn.addEventListener("click", () =>
      handleDeleteLocationEntry(loc.location_id),
    );

    locationEntriesListContainer.appendChild(templateClone);
  });
}

/**
 * Paruje string WKT "POINT(lon lat)" na obiekt {lon, lat} dla wyświetlania.
 * Dedykowana funkcja, aby uniknąć konfliktu nazw, jeśli ten skrypt jest ładowany z innymi.
 * @param {string} wktPoint
 */
function parseWKTPointForDisplayLoc(wktPoint) {
  if (!wktPoint || !wktPoint.toUpperCase().startsWith("POINT")) return null;
  try {
    const match = wktPoint.match(/\(([^)]+)\)/);
    if (!match || !match[1]) return null;
    const parts = match[1].split(" ");
    return { lon: parseFloat(parts[0]), lat: parseFloat(parts[1]) };
  } catch (e) {
    console.error("Błąd parsowania WKT dla lokalizacji:", wktPoint, e);
    return null;
  }
}

/**
 * Dodaje lub aktualizuje markery wpisów lokalizacji na mapie.
 * @param {Array<Object>} locations
 */
function updateLocationMarkers(locations) {
  Object.values(locationMarkers).forEach((marker) => locationMap.removeLayer(marker));
  for (const id in locationMarkers) {
      delete locationMarkers[id];
  }

  const latLngs = [];

  locations.forEach((loc) => {
    const coords = parseWKTPointForDisplayLoc(loc.position);
    if (coords) {
      const latLng = [coords.lat, coords.lon];
      latLngs.push({latlng: latLng, timestamp: loc.timestamp}); // Dodaj do rysowania trasy

      let popupContent = `<b>${new Date(loc.timestamp).toLocaleString()}</b><br>Źródło: ${loc.source}<br>Poz: ${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}`;
      popupContent += `<br><button class="text-blue-500 hover:underline mr-2" onclick="populateLocationFormForEditById(${loc.location_id})">Edytuj</button>`;
      popupContent += `<button class="text-red-500 hover:underline" onclick="handleDeleteLocationEntry(${loc.location_id})">Usuń</button>`;

      const marker = L.marker(latLng, {
        icon: locationMarkerIcon,
        locationId: loc.location_id,
      })
        .addTo(locationMap)
        .bindPopup(popupContent);
      locationMarkers[loc.location_id] = marker;
    }
  });

  drawTraveledPath(latLngs);
}

/**
 * Rysuje przebytą trasę na podstawie historycznych punktów.
 * @param {Array<Object>} pointsWithTimestamp - Lista obiektów {latlng, timestamp}.
 */
function drawTraveledPath(pointsWithTimestamp) {
  if (traveledPathPolyline) {
    locationMap.removeLayer(traveledPathPolyline);
    traveledPathPolyline = null;
  }
  // Sortuj punkty po timestamp rosnąco (od najstarszego do najnowszego)
  const sortedPoints = pointsWithTimestamp
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .map(p => p.latlng);

  if (sortedPoints.length > 1) {
    traveledPathPolyline = L.polyline(sortedPoints, {
      color: "cyan", // Inny kolor niż trasa planowana
      weight: 2,
      opacity: 0.7,
    }).addTo(locationMap);
  }
}

/**
 * Główna funkcja inicjalizująca i ładująca dane.
 */
async function initializeLocationHistoryManagement() {
  initLocationHistoryMap();
  const locations = await fetchLocationEntries();
  renderLocationEntriesList(locations);
  updateLocationMarkers(locations);

  if (locations.length > 0) {
    const bounds = L.latLngBounds(
      locations
        .map((loc) => parseWKTPointForDisplayLoc(loc.position))
        .filter(Boolean)
        .map((coords) => [coords.lat, coords.lon]),
    );
    if (bounds.isValid()) {
      locationMap.fitBounds(bounds, { padding: [30, 30] });
    }
  }
}

// --- Obsługa formularza (szkielety funkcji) ---

function handleLocationMapClick(e) {
  console.log("Kliknięto na mapie lokalizacji:", e.latlng);

  if (temporaryLocationMarker) {
    temporaryLocationMarker.setLatLng(e.latlng);
  } else {
    temporaryLocationMarker = L.marker(e.latlng, {
        icon: tempLocationIcon, // Użyj nowej ikony
        zIndexOffset: 1000 // Aby był na wierzchu
    }).addTo(locationMap);
  }

  if (locationEntryForm) {
    locationEntryForm.elements["loc_lat"].value = e.latlng.lat.toFixed(6);
    locationEntryForm.elements["loc_lon"].value = e.latlng.lng.toFixed(6);
    
    if (locationEntryForm.elements["location_id_form_field"].value !== "") {
        resetAndPrepareLocationFormForAdd(); // To usunie też temporaryLocationMarker
    } else {
        // Jeśli już w trybie dodawania, tylko aktualizujemy pozycję
    }
    // Ustaw domyślny timestamp na teraz, jeśli dodajemy nowy
    if (!locationEntryForm.elements["location_id_form_field"].value) {
        locationEntryForm.elements["timestamp"].value = datetimeLocalInputFormatLoc(new Date());
    }
    locationEntryForm.elements["loc_heading"].focus();
  }
}

function populateLocationFormForEdit(locationData) {
  if (!locationEntryForm) return;
  resetLocationEntryFormError();
  removeTemporaryLocationMarker();

  locationEntryForm.elements["location_id_form_field"].value =
    locationData.location_id;

  const localDate = new Date(locationData.timestamp); // JS Date object z UTC string
  locationEntryForm.elements["timestamp"].value = datetimeLocalInputFormatLoc(localDate);

  const coords = parseWKTPointForDisplayLoc(locationData.position);
  if (coords) {
    locationEntryForm.elements["loc_lat"].value = coords.lat.toFixed(6);
    locationEntryForm.elements["loc_lon"].value = coords.lon.toFixed(6);
  } else {
    locationEntryForm.elements["loc_lat"].value = "";
    locationEntryForm.elements["loc_lon"].value = "";
  }
  locationEntryForm.elements["loc_heading"].value = parseFloat(locationData.heading).toFixed(2);
  locationEntryForm.elements["loc_accuracy"].value = locationData.accuracy_meters !== null ? parseFloat(locationData.accuracy_meters).toFixed(1) : "";
  // Pole source nie jest edytowalne w formularzu, backend ustawi na "manual"

  if (locationEntryFormTitle)
    locationEntryFormTitle.textContent = "Edytuj Wpis Lokalizacji";
  if (submitLocationEntryFormBtn)
    submitLocationEntryFormBtn.textContent = "Zapisz Zmiany";
}

async function populateLocationFormForEditById(locationId) {
    try {
        const response = await fetch(`/admin/vessels/${CURRENT_VESSEL_ID_LOC}/location-history-management/locations/${locationId}`);
        if (!response.ok) {
             const errorData = await response.json().catch(() => ({detail: "Błąd serwera"}));
            throw new Error(`Nie udało się pobrać danych lokalizacji: ${errorData.detail || response.statusText}`);
        }
        const locData = await response.json();
        populateLocationFormForEdit(locData);
        if(locationMap.closePopup) locationMap.closePopup();
    } catch (error) {
        console.error("Błąd pobierania danych lokalizacji do edycji:", error);
        setLocationEntryFormError("Nie udało się załadować danych do edycji.");
    }
}


function resetAndPrepareLocationFormForAdd() {
  if (!locationEntryForm) return;
  locationEntryForm.reset();
  locationEntryForm.elements["location_id_form_field"].value = "";
  if (locationEntryFormTitle)
    locationEntryFormTitle.textContent = "Dodaj Wpis Lokalizacji";
  if (submitLocationEntryFormBtn)
    submitLocationEntryFormBtn.textContent = "Dodaj Wpis";
  resetLocationEntryFormError();
  removeTemporaryLocationMarker(); 
}

function removeTemporaryLocationMarker() {
    if (temporaryLocationMarker) {
        locationMap.removeLayer(temporaryLocationMarker);
        temporaryLocationMarker = null;
    }
}

async function handleLocationEntryFormSubmit(event) {
  event.preventDefault();
  resetLocationEntryFormError();
  removeTemporaryLocationMarker();

  const formData = new FormData(locationEntryForm);

  const lat = parseFloat(formData.get("latitude"));
  const lon = parseFloat(formData.get("longitude"));
  const heading = parseFloat(formData.get("heading"));

  if (isNaN(lat) || isNaN(lon)) {
    setLocationEntryFormError("Nieprawidłowe współrzędne geograficzne.");
    return;
  }
   if (isNaN(heading) || heading < 0 || heading >= 360) {
    setLocationEntryFormError("Nieprawidłowa wartość kursu (0-359.99).");
    return;
  }

  const localTimestampString = formData.get("timestamp"); // Użyj name="timestamp"
  if (!localTimestampString) {
      setLocationEntryFormError("Timestamp jest wymagany.");
      return;
  }

  const localDateObject = new Date(localTimestampString);
  const utcTimestampString = localDateObject.toISOString();

  const accuracyVal = formData.get("accuracy_meters");
  let accuracy_meters_payload = null;
  if (accuracyVal) {
    const parsedAccuracy = parseFloat(accuracyVal);
    if (isNaN(parsedAccuracy) || parsedAccuracy < 0 || parsedAccuracy > 99999.99) {
      setLocationEntryFormError("Dokładność musi być liczbą między 0 a 99999.99.");
      return;
    }
    accuracy_meters_payload = parsedAccuracy.toFixed(1); // lub 2, jeśli chcesz zachować precyzję
  }

  const payload = {
    timestamp: utcTimestampString, // WYSYŁAMY CZAS UTC
    position: `POINT (${lon.toFixed(6)} ${lat.toFixed(6)})`, // Poprawiony WKT
    heading: heading.toFixed(2),
    accuracy_meters: accuracy_meters_payload
  };
  if (!payload.accuracy_meters) delete payload.accuracy_meters;

  if (payload.accuracy_meters === null) {
    delete payload.accuracy_meters;
  }

  console.log("Wysyłany payload (poprawiony):", JSON.stringify(payload, null, 2)); // Do debugowania

  let url, method;
  const locationId = formData.get("location_id_form"); // Pobierz ID dla sprawdzenia czy edycja
  if (locationId) {
    // Edycja
    url = `/admin/vessels/${CURRENT_VESSEL_ID_LOC}/location-history-management/locations/${locationId}`;
    method = "PUT";
  } else {
    // Dodawanie
    url = `/admin/vessels/${CURRENT_VESSEL_ID_LOC}/location-history-management/locations/`;
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
          errorDetail = errorData.detail
            .map((err) => {
              const field =
                err.loc && err.loc.length > 1 ? err.loc[1] : "body";
              return `${field}: ${err.msg}`;
            })
            .join("; ");
        } else if (errorData.detail) {
          errorDetail = errorData.detail;
        } else {
          errorDetail = JSON.stringify(errorData);
        }
      } catch (e) {
        errorDetail = await response.text();
      }
      throw new Error(
        `Operacja nie powiodła się (status: ${response.status}): ${errorDetail}`,
      );
    }

    const updatedLocations = await fetchLocationEntries();
    renderLocationEntriesList(updatedLocations);
    updateLocationMarkers(updatedLocations);
    resetAndPrepareLocationFormForAdd();
  } catch (error) {
    console.error("Błąd zapisu wpisu lokalizacji:", error);
    setLocationEntryFormError(error.message);
  }
}

async function handleDeleteLocationEntry(locationId) {
  if (!confirm("Czy na pewno chcesz usunąć ten wpis lokalizacji?")) return;
  resetLocationEntryFormError();
  removeTemporaryLocationMarker();

  try {
    const response = await fetch(
      `/admin/vessels/${CURRENT_VESSEL_ID_LOC}/location-history-management/locations/${locationId}`,
      {
        method: "DELETE",
      },
    );
    if (!response.ok && response.status !== 204) {
      const errorData = await response.json().catch(() => ({detail: "Błąd serwera"}));
      throw new Error(
        `Nie udało się usunąć wpisu: ${errorData.detail || response.statusText}`,
      );
    }
    const updatedLocations = await fetchLocationEntries();
    renderLocationEntriesList(updatedLocations);
    updateLocationMarkers(updatedLocations);
    if (locationEntryForm.elements["location_id_form_field"].value === String(locationId)) {
      resetAndPrepareLocationFormForAdd();
    }
  } catch (error) {
    console.error("Błąd usuwania wpisu lokalizacji:", error);
    alert(`Błąd usuwania: ${error.message}`);
  }
}

// --- Funkcje pomocnicze dla formularza ---
function setLocationEntryFormError(message) {
    if (locationEntryFormError) {
        locationEntryFormError.textContent = message;
        locationEntryFormError.classList.remove("hidden"); // Pokaż błąd
    }
}
function resetLocationEntryFormError() {
    if (locationEntryFormError) {
        locationEntryFormError.textContent = "";
        locationEntryFormError.classList.add("hidden"); // Ukryj błąd
    }
}

/**
 * Formatuje obiekt Date na string akceptowany przez input[type="datetime-local"].
 * Dedykowana funkcja, aby uniknąć konfliktu.
 * @param {Date} date
 */
function datetimeLocalInputFormatLoc(date) {
  if (!(date instanceof Date) || isNaN(date)) return "";
  const YYYY = date.getFullYear();
  const MM = String(date.getMonth() + 1).padStart(2, "0");
  const DD = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return `${YYYY}-${MM}-${DD}T${hh}:${mm}`;
}

// Inicjalizacja po załadowaniu DOM
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("location-history-map")) {
    initializeLocationHistoryManagement();

    if (locationEntryForm) {
      locationEntryForm.addEventListener(
        "submit",
        handleLocationEntryFormSubmit,
      );
    }
    if (cancelLocationEntryFormBtn) {
      cancelLocationEntryFormBtn.addEventListener(
        "click",
        resetAndPrepareLocationFormForAdd,
      );
    }
  }
});
