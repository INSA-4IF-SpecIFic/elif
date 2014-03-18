/* \!/ You must include editor.js before this file !!! */

var initExercise = function(exerciseId) {

    //hide edition inputs (title and score)
    $(".hidden-input").hide();
    $(".glyphicon-pencil").hide();

    // Unpublish exercise
    apiCall('/api/exercise/'+ exerciseId + '/unpublish', 'POST', {}, function(data) {
        if(!data.ok) {
            notification.error("Failed to unpublish exercise: " + data.result);
        }
    });


    // Disable add button
    $('#btn-add-test').attr('disabled', 'disabled');

    //tags input configuration
    $(".tagsManager").tagsManager({
        prefilled: null,
        CapitalizeFirstLetter: true,
        preventSubmitOnEnter: true,
        typeahead: true,
        typeaheadAjaxSource: "/api/tags",
        typeaheadSource: ["Algorithms","Trees","Sort"],
        delimiters: [9, 13, 44], // tab, enter, comma
        backspace: [8],
        blinkBGColor_1: '#FFFF9C',
        blinkBGColor_2: '#CDE69C',
        hiddenTagListName: 'hiddenTagList'
    });

    // Load the exercise's test list
    apiCall('/api/exercise/' + exerciseId, 'GET', {}, function(data) {
        if(data.ok) {
            var exercise = data.result;
            var tags = exercise.tags;
            for (var i = 0; i < tags.length; i++) {
                $(".tagsManager").tagsManager('pushTag',tags[i]);
            }
            $('#tests_placeholder').html(testsListTemplate(exercise));
        }
        else {
            notification.error("Failed to load exercise: " + data.result);
        }
    });

    // Check if the test's input and output are set (not empty) and
    // enable/disable the "Add test" button accordingly
    var validateTestParams = function() {
        if ($('#test-input').val().length > 0 && $('#test-output').val().length > 0) {
            $('#btn-add-test').removeAttr('disabled');
        }
        else {
            $('#btn-add-test').attr('disabled', 'disabled');
        }
    };

    $('#test-input').on('input', validateTestParams);
    $('#test-output').on('input', validateTestParams);


    // Expand a test's view (by clicking on its heading)
    $('.tests').on('click', 'li .heading', function(e) {
        $li = $(this).closest('li');
        $('.tests li').not($li).find('.details').hide(200);
        $li.find('.details').stop();
        $li.find('.details').toggle(400);
    });

    // Add a test
    $('#btn-add-test').click(function() {
        var $this = $(this)
        var input  = $("#test-input").val();
        var output = $("#test-output").val();
        var exerciseId = $('#exercise').attr('data-id');

        var params = { input: input, output: output, exercise_id: exerciseId };

        apiCall('/api/test/', 'POST', params, function(data) {
            if(data.ok) {
                var exercise = data.result
                $('#tests_placeholder').html(testsListTemplate(exercise));
            }
            else {
                notification.error("Failed to add test: " + data.result);
            }
        });
    });


    // Delete a test
    $('.tests').on('click', '.heading .delete', function(e) {
        $this = $(this).closest('li');
        var test_id = $this.attr('data-test-id');

        var exerciseId = $('#exercise').attr('data-id');

        var params = {exercise_id: exerciseId };

        apiCall('/api/test/' + test_id, 'DELETE', params, function(data) {
            $this.hide(200, function() {
                $this.remove();
            });
        });

        // Avoid triggering an event on the parent li
        e.stopPropagation();
    });
};


var save = function(exerciseId, publish) {
    var title = $("#exercise-title").text();
    var description = descriptionEditor.getElement('editor').body.innerText;
    var tags = $('[name="hiddenTagList"]').val();
    var score = $('#score').val();
    if (score == "") {
        score = $('#score').attr('placeholder');
    }
    var boilerplateCode  = exerciseEditor.getValue();
    var referenceCode = referenceEditor.getValue();

    console.log("title : " + title);
    console.log("description : " + description);
    console.log("exercise code : " + boilerplateCode);
    console.log("reference code : " + referenceCode);
    console.log("tags : " + tags);
    console.log("score : " + score);

    params = { title: title, description: description,
               boilerplate_code: boilerplateCode, reference_code: referenceCode,
               published: publish, tags: tags, score: score};

    apiCall('/api/exercise/' + exerciseId, 'POST', params, function(data) {
        if(data.ok) {
            if (publish) {
                $('#publish-button').removeAttr('disabled', 'disabled');
                $(location).attr('href', "/");
            }
        }
        else {
            notification.error("Failed to load exercise: " + data.result);
        }
    });
}

