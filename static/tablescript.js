function fit_table(){
    var raw_height = $("#selBody").height()+$("#daButtons").height()+$("#selHead").height();
    var win_height = window.innerHeight * 0.6;
    $("#selected").css("height", win_height > raw_height ? raw_height : win_height)
}

$(window).resize(fit_table);

function create_table (){
    deselect();
    for (prop in treeData){
	if (prop == "object" || prop == "module"){
	    $("#objmod").html(prop)
	    $("#value").html(treeData[prop])
	}else if (prop != 'from' && prop != 'to' && prop != 'parent' && prop != 'file'){ // Avoid editing machine-written properties!
	    $("#body").append($("<tr>")
			      .append($("<td>").html(prop))
			      .append($("<td>").html(treeData[prop])))
	}
	
    }
}

function selectNode(){
    create_table();
    $("#selected").show();
    $("#selected table").show()
    fit_table();
}



function deselect(){
    $("#objmod, #value, #body").html("")
    $("#selected").css("height", "auto");
    $("#editButtonRow").show()
    $("#otherButtons").hide();
    $("#selected table").hide()
    $("#selected").hide();
}

function validate_blanks(selector){
    var blanks = false;
    $.makeArray($(selector)).forEach(function(e){
	if ($(e).val().trim() == ""){
	    $(e).css("border", "1px solid red");
	    if(!blanks)
		$(e).focus();
	    blanks = true;
	}
    })
    if (blanks){
	alert("Fill in the highlighted fields before you proceed");
    }
    return blanks;
}

$(function(){
    $("#selected").hide();
    $("#editButton").click(function(e){
	$("#editButtonRow").hide();
	$("#otherButtons").show();
	$("#body").html("")
	for (prop in treeData){
	    if (prop != "object" && prop != "module"){
		var tr = $("<tr>")
			.append($("<td>").addClass("propertyName").html(prop))
			.append($("<td>")
				.append($("<input>")
					.val(treeData[prop])
					.attr("name", prop)
					.attr("type", "text")))
		if (prop != "name")
		    tr.prepend($("<td>")
			       .append($("<button>")
				       .addClass("deleteButton")
				       .addClass("deleteProperty")
				       .html("X")))
		else
		    tr.prepend($("<td>"))
		$("#body").append(tr);
	    }
	}
	console.log(treeData);
    })
    $("#cancelButton").click(function(e){
	$("#editButtonRow").show();
	$("#otherButtons").hide();
	$("#body").html("");
	selectNode();
    })
    $("#saveObject").click(function(e){
	if(validate_blanks("#body input"))
	    return;
	function isNameAlreadyUsed(testValue) {
	    // Helper function to make sure we don't make non-unique names.
	    for (leaf in tree) {
		for (attrKey in tree[leaf]) {
		    if (attrKey == 'name' && tree[leaf][attrKey] == testValue) {
			return true
		    }
		}
	    }
	    return false
	}
	var propNames = $("#body td.propertyName");
	for(i=0; i<propNames.length; i++){
	    var key = propNames[i].innerHTML;
	    var newValue = $("#body input[name="+key+"]").val();
	    var oldValue = treeData[key];
	    if (key=='name') {
		// 1. If the name is already the name of something else, skip the renaming.
		if (isNameAlreadyUsed(newValue) && oldValue != newValue) {
		    // cell.innerHTML = oldValue
		    $("#body input[name=name]").val(oldValue);
		    alert('Please choose a unique name.');
		}
		else {
		    treeData[key] = newValue
		    // cell.innerHTML = newValue
		    // k.innerHTML = key
		    // 2. If the name is unique, go through EVERY attribute in the tree and replace the old name with the new one.
		    
		    for (leaf in tree) {
			for (attrKey in tree[leaf]) {
			    if (oldValue == tree[leaf][attrKey]) {console.log(tree[leaf]); tree[leaf][attrKey] = newValue}
			}
		    }
		    // 3. Go through the nodes and replace the name there too. UGH!
		    nodeIndex = findIndex(nodes, 'name', oldValue)
		    if (nodeIndex != "") {nodes[nodeIndex]['name'] = newValue}
		}
	    }else{
		treeData[key] = newValue;
	    }
	}
	Object.keys(treeData).filter(function(e){
	    return $.makeArray(propNames).map(function(x){
		return x.innerHTML;
	    }).indexOf(e) == -1;
	}).forEach(function(e){
	    if (e != "object" && e != "module")
		delete treeData[e];
	})
	$.makeArray($("#body input.newPropertyName")).map(function(e){
	    return e.value;
	}).forEach(function(e, i){
	    if (e.trim() != "")
		treeData[e] = $("#body input.newPropertyValue")[i].value;
	})
	$("#otherButtons").hide();
	$("#editButtonRow").show();
	selectNode();
    })
    $(document).on("click", ".deleteProperty", function(e){
	$(this).parent().parent().remove();
    })
    $("#addAttribute").click(function(e){
	if (validate_blanks(".newPropertyName, .newPropertyValue"))
	    return;
	$("#body").append($("<tr>")
			  .append($("<td>")
				  .append($("<button>")
					  .addClass("deleteButton")
					  .addClass("deleteProperty")
					  .html("X")))
			  .append($("<td>")
				  .append($("<input>")
					  .addClass("newPropertyName")
					  .attr("type", "text")))
			  .append($("<td>")
				  .append($("<input>")
					  .addClass("newPropertyValue")
					  .attr("type", "text"))));
	fit_table();
    })
    $("#deleteObject").click(function(e){
	deleteObject(ti);
    })
})
