
/**
 * Updates the content of the latitude and longitude inputs
 *  for a specific coordinates field after click on the map
 *  or dragging of the marker
 * 
 * @param {str} name of the field on the django app
 * @param {float} lat latitude of the data source
 * @param {float} lng longitude of the data source
 */
const set_latlng = (name, lat, lng) => {
    $(`#id_${name}_0`).val(lat);
    $(`#id_${name}_1`).val(lng);
};

$(".coordinates-map").each((index, element) => {
    // create the map
    const map = L.map(element.id).setView([29,-401], 3);
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
            set_latlng(name, dragEvent.target._latlng.lat, dragEvent.target._latlng.lng);
        });
    }

    map.on("click", (e) => {
        if (marker) {
            map.removeLayer(marker);
        }
        marker = L.marker(e.latlng, {draggable: true});
        marker.addTo(map);

        marker.on("dragend", (dragEvent) => {
            set_latlng(name, dragEvent.target._latlng.lat, dragEvent.target._latlng.lng);
        });

        set_latlng(name, e.latlng.lat, e.latlng.lng);
    });
});
