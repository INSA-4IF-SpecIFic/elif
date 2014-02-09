var websocketURI = function() {
    var loc = window.location, new_uri;
    if (loc.protocol === "https:") {
        new_uri = "wss:";
    } else {
        new_uri = "ws:";
    }
    new_uri += "//" + loc.host;
    return new_uri;
}

var submitCode = function(exercise_id, code) {
    var params = {exercise_id: exercise_id, code: code};
    apiCall('/compile', 'POST', params, function(data) {
        console.log(data);

        // If the code submission still haven't been processed, we poll the server again
        if (!data.processed) {
            submitCode(exercise_id, code);
            return;
        }

        // Otherwise, we show the result
        if (data.compilation.stderr) {
            $('.output').attr('class', 'output');
            $('.output').addClass('error');
            $('.output').html(preprocessText(data.compilation.stderr));
            $('.output').fadeIn(500);
        }
        else if (data.execution.stdout) {
            $('.output').attr('class', 'output');
            $('.output').addClass('execution');
            $('.output').html(preprocessText(data.execution.stdout));
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
    editor.setFontSize(18);
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
