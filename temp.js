// Scripps Institution of Oceanography
// Author: Jeff Sevadjian
// jsevadjian@ucsd.edu

// Chart for Temperature

$.get("/csv/temp.csv", function (data) {
  $("#container_temp").highcharts("StockChart", {
    boost: {
      enabled: true,
    },

    chart: {
      marginTop: 0,
    },

    xAxis: {
      labels: {
        enabled: false,
      },
    },

    yAxis: {
      labels: {
        style: {
          color: cmap[0],
        },
      },
      title: {
        text: "Temperature [°C]",
        style: {
          color: cmap[0],
        },
      },
      lineColor: cmap[0],
      tickColor: cmap[0],
    },

    data: {
      csv: data,
    },

    plotOptions: {
      series: {
        boostThreshold: 1,
      },
    },

    series: [
      {
        // 10 m
        index: 0,
        color: cmapThermal14[13],
        marker: {
          fillColor: cmapThermal14[13],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">10&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 20 m
        index: 1,
        color: cmapThermal14[12],
        marker: {
          fillColor: cmapThermal14[12],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">20&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 30 m
        index: 2,
        color: cmapThermal14[11],
        marker: {
          fillColor: cmapThermal14[11],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">30&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 40 m
        index: 3,
        color: cmapThermal14[10],
        marker: {
          fillColor: cmapThermal14[10],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">40&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 60 m
        index: 4,
        color: cmapThermal14[9],
        marker: {
          fillColor: cmapThermal14[9],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">60&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 75 m
        index: 5,
        color: cmapThermal14[8],
        marker: {
          fillColor: cmapThermal14[8],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">75&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 150 m
        index: 6,
        color: cmapThermal14[7],
        marker: {
          fillColor: cmapThermal14[7],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">150&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 300 m
        index: 7,
        color: cmapThermal14[6],
        marker: {
          fillColor: cmapThermal14[6],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">300&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 500 m
        index: 8,
        color: cmapThermal14[5],
        marker: {
          fillColor: cmapThermal14[5],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">500&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 750 m
        index: 9,
        color: cmapThermal14[4],
        marker: {
          fillColor: cmapThermal14[4],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">750&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 1000 m
        index: 10,
        color: cmapThermal14[3],
        marker: {
          fillColor: cmapThermal14[3],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">1000&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 2200 m
        index: 11,
        color: cmapThermal14[2],
        marker: {
          fillColor: cmapThermal14[2],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">2200&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
      {
        // 4000 m
        index: 12,
        color: cmapThermal14[1],
        marker: {
          fillColor: cmapThermal14[1],
        },
        tooltip: {
          pointFormat:
            '<div style="height:20px; width:280px">' +
            '<div style="float:left; margin-left:160px"><span style="color:{point.color}">&nbsp;&nbsp;&nbsp;\u25CF</span></div>' +
            '<div style="width:50px; text-align:right; float:left">4000&nbsp;m</div>' +
            '<div style="width:45px; text-align:right; float:right"><b>{point.y}</b></div>' +
            "</div>",
        },
      },
    ],

    tooltip: {
      valueDecimals: 2,
      headerFormat:
        "<div>" +
        '<div style="margin-right:115px">' +
        '<p style="text-align:right; margin-bottom:0px; margin-top:0px">{point.key}</p></div></div>' +
        '<div style="overflow:auto; width:280px">',
      footerFormat: "</div>",
      positioner: function (labelWidth, labelHeight, point) {
        var chart = this.chart;
        return {
          x: chart.plotLeft + chart.plotWidth - 160,
          y: chart.plotTop - 25,
        };
      },
    },
  }); //end temp container
}); //end $.get fn for temp
