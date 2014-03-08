function searchWords() {
	var search = $('#search').val();
	var tags = "";
	$('.tag.selected').each( function() {
		var name = $(".name", this).text();
		tags += name + " ";
	})

	apiCall('/api/exercise/search', 'POST', {words : search, tags: tags}, function(data) {
		var exercises = data.result;
		var $exercises = $("#exercises-list");
		var $unpublished = $("#unpublished-list");
		$exercises.html('');
		$unpublished.html('');
		for (var i = 0; i < exercises.length; i++) {
            if(exercises[i].published) {
                $exercises.append(exerciseTemplate(exercises[i]));
            }
            else {
                $unpublished.append(unpublishedTemplate(exercises[i]));
            }
		}
	});
}

$(document).ready(function() {
	exerciseTemplate = loadTemplate('#exercise-template');
    unpublishedTemplate = loadTemplate('#unpublished-exercise-template');

	// Initializing exercises
	searchWords();

	$('#search').on("keyup", searchWords);
	// Binding the click on a tag
	$(document).on("click", '.tag', function()  {
		$('#search').val('');
		$element = $(this);
		if ($element.hasClass('selected')) {
			$element.removeClass('selected');
		} else {
			$element.addClass('selected');
		}
		searchWords();
	});
})
