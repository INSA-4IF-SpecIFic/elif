$(document).ready(function(){
    /* Editor initialization and configuration */
    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/textmate");
    editor.setFontSize(14);
    editor.setShowPrintMargin(false);
    editor.getSession().setMode("ace/mode/c_cpp");

    /* Formatting the markdown description */
    var description_markdown = $('.description').text();
    var description_html = markdown.makeHtml(description_markdown);
    $('.description').html(description_html);

    /* Binding the submit button */
    $('.btn-submit').click(function() {
        params = {code: editor.getValue()};
        apiCall('/compile', 'POST', params, function(data) {
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
    });

});
