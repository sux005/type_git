// Scripps Institution of Oceanography
// Author: Jeff Sevadjian
// jsevadjian@ucsd.edu

// Get current time, will use to set x-max
var jsTime = new Date();
var currTime = jsTime.getTime();

function syncExtremes(e) {
  var thisChart = this.chart;
  var xMin = e.min;
  var xMax = e.max;

  if (e.trigger !== "syncExtremes") {
    // Modernized loop: replaced Highcharts.each with Highcharts.charts.forEach
    Highcharts.charts.forEach(function (chart) {
      // Check if chart exists and isn't the one currently being interacted with
      if (chart && chart !== thisChart) {
        if (chart.xAxis[0].setExtremes) {
          if (e.trigger == "rangeSelectorButton") {
            if (e.rangeSelectorButton.type == "week") {
              chart.xAxis[0].setExtremes(
                currTime - 7 * 86400 * 1000,
                currTime,
                1,
                0,
                { trigger: "syncExtremes" },
              );
            } else if (e.rangeSelectorButton.type == "day") {
              chart.xAxis[0].setExtremes(
                currTime - 1 * 86400 * 1000,
                currTime,
                1,
                0,
                { trigger: "syncExtremes" },
              );
            } else if (e.rangeSelectorButton.type == "month") {
              chart.xAxis[0].setExtremes(
                currTime - 30.5 * 86400 * 1000,
                currTime,
                1,
                0,
                { trigger: "syncExtremes" },
              );
            } else if (e.rangeSelectorButton.type == "all") {
              chart.xAxis[0].setExtremes(xMin, currTime, 1, 0, {
                trigger: "syncExtremes",
              });
            }
          } else if (e.trigger == "zoom" || e.trigger == "pan") {
            chart.xAxis[0].setExtremes(xMin, xMax, 1, 0, {
              trigger: "syncExtremes",
            });
          }
        }
      }
    });
  }
}