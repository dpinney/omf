function post_to_url(path, params, method) {
	method = method || 'post' // Set method to post by default, if not specified.
	var form = document.createElement('form')
	form.setAttribute('method', method)
	form.setAttribute('action', path)
	for(var key in params) {
		if(params.hasOwnProperty(key)) {
			var hiddenField = document.createElement('input')
			hiddenField.setAttribute('type', 'hidden')
			hiddenField.setAttribute('name', key)
			hiddenField.setAttribute('value', params[key])
			form.appendChild(hiddenField)
		}
	}
	document.body.appendChild(form)
	form.submit()
}

function handle_files(files, contentsId, nameId) {
	// Helper function to pull file contents in to an allInputData data structure.
	// Read the file
	reader = new FileReader()
	reader.readAsText(files[0])
	// After loading, put the name and content in the right hidden inputs:
	reader.onload = function loaded(evt) {
		document.getElementById(nameId).value = files[0].name
		document.getElementById(contentsId).value = reader.result
	}
}

function insert_file_upload_block(fileName, dataVariableName) {
	// Helper function to insert a fully formed and omf-compatible file upload input item.
	// We built this because there are about 7 variables that refer to each and need to all be set correctly.
	parentDiv = document.currentScript.parentElement;

	let inputNode1 = document.createElement("input");
	inputNode1.setAttribute("id", fileName + "Handler");
	inputNode1.setAttribute("type", "file");
	inputNode1.style.display = "none";
	//inputNode1.addEventListener("change", handle_files(this.files,dataVariableName,fileName));
	parentDiv.appendChild(inputNode1);

	let inputNode2 = document.createElement("input");
	inputNode2.setAttribute("id", dataVariableName);
	inputNode2.setAttribute("name", dataVariableName);
	inputNode2.type = "hidden";
	parentDiv.appendChild(inputNode2);

	let innerDiv = document.createElement("div");
	parentDiv.appendChild(innerDiv);

	let labelNode = document.createElement("label");
	labelNode.setAttribute("for", fileName + "Handler");
	labelNode.className = "fileButton";
	labelNode.innerHTML = "Choose File";
	innerDiv.appendChild(labelNode);

	let inputNode3 = document.createElement("input");
	inputNode3.setAttribute("id", fileName);
	inputNode3.setAttribute("name", fileName);
	inputNode3.value = '';
	inputNode3.readOnly = true;
	inputNode3.className = "uploadFileName";
	innerDiv.appendChild(inputNode3)

	//inputNode1.addEventListener("change", handle_files(this.files,dataVariableName,fileName));
	inputNode1.addEventListener("change", function (){
		handle_files(this.files,dataVariableName,fileName);
	});

}


function ajaxReq(requestType, URL, asynch) {
	var xmlhttp
	if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
		xmlhttp=new XMLHttpRequest()
	}
	else {// code for IE6, IE5
		xmlhttp=new ActiveXObject("Microsoft.XMLHTTP")
	}
	xmlhttp.open(requestType, URL, asynch)
	xmlhttp.send()
	return xmlhttp.responseText
}

function gebi(id) {
	// Shorten a much-used method name:
	return document.getElementById(id)
}

function clone(obj) {
	// Deep copy of a given obj.
	if (null == obj || "object" != typeof obj) return obj;
	var copy = obj.constructor();
	for (var attr in obj) {
		if (obj.hasOwnProperty(attr)) copy[attr] = obj[attr];
	}
	return copy;
}

function tableClear(table) {
	try {
		while (table.rows.length>0) table.deleteRow(table.rows.length-1)
	}
	catch (err) {
		// Catch: we didn't have any rows.
	}
}

function getRadioSetting (className) {
	// Get which radio button is set for a group with a given className.
	value='';
	radios = document.getElementsByClassName(className);
	for (x in radios) {if (radios[x].checked) value = radios[x].value}
	return value
}

function time(func) {
	// How long does func take to execute?
	var start = +new Date()
	func()
	var end =  +new Date()
	return end - start
}

function round(number,precision) {
	return parseFloat(number.toPrecision(precision))
}

function randomGaussian() {
  // Get a Gaussian from a uniform(0,1) via the Box-Muller transform.
  do {
	x1 = 2 * Math.random() - 1
	x2 = 2 * Math.random() - 1
	rad = x1 * x1 + x2 * x2
  } while (rad >= 1 || rad == 0)
  c = Math.sqrt(-2 * Math.log(rad) / rad);
  return x1 * c
}

