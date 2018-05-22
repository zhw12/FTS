// __author__ : Zoey Li
// __description__: Function used with shortening abstracts and author lists
//   check commit 79e1c546927aed71da793249df81fbaea2bcd395
// __latest_update__: 07/30/2017

function show_full(btn){
	var text = btn.parentElement;
	if (text.className == "shortened"){
		var full_text = text.parentElement.getElementsByClassName('full')[0];
		full_text.removeAttribute('hidden');
		text.setAttribute('hidden','');
	}
 
}
function fold_full(btn){
	var full_text = btn.parentElement;
	if (full_text.className == "full"){
		var text = full_text.parentElement.getElementsByClassName('shortened')[0];
		text.removeAttribute('hidden');
		full_text.setAttribute('hidden','');
	}
 
}

var full_btn_list = document.getElementsByClassName('toggle-full');
for (var i=0;i<full_btn_list.length; i++){
	full_btn_list[i].addEventListener("click", 
			function(){
				show_full(this);
			});
	full_btn_list[i].style.cursor="default";
}

var fold_btn_list = document.getElementsByClassName('fold-full');

for (var j=0;j<fold_btn_list.length; j++){
	fold_btn_list[j].addEventListener("click", 
			function(){
				fold_full(this);
			});
	fold_btn_list[j].style.cursor="default";
}
