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
            setTimeout(function() { submissionState(submission_id); }, 1000);
            return;
        }

        // Otherwise, we show the result
        if (submission.compilation_error) {
            $('.output').attr('class', 'output');
            $('.output').addClass('error');
            $('.output').html(preprocessText(submission.compilation_log));
            $('.output').fadeIn(500);
        }
        else if (submission.test_results) {
            $('.output').attr('class', 'output');
            $('.output').addClass('execution');
            $('.output').html(preprocessText(submission.test_results.join('\n')));
            $('.output').fadeIn(500);
        }
        else {
            $('.output').hide();
        }
    });

}

$(document).ready(function(){
    /* Getting the current exercise's data */
    var exercise_id = $('#exercise').data('id');

    /* Editor initialization and configuration */
    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/textmate");
    editor.setFontSize(15);
    editor.setShowPrintMargin(false);
    editor.getSession().setMode("ace/mode/c_cpp");

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
        var code = editor.getValue();

        submitCode(exercise_id, code);

    });

});
