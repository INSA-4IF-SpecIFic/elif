/* \!/ You must include student.js before this file !!! */

var initExercise = function(exerciseId) {

    // Disable add button
    $('#btn-add-test').attr('disabled', 'disabled');

    // Load the exercise's test list
    apiCall('/api/exercise/' + exerciseId, 'GET', {}, function(data) {
        if(data.ok) {
            var exercise = data.result;
            $('#tests_placeholder').html(testsListTemplate(exercise));
        }
        else {
            notification.error("Failed to load exercise: " + data.result);
        }
    });

    // Check if the test's input and output are set (not empty) and
    // enable/disable the "Add test" button accordingly
    var validateTestParams = function() {
        if ($('#test-input').val().length > 0 && $('#test-output').val().length > 0) {
            $('#btn-add-test').removeAttr('disabled');
        }
        else {
            $('#btn-add-test').attr('disabled', 'disabled');
        }
    };

    $('#test-input').on('input', validateTestParams);
    $('#test-output').on('input', validateTestParams);


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
        var exerciseId = $('#exercise').attr('data-id');

        var params = { input: input, output: output, exercise_id: exerciseId };

        apiCall('/api/test/', 'POST', params, function(data) {
            if(data.ok) {
                var exercise = data.result
                $('#tests_placeholder').html(testsListTemplate(exercise));
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

        var exerciseId = $('#exercise').attr('data-id');

        var params = {exercise_id: exerciseId };

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
    var exerciseId = $exercise.data('id');
    var boilerplateCode = $exercise.data('boilerplate-code');
    var referenceCode   = $exercise.data('reference-code');

    /* Getting Handlebar templates */
    testsListTemplate = loadTemplate('#tests-list-template');

    /* Initialize tests interface */
    initExercise(exerciseId);

    /* Editor initialization and configuration */
    var exerciseEditor = ace.edit("exercise-editor");
    exerciseEditor.setTheme("ace/theme/textmate");
    exerciseEditor.setFontSize(15);
    exerciseEditor.setShowPrintMargin(false);
    exerciseEditor.getSession().setMode("ace/mode/c_cpp");
    exerciseEditor.setValue(boilerplateCode);

    var referenceEditor = ace.edit("main-editor");
    referenceEditor.setValue(referenceCode);

    /* Formatting the markdown description */
    var descriptionMarkdown = $('.description').text();
    var descriptionHtml = markdown.makeHtml(descriptionMarkdown);
    $('.description').html(descriptionHtml);
});
