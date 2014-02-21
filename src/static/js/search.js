function searchWords() {
	var search = $('#search').val();
	var tags = $('.tag.selected').text();
	console.log(tags);
	apiCall('/api/exercise/search', 'POST', {words : search, tags: tags}, function(data) {
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

	// Initializing exercises
	searchWords();

	// Binding the click on a tag
	$('.tag').click(function()  {
		$('#search').val('');
		$(".tag").removeClass('selected');
		$(this).addClass('selected');
		searchWords();
	});
})
