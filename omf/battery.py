'''
Created on Sep 16, 2014
addBattery(dictionary)

Adds one or more batteries to specified nodes in feeder.

Input: Dictionary containing feeder model in dictionary format and battery specifications
Output: Feeder model dictionary with specified battery/batteries added.
    Example:
        nodeList = ['Node633','Node632']
        battDict = {'feederDict': feeder_model, #In dictionary format
                'battNode': nodeList,
                'battEnergyRatingkWh':250,
                'invPowerRatingkW': 100,
                'battSOCpu': 0.5,
                'invControl':'LOAD_FOLLOWING',
                'controlSenseNode': 'Node633',
                'invChargeOnThresholdkW': 1500,
                'invChargeOffThresholdkW': 1700,
                'invDischargeOnThresholdkW': 1800,
                'invDischargeOffThresholdkW': 1750,
                }
        FeederModelWithBatteries = addBattery(battDict)
                
addBattery function only supports one battery being added to a given node/meter.

Nodes where battery is to be added can be a list.  All batteries added from list will have identical specifications (aside for location in feeder).

Recorders for individual batteries are not added.

@author: trevorhardy
'''

import feeder
import sys
import warnings



def addSingleBattery(battDict):
   #Check to see if node where battery is going to be added exists 
    feederTree = battDict['feederDict']
    nodeOK = 0
    for key1 in feederTree:
        for key2 in feederTree[key1]:
            if feederTree[key1][key2] == battDict['battNode'] and key2=='name':
                if 'object' in feederTree[key1] and (feederTree[key1]['object'] == 'meter' or feederTree[key1]['object'] == 'node'): #Attaching to a normal meter
                    meterType = 'meter'
                    phases = str( feederTree[key1]['phases'])
                elif 'object' in feederTree[key1] and (feederTree[key1]['object'] == 'triplex_meter' or feederTree[key1]['object'] == 'triplex_node'):
                    meterType = 'triplex_meter'
                    phases = str(feederTree[key1]['phases'])
                targetKey = key1  #Need this to find the nominal voltage of the node where the meter is being added.
                nodeOK = 1
                #Find available key value
                maxKey = feeder.getMaxKey(feederTree)          
    if nodeOK == 0:            
        raise Exception('Battery not able to be added at node {}; node does not exist.'.format(battDict['battNode']))  
    else:      
        #Getting parameters needed to add components
        meterNominalV = feederTree[targetKey]['nominal_voltage']
        #Add new meter, inverter, and battery to feeder dictionary
        meterName = str(battDict['battNode'])+'_meter'
        feederTree[str(maxKey + 1)]={'phases': phases, 
                                     'name': meterName,
                                     'parent':str(battDict['battNode']),
                                     'object': meterType,
                                     'nominal_voltage':str(meterNominalV)}  
        invName = str(battDict['battNode'])+'_inv'
        feederTree[str(maxKey + 2)]={'name':invName,
                                'parent': meterName,
                                'object': 'inverter',
                                'inverter_type':'FOUR_QUADRANT',
                                'four_quadrant_control_mode': battDict['invControl'].upper(),
                                'generator_mode':'CONSTANT_PQ',
                                'generator_status':'ONLINE',
                                'sense_object': str(battDict['controlSenseNode']),
                                'charge_lockout_time': str(battDict['invChargeLockoutTime']),
                                'discharge_lockout_time':str(battDict['invDischargeLockoutTime']),
                                'rated_power':str(battDict['invPowerRatingkW']) + ' kW',
                                'inverter_efficiency':str(battDict['invEfficiency']),
                                'charge_on_threshold':str(battDict['invChargeOnThresholdkW']) + ' kW',
                                'charge_off_threshold': str(battDict['invChargeOffThresholdkW']) + ' kW',
                                'discharge_on_threshold':str(battDict['invDischargeOnThresholdkW']) + ' kW',
                                'discharge_off_threshold':str(battDict['invDischargeOffThresholdkW']) + ' kW',
                                'max_discharge_rate':str(battDict['invMaxChargeRatekW']) + ' kW',
                                'max_charge_rate':str(battDict['invMaxDischargeRatekW']) + ' kW'} 
        batteryName = str(battDict['battNode'])+'_battery'
        feederTree[str(maxKey + 3)]={'name': batteryName,
                                'parent': invName,
                                'object': 'battery',
                                'use_internal_battery_model':'true',
                                'battery_type': str(battDict['battType']),
                                'battery_capacity': str(battDict['battEnergyRatingkWh']) + ' kWh',
                                'base_efficiency': str(battDict['battEfficiency']),
                                'state_of_charge': str(battDict['battSOCpu']),
                                'generator_mode':'SUPPLY_DRIVEN'}
    return feederTree

