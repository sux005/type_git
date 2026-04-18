// Scripps Institution of Oceanography
// Modified for Hackathon - Clean Version (No GeoJSON dependencies)

// 1. Define CCE Mooring Locations
var cce1Lon = "-122.52";
var cce1Lat = "33.49";

var cce2Lon = "-120.81";
var cce2Lat = "34.3150";

var cce3Lon = "-120.53732";
var cce3Lat = "34.44350";

var cce4Lon = "-120.48770";
var cce4Lat = "34.46680";

// 2. Define Leaflet Icon (Using CDN for icons to avoid local path issues)
var iconBlue = L.icon({
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// 3. Define CalCOFI Lines (Uses the 'calcofi' coordinates variable)
var CalCOFI_lines = L.polyline(calcofi, {
  color: "rgba(255, 255, 255, 0.6)", // White-ish lines look better on satellite
  weight: 2,
});

// 4. Define Mooring Markers
var CCE1 = L.marker([cce1Lat, cce1Lon], { icon: iconBlue }).bindPopup(
  "<b>CCE1 Mooring</b>",
);
var CCE2 = L.marker([cce2Lat, cce2Lon], { icon: iconBlue }).bindPopup(
  "<b>CCE2 Mooring</b>",
);
var CCE3 = L.marker([cce3Lat, cce3Lon], { icon: iconBlue }).bindPopup(
  "<b>CCE3 Mooring</b>",
);
var CCE4 = L.marker([cce4Lat, cce4Lon], { icon: iconBlue }).bindPopup(
  "<b>CCE4 Mooring</b>",
);

var CCE = L.layerGroup([CCE1, CCE2, CCE3, CCE4]);

// 5. Initialize the Map
// NOTE: Make sure your index.html has <div id="container_map"></div>
var myMap = L.map("container_map", {
  center: [34, -121],
  zoom: 6,
  scrollWheelZoom: false,
});

// 6. Add ESRI Satellite Imagery Basemap
L.tileLayer(
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  {
    attribution:
      "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
  },
).addTo(myMap);

// 7. Add Live SST (Sea Surface Temperature) Overlay from NOAA
var sstLayer = L.tileLayer
  .wms(
    "https://oceanwatch.pfeg.noaa.gov/thredds/wms/satellite/MUR41/ssta/1day?",
    {
      layers: "analysed_sst",
      format: "image/png",
      transparent: true,
      opacity: 0.4,
    },
  )
  .addTo(myMap);

// 8. Add Layer Controls
var overlayMaps = {
  "<b>CCE Moorings</b>": CCE,
  "CalCOFI Lines": CalCOFI_lines,
  "Temp Overlay": sstLayer,
};

L.control.layers(null, overlayMaps, { collapsed: false }).addTo(myMap);

// 9. Set Default Visibility
CCE.addTo(myMap);
CalCOFI_lines.addTo(myMap);