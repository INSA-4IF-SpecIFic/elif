function updateMonitored() {
    $('.progress-table').find('td, th').show();

    // If nothing is selected, we show all the exercises
    if ($('.exercises .selected').length == 0) {
        return;
    }

    // Otherwise we hide the exercises that aren't selected
    $('.exercises li:not(.selected)').each(function (i, exercise) {
        var exerciseId = $(exercise).data('exercise-id');
        var ix = $('.progress-table th[data-exercise-id="' + exerciseId + '"]').index();
        $('.progress-table').find('td:nth-child(' + (ix + 1) + '),th:nth-child(' + (ix + 1) + ')').hide();
    });
}

$(document).ready(function() {
    $('.exercises').on('click', 'li', function(e) {
        $(this).toggleClass('selected');

        updateMonitored();
    });
});
