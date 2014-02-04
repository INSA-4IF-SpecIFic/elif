$(document).ready(function(){
    /* Editor initialization and configuration */
    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/textmate");
    editor.setFontSize(14);
    editor.setShowPrintMargin(false);
    editor.getSession().setMode("ace/mode/c_cpp");

});
