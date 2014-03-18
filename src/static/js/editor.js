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
            setTimeout(function() { submissionState(submission_id); }, 200);
            return;
        }

        // We re-enable the 'Test' button since the code has been processed by the server.
        $('#test-button').removeAttr('disabled');

        // Set error anotations
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

        // Rendering the output
        $('#output').html(outputTemplate(submission));

        // Focusing on the output template
        $('.nav-tabs a[href="#output"]').tab('show');
    });

}

$(document).ready(function() {
    /* Getting the current exercise's data */
    var $exercise = $('#exercise');
    var exerciseId = $exercise.data('id');
    var boilerplateCode = $exercise.data('boilerplate-code');

    /* Getting Handlebar templates */
    outputTemplate = loadTemplate('#output-template');

    /* Editor initialization and configuration */
    mainEditor = ace.edit("main-editor");
    mainEditor.setTheme("ace/theme/textmate");
    mainEditor.setFontSize(15);
    mainEditor.setShowPrintMargin(false);
    mainEditor.getSession().setMode("ace/mode/c_cpp");
    mainEditor.setOption("dragEnabled", true);

    mainEditor.setValue(boilerplateCode);

    /* Binding tabs */
    $('.nav-tab a').click(function (e) {
      e.preventDefault()
      $(this).tab('show')
    })

    /* Binding the submit button */
    $('#test-button').click(function() {
        $(this).attr('disabled', 'disabled');

        var code = mainEditor.getValue();
        submitCode(exerciseId, code);
    });
});
