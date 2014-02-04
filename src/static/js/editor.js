$(document).ready(function(){
    /* Editor initialization and configuration */
    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/textmate");
    editor.setFontSize(14);
    editor.setShowPrintMargin(false);
    editor.getSession().setMode("ace/mode/c_cpp");

    /* Binding the submit button */
    $('.btn-submit').click(function() {
        params = {code: editor.getValue()};
        apiCall('/compile', 'POST', params, function(data) {
            $('.output').addClass('error');
            $('.output').html(preprocessText(data.stderr));
        });
    });

});
