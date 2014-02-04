$(document).ready(function(){
    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/textmate");
    editor.setFontSize(14);
    editor.getSession().setMode("ace/mode/c_cpp");

});
