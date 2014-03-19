/* \!/ You must include editor.js before this file !!! */

$(document).ready(function() {
	//hide edition inputs (title and score)
    $(".hidden-input").hide();
    $(".glyphicon-pencil").hide();
    /* Formatting the markdown description */
    var description_markdown = $('.description').text();
    var description_html = markdown.makeHtml(description_markdown);
    $('.description').html(description_html);

    var lastSubmissionCode = $('#exercise').data('submission-code');
	mainEditor.setValue(lastSubmissionCode);
});
