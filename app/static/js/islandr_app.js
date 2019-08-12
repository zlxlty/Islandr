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

    $("div.moment-icon").on('click', function(){

        var moment_id = parseInt($(this).attr("moment_id"), 10);

        $.ajax({
            data : {
                id : moment_id
            },
            type : "POST",
            url : Flask.url_for('moment.like_or_unlike')
        })
        .done(function(data){
            $('div[moment_id=' + moment_id + '][name="moment-icon"]').html(data['icon_html']);
            $('div[moment_id=' + moment_id + '][name="moment-text"]').html(data['text_html']);
        });

    });

});
