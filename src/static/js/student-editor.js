/* \!/ You must include editor.js before this file !!! */

$(document).ready(function() {
    /* Formatting the markdown description */
    var description_markdown = $('.description').text();
    var description_html = markdown.makeHtml(description_markdown);
    $('.description').html(description_html);
});
