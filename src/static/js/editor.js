var submitCode = function(exercise_id, code) {
    var params = {exercise_id: exercise_id, code: code};
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

        $('#output').html(output_template(submission));
        $('.nav-tabs a[href="#output"]').tab('show');
    });

}

var exerciseTests = function(exercise_id) {

    apiCall('/api/exercise/' + exercise_id, 'GET', {}, function(data) {
        console.log(data);

        var exercise = data.result;

        console.log(exercise);

        $('#tests_placeholder').html(tests_template(exercise));
    });


    // Expanding a test's view (by clicking on its heading)
    $('.tests').on('click', 'li', function(e) {
        console.log("ON CLICK");
        $li = $(this).closest('li');
        $('.tests li').not($li).find('.details').hide(200);

        $li.find('.details').stop();

        $li.find('.details').toggle(400);
    });



};


$(document).ready(function() {
    /* Getting the current exercise's data */
    var $exercise = $('#exercise');
    var exercise_id = $exercise.data('id');
    var boilerplateCode = $exercise.data('boilerplate-code');

    /* Getting Handlebar templates */
    output_template = loadTemplate('#output-template');
    tests_template = loadTemplate('#tests-template');

    exerciseTests(exercise_id);

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
    $('#test-button').click(function() {
        $(this).attr('disabled', 'disabled');

        var code = editor.getValue();
        submitCode(exercise_id, code);

    });

});
