$(function(){
    $("#new_post").submit(function(e){
	return submit_something("#new_post", e, "#allPosts", false)
    })
    $(document).on("submit", ".commentForm", function(e){
	var post_id = $(this).parent().attr("id");
	return submit_something(".post#"+post_id+" .commentForm", e, ".post#"+post_id+" .comments", true)
	
    })
})

function submit_something(form_selector, e, pendTo_selector, append){
    var data = $(form_selector).serialize();
    var url = $(form_selector).attr("action");
    $.ajax({
	url:url,
	data:data,
	method:"post",
	async:false,
    }).done(function(data){
	if (append)
	    $(pendTo_selector).append($(data));
	else
	    $(pendTo_selector).prepend($(data));
    })
    $(form_selector).children("input[type=text], textarea").val("").first().focus();
    e.preventDefault();
    return false;
}
