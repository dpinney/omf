import sys, os
sys.path.append('../../')
from pathlib import Path
from cymeToGridlab import *

def _tests(Network, Equipment, keepFiles=True):
    import os, json, traceback, shutil
    from solvers import gridlabd
    from matplotlib import pyplot as plt
    import feeder
    exceptionCount = 0       
    try:
        #db_network = os.path.abspath('./uploads/IEEE13.mdb')
        #db_equipment = os.path.abspath('./uploads/IEEE13.mdb')
        prefix = str(Path("testPEC.py").resolve()).strip('scratch\cymeToGridlabTests\testPEC.py') + "\uploads\\"      
        db_network = "C" + prefix + Network
        db_equipment = "C" + prefix + Equipment
        id_feeder = '650'
        conductors = prefix + "conductor_data.csv"
        #print "dbnet", db_network
        #print "eqnet", db_equipment               
        #print "conductors", conductors
        #cyme_base, x, y = convertCymeModel(db_network, db_equipment, id_feeder, conductors)
        cyme_base, x, y = convertCymeModel(str(db_network), str(db_equipment), test=True, type=2, feeder_id='CV160')    
        feeder.attachRecorders(cyme_base, "TriplexLosses", None, None)
        feeder.attachRecorders(cyme_base, "TransformerLosses", None, None)
        glmString = feeder.sortedWrite(cyme_base)
        feederglm = "C:\Users\Asus\Documents\GitHub\omf\omf\uploads\PEC.glm"
        #print "feeederglm", feederglm
        gfile = open(feederglm, 'w')
        gfile.write(glmString)
        gfile.close()
        #print 'WROTE GLM FOR'
        outPrefix = "C:\Users\Asus\Documents\GitHub\omf\omf\scratch\cymeToGridlabTests\\"          
        try:
            os.mkdir(outPrefix)
        except:
            pass # Directory already there.     
        '''Attempt to graph'''      
        try:
            # Draw the GLM.
            print "trying to graph"
            myGraph = feeder.treeToNxGraph(cyme_base)
            feeder.latLonNxGraph(myGraph, neatoLayout=False)
            plt.savefig(outPrefix + "PEC.png")
            print "outprefix", outPrefix + "PEC.png"
            print 'DREW GLM OF'
        except:
            exceptionCount += 1
            print 'FAILED DRAWING'
        try:
            # Run powerflow on the GLM.
            output = gridlabd.runInFilesystem(glmString, keepFiles=False)
            with open(outPrefix + "PEC.JSON",'w') as outFile:
                json.dump(output, outFile, indent=4)
            print 'RAN GRIDLAB ON\n'                 
        except:
            exceptionCount += 1
            print 'POWERFLOW FAILED'
    except:
        print 'FAILED CONVERTING'
        exceptionCount += 1
        traceback.print_exc()
    if not keepFiles:
        shutil.rmtree(outPrefix)
    return exceptionCount    
    '''db_network = os.path.abspath('./uploads/PasoRobles11cymsectiondevice[device]['phases']08.mdb')
    db_equipment = os.path.abspath('./uploads/PasoRobles1108.mdb')
    id_feeder = '182611108'
    conductors = os.path.abspath('./uploads/conductor_data.csv')
    cyme_base, x, y = convertCymeModel(db_network, db_equipment, id_feeder, conductors)
    glmString = feeder.sortedWrite(cyme_base)
    gfile = open("./uploads/PR1108Conversion.glm", 'w')
    gfile.write(glmString)
    gfile.close()'''
if __name__ == '__main__':
    #_tests("PEC-2014-DEC-17.mdb", "PEC_Equipment_CYME.mdb") #Old PEC File doesn't contain loads/transformer
    _tests("pecTotalNetwork_New.mdb", "RevisedEquipmentDatabase_New.mdb")