function randomChoice(inList) {
	return inList[Math.floor(Math.random() * inList.length)]
}

function randomInt(min,max) {
	return Math.floor(Math.random()*(max - min + 1) + min)
}

function zip(arrays) {
	// Take in two arrays as [A,B], return [[a1,b1],[a2,b2,],...]
	return arrays[0].map(function(_,i){
		return arrays.map(function(array){return array[i]})
	})
}

function partition(inL, eqRel) {
	// Group inL as compared by eqRel. Make sure the eqRel is an equivalence relation, or your brain will hurt.
	if (inL.length == 0) {return inL}
	if (inL.length == 1) {return [inL]}
	accum = []
	work = [inL[0]]
	for (i=1;i<inL.length;i++) {
		if (eqRel(inL[i], work[0])) {
			work.push(inL[i])
		}
		else {
			accum.push(work)
			work = [inL[i]]
		}
	}
	accum.push(work)
	return accum
}

function flatten1(matrix) {
	// Take [A1,A2,...An] and return an in-order list of the items in each Ai.
	accum = []
	for (i=0;i<matrix.length;i++) {
		if (typeof matrix[i] == 'object') {
			for (j=0;j<matrix[i].length;j++) {
				accum.push(matrix[i][j])
			}
		} else {
			accum.push(matrix[i])
		}
	}
	return accum
}

function arrMax(arr) {
	// Get max of an array.
	return Math.max.apply(null,arr)
}

function arrSum(arr) {
	// Sum an array.
	return arr.reduce(function(x,y){return x+y})
}

function indexFind(arr, fun) {
	// Given an array of objects, return the first one where fun(arr[i]) is true.
	for (i=0;i<arr.length;i++) {
		if (fun(arr[i])) {return i}
	}
	return -1
}
function dropPill(thisButton, name) {
	thisButton.style.color= 'black'
	thisButton.style.background= '#F8F8F8'
	thisButton.style.textAlign = 'left'
	thisButton.nextSibling.nextSibling.style.display = 'inline-block'
	thisButton.innerHTML = name + ' ▴'
	function clickCloseEvent() {
		thisButton.nextSibling.nextSibling.style.display = 'none'
		thisButton.innerHTML = name + ' ▾'
		this.removeEventListener('click', arguments.callee, true)
		thisButton.style.color= 'white'
		thisButton.style.background= 'transparent'
		if (window.event.toElement==thisButton) {event.stopPropagation()}
	}
	document.body.addEventListener('click', clickCloseEvent, true)
}
function clickCloseEvent(labelName, buttonName) {
	var thisButton = document.getElementById(buttonName);
	thisButton.nextSibling.nextSibling.style.display = 'none'
	thisButton.innerHTML = labelName + ' ▾'
	this.removeEventListener('click', arguments.callee, true)
	if (window.event.toElement==thisButton) {event.stopPropagation()}
}
function init() {
	// If we have input, put it back.
	if (allInputData != null) {
		restoreInputs()
		$("#modelName").prop("readonly", true)
	}
	if (allOutputData != null) {
		if (allOutputData['oldVersion'] == true) {
			try {
				document.getElementById("triangle-parent").style.visibility = "visible";
			}
			catch (e){}
		}
	} 
	if (allInputData != null) {
		modelUser = allInputData["user"]
	} else {
		modelUser = "none"
	}
	// Display elements based on model status
	if (modelStatus === "finished") {
		console.log("FINISHED")
		$(".postRun").css('display', 'block')
		$(".postRunInline").css('display', 'inline-block')
	} else if (modelStatus === "running") {
		console.log("RUNNING")
		$(".running").css('display', 'block')
		$(".runningInline").css('display', 'inline-block')
		$("input").prop("readonly", true)
		$("select").prop("disabled", true)
	} else {
		// stopped
		if (allInputData != null) {
			$(".stopped").show()
			$(".stoppedInline").show()
		}
	}
	/**
	 * Everyone can see the "duplicate" button, but only if the model is "finished" or stopped"
	 * Only model owners (and admin) can see the "share" button, but only if the model is "stopped" or "finished"
	 * Only model owners (and admin) can see the "run" button, but only if the model is "stopped" or "finished"
	 * Only model owners (and admin) can see the "delete" button, at ALL times
	 * Only model owners (and admin) can see the "cancel run" button, but only if the model is "running"
	 * Other stuff must display in accordance with the model status, the current viewer notwithstanding
	 */
	$("button#deleteButton").hide();
	$("button#shareButton").hide();
	$("button#duplicateButton").hide();
	$("button#runButton").hide();
	$("button#cancelButton").hide();
	// Display elements based on model status and user authorization
	if (modelStatus === "finished" || modelStatus === "stopped") {
		// Anyone can see the duplicate button
		$("button#duplicateButton").show();
	}
	if (modelUser === currentUser || currentUser === "admin") { 
		$("button#deleteButton").show();
		if (modelStatus == "stopped" || modelStatus == "finished") {
			$("button#shareButton").show();
			$("button#runButton").show();
		} else {
			// running
			$("button#cancelButton").show();
		}
	}
}
	

