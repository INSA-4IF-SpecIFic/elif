function searchWords() {
	var search = $('#search').val();
	apiCall('/searchByWords', 'POST', { words : search}, function(data) {
		var exercises = data.result;
		console.log(exercises);
		var $exercises = $(".exercises");
		$exercises.html('');
		for (var i = 0; i < exercises.length; i++) {
			$exercises.append(exerciseTemplate(exercises[i]));
		}
	});
}

$(document).ready(function() {
	$('#search').on("keyup", searchWords);
	exerciseTemplate = loadTemplate('#exercise-template'); 
})