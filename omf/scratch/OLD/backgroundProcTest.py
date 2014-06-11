'''
Runs a timer in a thread and updates a shared dictionary.
Gotta put this snipped into omf.py to get it to run.
It's WSGI-safe.
'''

### SHARED STATE TEST
backBoard = {'data':'notYet'}

from threading import Thread, Timer
import time

@app.route('/kickthread/')
def kickthread():
        def nancy():
                import time
                time.sleep(300)
                backBoard['data'] = 'THREADED ON THE TRACK.'
        backBoard['threadd'] = Thread(target=nancy)
        backBoard['threadd'].start()
        return 'DRAKE THREADED.'

def pestFunc():
        backBoard['currentTime'] = time.clock()
        Timer(1, pestFunc).start()

@app.route('/backgroundPester/')
def pester():
        backBoard['pestRef'] = Thread(target=pestFunc)
        backBoard['pestRef'].start()
        return 'PESTERING YALL'

@app.route('/readoff/')
def readoff():
        return str(backBoard)
