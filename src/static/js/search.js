function searchWords() {
	var search = $('#search').val();
	var tags = $('.tag.selected').text();
	apiCall('/api/exercise/search', 'POST', {words : search, tags: tags}, function(data) {
		var exercises = data.result;
		var $exercises = $(".exercises");
		$exercises.html('');
		for (var i = 0; i < exercises.length; i++) {
			$exercises.append(exerciseTemplate(exercises[i]));
		}
	});
}

$(document).ready(function() {
	exerciseTemplate = loadTemplate('#exercise-template');

	// Initializing exercises
	searchWords();

	$('#search').on("keyup", searchWords);
	// Binding the click on a tag
	$(document).on("click", '.tag', function()  {
		$('#search').val('');
		$(".tag").removeClass('selected');
		$(this).addClass('selected');
		searchWords();
	});
})
