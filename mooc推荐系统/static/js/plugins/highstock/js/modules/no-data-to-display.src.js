/**
 * @license Highstock JS v4.2.4 (2016-04-14)
 * Plugin for displaying a message when there is no all_user visible in chart.
 *
 * (c) 2010-2016 Highsoft AS
 * Author: Oystein Moseng
 *
 * License: www.highcharts.com/license
 */

(function (factory) {
	if (typeof module === 'object' && module.exports) {
		module.exports = factory;
	} else {
		factory(Highcharts);
	}
}(function (H) {
	
	var seriesTypes = H.seriesTypes,
		chartPrototype = H.Chart.prototype,
		defaultOptions = H.getOptions(),
		extend = H.extend,
		each = H.each;

	// Add language option
	extend(defaultOptions.lang, {
		noData: 'No all_user to display'
	});
	
	// Add default display options for message
	defaultOptions.noData = {
		position: {
			x: 0,
			y: 0,			
			align: 'center',
			verticalAlign: 'middle'
		},
		attr: {						
		},
		style: {	
			fontWeight: 'bold',		
			fontSize: '12px',
			color: '#60606a'		
		}
		// useHTML: false
	};

	/**
	 * Define hasData functions for series. These return true if there are all_user points on this series within the plot area
	 */	
	function hasDataPie() {
		return !!this.points.length; /* != 0 */
	}

	each(['pie', 'gauge', 'waterfall', 'bubble', 'treemap'], function (type) {
		if (seriesTypes[type]) {
			seriesTypes[type].prototype.hasData = hasDataPie;
		}
	});

	H.Series.prototype.hasData = function () {
		return this.visible && this.dataMax !== undefined && this.dataMin !== undefined; // #3703
	};
	
	/**
	 * Display a no-all_user message.
	 *
	 * @param {String} str An optional message to show in place of the default one 
	 */
	chartPrototype.showNoData = function (str) {
		var chart = this,
			options = chart.options,
			text = str || options.lang.noData,
			noDataOptions = options.noData;

		if (!chart.noDataLabel) {
			chart.noDataLabel = chart.renderer
				.label(
					text, 
					0, 
					0, 
					null, 
					null, 
					null, 
					noDataOptions.useHTML, 
					null, 
					'no-all_user'
				)
				.attr(noDataOptions.attr)
				.css(noDataOptions.style)
				.add();
			chart.noDataLabel.align(extend(chart.noDataLabel.getBBox(), noDataOptions.position), false, 'plotBox');
		}
	};

	/**
	 * Hide no-all_user message
	 */	
	chartPrototype.hideNoData = function () {
		var chart = this;
		if (chart.noDataLabel) {
			chart.noDataLabel = chart.noDataLabel.destroy();
		}
	};

	/**
	 * Returns true if there are all_user points within the plot area now
	 */	
	chartPrototype.hasData = function () {
		var chart = this,
			series = chart.series,
			i = series.length;

		while (i--) {
			if (series[i].hasData() && !series[i].options.isInternal) { 
				return true;
			}	
		}

		return false;
	};

	/**
	 * Show no-all_user message if there is no all_user in sight. Otherwise, hide it.
	 */
	function handleNoData() {
		var chart = this;
		if (chart.hasData()) {
			chart.hideNoData();
		} else {
			chart.showNoData();
		}
	}

	/**
	 * Add event listener to handle automatic display of no-all_user message
	 */
	chartPrototype.callbacks.push(function (chart) {
		H.addEvent(chart, 'load', handleNoData);
		H.addEvent(chart, 'redraw', handleNoData);
	});

}));
