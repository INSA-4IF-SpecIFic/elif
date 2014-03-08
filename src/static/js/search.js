function searchWords() {
	var search = $('#search').val();
	var tags = "";
	$('.tag.selected').each( function() {
		var name = $(".name", this).text();
		tags += name + " ";
	})
	apiCall('/api/exercise/search', 'POST', {words : search, tags: tags}, function(data) {
		var exercises = data.result;
		var userID = data.user;
		var $exercises = $("#exercises-list");
		var $unpublished = $("#unpublished-list");
		$exercises.html('');
		$unpublished.html('');
		for (var i = 0; i < exercises.length; i++) {
			var editor = (userID == exercises[i].author);
			var context = {exercise: exercises[i], editor: editor};
            if(exercises[i].published) {
                $exercises.append(exerciseTemplate(context));
            }
            else {
                $unpublished.append(exerciseTemplate(context));
            }
		}
	});
}

function getOccurences() {
	var $menu = $('.tagsmenu');
	apiCall('/api/occurrences', 'GET', {}, function(data) {
		var occurrences = data.occurrences;
		var tags = data.tags;
		console.log(occurrences);
		console.log(tags);
		$menu.html('');
		for (var i = 0; i < tags.length; i++) {
			$menu.append(tagTemplate({tag : tags[i], occurrence : occurrences[i]}));
		}      
	});
}

// Delete an exercise
function deleteExercise(button) {
    var exercise_id = $(button).attr('data-exercise-id');
    var params = {exercise_id: exercise_id };
    apiCall('/api/exercise', 'DELETE', params, function(data) {
        if(data.ok) {
            searchWords();
            getOccurences();
            notification.info("The exercise has been deleted");
        }
        else {
            notification.error("Failed to delete exercise: " + data.result);
        }
    });
}

$(document).ready(function() {
	exerciseTemplate = loadTemplate('#exercise-template');
	tagTemplate = loadTemplate('#tag-template');

	// Initializing exercises
	searchWords();
	// Initalizing tags
	getOccurences();

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
