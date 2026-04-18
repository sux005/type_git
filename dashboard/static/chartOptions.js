// Scripps Institution of Oceanography
// Author: Jeff Sevadjian
// jsevadjian@ucsd.edu

// https://stackoverflow.com/questions/8584902/get-closest-number-out-of-array
function closest(num, arr) {
	var mid;
	var lo = 0;
	var hi = arr.length - 1;
	while (hi - lo > 1) {
		mid = Math.floor ((lo + hi) / 2);
		if (arr[mid].x < num) {
			lo = mid;
		} else {
			hi = mid;
		}
	}
	if (num - arr[lo].x <= arr[hi].x - num) {
		return lo;
	}
	return hi;
}

// https://jsfiddle.net/jj6a9jot/5/
function searchPoint(event, chart, series) {
	var points = series.points;
	var x = chart.axes[0].toValue(event.chartX),
			range = 86400 * 1000;
	var ind = closest(x, points);
	if (points[ind].x > x - range && points[ind].x < x + range ) {
		return points[ind];
	}
}

function mouseEv(e) {
	var i, chart, event, point;
	for (i = 0; i < Highcharts.charts.length; i++) {
		chart = Highcharts.charts[i];
		event = chart.pointer.normalize(e.originalEvent); // Find coordinates within the chart
		for (j = 0; j < chart.series.length; j++) {
			point = chart.series[j].searchPoint(event, true); // Get the hovered point
			// point = searchPoint(event, chart, chart.series[j]); // Get the nearest point to mouse position
			if (point) {
				point.highlight(e);
			}
		}
	}
}

$('#container_temp').bind('mousemove touchmove touchstart', mouseEv);

//Override the reset function, we don't need to hide the tooltips and crosshairs.
Highcharts.Pointer.prototype.reset = function() {
  return undefined;
};

//Highlight a point by showing tooltip, setting hover state and drawing crosshair
Highcharts.Point.prototype.highlight = function(event) {
  this.onMouseOver(); // Show the hover marker
  // this.series.chart.tooltip.refresh(this); // Show the tooltip
  this.series.chart.xAxis[0].drawCrosshair(event, this); // Show the crosshair
};

// Define universal settings

Highcharts.setOptions({
	
  lang: {
  	rangeSelectorZoom: ''
  },

  credits: {
    enabled: false
  },

  chart: {
    plotBackgroundColor: {
    linearGradient: {
        x1: 0.5,
        y1: 0,
        x2: 0.5,
        y2: 1
      },
      stops: [
        [0, 'rgb(255, 255, 255)'],
        [1, 'rgb(240, 240, 240)']
      ]
    },
    plotBorderColor:  'rgb(150, 150, 150)',
    plotBorderWidth: 1,
    marginTop: 0,
    marginBottom: 10,
    marginLeft: 75,
    marginRight: 130,
    spacingRight: 0, //?
    zoomType: 'x',
		alignTicks: false,
		style: {
			fontSize: '14px',
			fontFamily: 'Roboto,Helvetica Neue,Arial,sans-serif'
		},
		panning: true,
		panKey: 'shift'
  },

	rangeSelector : {
		enabled: true,
		buttons: [{
			type: 'all',
			text: 'Reset zoom'
		}],
		buttonTheme: {
			width: 75
		},
		inputEnabled: false,
		buttonPosition: {
			x: -1,
			y: 10
		}
	},

	scrollbar: {
		enabled: false
	},

	navigator: {
		enabled: false
	},

  title: {
    // align: 'left',
    // x: -10,
    y: 8,
    style: {
			// 'font-size': '20px',
			'font-size': '18px',
			'font-weight': '300'
    },
    useHTML: true,
  },
	
  xAxis: {
		events: {
			afterSetExtremes: syncExtremes
		},
		max: currTime,
		ordinal: false,
		opposite: false,
    lineWidth: 0,
    gridLineWidth: 1,
    gridLineDashStyle: 'ShortDot',
    labels: {
      style: {
        "font-size": "100%"
      }
    },
    dateTimeLabelFormats: {
      hour: '%H:%M',
      day: '%H:%M<br><b>%m/%d/%Y</b>',
      week: '<b>%m/%d/%Y</b>',
      month: '<b>%m/%d/%Y</b>'
    },
    title: {
      style: {
        "fontSize": "16px",
        "font-weight": "normal",
        "color": "#333333"
      }
    },
    labels: {
    	distance: 10,
    	style: {
    		"font-size": "100%"
    	}
    },
    tickPixelInterval: 150
  },
	
  yAxis: {
		showLastLabel: true,
		ordinal: false,
		opposite: false,
  	startOnTick: false,
  	endOnTick: false,
		gridLineWidth: 0,
    lineWidth: 1,
    tickWidth: 1,
    lineColor: cmap[0],
    tickColor: cmap[0],
    labels: {
			y: 5,
      style: {
        "font-size": "100%",
        'color': cmap[0]
      }
    },
    title: {
      style: {
        "font-size": "120%",
        "font-weight": "normal",
        "color": cmap[0]
      },
      useHTML: true
    }
  },

	tooltip: {
		enabled: true,
		split: false, // **!!**
		animation: false,
		shadow: false,
		shared: true,
		// backgroundColor: 'rgba(255, 255, 255, 0.9)',
		backgroundColor: null,
		padding: 0,
		borderWidth: 0,
		dateTimeLabelFormats: {
			millisecond: '%m/%d/%Y %H:%M:%S',
			second: '%m/%d/%Y %H:%M',
			minute: '%m/%d/%Y %H:%M',
			hour: '%m/%d/%Y %H:%M',
			day: '%m/%d/%Y',
			month: '%m/%d/%Y',
			week: '%m/%d/%Y',
			year: '%m/%d/%Y'
		},
		useHTML: true,
		positioner: function (labelWidth, labelHeight, point) {
			var chart = this.chart;
			return { x: chart.plotLeft + chart.plotWidth - labelWidth, y: chart.plotTop - labelHeight - 2 }
		},
		style: {
			'fontSize': '14px'
		}
	},

	plotOptions: {
		series: {
			states: {
				hover: {
					lineWidthPlus: 0
				}
			},
			lineWidth: 1,
			marker: {
				enabled: true,
				radius: 2,
				symbol: "circle",
			},
			dataGrouping: {
				enabled: false,
				groupPixelWidth: 2,
				units: [[
					'hour', [1,2]
				],[
					'day', [1]
	     	]],
				dateTimeLabelFormats: {
					second: ['%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '-%H:%M:%S'],
					minute: ['%m/%d/%Y %H:%M', '%m/%d/%Y %H:%M', '-%H:%M'],
					hour: ['%m/%d/%Y %H:%M', '%m/%d/%Y %H:%M', '-%H:%M'],
					day: ['%m/%d/%Y', '%m/%d', '-%m/%d/%Y']
				}
			},
			connectNulls: false,
		},
		turboThreshold: 1 // testing for faster performance [not related to boost in any way] [doesn't help]
	},

	navigator: {
		enabled: false
	}

});

$.ajaxSetup({ cache: false });