def addBattery(battDict):
    #Validating input dictionary keys
    validKeys= ['feederDict',                   #REQUIRED
                'battNode',                     #REQUIRED     
                'battEnergyRatingkWh',          #REQUIRED
                'invControl',                   #REQUIRED
                'battEfficiency',               #optional
                'battType',                     #optional
                'battSOCpu',                    #optional   
                'invPowerRatingkW',             #REQUIRED
                'invChargeLockoutTime',         #optional
                'invDischargeLockoutTime',      #optional
                'invEfficiency',                #optional
                'invChargeOnThresholdkW',       #REQUIRED for LOAD_FOLLOWING control mode if and only if controlSenseAveragePowerkW not specified
                'invChargeOffThresholdkW',      #REQUIRED for LOAD_FOLLOWING control mode if and only if controlSenseAveragePowerkW not specified
                'invDischargeOffThresholdkW',   #REQUIRED for LOAD_FOLLOWING control mode if and only if controlSenseAveragePowerkW not specified
                'invDischargeOnThresholdkW',    #REQUIRED for LOAD_FOLLOWING control mode if and only if controlSenseAveragePowerkW not specified
                'invMaxDischargeRatekW',        #optional
                'invMaxChargeRatekW',           #optional
                'controlSenseNode',             #REQUIRED for LOAD_FOLLOWING
                'controlSenseAveragePowerkW',   #REQUIRED for LOAD_FOLLOWING control mode if and only if invCharge/DischargeOn/OffThresholdKW not specified
                'constantPOut',                 #REQUIRED for CONSTANT_PQ control mode      
                'constantQout']                 #REQUIRED for CONSTANT_PQ control mode 
    for key1 in battDict:
        if (key1 not in validKeys) and (key1 != 'feederDict'):
            raise KeyError ('{} found in input parameter dictionary and is not a valid parameter.'.format(key1))
    #Validating string parameter values
    if 'invControl' in battDict:
        isinstance(battDict['invControl'], basestring)
    else:
        raise Exception('Required parameter inverter control mode (\'invControl\') is undefined. ')
    if 'battType' in battDict:
        isinstance(battDict['battType'], basestring)
    else:
        battDict['battType'] = 'LI_ION'
        warnings.warn ('Battery type (\'battType\') is undefined, setting to \'LI_ION\'.')
    #Validating numeric parameter values
    if 'battEnergyRatingkWh' in battDict:
        if not (isinstance(battDict['battEnergyRatingkWh'], int) or isinstance(battDict['battEnergyRatingkWh'], float)) :
            raise TypeError('Parameter \'battEnergyRatingkWh\' is \'{}\', must be a numeric value.'.format(battDict['battEnergyRatingkWh']))
    else:
        raise Exception('Required parameter battery power rating (\'battEnergyRatingkWh\') undefined.')
    if 'battEfficiency' in battDict:
        if not (isinstance(battDict['battEfficiency'], int) or isinstance(battDict['battEfficiency'], float)) :
            raise TypeError('Parameter \'battEfficiency\' is \'{}\', must be a numeric value.'.format(battDict['battEfficiency']))
    else:
        battDict['battEfficiency'] = 0.85
        warnings.warn('Battery efficiency (\'battEfficiency\') undefined, setting to 0.85 (85%).')
    if 'battSOCpu' in battDict:
        if not (isinstance(battDict['battSOCpu'], int) or isinstance(battDict['battSOCpu'], float)) :
            raise TypeError('Parameter \'battSOCpu\' is \'{}\', must be a numeric value.'.format(battDict['battSOCpu']))
    else:
        battDict['battSOCpu'] = 1
        warnings.warn('Battery initial state-of-charge (\'battSOCpu\') undefined, setting to 1pu (full).')    
    if 'invPowerRatingkW' in battDict:
        if not (isinstance(battDict['invPowerRatingkW'], int) or isinstance(battDict['invPowerRatingkW'], float)) :
            raise TypeError('Parameter \'invPowerRatingkW\' is \'{}\', must be a numeric value.'.format(battDict['invPowerRatingkW']))
    else:
        raise Exception('Required parameter inverter power rating (\'invPowerRatingkW\') undefined.')
    if 'invChargeLockoutTime' in battDict:
        if not (isinstance(battDict['invChargeLockoutTime'], int) or isinstance(battDict['invChargeLockoutTime'], float)) :
            raise TypeError('Parameter \'invChargeLockoutTime\' is \'{}\', must be a numeric value.'.format(battDict['invChargeLockoutTime']))
    else:
        battDict['invChargeLockoutTime'] = 5
        warnings.warn('Inverter charge lockout time (\'invChargeLockoutTime\') undefined, setting to 5 seconds.')
    if 'invDischargeLockoutTime' in battDict:
        if not (isinstance(battDict['invDischargeLockoutTime'], int) or isinstance(battDict['invDischargeLockoutTime'], float)) :
            raise TypeError('Parameter \'invDischargeLockoutTime\' is \'{}\', must be a numeric type.'.format(battDict['invDischargeLockoutTime']))
    else:
        battDict['invDischargeLockoutTime'] = 5
        warnings.warn('Inverter discharge lockout time (\'invDischargeLockoutTime\') undefined, setting to 5 seconds.')
    if 'invEfficiency' in battDict:
        if not (isinstance(battDict['invEfficiency'], int) or isinstance(battDict['invEfficiency'], float)) :
            raise TypeError('Parameter \'invEfficiency\' is \'{}\', must be a numeric value.'.format(battDict['invEfficiency']))
    else:
        battDict['invEfficiency'] = 0.95
        warnings.warn('Inverter efficiency (\'invEfficiency\') undefined, setting to 0.95 (95%).' ) 
    if 'invMaxDischargeRatekW' in battDict:
        if not (isinstance(battDict['invMaxDischargeRatekW'], int) or isinstance(battDict['invMaxDischargeRatekW'], float)) :
            raise TypeError('Parameter \'invMaxDischargeRatekW\' is \'{}\', must be a numeric value.'.format(battDict['invMaxDischargeRatekW']))
    else:
        battDict['invMaxDischargeRatekW'] = battDict['invPowerRatingkW']
        warnings.warn('Inverter maximum discharge rate (\'invMaxDischargeRatekW\') undefined, setting to inverter power rating of {}kW.'.format(battDict['invPowerRatingkW']))   
    if 'invMaxChargeRatekW' in battDict:
        if not (isinstance(battDict['invMaxChargeRatekW'], int) or isinstance(battDict['invMaxChargeRatekW'], float)) :
            raise TypeError('Parameter \'invMaxChargeRatekW\' is \'{}\', must be a numeric value.'.format(battDict['invMaxChargeRatekW']))
    else:
        battDict['invMaxChargeRatekW'] = battDict['invPowerRatingkW']
        warnings.warn('Inverter maximum charge rate (\'invMaxChargeRatekW\') undefined, setting to inverter power rating of {}kW.'.format(battDict['invPowerRatingkW']))  
    if battDict['invControl'].upper() == 'CONSTANT_PQ':
        if 'constantPOut' in battDict:
            if not (isinstance(battDict['constantPOut'], int) or isinstance(battDict['constantPOut'], float)) :
                raise TypeError('Parameter \'constantPOut\' is \'{}\', must be a numeric value.'.format(battDict['constantPOut']))
        else:
            raise Exception('Required parameter constant real power out (\'constantPOut\') is undefined. ')
        if 'constantQOUT' in battDict:
            if not (isinstance(battDict['constantQOut'], int) or isinstance(battDict['constantQOut'], float)) :
                raise TypeError('Parameter \'constantQOut\' is \'{}\', must be a numeric value.'.format(battDict['constantQOut']))
        else:
            raise Exception('Required parameter constant reactive power out (\'constantQOut\') is undefined. ')
    elif battDict['invControl'].upper() == 'LOAD_FOLLOWING':
        if 'controlSenseAveragePowerkW' in battDict:
            if('invChargeOffThresholdkW' in battDict or 'invDischargeOffThresholdkW' in battDict or 
            'invChargeOnThresholdkW' in battDict or 'invDischargeOnThresholdkW' in battDict):
                raise Exception('Conflicting inverter settings detected. Only either \'controlSenseAveragePowerkW\' or the set of \'invChargeOffThresholdkW\', \'invChargeOnThresholdkW\', \'invDischargeOffThresholdkW\', \'invDischargeOnThresholdkW\' can be defined.')
            if not (isinstance(battDict['controlSenseAveragePowerkW'], int) or isinstance(battDict['controlSenseAveragePowerkW'], float)) :
                raise TypeError('Parameter \'controlSenseAveragePowerkW\' is \'{}\', must be a numeric type.'.format(battDict['controlSenseAveragePowerkW']))
            print 'Setting inverter hysteris to default levels based on value of \'invChargeOnThresholdkW\'.'
            battDict['invChargeOffThresholdkW'] = battDict['controlSenseAveragePowerkW'] * 0.95
            battDict['invDischargeOffThresholdkW'] = battDict['controlSenseAveragePowerkW'] * 1.05
            battDict['invChargeOnThresholdkW'] = battDict['controlSenseAveragePowerkW'] * 0.7
            battDict['invDischargeOnThresholdkW'] = battDict['controlSenseAveragePowerkW'] * 1.3
        elif('invChargeOffThresholdkW' in battDict and 'invDischargeOffThresholdkW' in battDict and 
            'invChargeOnThresholdkW' in battDict and 'invDischargeOnThresholdkW' in battDict):
            if 'controlSenseAveragePowerkW' in battDict:
                raise Exception('Conflicting inverter settings detected. Only either \'controlSenseAveragePowerkW\' or the set of \'invChargeOffThresholdkW\', \'invChargeOnThresholdkW\', \'invDischargeOffThresholdkW\', \'invDischargeOnThresholdkW\' can be defined.')
        else:
            raise Exception('Either \'controlSenseAveragePowerkW\' or the set of \'invChargeOffThresholdkW\', \'invChargeOnThresholdkW\', \'invDischargeOffThresholdkW\', \'invDischargeOnThresholdkW\' can and must be defined.') 
    else:
        raise ValueError('{} is an unsupported value for \'invControl\'. Valid values are \'CONSTAN_PQ\' or \'LOAD_FOLLOWING\'.'.format(battDict['invControl']))
    #Adding in generators module declaration
    maxKey = feeder.getMaxKey(battDict['feederDict'])
    battDict['feederDict'][str(maxKey + 1)]={'omftype': 'module', 
                                             'argument': 'generators'}
    battNodeList = battDict['battNode']
    for index in range(len(battNodeList)):
        battDict['battNode'] = battNodeList[index]
        battDict['feederDict'] = addSingleBattery(battDict)
    return battDict['feederDict']
        
def _tests():  
    #Import GLM and convert to dictionary when directly called from the command line. When used as a Python module, 
    # will be handed a dictionary containing the feeder model and the parameters for the battery being added.
    convOut = feeder.parse(sys.argv[1])
    nodeList = ['Node633']
    battDict = {'feederDict':convOut,
                'battNode': nodeList,
                'battEnergyRatingkWh':250,
                'invPowerRatingkW': 100,
                'battSOCpu': 0.5,
                'invControl':'LOAD_following',
                'controlSenseNode': 'Node633',
                'invChargeOnThresholdkW': 1500,
                'invChargeOffThresholdkW': 1700,
                'invDischargeOnThresholdkW': 1800,
                'invDischargeOffThresholdkW': 1750,
                }
    outTree = addBattery(battDict)
    if outTree == 0:
        print 'Failed to add battery. Continuing on...'
    GLM = feeder.sortedWrite(outTree)
    f = open('testFeeder.glm','w')
    f.write(GLM)

if __name__ == '__main__': #Only run if we are calling from the command line, commonly to test functionality
    _tests()