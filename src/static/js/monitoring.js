var updateMonitored = function() {
    $('.progress-table').find('td, th').show();

    // If nothing is selected, we show all the exercises
    if ($('.exercises .selected').length == 0) {
        return;
    }

    // Otherwise we hide the exercises that aren't selected
    $('.exercises li:not(.selected)').each(function (i, exercise) {
        var exerciseId = $(exercise).data('exercise-id');
        var ix = $('.progress-table th[data-exercise-id="' + exerciseId + '"]').index();
        $('.progress-table').find('td:nth-child(' + ix + '),th:nth-child(' + ix + ')').hide();
    });
}

$(document).ready(function() {
    $('.exercises').on('click', 'li', function(e) {
        $(this).toggleClass('selected');

        updateMonitored();
    });
});
