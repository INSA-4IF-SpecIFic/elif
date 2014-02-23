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

    // Disable add button
    $('#btn-add-test').attr('disabled', 'disabled');

    // Load the exercise's test list
    apiCall('/api/exercise/' + exercise_id, 'GET', {}, function(data) {
        console.log(data);

        var exercise = data.result;

        console.log(exercise);

        $('#tests_placeholder').html(tests_list_template(exercise));
    });

    // Check if the test's input and output are set (not empty) and
    // enable/disable the "Add test" button accordingly
    var validateSettings = function() {
        if($('#test-input').val() > 0 && $('#test-output').val() > 0) {
            $('#btn-add-test').removeAttr('disabled');
        }
        else {
            $('#btn-add-test').attr('disabled', 'disabled');
        }
    };

    $('#test-input').on('input', function() {
        validateSettings()
    });

    $('#test-output').on('input', function() {
        validateSettings()
    });


    // Expand a test's view (by clicking on its heading)
    $('.tests').on('click', 'li .heading', function(e) {
        $li = $(this).closest('li');
        $('.tests li').not($li).find('.details').hide(200);
        $li.find('.details').stop();
        $li.find('.details').toggle(400);
    });

    // Add a test
    $('#btn-add-test').click(function() {
        var $this = $(this)
        var input  = $("#test-input").val();
        var output = $("#test-output").val();
        var exercise_id = $('#exercise').attr('data-id');

        var params = { input: input, output: output, exercise_id: exercise_id };

        apiCall('/api/test/', 'POST', params, function(data) {
            if(data.ok) {
                var exercise = data.result
                $('#tests_placeholder').html(tests_list_template(exercise));
            }
            else {
                notification.error("Failed to add test: " + data.result);
            }
        });
    });


    // Delete a test
    $('.tests').on('click', '.heading .delete', function(e) {
        $this = $(this).closest('li');
        var test_id = $this.attr('data-test-id');

        var exercise_id = $('#exercise').attr('data-id');

        var params = {exercise_id: exercise_id };

        apiCall('/api/test/' + test_id, 'DELETE', params, function(data) {
            $this.hide(200, function() {
                $this.remove();
            });
        });

        // Avoid triggering an event on the parent li
        e.stopPropagation();
    });

};


$(document).ready(function() {
    /* Getting the current exercise's data */
    var $exercise = $('#exercise');
    var exercise_id = $exercise.data('id');
    var boilerplateCode = $exercise.data('boilerplate-code');

    /* Getting Handlebar templates */
    output_template = loadTemplate('#output-template');
    tests_list_template = loadTemplate('#tests-list-template');

    /* Initialize tests interface */
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
