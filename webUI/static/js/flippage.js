// __author__ : Zoey Li
// __description__: This is the function used with pagination
//   check commit abd53a27df8bcca1aab778f9b2c754e28c7758ef       
// __latest_update__: 07/19/2017
var pagelist = document.getElementsByClassName('pagination')[0];
var lielement = pagelist.getElementsByClassName('active')[0];
var current_page = parseInt(lielement.firstChild.text);
var max_page = parseInt(pagelist.children[pagelist.children.length-2].firstChild.text);


function flip(page){
	var form = document.getElementById('search-form');
	var input = document.getElementById('page');
	if (page >0 && page<= max_page){
		input.value=parseInt(page);
		// Submit another form and works as submitting a new query
		form.submit();
	}

}

var prev_btn = document.getElementById('prev-btn');
var next_btn = document.getElementById('next-btn');
//check if disabled 
if (current_page == 1){
	prev_btn.parentElement.className='disabled';
}
else{
	prev_btn.addEventListener("click",
	function prev_page(){
		current_page--;
		flip(current_page);

});
prev_btn.style.cursor="default";
}

if (current_page == max_page){
	next_btn.parentElement.className="disabled";
}
else{
	next_btn.addEventListener("click",
	function next_page(){
		current_page++;
		flip(current_page);

	});
next_btn.style.cursor="default";
}


for (var i=1;i<=pagelist.children.length-1;i++){
	(function(){
	var btn = pagelist.children[i].firstChild;
	if (isNaN(parseInt(btn.text))) return;
	
	var page = parseInt(btn.text);
	btn.addEventListener("click",
		function(){
			flip(page);
		});
	btn.style.cursor="default";
	}());//closure to avoid overwriting of listener
}

