$(function(){
    $.makeArray($(".feeder_page, .analysis_page")).map(function(f){
	if ($(f).html() == "1")
	    $(f).replaceWith($("<span>").html("1"))
    })
    $(document).on("click", ".feeder_page, .analysis_page", function(e){
	var type = $(this).attr("type");
	var page = $(this).html();
	var link_selector = $(this).attr("class") == "feeder_page" ? "Feeders" : "Analyses";
	var pid = $(this).parent().attr("id")
	var the_class = $(this).attr("class")
	var self = this;
	for (interval in all_intervals){
	    clearInterval(all_intervals[interval]);
	}
	all_intervals = {};
	show_spinner();
	$.ajax({
	    url:"/retrievePage/"+link_selector+"/"+type+"/"+page
	}).done(function(data){
	    $("#spinner").hide();
	    $("tbody."+type+link_selector).html(data);
	    $.makeArray($("#"+pid).children("span")).map(function(s){
		$(s).replaceWith($("<a>").attr("href", "#").attr("type", type).attr("class", the_class).html($(s).html()))
	    })
	    $(self).replaceWith($("<span>").html(page))
	    run_statuses();
	})
	e.preventDefault();
	return false;
    })
})

function show_spinner(){
    var top = (window.innerHeight - $("#spinner").height())/2;
    var left = (window.innerWidth - $("#spinner").width())/2;
    $("#spinner").show().css("top", top).css("left", left);
}