function restoreInputs() {
	// Restore all the input values that were used and stored in allInputData.json
	gebi("titleText").innerHTML = allInputData.modelName
	for (index in allInputData) {
		try {document.querySelector("#" + index).value = allInputData[index]}
		catch(err){}
	}
}

function delimitNumbers(nStr) {
	// Add commas to numbers and round to a decent length.
	nStr += ''
	x = nStr.split('.')
	x1 = x[0]
	x2 = x.length > 1 ? '.' + x[1] : ''
	rgx = /(\d+)(\d{3})/
	while (rgx.test(x1)) {
		x1 = x1.replace(rgx, '$1' + ',' + '$2')
	}
	return x1 + x2
}

function cancelModel() {
	params = {user:allInputData.user,
		modelName:allInputData.modelName,
		modelType:allInputData.modelType}
	post_to_url("/cancelModel/", params, "POST")
}

function deleteModel() {
	if (confirm("Deleting this model cannot be undone. Continue?")){
		post_to_url("/delete/Model/"+allInputData.user+"/"+allInputData.modelName, {}, "POST")
	} else {
		return false
	}
}

/**
 *
 */
function shareModel() {
	const viewers = allInputData.viewers == null ? [] : allInputData.viewers;
	const modal = document.createElement("div");
	modal.id = "emailModal";
	const modalContent = document.createElement("div");
	modalContent.id = "emailModalContent";
	modal.append(modalContent);
	// Add title and instructions
	const h = document.createElement("h1");
	h.textContent = "Share";
	modalContent.append(h);
	const p = document.createElement("p");
	p.textContent = "As the model owner, you may view, duplicate, run, share, and delete this model. " + 
		"Users that you choose to share with may only view and duplicate this model.";
	modalContent.append(p);
	const privacyIndicator = document.createElement("p");
	if (viewers.length === 0) {
		privacyIndicator.textContent = "The model is currently private."
	} else {
		privacyIndicator.textContent = "The model is currently shared."
	}
	modalContent.append(privacyIndicator);
	// Create form and table
	const form = document.createElement("form");
	modalContent.append(form);
	const div = document.createElement("div");
	div.classList.add("tableContainer");
	form.append(div);
	
	const table = document.createElement("table");
	div.append(table);
	const tbody = document.createElement("tbody");
	table.append(tbody);
	for (const email of viewers) {
		const row = getEmailRow()
		row.querySelector("input[name='email']").value = email;
		tbody.append(row);
	}
	// Add add button
	const addButton = getAddButton();
	form.append(addButton);
	// Add buttons
	const buttonDiv = document.createElement("div");
	buttonDiv.classList.add("buttonDiv");
	form.append(buttonDiv);
	const submitButton = getSubmitButton();
	buttonDiv.append(submitButton);
	const closeButton = getCloseButton();
	buttonDiv.append(closeButton);
	form.addEventListener("submit", e => {
		e.preventDefault();
		submitButton.disabled = true;
		const formData = new FormData(form);
		formData.set("user", allInputData.user);
		formData.set("modelName", allInputData.modelName);
		$.ajax({
			type: "POST",
			url: "/shareModel",
			data: formData,
			processData: false,
			contentType: false
		}).done(function(data, text, jqXHR) {
			const emails = JSON.parse(jqXHR.responseText);
			allInputData.viewers = emails;
			closeButton.click();
			shareModel();
			alert("Successfully updated your selection of shared users.");
		}).fail(function(jqXHR, textStatus, errorThrown) {
			resetInvalidFlags();
			if (jqXHR.status === 409) {
				// Notify user that model is running
				alert(jqXHR.responseText);
			} else if (jqXHR.status === 400) {
				// Mark invalid usernames
				const invalidEmails = JSON.parse(jqXHR.responseText)
				Array.from(tbody.getElementsByTagName("input")).forEach(input => {
					if (invalidEmails.includes(input.value)) {
						const td = input.parentElement.nextElementSibling;
						td.removeAttribute("style");
					}
				});
			}

		}).always(function() {
			submitButton.disabled = false;
		});
	});
	document.body.prepend(modal);

	function resetInvalidFlags() {
		Array.from(tbody.querySelectorAll("td[data-isinvalid='true']")).forEach(td => {
			td.style.display = "none";
		});
	}

	function getSubmitButton() {
		const submitButton = document.createElement("button");
		submitButton.type = "submit";
		submitButton.style.marginRight = "14px";
		submitButton.textContent = "Update Sharing";
		return submitButton;
	}

	function getCloseButton() {
		const closeButton = document.createElement("button");
		closeButton.textContent = "Close";
		closeButton.classList.add("deleteButton");
		closeButton.type = "button";
		closeButton.addEventListener("click", function() {
			document.getElementById("emailModal").remove();
		});
		return closeButton;
	}

	function getEmailRow() {
		const row = document.createElement("tr");
		let cell = document.createElement("td");
		row.append(cell);
		const deleteButton = document.createElement("button");
		deleteButton.type = "button";
		deleteButton.classList.add("deleteButton");
		deleteButton.innerHTML = "&#9587;"
		deleteButton.addEventListener("click", function() {
			row.remove();
		});
		cell.append(deleteButton);
		cell = document.createElement("td");
		row.append(cell);
		const input = document.createElement("input");
		input.type = "text";
		input.name = "email";
		input.required = true; // don't let the user submit an empty string as an email
		cell.append(input);
		cell = document.createElement("td");
		cell.textContent = "Invalid username";
		cell.dataset.isinvalid = "true";
		cell.style.display = "none";
		row.append(cell);
		input.addEventListener("change", () => { cell.style.display = "none"; })
		return row;
	}

	function getAddButton() {
		const addButton = document.createElement("button");
		addButton.type = "button";
		addButton.textContent = "Add User";
		addButton.addEventListener("click", function() {
			const emailRow = getEmailRow();
			tbody.prepend(emailRow);
		});
		return addButton;
	}
}

