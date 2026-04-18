
// Scripps Institution of Oceanography
// Author: Jeff Sevadjian
// jsevadjian@ucsd.edu

// define CCE locations
var cce1Lon = '-122.52';
var cce1Lat = '33.49';

var cce2Lon = '-120.81';
var cce2Lat = '34.3150';

var cce3Lon = '-120.53732';
var cce3Lat = '34.44350';

var cce4Lon = '-120.48770';
var cce4Lat = '34.46680';

// define styles for Leaflet marker icons
var iconBlue = L.icon({
	iconUrl: '../assets/img/leaflet/marker-icon-2x-blue.png',
	shadowUrl: '../assets/img/leaflet/marker-shadow.png',
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
	shadowSize: [41, 41]
});

// define style for historical GPS fixes
var markerStyle = {
	radius: 2,
	fillColor: "gray",
	color: "black",
	weight: 1,
	opacity: 1,
	fillOpacity: 0.5
};

// -------------------- //

// Define CalCOFI lines, CCE Moorings

var CalCOFI_lines = L.polyline(calcofi, {
	color: 'rgba(100,100,100,0.5)'
});

var CCE1 = L.marker([cce1Lat, cce1Lon], {
	icon: iconBlue
}).bindPopup('<div style="text-align:center"><a href="../cce1/cce1_19" target="_blank"><b>CCE1</b></a><br>Mooring</div>');

var CCE2 = L.marker([cce2Lat, cce2Lon], {
	icon: iconBlue
}).bindPopup('<div style="text-align:center"><a href="../cce2/cce2_19" target="_blank"><b>CCE2</b></a><br>Mooring</div>');

var CCE3 = L.marker([cce3Lat, cce3Lon], {
	icon: iconBlue
}).bindPopup('<div style="text-align:center"><a href="../cce3/cce3_02" target="_blank"><b>CCE3</b></a><br>Mooring</div>');

var CCE4 = L.marker([cce4Lat, cce4Lon], {
  icon: iconBlue
}).bindPopup('<div style="text-align:center"><a href="../mini_moorings/cce4/cce4_01" target="_blank"><b>CCE4</b></a><br>Mooring</div>');

var CalCOFI_lines = L.polyline(calcofi, {
	color: 'rgba(100,100,100,0.5)'
});

var CCE = L.layerGroup([CCE1, CCE2, CCE3, CCE4]);

// -------------------- //

// make AJAX request for CalCOFI positions data
var pos = $.ajax({
	// url: "json/calcofi_pos.geojson",
	url: "json/113_station_positions.geojson",
	beforeSend: function(xhr) { //otherwise get some badly-formed error
		if (xhr.overrideMimeType) {
			xhr.overrideMimeType("application/json");
		}
	},
	dataType: "json",
});

// once all the position data have loaded...
$.when(pos).done(function() {

	// Create the map
	var myMap = L.map(mapID, {
		center: [34, -123],
		zoom: 5
	});

	// // Add the Ocean Basemap layer
	// L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}', {}).addTo(myMap);

	// Add the ESRI Basemap layer
	var esriLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
		attribution: 'ESRI'
	}).addTo(myMap);

	// Add SST overlay
	// https://thredds1.pfeg.noaa.gov/thredds/wms/satellite/MUR41/ssta/1day?service=WMS&version=1.3.0&request=GetCapabilities
	var murThreddsWmsLayer = L.tileLayer.wms('https://oceanwatch.pfeg.noaa.gov/thredds/wms/satellite/MUR41/ssta/1day?', {
		attribution: '<a href="https://oceanwatch.pifsc.noaa.gov/" target="_blank">NOAA Oceanwatch</a>',
		layers: 'analysed_sst',
		format: 'image/png',
		transparent: true,
		opacity: 0.5,
		COLORSCALERANGE: '280.15,302.15'
	}).addTo(myMap);

	// Create GeoJSON layer
	var CalCOFI_dots = L.geoJSON(pos.responseJSON, {
		pointToLayer: function (feature, latlng) {
			return L.circleMarker(latlng, markerStyle)
		}
	});

	var CalCOFI = L.layerGroup([CalCOFI_lines, CalCOFI_dots]);

	// define overlay objects
	var overlayMaps = {
		'<b>CCE</b>': CCE,
		'CalCOFI': CalCOFI
	};

	// create layers control
	L.control.layers(null, overlayMaps,{collapsed:false}).addTo(myMap);

	// default layers
	CalCOFI.addTo(myMap);
	CCE.addTo(myMap);

// // add colorbar [legend]
// var testLegend = L.control({
// 	position: 'topright'
// });

// // var testWMS = 'https://ogcie.iblsoft.com/metocean/wms';
// var testWMS = 'https://oceanwatch.pfeg.noaa.gov/thredds/wms/satellite/MUR41/ssta/1day';
// testLegend.onAdd = function(myMap) {
// 	// var src = testWMS + "?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=gfs-temperature-isbl&STYLE=default";
// 	var src = testWMS + "?SERVICE=WMS&REQUEST=GetLegendGraphic&LAYER=analysed_sst&STYLE=default&COLORSCALERANGE=278.15,304.15";
// 	var div = L.DomUtil.create('div', 'info legend');
// 	div.innerHTML += '<img src="' + src + '" alt="legend">';
// 	return div;
// };

// testLegend.addTo(myMap);

// var mouseLat, mouseLon;
// myMap.on("mousemove", function (event) {
// 	mouseLat = event.latlng.lat.toFixed(6);
// 	mouseLon = event.latlng.lng.toFixed(6);
// 	document.getElementById("mousePos").innerHTML='[' +mouseLon +', ' +mouseLat +']';
// });

	// //disable scrolling
	// myMap.scrollWheelZoom.disable()

}); //when-done function
