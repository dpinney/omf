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

function dropPill(thisButton, name) {
	thisButton.nextSibling.nextSibling.style.display = 'inline-block'
	thisButton.innerHTML = name + ' ▴'
	function clickCloseEvent() {
		// Close the menu:
		thisButton.nextSibling.nextSibling.style.display = 'none'
		thisButton.innerHTML = name + ' ▾'
		// Remove the event when it's fired once:
		this.removeEventListener('click', arguments.callee, true)
		// Chill with the propagation, man. Tends not to work...
		// event.stopPropagation()
	}
	// Add that function as a listener to take care of closing: 
	document.body.addEventListener('click', clickCloseEvent, true)
}

function dropPillAndStay(thisButton, name) {
	if (typeof this.currentState == 'undefined' || this.currentState == 'raised') {
		thisButton.nextSibling.nextSibling.style.display = 'inline-block'
		thisButton.innerHTML = name + ' &times;'
		this.currentState = 'dropped'
	} else {
		thisButton.nextSibling.nextSibling.style.display = 'none'
		thisButton.innerHTML = name + ' ▾'
		this.currentState = 'raised'
	}
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

function showProgressDialog(dialogMessage) {
	// Make the elements.
	background = document.createElement('div')
	background.id = 'progressBackground'
	progContent = document.createElement('div')
	progContent.id = 'progressContent'
	spinner = document.createElement('img')
	spinner.src = '/static/spinner.gif'
	progressText = document.createElement('h2')
	progressText.id = 'progressText'
	progressText.textContent = dialogMessage
	// Insert the elements.
	document.body.appendChild(background)
	document.body.appendChild(progContent)
	progContent.appendChild(spinner)
	progContent.appendChild(progressText)
}

function removeProgressDialog() {
	document.body.removeChild(gebi('progressBackground'))
	document.body.removeChild(gebi('progressContent'))
}