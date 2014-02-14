var submitCode = function(exerciseId, code) {
    var params = {exerciseId: exerciseId, code: code};
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

        // We re-enable the 'Test' button since the code has been processed by the server.
        $('#test-button').removeAttr('disabled');

        $('#output').html(output_template(submission));
        $('.nav-tabs a[href="#output"]').tab('show');
    });

}


$(document).ready(function() {
    /* Getting the current exercise's data */
    var $exercise = $('#exercise');
    var exerciseId = $exercise.data('id');
    var boilerplateCode = $exercise.data('boilerplate-code');

    /* Getting Handlebar templates */
    output_template = loadTemplate('#output-template');

    /* Editor initialization and configuration */
    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/textmate");
    editor.setFontSize(15);
    editor.setShowPrintMargin(false);
    editor.getSession().setMode("ace/mode/c_cpp");

    editor.setValue(boilerplateCode);

    /* Formatting the markdown description */
    var description_markdown = $('.description').text();
    var description_html = markdown.makeHtml(description_markdown);
    $('.description').html(description_html);

    /* Binding tabs */
    $('.nav-tab a').click(function (e) {
      e.preventDefault()
      $(this).tab('show')
    })

    /* Binding the submit button */
    $('.btn-submit').click(function() {
        $(this).attr('disabled', 'disabled');

        var code = editor.getValue();
        submitCode(exerciseId, code);

    });

});
