// loginform is in this contexte a signup form
// TODO : minimum password length is hardcoded; maybe we should find a way to pass configuration to JS files ?

var minimumPasswordLength = 6;

validForm = function() {
    var $form = $('.loginform');
    var email = $form.find('input[name="email"]').val();
    var username = $form.find('input[name="username"]').val();
    var password = $form.find('input[name="password"]').val();
    var passwordConfirmation = $form.find('input[name="passwordCtrl"]').val();

    if (passwordConfirmation != password) {
        notification.error("Password confirmation doesn't match password")
        return false;
    }
    if (password.length < minimumPasswordLength) {
        notification.error("The password must be at least " + minimumPasswordLength + " characters long");
        return false;
    }
}

$(document).ready(function() {
    $('.loginform').on('submit', function() {
        return validForm();
    })
});