function editTitle() {
    var title = $(this).text();
    $(this).hide();
    var $inputExercise = $("#title-input");
    $inputExercise.val(title);
    $inputExercise.show();
    $inputExercise.focus();
}

function editScore() {
    var score = $(this).find(".value").text();
    $(this).hide();
    var $inputScore = $("#score");
    $inputScore.val(score);
    $inputScore.show();
    $('#score-check').show();
    $inputScore.focus();
}


$(document).ready(function() {
    /* Getting the current exercise's data */
    var $exercise = $('#exercise');
    var exerciseId = $exercise.data('id');
    var boilerplateCode = $exercise.data('boilerplate-code');
    var referenceCode   = $exercise.data('reference-code');

    /* Getting Handlebar templates */
    testsListTemplate = loadTemplate('#tests-list-template');

    /* Initialize tests interface */
    initExercise(exerciseId);

    /* Editor initialization and configuration */
    exerciseEditor = ace.edit("exercise-editor");
    exerciseEditor.setTheme("ace/theme/textmate");
    exerciseEditor.setFontSize(15);
    exerciseEditor.setShowPrintMargin(false);
    exerciseEditor.getSession().setMode("ace/mode/c_cpp");
    exerciseEditor.setValue(boilerplateCode);

    referenceEditor = ace.edit("main-editor");
    referenceEditor.setValue(referenceCode);

    var opts = {
      container: 'description-editor',
      textarea: 'description-editor-content',
      basePath: '/static/css/',
      clientSideStorage: true,
      localStorageName: 'description-editor',
      useNativeFullscreen: true,
      parser: marked,
      file: {
        name: 'description-editor',
        defaultContent: '',
        autoSave: 100
      },
      theme: {
        base: 'teacher-editor.css',
        preview: 'description-editor.css',
        editor: 'epiceditor/editor/epic-light.css'
      },
      button: {
        preview: true,
        fullscreen: true,
        bar: "auto"
      },
      focusOnLoad: false,
      shortcut: {
        modifier: 18,
        fullscreen: 70,
        preview: 80
      },
      string: {
        togglePreview: 'Toggle Preview Mode',
        toggleEdit: 'Toggle Edit Mode',
        toggleFullscreen: 'Enter Fullscreen'
      },
      autogrow: true
    }

    descriptionEditor = new EpicEditor(opts);
    descriptionEditor.load();
    descriptionEditor._setupTextareaSync();
    descriptionEditor.preview();

    $('#save-button').click(function() {
        var $this = $(this);
        $this.attr('disabled', 'disabled');
        save(exerciseId, false);
        $this.removeAttr('disabled', 'disabled');
    });

    $('#publish-button').click(function() {
        var $this = $(this);
        $this.attr('disabled', 'disabled');
        save(exerciseId, true);
    });

    $('#delete-button').click(function() {
        var params = {exercise_id: exerciseId };
        console.log("delete");
        apiCall('/api/exercise', 'DELETE', params, function(data) {
            if(data.ok) {
                window.location.replace('/');
            }
            else {
                notification.error("Failed to delete exercise: " + data.result);
            }
        });
    });

    //actions on title and score fields
    $('#panel-title').on( "mouseleave",function() {
        var $titleInput = $("#title-input");
        var $titleField = $('#exercise-title');
        $titleInput.hide();
        var title = $titleInput.val();
        if (title != "") {
            $titleField.text(title);
        }
        $titleField.show();

        var $score = $('#score');
        if (!$score.hasClass('invalid')) {
            var score = $score.val();
            if (score == "") {
                score = $score.attr('placeholder');
            }
            $('#score-check').hide();
            $(".coins").show();
            $(".coins").find(".value").text(score);
            $score.hide();
            $(".glyphicon-pencil").hide();
        }
    });

    $('#panel-title').on( "mouseenter",function() {
        $(".glyphicon-pencil").show();
    });

    $('#exercise-title').on("click", editTitle);

    $('.coins').on("click", editScore);

    //numeric check on score field
    $('#score').on("keyup", function () {
        var $element = $(this);
        var input = $element.val();
        if (input.match(/^[0-9]+$/) || input == "") {
            $element.removeClass('invalid');
            $('#score-check').attr('class', "glyphicon glyphicon-ok");
            $('#publish-button').removeAttr("disabled");
            $('#save-button').removeAttr("disabled");
        } else {
            $element.addClass('invalid');
            $('#score-check').attr('class', "glyphicon glyphicon-remove");
            $('#publish-button').attr('disabled', 'disabled');
            $('#save-button').attr('disabled', 'disabled');
        }
    });

});

