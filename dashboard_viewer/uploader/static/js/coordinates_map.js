
/**
 * Updates the content of the latitude and longitude inputs
 *  for a specific coordinates field after click on the map
 *  or dragging of the marker
 * 
 * @param {string} name of the field on the django app
 * @param latlng LatLng leaflet object relative to the coordinates of the data source
 */
const set_latlng = (name, latlng) => {
    const wrapped_latlng =  L.latLng(latlng).wrap();
    $(`#id_${name}_0`).val(wrapped_latlng.lat);
    $(`#id_${name}_1`).val(wrapped_latlng.lng);
};

$(".coordinates-map").each((index, element) => {
    // create the map
    const map = L.map(element.id).setView([24, -36], 3);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    const name = element.id.substring(4);
    let marker;

    // place a marker for already build data sources
    const lat = $(`#id_${name}_0`).val(), lng = $(`#id_${name}_1`).val();
    if (lat && lng) {
        marker = L.marker({"lat":lat, "lng": lng}, {draggable: true});
        marker.addTo(map);
        marker.on("dragend", (dragEvent) => {
            set_latlng(name, dragEvent.target._latlng);
        });
    }

    map.on("click", (e) => {
        if (marker) {
            map.removeLayer(marker);
        }
        marker = L.marker(e.latlng, {draggable: true});
        marker.addTo(map);

        marker.on("dragend", (dragEvent) => {
            set_latlng(name, dragEvent.target._latlng);
        });

        set_latlng(name, e.latlng);
    });
});
