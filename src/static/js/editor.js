var submitCode = function(exerciseId, code) {
    var params = {exercise_id: exerciseId, code: code};
    apiCall('/api/submission', 'POST', params, function(data) {
        console.log(data);

        // we wait a bit then send a first request to know the submission's state
        submissionState(data.result._id['$oid']);
    });

}

var submissionState = function(submission_id) {
    console.log(submission_id);
    apiCall('/api/submission/' + submission_id, 'GET', {}, function(data) {
        console.log(data);

        var submission = data.result;

        // If the code submission still haven't been processed, we poll the server again
        if (!submission.processed) {
            setTimeout(function() { submissionState(submission_id); }, 1000);
            return;
        }

        // We re-enable the 'Test' button and hide the loading spinner since the code has been processed by the server.
        $('#test-button .spinner').hide();
        $('#test-button').removeAttr('disabled');

        // We set error anotations in the code editor
        var annotations = [];
        $.each(submission.errors, function(i, error) {
            annotations.push({
              row: error.row - 1,
              column: error.column,
              text: error.message,
              type: "error"
            });
        });
        mainEditor.getSession().setAnnotations(annotations);

        // We update the user's score
        var oldScore = parseInt($('#user-score').text());
        var newScore = data.user_score;

        $('#user-score').text(newScore);
        // Aaaaand a little "flashing" effect and a notification if the score changed
        // TODO : Which one should we keep ? Both feels like too much.
        if (newScore != oldScore) {
            $('.username').fadeOut(350).fadeIn(350).fadeOut(350).fadeIn(200);
            setTimeout(function() {notification.success("Congratulations ! Your total score is now " + newScore + " !")}, 1000);
        }

        // Rendering the output
        $('#output').html(outputTemplate(submission));

        // Focusing on the output template
        $('.nav-tabs a[href="#output"]').tab('show');
    });

}

initializeEditor = function(editor_id) {
    var editor = ace.edit(editor_id);
    editor.setTheme("ace/theme/textmate");
    editor.setFontSize(15);
    editor.setShowPrintMargin(false);
    editor.getSession().setMode("ace/mode/c_cpp");
    editor.setOption("dragEnabled", true);
    return editor
}

$(document).ready(function() {
    /* Getting the current exercise's data */
    var $exercise = $('#exercise');
    var exerciseId = $exercise.data('id');

    /* Getting Handlebar templates */
    outputTemplate = loadTemplate('#output-template');

    /* Editor initialization and configuration */
    mainEditor = initializeEditor("main-editor");

    /* Binding tabs */
    $('.nav-tab a').click(function (e) {
      e.preventDefault()
      $(this).tab('show')
    })

    /* Binding the submit button */
    $('#test-button').click(function() {
        $(this).find('.spinner').css('display', 'inline-block');
        $(this).attr('disabled', 'disabled');

        var code = mainEditor.getValue();
        submitCode(exerciseId, code);
    });
});
