// Runs when the document is ready

$( document ).ready(function() {

var timer = setInterval(check_max_id, 5000);
//clearInterval(timer);

$(".comment-label").click(showOrHideCommentForm);
 var csrftoken = getCsrftoken();
  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
          }
      }
  });

$(".comment-form").on('submit', postCommentForm);

function check_max_id(){
    // if the #max_id has a value
    var past_max =  $('#max_id').val() ? past_max = $('#max_id').val() : past_max = "0";
    var url = "check_id/" + past_max;
    $.get(url, function(data){
        var outerdiv = $('#posts_div');
        if(data){
            console.log(data);
            $('#posts_div').prepend(data);
            $.get("get_max_id/", function(data){
                var new_max_id = data.new_max_id;
                console.log(new_max_id);
                $('#max_id').val(new_max_id);
            });
        }

    });

}



function showOrHideCommentForm(){
    var id = $(this)[0].id;
    var form_id = "#comment-form-"+id;
    if($(form_id).is(":visible")){
        $(form_id).hide();
    }else{
        $(form_id).show();
    }
}

function getCsrftoken() {
    var name = 'csrftoken';
    var csrfValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // if this cookie string begin with the name 'csrftoken' e.g. csrftoken='xxxxxx'
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                csrfValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return csrfValue;
  }
  // set the request header.
  function csrfSafeMethod(method) {
    // these types of requests will not need a csrf token.
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }
    // set the csrf token in the request.

  // post the comment
  function postCommentForm(e){
    e.preventDefault();
    var idToken = $(this)[0].id;
    var url = '/grumblr/comment/'+idToken;
    console.log("here")
    $.post(url, $('#'+idToken).serialize() ,function(data){
        if(data.error){
            $("#"+idToken+"-error").val(data.error);
             $("#"+idToken+"-error").show();

        }

        if(data){
            $("#"+idToken+"-error").hide();
                console.log($("#"+idToken+'-div'));

                $("#"+idToken+'-div').append(data);
                $("#"+idToken).show();
                var id = idToken.match(/\d+/);
                // update comment count
                $.get("/grumblr/get_comment_count/"+id, function(data){
                    console.log("enter");
                    $("#"+id).html("Comment("+data.count+")");
                })
                $('#'+idToken).find("textarea").val('');

        }
    });
  }

}); // End of $(document).ready
