var chart = AmCharts.makeChart("chartdiv", {
    "type": "pie",
	"theme": "none",
    "titles": [{
        "text": "Visitors countries",
        "size": 16
    }],
    "dataProvider": [
{
"keyword": "Kaushik",
"occurences": 9.5

},{
"keyword": "Apoorva",
"occurences": 7.5

},{
"keyword": "Dilip",
"occurences": 7.1

},{
"keyword": "Chaitanya",
"occurences": 8.6 

}],
"valueField": "occurences",
    "titleField": "keyword",
    "startEffect": "elastic",
    "startDuration": 2,
    "labelRadius": 15,
    "innerRadius": "50%",
    "depth3D": 10,
    "balloonText": "[[keyword]]<br><span style='font-size:14px'><b>[[occurences]]</b> ([[percents]]%)</span>",
    "angle": 15,
    "exportConfig":{	
      menuItems: [{
      icon: '/lib/3/images/export.png',
      format: 'png'	  
      }]  
	}
});
jQuery('.chart-input').off().on('input change',function() {
	var property	= jQuery(this).data('property');
	var target		= chart;
	var value		= Number(this.value);
	chart.startDuration = 0;

	if ( property == 'innerRadius') {
		value += "%";
	}

	target[property] = value;
	chart.validateNow();
});
