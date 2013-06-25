import time
from multiprocessing import Process
from flask import Flask

app = Flask(__name__)

def testFun():
	print 'Starting'
	time.sleep(3)
	print '3 Seconds Later'
backProc = Process(target=testFun, args=())
backProc.start()

@app.route('/')
def root():
	return 'Root'

if __name__ == '__main__':
	app.run(debug=True, use_reloader=False)
