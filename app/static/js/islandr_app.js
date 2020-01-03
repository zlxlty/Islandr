/*
 * @Author: Tianyi Lu
 * @Description: Islandr JS
 * @Date: 2020-01-03 15:05:40
 * @LastEditors  : Tianyi Lu
 * @LastEditTime : 2020-01-03 15:49:08
 */

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

    $("button.QR-Code").on('click', function(){

        var event_id = parseInt($(this).attr("event_id"), 10);

        $.ajax({
            data : {
                id : event_id
            },
            type : "POST",
            url : Flask.url_for('event.qr_code')
        })
        .done(function(data){
            $('div[name="QR-Display"]').html(data['QR_html'])
        });

        
    });

    $("input.limited-file-size").bind('change', function(){

        var i;
        for (i = 0; i < this.files.length; i++) {
            console.log(i);
            console.log(this.files[i]);
            var size = this.files[i].size/1024/1024;
            console.log(size);
            size = size.toFixed(2);

            if (size > 5) {
                alert('Maximum size allowed for EACH file is 5MB. You have uploaded a : ' + size + "MB file.");
                $(this).val("");
            }
        }

    });

});
