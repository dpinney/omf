function groupBy(inArr, func) {
	// Take a list and func, and group items in place comparing with func.
	// Make sure the func is an equivalence relation, or your brain will hurt.
	if (inArr == []) {return inArr}
	else if (inArr.length == 1) {return [inArr]}
	newL = [[inArr[0]]]
	for (i=1;i<inArr.length;i++) {
		console.log(['comparing',inArr[i], newL.slice(-1)[0][0]])
		if (func(inArr[i], newL.slice(-1)[0][0])) {
			newL.slice(-1)[0].push(inArr[i])
		}
		else {
			newL.push([inArr[i]])
		}
	}
	return newL
}

function aggSeries(timeStamps, timeSeries, func, level) {
	// Different substring depending on what level we aggregate to:
	if (level=='month') {endPos = 7}
	else if (level=='day') {endPos = 10}
	combo = zip(timeStamps, timeSeries)
	// Group by level:
	groupedCombo = groupBy(combo, function(x1,x2) {x1[0].slice(0,endPos)==x2[0].slice(0,endPos)})
	// Get rid of the timestamps:
	//TODO: port the following line from python to javascript:
	// groupedRaw = [[pair[1] for pair in group] for group in groupedCombo]
	return groupedRaw.map(func)
}
