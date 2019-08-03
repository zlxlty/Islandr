$(document).ready(function () {

    $('#form-with-disable').submit(function() {

        $("#disable-submitBtn").attr("disabled", true);
        $("#disable-submitBtn").val("Please wait ... ");
        return true;

    });

    $('#form-with-disable-hard').submit(function() {

        $("#submit").attr("disabled", true);
        $("#submit").val("Please wait ... ");
        return true;

    });

});
