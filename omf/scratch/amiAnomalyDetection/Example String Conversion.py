from datetime import datetime

testString = '10/1/2012 11:00:00 PM'

dtObject = datetime.strptime(testString, '%m/%d/%Y %H:%M:%S %p')

print dtObject.isoformat()