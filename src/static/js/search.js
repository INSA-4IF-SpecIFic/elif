function valider() {		
	var search = document.getElementById('parTags').value;
	console.log(search);
	$.get('/searchByWords', { words : search});
}

$(document).ready(function() { 
})