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
		// If we're hitting the current button, stop propagation so we don't re-open it again instantly.
		if (window.event.toElement==thisButton) {event.stopPropagation()}
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
	background.style.zIndex = '9998'
	progContent = document.createElement('div')
	progContent.id = 'progressContent'
	progContent.style.zIndex = '9999'
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
	if (gebi('progressBackground')!=null)
		document.body.removeChild(gebi('progressBackground'))
	if (gebi('progressContent')!=null)
		document.body.removeChild(gebi('progressContent'))
}

function showProgressBar(dialogMessage) {
	// Make the elements.
	background = document.createElement('div')
	background.id = 'progressBackground'
	background.style.zIndex = '9998'
	progContent = document.createElement('div')
	progContent.id = 'progressContent'
	progContent.style.zIndex = '9999'
	progBar = document.createElement('div')
	progBar.id = 'progBar' 
	progColor = document.createElement('div')
	progColor.id = 'progColor'
	progressText = document.createElement('h2')
	progressText.id = 'progressText'
	progressText.textContent = dialogMessage
	// Insert the elements.
	document.body.appendChild(background)
	document.body.appendChild(progContent)
	progBar.appendChild(progColor)
	progContent.appendChild(progBar)
	progContent.appendChild(progressText)
}

function removeProgressBar() {
	if (gebi('progressBackground')!=null)
		document.body.removeChild(gebi('progressBackground'))
	if (gebi('progressContent')!=null)
		document.body.removeChild(gebi('progressContent'))
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