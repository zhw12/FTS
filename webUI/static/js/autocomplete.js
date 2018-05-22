var geoNamesUsername = 'uberboomtest';

/**
 * Initialize typeahead.js
 */
$('.typeahead').typeahead([{
	name: 'posts',
	remote: {
		url: '128.111.54.50:9200/_search?from=0&size=3&q=machine',
		filter: function(parsedResponse) {
			var result = [];
      $.each(parsedResponse.hits.hits, function(){
        var item = $(this)[0]._source;
        result.push({
          id: item.iD,
          author: item.author,
          value: item.name,
          name: item.name,
          content: item.content
        });
      });
			return result;
		}
	},
  cache: false,
  header: '<h4 class="suggestion-header">Posts</h4>',
	template: [
		'<p class="geo-name">{{name}}</p>',
		'<p class="geo-country">{{author}}</p>',
    '<p class="geo-country text-muted">{{content}}</p>'
	].join(''),
	engine: Hogan
},
{
  name: 'movies',
  remote: {
    url: 'https://elastic-quoc99.rhcloud.com/test/movies/_search?from=0&size=3&q=%QUERY*',
    filter: function(response){
      var result = [];
      $.each(response.hits.hits, function(){
        var item = $(this)[0]._source;
        result.push({
          id: item.id,
          director: item.director,
          value: item.name,
          name: item.name,
          year: item.year
        });
      });
			return result;
    }
  },
  cache: false,
  header: '<h4 class="suggestion-header">Movies<h4>',
  template: ['<a href="#"><div>',
    '<p class="geo-name">{{name}}</p>',
             '<p class="geo-country text-muted">{{director}} - {{year}}</p>',
             '</div></a>'
    ].join(''),
  engine: Hogan
}]);


/**
 * Fix tt hint
 */
$('.typeahead').on('typeahead:initialized', function(e, data) {
	// fix for using twitter bootstrap
	var hint = $(e.target).prev('.tt-hint');
	var small = $(e.target).is('.input-sm');
	var large = $(e.target).is('.input-lg');
	if (small) {
		hint.addClass('input-sm');
	} else if (large) {
		hint.addClass('input-lg');
	} else {
		hint.addClass('input');
	}
	hint.addClass('form-control');
});