function duplicateModel() {
	newName = prompt("Create a duplicate with name", allInputData.modelName)
	while (! /^[\w\s]+$/.test(newName)){
		newName = prompt("Public a copy with new name, only letters, digits and underscore are allowed in the model name.\nPlease rename your new model", allInputData.modelName)
	}
	if (newName) {
		$.ajax({url:"/uniqObjName/Model/" + currentUser + "/" + newName}).done(function(data) {
			if (data.exists) {
				alert("There is already a model named " + newName)
				duplicateModel()
			} else {
				post_to_url("/duplicateModel/" + allInputData.user + "/" + allInputData.modelName+"/", {"newName":newName})
			}
		})
	}
}

function isFormValid() {
	// Form Validation for Safari browsers
	var inputForm = document.getElementsByTagName('form')[0]
	var inputs = document.getElementsByTagName('input')
	var errors = 0
	for (var i = 0; i < inputs.length; i++) {
		var patt = new RegExp(inputs[i].pattern)
		if (!patt.test(inputs[i].value)) {
			inputs[i].style.backgroundColor = 'red'
			inputs[i].focus()
			errors++
		} else {
			inputs[i].style.backgroundColor = 'gainsboro'
		}
	}
	console.log(errors)
	if (errors) {
		alert("Found [" + errors + "] errors, Please fix inputs in red.")
	} else {
		inputForm.submit()
	}
}

function createModelName(modelType, modelName) {
	var username = sessionStorage.getItem('user');
	console.log(username)
	if (typeof(modelName)==='undefined') modelName = '';
	modelName = prompt("Create a model with name", modelName)
	while (! /^[\w\s]+$/.test(modelName)){
		modelName = prompt("Only letters, digits and underscore are allowed in the model name.\nPlease rename your new model")
	}
	if (modelName) {
		$.ajax({
			url:"/uniqObjName/Model/" + username + "/" + modelName
		}).done(function(data) {
			if (data.exists) {
				alert("There is already a model named " + modelName)
				createModelName(modelType, modelName)
			} else {
				post_to_url("/newModel" + "/"+ modelType + "/" + modelName)
			}
		}).fail(function(jqXHR, textStatus, errorThrown) {
			alert("AJAX request failed to get a successful response from the server.");
		});
	}
}
	
function showSaveAlert(url){
	alert("To return to this model in the future, save this url:\n" + url)
}