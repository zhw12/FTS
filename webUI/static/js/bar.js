var chart = c3.generate({
		bindto: '#c3-chart',
		padding: {
				top: 40,
				right: 100,
				bottom: 0,
				left: 100,
		},
    data: {
				x: 'year',
        columns: output_json['barData'],
        type: 'bar'
    },
    bar: {
        width: {
            ratio: 0.5 // this makes bar width 50% of length between ticks
        }
        // or
        //width: 100 // this makes bar width 100px
    },
		axis: {
        x: {
            label: {
                text: 'Year',
                position: 'outer-right'
                // inner-right : default
                // inner-center
                // inner-left
                // outer-right
                // outer-center
                // outer-left
            },
        },
        y: {
            label: {
                text: 'Normalized Paper Frequency',
                position: 'outer-middle',
                // inner-top : default
                // inner-middle
                // inner-bottom
                // outer-top
                // outer-middle
                // outer-bottom
            },
            // tick: {
            //     max: 0.03,
            //     min: 0.0,
            //     count: 8,
            //     format: function (d) { console.log(d.toFixed(3)); return d.toFixed(3); }
            // }
        },
    }
});

d3.select('#c3-chart svg').append('text')
    .attr('x', d3.select('#c3-chart svg').node().getBoundingClientRect().width / 2)
    .attr('y', 20)
    .attr('text-anchor', 'middle')
    .style('font-size', output_json['titleFont'])
    .text(output_json['title']);

d3.select('#c3-chart svg').append('text')
    .attr('x', d3.select('#c3-chart svg').node().getBoundingClientRect().width / 2)
    .attr('y', 40)
    .attr('text-anchor', 'middle')
    .style('font-size', output_json['subtitleFont'])
    .text(output_json['subtitle']);
		// .append('tspan')
    //     .text(output_json['title'])
		// 		.attr('text-anchor', 'middle')
		// 		.attr("dy", '0em' )
		// .append('tspan')
		// 		.text('deep')
		// 		.attr('text-anchor', 'middle')
		// 		.attr("dy", '1em' )
        // .attr('dy', '.4em');

// setTimeout(function () {
//     chart.load({
//         columns: [
//             ['data3', 130, -150, 200, 300, -200, 100]
//         ]
//     });
// }, 1000);
