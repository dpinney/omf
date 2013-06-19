memoryBoard = {}

@app.route('/board/<bKey>/<bVal>')
def board(bKey='1',bVal=''):
        memoryBoard[bKey]=bVal
        return str(memoryBoard)

backBoard = {'data':'notYet'}

@app.route('/kickoff/')
def kickoff():
        def zack():
                import time
                time.sleep(100)
                backBoard['data'] = 'Startd frm the bottom, now Im here.'
        backer = backgroundProc(zack,[])
        backer.run()
        return 'DRAKE INITIALIZIED.'

@app.route('/readoff/')
def readoff():
        return str(backBoard)
