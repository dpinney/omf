''' Convert a Milsoft Windmil feeder model into an OMF-compatible version. '''

import feeder, csv, random, math, copy
from StringIO import StringIO

def convert(stdString,seqString):
    ''' Take in a .std and .seq strings from Milsoft and spit out a (json dict, int, int).'''
    def csvToArray(csvString):
        ''' Simple csv data ingester. '''
        csvReader = csv.reader(StringIO(csvString))
        outArray = []
        for row in csvReader:
            outArray += [row]
        return outArray
    # Get all components from the .std:
    components = csvToArray(stdString)[1:]
    # Get all hardware stats from the .seq:
    hardwareStats = csvToArray(seqString)[1:]
    # We dropped the first rows which are metadata (n.b. there are no headers)
    # Get nominal voltage:
    nominal_voltage = 14400
    for ob in components:
        if ob[1] == 9: nominal_voltage = str(float(ob[14])*1000)
    # The number of allowable sub objects:
    subObCount = 100
    # Helper for lat/lon conversion.
    def convertToPixel():
        x_list = []
        y_list = []
        x_pixel_range = 1200
        y_pixel_range = 800
        for component in components:
            x_list.append(float(component[5]))
            y_list.append(float(component[6]))
        # according to convert function  f(x) = a * x + b
        try:
            x_a = x_pixel_range / (max(x_list) - min(x_list))
            x_b = -x_a * min(x_list)
            y_a = y_pixel_range / (max(y_list) - min(y_list))
            y_b = -y_a * min(y_list)
        except:
            x_a,x_b,y_a,y_b = (0,0,0,0)
        return x_a, x_b, y_a, y_b
    [x_scale, x_b, y_scale, y_b] = convertToPixel()
    def obConvert(objectList):
        ''' take a row in the milsoft .std and turn it into a gridlab-type dict'''

        # -----------------------------------------------
        # Globals and helper functions:
        # -----------------------------------------------

        gridlabFields = {   1 : 'overhead_line',    # Overhead Line (Type 1)
                            2 : 'capacitor',        # Capacitor (Type 2)
                            3 : 'underground_line', # Underground Line (Type 3)
                            4 : 'regulator',        # Regulator (Type 4)
                            5 : 'transformer',      # Transformer (Type 5)
                            6 : 'switch',           # Switch (Type 6)
                            8 : 'node',             # Node (Type 8)
                            9 : 'node',             # Source (Type 9)
                            10 : 'fuse',            # Overcurrent Device (Type 10)
                            11 : 'ZIPload',         # Motor (Type 11)
                            12 : 'diesel_dg',       # Generator (Type 12)
                            13 : 'load' }           # Consumer (Type 13)

        allNames = [x[0] for x in components]

        def statsByName(deviceName):
            ''' Helper function to query the hardware csv. '''
            for row in hardwareStats:
                if row[0] == deviceName:
                    return row
            return None

        def safeGet(arr, pos, default):
            ''' Return item at pos in arr, or if it fails return default. '''
            try:
                return arr[pos]
            except:
                return default

        def convertGenericObject(objectList):
            ''' this converts attributes that are in every milsoft object regardless of hardware type '''
            newOb = {}
            # Need to replace invalid characters in names:
            newOb['name'] = objectList[0].replace('.','x')
            newOb['object'] = gridlabFields[int(objectList[1])]
            # Convert lat-lon if we have them.
            # convert to the relative pixel position f(x) = a * x + b
            newOb['latitude'] = str(x_scale * float(objectList[5]) + x_b)
            newOb['longitude'] = str(800 - (y_scale * float(objectList[6]) + y_b))
            # Some non-Gridlab elements:
            newOb['guid'] = objectList[49].replace('{','').replace('}','')
            newOb['parentGuid'] = objectList[50].replace('{','').replace('}','')
            # Make sure names are unique:
            if allNames.count(newOb['name']) > 1:
                newOb['name'] = newOb['guid']
            return newOb

        # -----------------------------------------------
        # Conversion functions for each type of hardware:
        # -----------------------------------------------
        def convertSwitch(switchList):
            switch = convertGenericObject(switchList)
            switch['status'] = ('OPEN' if switchList[9]=='O' else 'CLOSED')
            switch['phases'] = switchList[2]
            return switch

        def convertOvercurrentDevice(ocDeviceList):
            fuse = convertGenericObject(ocDeviceList)
            fuse['phases'] = ocDeviceList[2]
            fuse['current_limit'] = '9999.0 A'
            # TODO: Figure out why code below causes convergence errors for some feeders.
            # if 'OC' in fuse['name'] or 'FS' in fuse['name'] or 'NF14' in fuse['name']:
            #   ocNameInSEQ = ocDeviceList[7]
            #   if ocNameInSEQ == "": ocNameInSEQ = ocDeviceList[8]
            #   if ocNameInSEQ == "": ocNameInSEQ = ocDeviceList[9]
            #   if ocNameInSEQ == "": ocNameInSEQ = ocDeviceList[10]
            #   try: fuse['current_limit'] = statsByName(ocNameInSEQ)[3]+' A'
            #   except: fuse['current_limit'] = '9999.0 A'
            return fuse

        def convertGenerator(genList):
            generator = convertGenericObject(genList)
            generator['Gen_mode'] = 'CONSTANTPQ'
            generator['Gen_status'] = ('OFFLINE' if genList[26]=='1' else 'ONLINE')
            generator['phases'] = "ABCN"
            return generator

        def convertMotor(motorList):
            motor = convertGenericObject(motorList)
            motor['Gen_mode'] = 'CONSTANTPQ'
            # Convert horsepower to kW:
            motor['base_power'] = float(motorList[27])*0.73549875
            # These constants come from the fan load in simpleMarketSystem:
            motor['power_fraction'] = 0.013500
            motor['impedance_fraction'] = 0.733200
            motor['current_fraction'] = 0.253400
            motor['power_pf'] = -1.000000
            motor['current_pf'] = 0.950000
            motor['impedance_pf'] = 0.970000
            return motor

        def convertConsumer(consList):
            consumer = convertGenericObject(consList)
            consumer['phases'] = consList[2]


            loadClassMap = {    0 : 'R',
                                1 : 'C',
                                2 : 'C',
                                3 : 'U',
                                4 : 'U',
                                5 : 'A',
                                6 : 'I',
                                7 : 'U',
                                8 : 'U',
                                9 : 'U',
                                10: 'U'
                            }
            consumer['load_class'] = loadClassMap[int(consList[23])]
            # Determine the commercial load connection wye or delta
            if consumer['load_class'] == 'C':
                load_mix = statsByName(consList[8])
                if load_mix is None:
                    pass
                elif load_mix[5] == 'W':#Wye-Wye connected load
                    phases = consumer['phases'] + 'N'
                    consumer['phases'] = phases
                elif load_mix[5] == 'D':#Delta connected load
                    phases = consumer['phases'] + ('D' if len(consList[2]) >= 2 else '')
                    consumer['phases'] = phases

            #MAYBEFIX: support kVars.
            consumer['constant_power_A'] = str(float(consList[12])*1000) + ('+' if float(consList[15]) >= 0.0 else '-') + str(abs(float(consList[15])*1000)) + 'j'
            consumer['constant_power_B'] = str(float(consList[13])*1000) + ('+' if float(consList[16]) >= 0.0 else '-') + str(abs(float(consList[16])*1000)) + 'j'
            consumer['constant_power_C'] = str(float(consList[14])*1000) + ('+' if float(consList[17]) >= 0.0 else '-') + str(abs(float(consList[17])*1000)) + 'j'
            consumer['nominal_voltage'] = '120'
            return consumer

        def convertNode(nodeList):
            node = convertGenericObject(nodeList)
            #Find the connect type
            load_mix = statsByName(nodeList[8])
            if load_mix is None or load_mix[5] == 'W':#Wye connected
                node['phases'] = nodeList[2] + 'N'
            elif load_mix[5] == 'D':#Delta connected
                node['phases'] = nodeList[2] + ('D' if len(nodeList[2]) >= 2 else '')
            else:
                node['phases'] = nodeList[2] + 'N'

            #MAYBEFIX: can we get nominal voltage from the windmil file?
            node['nominal_voltage'] = nominal_voltage

            if nodeList[15] != '0' or nodeList[16] != '0' or nodeList[17] != '0' or nodeList[18] != '0' or nodeList[19] != '0' or nodeList[20] != '0': # this node is actually a load
                node['object'] = 'load'
                node['constant_power_A'] = str(float(nodeList[15])*1000) + ('+' if float(nodeList[18]) >= 0.0 else '-') + str(abs(float(nodeList[18])*1000)) + 'j'
                node['constant_power_B'] = str(float(nodeList[16])*1000) + ('+' if float(nodeList[19]) >= 0.0 else '-') + str(abs(float(nodeList[19])*1000)) + 'j'
                node['constant_power_C'] = str(float(nodeList[17])*1000) + ('+' if float(nodeList[20]) >= 0.0 else '-') + str(abs(float(nodeList[20])*1000)) + 'j'

                node['load_class'] = 'C' #setting all nodes with loads on them as commercial loads as we can't know the load classification. If they want the load to be residential then they need to classify the node as a consumer object in the windmil model.
            return node

        def convertSource(sourceList):
            source = convertGenericObject(sourceList)
            #Find the connect type
            if sourceList[16] == 'W':#Wye connected
                source['phases'] = sourceList[2] + 'N'
            else:#Delta connected
                source['phases'] = sourceList[2] + ('D' if len(sourceList[2]) >= 2 else '')
            source['nominal_voltage'] = str(float(sourceList[14])*1000)
            source['bustype'] = 'SWING'
            return source

        def convertCapacitor(capList):
            capacitor = convertGenericObject(capList)
            if  capList[17] == '1': #Delta connected
                capacitor['phases'] = capList[2] + ('D' if len(capList[2]) >= 2 else '')
            else:
                capacitor['phases'] = capList[2] + 'N'
            #MAYBEFIX: change these from just default values:
            if capList[19] in capacitor['phases']:
                capacitor['pt_phase'] = capList[19]
            capacitor['phases_connected'] = capacitor['phases']
            if capList[12] == '0':
                capacitor['control'] = 'MANUAL'
            elif capList[12] == '1':
                capacitor['control'] = 'VOLT'
                capacitor['voltage_set_high'] = capList[15]
                capacitor['voltage_set_low'] = capList[14]
                capacitor['time_delay'] = '300.0'
                capacitor['dwell_time'] = '0.0'
            else:
                capacitor['control'] = 'MANUAL'
            #MAYBEFIX: Handle the other control types in WindMil Properly
            if 'A' in capacitor['phases']:
                capacitor['capacitor_A'] = str(float(capList[8])*1000)
                if capList[13] == '1':
                    capacitor['switchA'] = 'CLOSED'
                else:
                    capacitor['switchA'] = 'OPEN'
            if 'B' in capacitor['phases']:
                capacitor['capacitor_B'] = str(float(capList[9])*1000)
                if capList[13] == '1':
                    capacitor['switchB'] = 'CLOSED'
                else:
                    capacitor['switchB'] = 'OPEN'
            if 'C' in capacitor['phases']:
                capacitor['capacitor_C'] = str(float(capList[10])*1000)
                if capList[13] == '1':
                    capacitor['switchC'] = 'CLOSED'
                else:
                    capacitor['switchC'] = 'OPEN'
            if len(capacitor['phases']) > 1:
                capacitor['control_level'] = 'BANK'
            else:
                capacitor['control_level'] = 'INDIVIDUAL'
            capacitor['nominal_voltage'] = nominal_voltage
            return capacitor

        def convertOhLine(ohLineList):
            myIndex = components.index(objectList)*subObCount
            overhead = convertGenericObject(ohLineList)
            # MAYBEFIX: be smarter about multiple neutrals.
            load_mix = statsByName(ohLineList[14])
            if load_mix is None or load_mix[5] == 'W':#Wye connected line
                overhead['phases'] = ohLineList[2] + ('N' if ohLineList[33]=='1' else '')
            else: #Delta connected line
                # Delta connections are breaking things.
                # overhead['phases'] = ohLineList[2] + ('D' if len(ohLineList[2]) >= 2 else '')
                overhead['phases'] = ohLineList[2]

            overhead['length'] = ('10' if float(ohLineList[12])<10 else ohLineList[12])
            overhead[myIndex+1] = { 'omfEmbeddedConfigObject':'configuration object line_configuration',
                            'name': overhead['name'] + '-LINECONFIG'}
            overhead[myIndex+1][myIndex+2] = {  'omfEmbeddedConfigObject' : 'spacing object line_spacing',
                                'name': overhead['name'] + '-LINESPACING'}
            #Grab line spacing distances
            # Find name of construction code
            if ohLineList[13] == 'NONE':
                construction_description = 'SystemCnstDefault'
            else:
                construction_description = ohLineList[13]
            # Find the construction code in hardwareStats
            construction_stats = statsByName(construction_description)
            if construction_stats is None:
                #Couldn't find construction object. Using defalut phase distances. Distances are from IEEE 4 Node
                Dab = 2.5
                Dac = 7.0
                Dan = 5.656854
                Dbc = 4.5
                Dbn = 4.272002
                Dcn = 5.0
            else:
                # Find the distances in feet between each conductor
                Dab = math.sqrt(((float(construction_stats[19]) - float(construction_stats[20]))*(float(construction_stats[19]) - float(construction_stats[20]))) + ((float(construction_stats[23]) - float(construction_stats[24]))*(float(construction_stats[23]) - float(construction_stats[24]))))/12
                Dac = math.sqrt(((float(construction_stats[19]) - float(construction_stats[21]))*(float(construction_stats[19]) - float(construction_stats[21]))) + ((float(construction_stats[23]) - float(construction_stats[25]))*(float(construction_stats[23]) - float(construction_stats[25]))))/12
                Dan = math.sqrt(((float(construction_stats[19]) - float(construction_stats[22]))*(float(construction_stats[19]) - float(construction_stats[22]))) + ((float(construction_stats[23]) - float(construction_stats[26]))*(float(construction_stats[23]) - float(construction_stats[26]))))/12
                Dbc = math.sqrt(((float(construction_stats[20]) - float(construction_stats[21]))*(float(construction_stats[20]) - float(construction_stats[21]))) + ((float(construction_stats[24]) - float(construction_stats[25]))*(float(construction_stats[24]) - float(construction_stats[25]))))/12
                Dbn = math.sqrt(((float(construction_stats[20]) - float(construction_stats[22]))*(float(construction_stats[20]) - float(construction_stats[22]))) + ((float(construction_stats[24]) - float(construction_stats[26]))*(float(construction_stats[24]) - float(construction_stats[26]))))/12
                Dcn = math.sqrt(((float(construction_stats[21]) - float(construction_stats[22]))*(float(construction_stats[21]) - float(construction_stats[22]))) + ((float(construction_stats[25]) - float(construction_stats[26]))*(float(construction_stats[25]) - float(construction_stats[26]))))/12
            # Add distances to dictionary when appropriate
            if 'A' in overhead['phases'] and 'B' in overhead['phases']:
                if Dab > 0:
                    overhead[myIndex+1][myIndex+2]['distance_AB'] = '{:0.6f}'.format(Dab)
                else:
                    overhead[myIndex+1][myIndex+2]['distance_AB'] = '{:0.6f}'.format(2.5)
            else:
                overhead[myIndex+1][myIndex+2]['distance_AB'] = '{:0.6f}'.format(0.0)
            if 'A' in overhead['phases'] and 'C' in overhead['phases']:
                if Dac > 0:
                    overhead[myIndex+1][myIndex+2]['distance_AC'] = '{:0.6f}'.format(Dac)
                else:
                    overhead[myIndex+1][myIndex+2]['distance_AC'] = '{:0.6f}'.format(7.0)
            else:
                overhead[myIndex+1][myIndex+2]['distance_AC'] = '{:0.6f}'.format(0.0)
            if 'A' in overhead['phases'] and 'N' in overhead['phases']:
                if Dan > 0:
                    overhead[myIndex+1][myIndex+2]['distance_AN'] = '{:0.6f}'.format(Dan)
                else:
                    overhead[myIndex+1][myIndex+2]['distance_AN'] = '{:0.6f}'.format(5.656854)
            else:
                overhead[myIndex+1][myIndex+2]['distance_AN'] = '{:0.6f}'.format(0.0)
            if 'B' in overhead['phases'] and 'C' in overhead['phases']:
                if Dbc > 0:
                    overhead[myIndex+1][myIndex+2]['distance_BC'] = '{:0.6f}'.format(Dbc)
                else:
                    overhead[myIndex+1][myIndex+2]['distance_BC'] = '{:0.6f}'.format(4.5)
            else:
                overhead[myIndex+1][myIndex+2]['distance_BC'] = '{:0.6f}'.format(0.0)
            if 'B' in overhead['phases'] and 'N' in overhead['phases']:
                if Dbn > 0:
                    overhead[myIndex+1][myIndex+2]['distance_BN'] = '{:0.6f}'.format(Dbn)
                else:
                    overhead[myIndex+1][myIndex+2]['distance_BN'] = '{:0.6f}'.format(4.272002)
            else:
                overhead[myIndex+1][myIndex+2]['distance_BN'] = '{:0.6f}'.format(0.0)
            if 'C' in overhead['phases'] and 'N' in overhead['phases']:
                if Dcn > 0:
                    overhead[myIndex+1][myIndex+2]['distance_CN'] = '{:0.6f}'.format(Dcn)
                else:
                    overhead[myIndex+1][myIndex+2]['distance_CN'] = '{:0.6f}'.format(5.0)
            else:
                overhead[myIndex+1][myIndex+2]['distance_CN'] = '{:0.6f}'.format(0.0)
            eqdbIndex = {'A':8,'B':9,'C':10,'N':11}
            condIndex = {'A':3,'B':4,'C':5,'N':6}
            for letter in overhead['phases']:
                lineIndex = eqdbIndex[letter]
                hardware = statsByName(ohLineList[lineIndex])
                if hardware is None:
                    res = '0.306'
                    geoRad = '0.0244'
                    diameter = '0.721'
                else:
                    res = hardware[5]
                    if res == '0':
                        res = '0.306'
                    geoRad = hardware[6]
                    if geoRad == '0':
                        geoRad = '0.0244'
                    diameter = hardware[8]
                    if diameter == '0':
                        diameter = '0.721'
                overhead[myIndex+1][myIndex+condIndex[letter]] = {  'omfEmbeddedConfigObject':'conductor_' + letter + ' object overhead_line_conductor',
                                                            'name': overhead['name'] + '_conductor_' + letter,
                                                            'resistance': res,
                                                            'geometric_mean_radius': geoRad,
                                                            'diameter' : diameter}
            # Check to see if there is distributed load on the line
            if 'A' in overhead['phases'] and (ohLineList[19] != '0' or ohLineList[22] != '0'):
                overhead['distributed_load_A'] = float(ohLineList[19])*1000 + float(ohLineList[22])*1000j
            if 'B' in overhead['phases'] and (ohLineList[20] != '0' or ohLineList[23] != '0'):
                overhead['distributed_load_B'] = float(ohLineList[20])*1000 + float(ohLineList[23])*1000j
            if 'C' in overhead['phases'] and (ohLineList[21] != '0' or ohLineList[24] != '0'):
                overhead['distributed_load_C'] = float(ohLineList[21])*1000 + float(ohLineList[24])*1000j
            return overhead

        def convertUgLine(ugLineList):
            myIndex = components.index(objectList)*subObCount
            underground = convertGenericObject(ugLineList)
            # MAYBEFIX: be smarter about multiple neutrals.
            load_mix = statsByName(ugLineList[14])
            if load_mix is None or load_mix[5] == 'W':#Wye connected line
                underground['phases'] = ugLineList[2] + ('N' if ugLineList[33]=='1' else '')
            else: #Delta connected line
                # Delta loads are breaking things.
                # underground['phases'] = ugLineList[2] + ('D' if len(ugLineList[2]) >= 2 else '')
                underground['phases'] = ugLineList[2]
            underground['length'] = ('10' if float(ugLineList[12])<10 else ugLineList[12])
            underground[myIndex+1] = {  'omfEmbeddedConfigObject':'configuration object line_configuration',
                                'name': underground['name'] + '-LINECONFIG'}
            underground[myIndex+1][myIndex+2] = {   'omfEmbeddedConfigObject' : 'spacing object line_spacing',
                                    'name':underground['name'] + '-LINESPACING'}
            #Grab line spacing distances
            # Find name of construction code
            if ugLineList[13] == 'NONE':
                construction_description = 'SystemCnstDefault'
            else:
                construction_description = ugLineList[13]
            # Find the construction code in hardwareStats
            construction_stats = statsByName(construction_description)
            if construction_stats is None:
                #Couldn't find construction object. Using defalut phase distances. Distances are from IEEE 4 Node
                Dab = 2.5
                Dac = 7.0
                Dan = 5.656854
                Dbc = 4.5
                Dbn = 4.272002
                Dcn = 5.0
            else:
                # Find the distances in feet between each conductor
                Dab = math.sqrt(((float(construction_stats[19]) - float(construction_stats[20]))*(float(construction_stats[19]) - float(construction_stats[20]))) + ((float(construction_stats[23]) - float(construction_stats[24]))*(float(construction_stats[23]) - float(construction_stats[24]))))/12
                Dac = math.sqrt(((float(construction_stats[19]) - float(construction_stats[21]))*(float(construction_stats[19]) - float(construction_stats[21]))) + ((float(construction_stats[23]) - float(construction_stats[25]))*(float(construction_stats[23]) - float(construction_stats[25]))))/12
                Dan = math.sqrt(((float(construction_stats[19]) - float(construction_stats[22]))*(float(construction_stats[19]) - float(construction_stats[22]))) + ((float(construction_stats[23]) - float(construction_stats[26]))*(float(construction_stats[23]) - float(construction_stats[26]))))/12
                Dbc = math.sqrt(((float(construction_stats[20]) - float(construction_stats[21]))*(float(construction_stats[20]) - float(construction_stats[21]))) + ((float(construction_stats[24]) - float(construction_stats[25]))*(float(construction_stats[24]) - float(construction_stats[25]))))/12
                Dbn = math.sqrt(((float(construction_stats[20]) - float(construction_stats[22]))*(float(construction_stats[20]) - float(construction_stats[22]))) + ((float(construction_stats[24]) - float(construction_stats[26]))*(float(construction_stats[24]) - float(construction_stats[26]))))/12
                Dcn = math.sqrt(((float(construction_stats[21]) - float(construction_stats[22]))*(float(construction_stats[21]) - float(construction_stats[22]))) + ((float(construction_stats[25]) - float(construction_stats[26]))*(float(construction_stats[25]) - float(construction_stats[26]))))/12
            # Add distances to dictionary when appropriate
            if 'A' in underground['phases'] and 'B' in underground['phases']:
                underground[myIndex+1][myIndex+2]['distance_AB'] = '{:0.6f}'.format(Dab)
            else:
                underground[myIndex+1][myIndex+2]['distance_AB'] = '{:0.1f}'.format(0.0)
            if 'A' in underground['phases'] and 'C' in underground['phases']:
                underground[myIndex+1][myIndex+2]['distance_AC'] = '{:0.6f}'.format(Dac)
            else:
                underground[myIndex+1][myIndex+2]['distance_AC'] = '{:0.1f}'.format(0.0)
            if 'A' in underground['phases'] and 'N' in underground['phases']:
                underground[myIndex+1][myIndex+2]['distance_AN'] = '{:0.6f}'.format(Dan)
            else:
                underground[myIndex+1][myIndex+2]['distance_AN'] = '{:0.1f}'.format(0.0)
            if 'B' in underground['phases'] and 'C' in underground['phases']:
                underground[myIndex+1][myIndex+2]['distance_BC'] = '{:0.6f}'.format(Dbc)
            else:
                underground[myIndex+1][myIndex+2]['distance_BC'] = '{:0.1f}'.format(0.0)
            if 'B' in underground['phases'] and 'N' in underground['phases']:
                underground[myIndex+1][myIndex+2]['distance_BN'] = '{:0.6f}'.format(Dbn)
            else:
                underground[myIndex+1][myIndex+2]['distance_BN'] = '{:0.1f}'.format(0.0)
            if 'C' in underground['phases'] and 'N' in underground['phases']:
                underground[myIndex+1][myIndex+2]['distance_CN'] = '{:0.6f}'.format(Dcn)
            else:
                underground[myIndex+1][myIndex+2]['distance_CN'] = '{:0.1f}'.format(0.0)
            #MAYBEFIX: actually get conductor values!
            eqdbIndex = {'A':8,'B':9,'C':10,'N':11}
            condIndex = {'A':3,'B':4,'C':5,'N':6}
            for letter in underground['phases']:
                lineIndex = eqdbIndex[letter]
                hardware = statsByName(ugLineList[lineIndex])
                if hardware is None:
                    # Concentric Neutral 15 kV 2000 circular mil stranded AA
                    conductor_resistance = '1.541000'
                    conductor_diameter = 0.292
                    conductor_gmr = '0.008830'
                    neutral_resistance = '14.872200'
                    neutral_diameter = 0.0641
                    neutral_gmr = '0.002080'
                    neutral_strands = '6'
                    outer_diameter = 0.98
                    insulation_relative_permitivity = '1'
                    underground[myIndex+1][myIndex+condIndex[letter]] = {   'omfEmbeddedConfigObject':'conductor_' + letter + ' object underground_line_conductor',
                                                                            'conductor_resistance' : conductor_resistance,
                                                                            'shield_resistance' : '0.000000',
                                                                            'neutral_gmr' : neutral_gmr,
                                                                            'outer_diameter' : '{:0.6f}'.format(outer_diameter),
                                                                            'neutral_strands' : neutral_strands,
                                                                            'neutral_resistance' : neutral_resistance,
                                                                            'neutral_diameter' : '{:0.6f}'.format(neutral_diameter),
                                                                            'conductor_diameter' : '{:0.6f}'.format(conductor_diameter),
                                                                            'shield_gmr' : '0.000000',
                                                                            'conductor_gmr' : conductor_gmr,
                                                                            'insulation_relative_permitivitty' : insulation_relative_permitivity}
                elif float(hardware[1]) == 2.0:
                    conductor_resistance = hardware[4]
                    if conductor_resistance == '0':
                        conductor_resistance = '1.541000'
                    conductor_diameter = float(hardware[17])*12
                    if conductor_diameter == 0.0:
                        conductor_diameter = 0.292
                    conductor_gmr = hardware[5]
                    if conductor_gmr == '0':
                        conductor_gmr = '0.008830'
                    neutral_resistance = hardware[6]
                    if neutral_resistance == '0':
                        neutral_resistance = '14.087220'
                    neutral_diameter = (float(hardware[9]) - float(hardware[12]))*12
                    if neutral_diameter == 0.0:
                        neutral_diameter = 0.0641
                    neutral_gmr = hardware[16]
                    if neutral_gmr == '0':
                        neutral_gmr = '0.002080'
                    neutral_strands = hardware[7]
                    if neutral_strands == '0':
                        neutral_strands = '6'
                    outer_diameter = float(hardware[9])*12
                    if outer_diameter == 0.0:
                        outer_diameter = 0.98
                    insulation_relative_permitivity = hardware[11]
                    if insulation_relative_permitivity == '0':
                        insulation_relative_permitivity = '1'
                    underground[myIndex+1][myIndex+condIndex[letter]] = {   'omfEmbeddedConfigObject':'conductor_' + letter + ' object underground_line_conductor',
                                                                            'conductor_resistance' : conductor_resistance,
                                                                            'shield_resistance' : '0.000000',
                                                                            'neutral_gmr' : neutral_gmr,
                                                                            'outer_diameter' : '{:0.6f}'.format(outer_diameter),
                                                                            'neutral_strands' : neutral_strands,
                                                                            'neutral_resistance' : neutral_resistance,
                                                                            'neutral_diameter' : '{:0.6f}'.format(neutral_diameter),
                                                                            'conductor_diameter' : '{:0.6f}'.format(conductor_diameter),
                                                                            'shield_gmr' : '0.000000',
                                                                            'conductor_gmr' : conductor_gmr,
                                                                            'insulation_relative_permitivitty' : insulation_relative_permitivity}
            # Check to see if there is distributed load on the line
            if 'A' in underground['phases'] and (ugLineList[19] != '0' or ugLineList[22] != '0'):
                underground['distributed_load_A'] = float(ugLineList[19])*1000 + ('+' if float(ugLineList[22]) >= 0.0 else '-') + abs(float(ugLineList[22]))*1000j
            if 'B' in underground['phases'] and (ugLineList[20] != '0' or ugLineList[23] != '0'):
                underground['distributed_load_B'] = float(ugLineList[20])*1000 + ('+' if float(ugLineList[23]) >= 0.0 else '-') + abs(float(ugLineList[23]))*1000j
            if 'C' in underground['phases'] and (ugLineList[21] != '0' or ugLineList[24] != '0'):
                underground['distributed_load_C'] = float(ugLineList[21])*1000 + ('+' if float(ugLineList[24]) >= 0.0 else '-') + abs(float(ugLineList[24]))*1000j
            return underground

        def convertRegulator(regList):
            myIndex = components.index(objectList)*subObCount
            regulator = convertGenericObject(regList)
            regulator['phases'] = regList[2]
            # Grab regulator configuration parameters
            reg_hardware = statsByName(regList[11])
            if reg_hardware is not None:
                band_width = str(float(reg_hardware[7])*120)
                if float(reg_hardware[6]) > 0.0:
                    raise_taps = str(math.ceil(float(reg_hardware[4])/float(reg_hardware[6])))
                    lower_taps = str(math.ceil(float(reg_hardware[5])/float(reg_hardware[6])))
                else:
                    raise_taps = '16'
                    lower_taps = '16'
                if float(raise_taps) == 0.0 and float(reg_hardware[4]) > 0.0:
                    raise_taps = '16'
                if float(lower_taps) == 0.0 and float(reg_hardware[5]) > 0.0:
                    lower_taps = '16'

                if float(reg_hardware[4]) > 0.0:
                    regulation = reg_hardware[4]
                elif float(reg_hardware[5]) > 0.0:
                    regulation = reg_hardware[5]
                else:
                    regulation = '0.1'
                if float(reg_hardware[3]) > 0.0:
                    ctr = reg_hardware[3]
                else:
                    ctr = '700'
            else:
                ctr = '700'
                band_width = '2'
                raise_taps = '16'
                lower_taps = '16'
                regulation = '0.1'
            if regList[9] == '0': # Each phase is controlled independently
                band_center = str(float(regList[14])*120)
                control_level = 'INDIVIDUAL'
            if regList[9] == '1': # Bank with A as control phase
                band_center = str(float(regList[14])*120)
                control_level = 'BANK'
                CT_Phase = 'A'
                PT_Phase = 'A'
            if regList[9] == '2': # Bank with B as control phase
                band_center = str(float(regList[15])*120)
                control_level = 'BANK'
                CT_Phase = 'B'
                PT_Phase = 'B'
            if regList[9] == '3': # Bank with C as control phase
                band_center = str(float(regList[16])*120)
                control_level = 'BANK'
                CT_Phase = 'C'
                PT_Phase = 'C'
            if float(band_center) == 0.0:
                band_center = '122'
            ldc_r_A = regList[17]
            ldc_r_B = regList[18]
            ldc_r_C = regList[19]
            ldc_x_A = regList[20]
            ldc_x_B = regList[21]
            ldc_x_C = regList[22]
            if float(ldc_r_A) > 0.0 or float(ldc_r_B) > 0.0 or float(ldc_r_C) > 0.0 or float(ldc_x_A) > 0.0 or float(ldc_x_B) > 0.0 or float(ldc_x_C) > 0.0:
                control = 'LINE_DROP_COMP'
            else:
                control = 'OUTPUT_VOLTAGE'
            #MAYBEFIX: figure out whether I'll run into trouble if the following integer isn't unique:
            regulator[myIndex+1] = {}
            regulator[myIndex+1]['name'] = regulator['name'] + '-CONFIG'
            regulator[myIndex+1]['omfEmbeddedConfigObject'] = 'configuration object regulator_configuration'
            #MAYBEFIX: change these from just default values:
            regulator[myIndex+1]['connect_type'] = 'WYE_WYE'
            regulator[myIndex+1]['band_center'] = band_center
            regulator[myIndex+1]['band_width'] = band_width
            regulator[myIndex+1]['time_delay'] = '30.0'
            regulator[myIndex+1]['raise_taps'] = raise_taps
            regulator[myIndex+1]['lower_taps'] = lower_taps
            regulator[myIndex+1]['CT_phase'] = regulator['phases']
            regulator[myIndex+1]['PT_phase'] = regulator['phases']
            regulator[myIndex+1]['regulation'] = regulation
            if ctr is not None:
                regulator[myIndex+1]['current_transducer_ratio'] = ctr
            if float(ldc_r_A) != 0.0 and 'A' in regulator['phases']:
                regulator[myIndex+1]['compensator_r_setting_A'] = str(float(ldc_r_A)*120)
            if float(ldc_x_A) != 0.0 and 'A' in regulator['phases']:
                regulator[myIndex+1]['compensator_x_setting_A'] = str(float(ldc_x_A)*120)
            if float(ldc_r_B) != 0.0 and 'B' in regulator['phases']:
                regulator[myIndex+1]['compensator_r_setting_B'] = str(float(ldc_r_B)*120)
            if float(ldc_x_B) != 0.0 and 'B' in regulator['phases']:
                regulator[myIndex+1]['compensator_x_setting_B'] = str(float(ldc_x_B)*120)
            if float(ldc_r_C) != 0.0 and 'C' in regulator['phases']:
                regulator[myIndex+1]['compensator_r_setting_C'] = str(float(ldc_r_C)*120)
            if float(ldc_x_C) != 0.0 and 'C' in regulator['phases']:
                regulator[myIndex+1]['compensator_x_setting_C'] = str(float(ldc_x_C)*120)
            regulator[myIndex+1]['Control'] = control
            regulator[myIndex+1]['control_level'] = control_level
            regulator[myIndex+1]['Type'] = 'A'
            if 'A' in regulator['phases']:
                regulator[myIndex+1]['tap_pos_A'] = '1'
            if 'B' in regulator['phases']:
                regulator[myIndex+1]['tap_pos_B'] = '1'
            if 'C' in regulator['phases']:
                regulator[myIndex+1]['tap_pos_C'] = '1'
            return regulator

        def convertTransformer(transList):
            myIndex = components.index(objectList)*subObCount
            transformer = convertGenericObject(transList)
            transformer['phases'] = transList[2]
            # transformer['nominal_voltage'] = '2400'
            transformer[myIndex+1] = {}
            transformer[myIndex+1]['name'] = transformer['name'] + '-CONFIG'
            transformer[myIndex+1]['omfEmbeddedConfigObject'] = 'configuration object transformer_configuration'
            transformer[myIndex+1]['primary_voltage'] = str(float(transList[10])*1000)
            transformer[myIndex+1]['secondary_voltage'] = str(float(transList[13])*1000)
            # Grab transformer phase hardware. NOTE: the default values were averages from the test files.
            if 'A' in transformer['phases']:
                trans_config = statsByName(transList[24])
                no_load_loss = safeGet(trans_config, 20, 0)
                percent_z = safeGet(trans_config, 4, 3)
                x_r_ratio = safeGet(trans_config, 7, 5)
            elif 'B' in transformer['phases']:
                trans_config = statsByName(transList[25])
                no_load_loss = safeGet(trans_config, 21, 0)
                percent_z = safeGet(trans_config, 5, 3)
                x_r_ratio = safeGet(trans_config, 8, 5)
            else:
                trans_config = statsByName(transList[26])
                no_load_loss = safeGet(trans_config, 22, 0)
                percent_z = safeGet(trans_config, 6, 3)
                x_r_ratio = safeGet(trans_config, 9, 5)
            # Set the shunt impedance
            if float(no_load_loss) > 0.0:
                r_shunt = float(transList[10])*float(transList[10])*1000/float(no_load_loss)
                x_shunt = r_shunt*float(x_r_ratio)
                transformer[myIndex+1]['shunt_impedance'] = str(r_shunt) + '+' + str(x_shunt) + 'j'
            # Set series impedance
            if float(percent_z) > 0.0:
                r_series = float(percent_z)*0.01/math.sqrt(1+(float(x_r_ratio)*float(x_r_ratio)))
                x_series = r_series*float(x_r_ratio)
                transformer[myIndex+1]['impedance'] = str(r_series) + '+' + str(x_series) + 'j'
            else:
                transformer[myIndex+1]['impedance'] = '0.00033+0.0022j'
            # Override zero values for reactance and resistances.
            impedance = transformer[myIndex+1]['impedance']
            impReal = impedance.split('+')[0]
            impImag = impedance.split('+')[1]
            if float(impReal) == 0:
                impReal = '0.05'
                impedance = impReal+"+"+impImag
            if float(impImag.strip('j')) == 0:
                print "Reactance for a transformer is 0:"
                impImag = '0.02j'
                impedance = impReal+"+"+impImag
                print "Hacked it to:", str(impedance)
            transformer[myIndex+1]['impedance'] = impedance
            # NOTE: Windmil doesn't export any information on install type, but Gridlab only puts it in there for info reasons.
            # transformer[1]['install_type'] = 'POLETOP'
            transPhases = transList[2]
            if 1 == len(transPhases):
                transformer[myIndex+1]['connect_type'] = 'SINGLE_PHASE_CENTER_TAPPED'
            else:
                #MAYBEFIX: support other types of windings (D-D, D-Y, etc.)
                transformer[myIndex+1]['connect_type'] = 'WYE_WYE'
            #MAYBEFIX: change these from just default values:
            transformer[myIndex+1]['power_rating'] = str(float(transList[19]) + float(transList[20]) + float(transList[21]))
            if float(transList[19]) > 0:
                transformer[myIndex+1]['powerA_rating'] = transList[19]

            if float(transList[20]) > 0:
                transformer[myIndex+1]['powerB_rating'] = transList[20]

            if float(transList[21]) > 0:
                transformer[myIndex+1]['powerC_rating'] = transList[21]
            #MAYBEFIX: and change these, which were added to make the transformer work on multiple phases:
            return transformer
        # Simple lookup table for which function we need to apply:
        objectToFun =    {  1 : convertOhLine,
                            2 : convertCapacitor,
                            3 : convertUgLine,
                            4 : convertRegulator,
                            5 : convertTransformer,
                            6 : convertSwitch,
                            8 : convertNode,
                            9 : convertSource,
                            10 : convertOvercurrentDevice,
                            11 : convertMotor,
                            12 : convertGenerator,
                            13 : convertConsumer }
        # Apply fun:
        return objectToFun[int(objectList[1])](objectList)

    # If we got numbered phases, convert them to letters.
    for ob in components:
        phaseNumToLetter = {'1':'A','2':'B','3':'C','4':'AB','5':'AC','6':'BC','7':'ABC'}
        # replace numbers, leave letters alone.
        ob[2] = phaseNumToLetter.get(ob[2],ob[2])

    # Convert to a list of dicts:
    convertedComponents = [obConvert(x) for x in components]

    def fixCompConnectivity(comp):
        ''' Rejigger the connectivity attributes to work with Gridlab '''
        # Different object connectivity classes:
        fromToable = ['overhead_line','underground_line','regulator','transformer','switch','fuse']
        nodable = ['node']
        parentable = ['capacitor','ZIPload','diesel_dg','load']

        def getByGuid(guid):
            candidates = [x for x in convertedComponents if 'guid' in x.keys() and x['guid'] == guid]
            if len(candidates) == 0:
                return {}
            else:
                return candidates[0]

        def getByName(name):
            candidates = [x for x in convertedComponents if 'name' in x.keys() and x['name'] == name]
            if len(candidates) == 0:
                return {}
            else:
                return candidates[0]

        def parentType(ob):
            thing = getByGuid(ob['guid'])
            parent = getByGuid(thing['parentGuid'])
            if 'object' in parent.keys():
                return parent['object']
            else:
                pass # print parent

        def phaseMerge(*arg):
            concated = ''.join(arg)
            return ''.join(sorted(set(concated)))

        # If we already stripped the GUID, don't process:
        if 'guid' not in comp.keys():
            return False

        # Hang on to the component's parent:
        parent = getByGuid(comp['parentGuid'])

        # Rejigger the attributes:
        if comp['object'] in parentable and parentType(comp) in nodable:
            comp['parent'] = parent['name']
        elif comp['object'] in fromToable and parentType(comp) in nodable:
            comp['from'] = parent['name']
        elif comp['object'] in parentable and parentType(comp) in fromToable:
            if 'to' in parent.keys():
                comp['parent'] = parent['to']
                # Making sure our nodes have the superset of connected phases:
                interNode = getByName(parent['to'])
                interNode['phases'] = phaseMerge(interNode['phases'],comp['phases'])
            else:
                # Gotta insert a node between lines and parentable objects:
                newNode = {'object':'node',
                           'phases':comp['phases'],
                           'name': 'node' + comp['name'] + parent['name'],
                            'nominal_voltage':nominal_voltage,
                            'latitude': comp['latitude'],
                            'longitude': comp['longitude']}
                convertedComponents.append(newNode)
                parent['to'] = newNode['name']
                comp['parent'] = newNode['name']
        elif comp['object'] in fromToable and parentType(comp) in fromToable:
            if 'to' in parent.keys():
                comp['from'] = parent['to']
                # Making sure our nodes have the superset of connected phases:
                interNode = getByName(parent['to'])
                interNode['phases'] = phaseMerge(interNode['phases'],comp['phases'])
            else:
                # Gotta insert a node between two lines:
                newNode = {'object':'node',
                           'phases':comp['phases'],
                           'name': 'node' + comp['name'] + parent['name'],
                            'nominal_voltage':nominal_voltage,
                            'latitude': comp['latitude'],
                            'longitude': comp['longitude']}
                convertedComponents.append(newNode)
                parent['to'] = newNode['name']
                comp['from'] = newNode['name']
        elif comp['object'] in nodable and parentType(comp) in fromToable:
            parent['to'] = comp['name']
        else:
            # Here we're in an error case (like loads connected to loads), so do nothing:
            return False
        return True

    # Fix the connectivity:
    for comp in convertedComponents:
        fixCompConnectivity(comp)

    # Go to a dictionary format so we have a valid glmTree. Start at 1 so we have room for headers:
    glmTree = {(1+convertedComponents.index(x))*subObCount:x for x in convertedComponents}

    #MAYBEFIX: REMOVE THIS DISASTER HERE AND FIGURE OUT WHY SOME LINKS ARE MALFORMED
    for key in glmTree.keys():
        # if ('from' in glmTree[key].keys() and 'to' not in glmTree[key].keys()) or ('to' in glmTree[key].keys() and 'from' not in glmTree[key].keys()):
        if glmTree[key]['object'] in ['overhead_line','underground_line','regulator','transformer','switch','fuse'] and ('to' not in glmTree[key].keys() or 'from' not in glmTree[key].keys()):
            # print [glmTree[key]['name'], glmTree[key]['object']]
            del glmTree[key]

    #Strip guids:
    for key in glmTree:
        if 'guid' in glmTree[key]: del glmTree[key]['guid']
        if 'parentGuid' in glmTree[key]: del glmTree[key]['parentGuid']

    def fixLinkPhases(comp):
        def getByName(name):
            candidates = [glmTree[x] for x in glmTree if 'name' in glmTree[x] and glmTree[x]['name'] == name]
            if len(candidates) == 0:
                return {}
            else:
                return candidates[0]

        def phaseMin(x,y):
            return ''.join(set(x).intersection(set(y)))

        if comp['object'] in ['overhead_line','underground_line','regulator','transformer','switch','fuse']:
            fromPhases = getByName(comp['from'])['phases']
            toPhases = getByName(comp['to'])['phases']
            comp['phases'] = phaseMin(fromPhases, toPhases)
            if 'N' in comp['phases'] and (comp['object'] == 'overhead_line' or comp['object'] == 'underground_line'):
                key = 0
                for y in comp.keys():
                    if type(y) is int:
                        key = y+5
                        if key in comp[y].keys():# line_configuration has a neutral conductor
                            pass
                        else:
                            comp['phases'] = comp['phases'].replace('N','')

            return True
        else:
            return False

    for key in glmTree:
        fixLinkPhases(glmTree[key])

    # Convert lines with distributed load
    def convDistLoadLines(glm_dict):
        last_key = len(glm_dict)
        # Grab all the keys of overhead or underground lines that have distributed loads
        dl_line_keys = [x for x in glm_dict if 'distributed_load_A' in glm_dict[x] or 'distributed_load_B' in glm_dict[x] or 'distributed_load_C' in glm_dict[x]]

        for y in dl_line_keys:
            # create an intermedate node and two loads
            # first find from node object and to node
            node12 = None
            load1 = None
            load2 = None
            for x in glm_dict:
                if 'name' in glm_dict[x] and glm_dict[x]['name'] == glm_dict[y]['from']:
                    node12 = copy.deepcopy(glm_dict[x])
                    load1 = copy.deepcopy(glm_dict[x])
                    if 'bustype' in glm_dict[x]:
                        del node12['bustype']
                        del load1['bustype']
                if 'name' in glm_dict[x] and glm_dict[x]['name'] == glm_dict[y]['to']:
                    load2 = copy.deepcopy(glm_dict[x])


            if node12 != None and load1 != None and load2 != None:
                node12['name'] = 'node_' + glm_dict[y]['name'] + '_1'
                node12['phases'] = glm_dict[y]['phases']

                load1['name'] = glm_dict[y]['name'] + '_distributed_load_1'
                load1['parent'] = node12['name']
                load1['phases'] = node12['phases']
                load1['object'] = 'load'
                load1['load_class'] = 'C'

                load2['name'] = glm_dict[y]['name'] + '_distributed_load_2'
                load2['parent'] = glm_dict[y]['to']
                load2['phases'] = node12['phases']
                load2['object'] = 'load'
                load2['load_class'] = 'C'

                # split the load by 2/3 and 1/3

                if 'distributed_load_A' in glm_dict[y]:
                    load1['constant_power_A'] = str(glm_dict[y]['distributed_load_A'].real*2/3) + ('+' if glm_dict[y]['distributed_load_A'].imag >= 0.0 else '-') + str(abs(glm_dict[y]['distributed_load_A'].imag*2/3)) + 'j'
                    load2['constant_power_A'] = str(glm_dict[y]['distributed_load_A'].real/3) + ('+' if glm_dict[y]['distributed_load_A'].imag >= 0.0 else '-') + str(abs(glm_dict[y]['distributed_load_A'].imag/3)) + 'j'
                    del glm_dict[y]['distributed_load_A']
                if 'distributed_load_B' in glm_dict[y]:
                    load1['constant_power_B'] = str(glm_dict[y]['distributed_load_B'].real*2/3) + ('+' if glm_dict[y]['distributed_load_B'].imag >= 0.0 else '-') + str(abs(glm_dict[y]['distributed_load_B'].imag*2/3)) + 'j'
                    load2['constant_power_B'] = str(glm_dict[y]['distributed_load_B'].real/3) + ('+' if glm_dict[y]['distributed_load_B'].imag >= 0.0 else '-') + str(abs(glm_dict[y]['distributed_load_B'].imag/3)) + 'j'
                    del glm_dict[y]['distributed_load_B']
                if 'distributed_load_C' in glm_dict[y]:
                    load1['constant_power_C'] = str(glm_dict[y]['distributed_load_C'].real*2/3) + ('+' if glm_dict[y]['distributed_load_C'].imag >= 0.0 else '-') + str(abs(glm_dict[y]['distributed_load_C'].imag*2/3)) + 'j'
                    load2['constant_power_C'] = str(glm_dict[y]['distributed_load_C'].real/3) + ('+' if glm_dict[y]['distributed_load_C'].imag >= 0.0 else '-') + str(abs(glm_dict[y]['distributed_load_C'].imag/3)) + 'j'
                    del glm_dict[y]['distributed_load_C']

            #Split line into two line segments, 1/4 long and 3/4 long
            line_segment1 = copy.deepcopy(glm_dict[y])
            line_segment2 = copy.deepcopy(glm_dict[y])
            line_segment1['name'] = glm_dict[y]['name'] + '_LINESEG1'
            line_segment1['length'] = str(float(glm_dict[y]['length'])/4)
            line_segment1['to'] = node12['name']
            line_segment2['name'] = glm_dict[y]['name'] + '_LINESG2'
            line_segment2['length'] = str(float(glm_dict[y]['length'])*3/4)
            line_segment2['from'] = node12['name']

            #Rename all embedded objects
            for a in line_segment1.keys():
                if type(line_segment1[a]) is dict:
                    line_segment1[a]['name'] = line_segment1['name'] + '-LINECONFIG'
                    for b in line_segment1[a].keys():
                        if type(line_segment1[a][b]) is dict and 'omfEmbeddedConfigObject' in line_segment1[a][b] and line_segment1[a][b]['omfEmbeddedConfigObject'] == 'spacing object line_spacing':
                            line_segment1[a][b]['name'] = line_segment1['name'] + '-LINESPACING'
                        elif type(line_segment1[a][b]) is dict and 'omfEmbeddedConfigObject' in line_segment1[a][b] and 'conductor_A' in line_segment1[a][b]['omfEmbeddedConfigObject']:
                            line_segment1[a][b]['name'] = line_segment1['name'] + '-CONDUCTOR_A'
                        elif type(line_segment1[a][b]) is dict and 'omfEmbeddedConfigObject' in line_segment1[a][b] and 'conductor_B' in line_segment1[a][b]['omfEmbeddedConfigObject']:
                            line_segment1[a][b]['name'] = line_segment1['name'] + '-CONDUCTOR_B'
                        elif type(line_segment1[a][b]) is dict and 'omfEmbeddedConfigObject' in line_segment1[a][b] and 'conductor_C' in line_segment1[a][b]['omfEmbeddedConfigObject']:
                            line_segment1[a][b]['name'] = line_segment1['name'] + '-CONDUCTOR_C'
                        elif type(line_segment1[a][b]) is dict and 'omfEmbeddedConfigObject' in line_segment1[a][b] and 'conductor_N' in line_segment1[a][b]['omfEmbeddedConfigObject']:
                            line_segment1[a][b]['name'] = line_segment1['name'] + '-CONDUCTOR_N'

            for a in line_segment2.keys():
                if type(line_segment2[a]) is dict:
                    line_segment2[a]['name'] = line_segment2['name'] + '-LINECONFIG'
                    for b in line_segment2[a].keys():
                        if type(line_segment2[a][b]) is dict and 'omfEmbeddedConfigObject' in line_segment2[a][b] and line_segment2[a][b]['omfEmbeddedConfigObject'] == 'spacing object line_spacing':
                            line_segment2[a][b]['name'] = line_segment2['name'] + '-LINESPACING'
                        elif type(line_segment2[a][b]) is dict and 'omfEmbeddedConfigObject' in line_segment2[a][b] and 'conductor_A' in line_segment2[a][b]['omfEmbeddedConfigObject']:
                            line_segment2[a][b]['name'] = line_segment2['name'] + '-CONDUCTOR_A'
                        elif type(line_segment2[a][b]) is dict and 'omfEmbeddedConfigObject' in line_segment2[a][b] and 'conductor_B' in line_segment2[a][b]['omfEmbeddedConfigObject']:
                            line_segment2[a][b]['name'] = line_segment2['name'] + '-CONDUCTOR_B'
                        elif type(line_segment2[a][b]) is dict and 'omfEmbeddedConfigObject' in line_segment2[a][b] and 'conductor_C' in line_segment2[a][b]['omfEmbeddedConfigObject']:
                            line_segment2[a][b]['name'] = line_segment2['name'] + '-CONDUCTOR_C'
                        elif type(line_segment2[a][b]) is dict and 'omfEmbeddedConfigObject' in line_segment2[a][b] and 'conductor_N' in line_segment2[a][b]['omfEmbeddedConfigObject']:
                            line_segment2[a][b]['name'] = line_segment2['name'] + '-CONDUCTOR_N'

            glm_dict[y] = line_segment1
            glm_dict[last_key*subObCount] = node12
            last_key += 1
            glm_dict[last_key*subObCount] = load1
            last_key += 1
            glm_dict[last_key*subObCount] = line_segment2
            last_key += 1
            glm_dict[last_key*subObCount] = load2
            last_key += 1

        return glm_dict

    glmTree = convDistLoadLines(glmTree)
    # Fix nominal voltage
    def fix_nominal_voltage(glm_dict, volt_dict):
        for x in glm_dict:
            if 'parent' in glm_dict[x].keys() and glm_dict[x]['parent'] in volt_dict.keys() and glm_dict[x]['name'] not in volt_dict.keys():
                glm_dict[x]['nominal_voltage'] = volt_dict[glm_dict[x]['parent']]
                volt_dict[glm_dict[x]['name']] = glm_dict[x]['nominal_voltage']
            elif 'from' in glm_dict[x].keys() and glm_dict[x]['from'] in volt_dict.keys() and glm_dict[x]['name'] not in volt_dict.keys():
                if glm_dict[x]['object'] == 'transformer':
                    for y in glm_dict[x]:
                        if type(y) is int:
                            nv = glm_dict[x][y]['secondary_voltage']

                    glm_dict[x]['nominal_voltage'] = nv
                else:
                    glm_dict[x]['nominal_voltage'] = volt_dict[glm_dict[x]['from']]

                volt_dict[glm_dict[x]['name']] = glm_dict[x]['nominal_voltage']
                for y in glm_dict:
                    if 'name' in glm_dict[y] and glm_dict[y]['name'] == glm_dict[x]['to']:
                        glm_dict[y]['nominal_voltage'] = glm_dict[x]['nominal_voltage']
                        volt_dict[glm_dict[y]['name']] = glm_dict[y]['nominal_voltage']
            # Regulator_Configuration set to Swing
            try:
                if 'SWING' in glm_dict[x].values():
                    nominalVoltageSwing = float(glm_dict[x]['nominal_voltage'])
                if 'regulator' in glm_dict[x].values():
                    for key, value in glm_dict[x].iteritems():
                        if 'band_center' in glm_dict[x][key]:
                            bandWidthRegulator = float(glm_dict[x][key]['band_width'])
                            if (glm_dict[x][key]['band_center'] != nominalVoltageSwing):
                                glm_dict[x][key]['band_center'] = nominalVoltageSwing
                                glm_dict[x][key]['band_width'] =  (bandWidthRegulator * nominalVoltageSwing) / 120
            except:
                print "\n   Couldn't set regulator_configuration to the swing bus nominal_voltage."

    parent_voltage = {}
    current_parents = len(parent_voltage)
    previous_parents = 0

    for obj in glmTree:
        if 'bustype' in glmTree[obj] and glmTree[obj]['bustype'] == 'SWING':
            parent_voltage[glmTree[obj]['name']] = glmTree[obj]['nominal_voltage']
            current_parents = len(parent_voltage)

    while current_parents > previous_parents:
        fix_nominal_voltage(glmTree, parent_voltage)
        previous_parents = current_parents
        current_parents = len(parent_voltage)

    # figure out the PT rating for regulators
    for x in glmTree.keys():
        if 'object' in glmTree[x].keys() and glmTree[x]['object'] == 'regulator':
            for y in glmTree[x].keys():
                if type(glmTree[x][y]) is dict:
                    glmTree[x][y]['power_transducer_ratio'] = str(float(glmTree[x].get('nominal_voltage', 14400))/120)

    # Delete nominal_voltage from link objects
    del_nom_volt_list = ['overhead_line', 'underground_line', 'regulator', 'transformer', 'switch', 'fuse', 'ZIPload', 'diesel_dg']
    for x in glmTree:
        if 'object' in glmTree[x].keys() and glmTree[x]['object'] in del_nom_volt_list and 'nominal_voltage' in glmTree[x].keys():
            del glmTree[x]['nominal_voltage']

    def secondarySystemFix(glm):
        def unused_key(dic, key_multiplier):
            free_key = (int(max(dic.keys())/key_multiplier) + 1)*key_multiplier
            return free_key
        allLoadKeys = [x for x in glm if 'object' in glm[x] and 'parent' in glm[x] and glm[x]['object']=='load' and 'load_class' in glm[x] and glm[x]['load_class'] == 'R']
        allNamesNodesOnLoads = list(set([glm[key]['parent'] for key in allLoadKeys]))
        all2ndTransKeys = []
        all2ndLoadKeys = []
        all2ndNodeKeys = []
        def nameToKey(name):
            hits = [x for x in glm if 'name' in glm[x] and glm[x]['name'] == name]
            if len(hits) == 0:
                return []
            else:
                return hits
        for key in glm:
            if 'object' in glm[key] and glm[key]['object'] == 'transformer':
                #fromName = glm[key]['from']
                toName = glm[key]['to']
                #if fromName in allNamesNodesOnLoads:
                #   all2ndTransKeys.append(key)
                #   all2ndNodeKeys.extend(nameToKey(fromName))
                #   all2ndLoadKeys.extend([x for x in glm if 'parent' in glm[x] and 'object' in glm[x] and glm[x]['object'] == 'load' and glm[x]['parent'] == fromName])
                if toName in allNamesNodesOnLoads:
                    all2ndTransKeys.append(key)
                    all2ndNodeKeys.extend(nameToKey(toName))
                    all2ndLoadKeys.extend([x for x in glm if 'parent' in glm[x] and 'object' in glm[x] and glm[x]['object'] == 'load' and glm[x]['parent'] == toName])
                else:
                    # this ain't no poletop transformer
                    pass
        # Fix da nodes.
        # {'phases': 'BN', 'object': 'node', 'nominal_voltage': '2400', 'name': 'nodeS1806-32-065T14102'}
        # object triplex_meter { phases BS; nominal_voltage 120; };
        for nodeKey in all2ndNodeKeys:
            phases = set(glm[nodeKey]['phases'])
            #if the node has multiple phases we need to split it out to multiple triplex_meters
            for y in phases:
                if y != 'N' and y != 'D':
                    new_key = unused_key(glm,subObCount)
                    glm[new_key] = {'object' : 'triplex_meter',
                                    'name' : glm[nodeKey]['name'] + '_' + y,
                                    'phases' : y + 'S',
                                    'nominal_voltage' : '120'}
        # Fix da loads.
        #{'phases': 'BN', 'object': 'load', 'name': 'S1806-32-065', 'parent': 'nodeS1806-32-065T14102', 'load_class': 'R', 'constant_power_C': '0', 'constant_power_B': '1.06969', 'constant_power_A': '0', 'nominal_voltage': '120'}
        for loadKey in all2ndLoadKeys:
            phases = set(glm[loadKey]['phases'])
            for y in phases:
                if y != 'N' and y != 'D':
                    new_key = unused_key(glm,subObCount)
                    glm[new_key] = {'object' : 'triplex_node',
                                    'name' : glm[loadKey]['name'] + '_' + y,
                                    'phases' : y + 'S',
                                    'parent' : glm[loadKey]['parent'] + '_' + y,
                                    'nominal_voltage' : '120'}

                    if y == 'A':
                        glm[new_key]['power_12'] = glm[loadKey]['constant_power_A']
                    elif y == 'B':
                        glm[new_key]['power_12'] = glm[loadKey]['constant_power_B']
                    elif y == 'C':
                        glm[new_key]['power_12'] = glm[loadKey]['constant_power_C']
        # Gotta fix the transformer phases too...
        for key in all2ndTransKeys:
            phases = set(glm[key]['phases'])
            for y in phases:
                if y != 'N' and y != 'D':
                    new_key = unused_key(glm,subObCount)
                    glm[new_key] = {'object' : 'transformer',
                                    'name' : glm[key]['name'] + '_' + y,
                                    'phases' : y + 'S',
                                    'from' : glm[key]['from'],
                                    'to' : glm[key]['to'] + '_' + y}
                    for z in glm[key]:
                        if type(z) is int:
                            glm[new_key][new_key+1] = {'omfEmbeddedConfigObject' : 'configuration object transformer_configuration',
                                                       'name' : glm[new_key]['name'] + '-CONFIG',
                                                       'primary_voltage' : glm[key][z]['primary_voltage'],
                                                       'secondary_voltage' : '120.0',
                                                       'connect_type' : 'SINGLE_PHASE_CENTER_TAPPED',
                                                       'impedance' : glm[key][z]['impedance']}
                            if 'shunt_impedance' in glm[key][z]:
                                glm[new_key][new_key+1]['shunt_impedance'] = glm[key][z]['shunt_impedance']
                            #NOTE: default values are average of all .std data sets we've seen.
                            if y == 'A':
                                glm[new_key][new_key+1]['power_rating'] = glm[key][z].get('powerA_rating', 250)
                                glm[new_key][new_key+1]['powerA_rating'] = glm[key][z].get('powerA_rating', 250)
                            elif y == 'B':
                                glm[new_key][new_key+1]['power_rating'] = glm[key][z].get('powerB_rating', 250)
                                glm[new_key][new_key+1]['powerB_rating'] = glm[key][z].get('powerB_rating', 250)
                            elif y == 'C':
                                glm[new_key][new_key+1]['power_rating'] = glm[key][z].get('powerC_rating', 250)
                                glm[new_key][new_key+1]['powerC_rating'] = glm[key][z].get('powerC_rating', 250)
        # Delete original transformers, nodes and loads that the split phase objects are representing
        for key in all2ndTransKeys:
            del glm[key]
        for key in all2ndLoadKeys:
            del glm[key]
        for key in all2ndNodeKeys:
            del glm[key]
    # Fixing the secondary (triplex) system.
    secondarySystemFix(glmTree)

    def dedupGlm(compName, glmRef):
        '''
        Assume compName is transformer_configuration
        1. pull out a list of all transformer_configuration dicts.
        2. process to make redundant ones into tuples
        3. go through the list backwards and collapse chains of references. or fold carefully until we can't fold any more.
        4. actually replace the names on other objects and then delete the tuples.
        '''
        def isSameMinusName(x,y):
            newX = {val:x[val] for val in x if val != 'name'}
            newY = {val:y[val] for val in y if val != 'name'}
            return newX==newY
        def dupToTup(inList):
            # Go through a list of components, and given two identicals (up to name) in a row, replace the first one with (name1, name2).
            for i in xrange(0,len(inList)-1):
                if isSameMinusName(inList[i], inList[i+1]):
                    inList[i] = (inList[i]['name'], inList[i+1]['name'])
                else:
                    pass
        def dechain(tupleList):
            # Go backwards through a list of tuples and change e.g. (1,2),(2,3),(3,4) into (1,4),(2,4),(3,4).
            for i in xrange(len(tupleList)-1,0,-1):
                if tupleList[i][0] == tupleList[i-1][1]:
                    tupleList[i-1] = (tupleList[i-1][0], tupleList[i][1])
                else:
                    pass

        # sort the components, ignoring their names:
        compList = sorted([glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object']==compName], key=lambda x:{val:x[val] for val in x if val != 'name'})

        dupToTup(compList)

        nameMaps = [x for x in compList if type(x) is tuple]
        realConfigs = [x for x in compList if type(x) is dict]

        dechain(nameMaps)

        #Debug: print the amount of collapse:
        # print 'WORKING ON ' + compName
        # print 'Mappings:'
        # print len(nameMaps)
        # print 'Real configs:'
        # print len(realConfigs)
        # print 'Total:'
        # print len(nameMaps) + len(realConfigs)

        nameDictMap = {x[0]:x[1] for x in nameMaps}

        # Killing duplicate objects
        iterKeys = glmRef.keys()
        for x in iterKeys:
            if 'name' in glmRef[x] and glmRef[x]['name'] in nameDictMap.keys():
                del glmRef[x]

        # Rewiring all objects
        iterKeys = glmRef.keys()
        if compName == 'transformer_configuration':
            transformers = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'transformer']
            for tranny in transformers:
                if tranny['configuration'] in nameDictMap.keys(): tranny['configuration'] = nameDictMap[tranny['configuration']]
        elif compName == 'regulator_configuration':
            regulators = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'regulator']
            for reggy in regulators:
                if reggy['configuration'] in nameDictMap.keys(): reggy['configuration'] = nameDictMap[reggy['configuration']]
        elif compName == 'line_spacing':
            lineConfigs = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'line_configuration']
            for config in lineConfigs:
                if config['spacing'] in nameDictMap.keys(): config['spacing'] = nameDictMap[config['spacing']]
        elif compName == 'overhead_line_conductor' or compName == 'underground_line_conductor':
            lineConfigs = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'line_configuration']
            for config in lineConfigs:
                if 'conductor_A' in config.keys():
                    if config['conductor_A'] in nameDictMap.keys(): config['conductor_A'] = nameDictMap[config['conductor_A']]
                if 'conductor_B' in config.keys():
                    if config['conductor_B'] in nameDictMap.keys(): config['conductor_B'] = nameDictMap[config['conductor_B']]
                if 'conductor_C' in config.keys():
                    if config['conductor_C'] in nameDictMap.keys(): config['conductor_C'] = nameDictMap[config['conductor_C']]
                if 'conductor_N' in config.keys():
                    if config['conductor_N'] in nameDictMap.keys(): config['conductor_N'] = nameDictMap[config['conductor_N']]
        elif compName == 'line_configuration':
            lines = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] in ['overhead_line','underground_line']]
            for line in lines:
                if line['configuration'] in nameDictMap.keys(): line['configuration'] = nameDictMap[line['configuration']]

    # Fully disembed and remove duplicate configuration objects:
    feeder.fullyDeEmbed(glmTree)
    dedupGlm('transformer_configuration', glmTree)
    dedupGlm('regulator_configuration', glmTree)
    dedupGlm('line_spacing', glmTree)
    dedupGlm('overhead_line_conductor', glmTree)
    dedupGlm('underground_line_conductor', glmTree)
    # NOTE: This last dedup has to come last, because it relies on doing conductors and spacings first!
    dedupGlm('line_configuration', glmTree)
    # Throw some headers on that:
    genericHeaders = [  {"timezone":"PST+8PDT","stoptime":"'2000-01-01 00:00:00'","starttime":"'2000-01-01 00:00:00'","clock":"clock"},
                        {"omftype":"#set","argument":"minimum_timestep=60"},
                        {"omftype":"#set","argument":"profiler=1"},
                        {"omftype":"#set","argument":"relax_naming_rules=1"},
                        {"omftype":"#include","argument":"\"schedules.glm\""},
                        {"omftype":"module","argument":"generators"},
                        {"omftype":"module","argument":"tape"},
                        {"module":"residential","implicit_enduses":"NONE"},
                        {"solver_method":"NR","NR_iteration_limit":"50","module":"powerflow"},
                        {"omftype": "module", "argument": "climate"},
                        {"object":"climate", "name":"Climate", "interpolate": "QUADRATIC", "tmyfile": "climate.tmy2"}]
    for headId in xrange(len(genericHeaders)):
        glmTree[headId] = genericHeaders[headId]

    # Go through and put lat/lons on meters and loads.
    nameToIndex = {glmTree[key].get('name',''):key for key in glmTree}
    for key in glmTree:
        thisOb = glmTree[key]
        if thisOb.get('object','') == 'transformer':
            fromOb = glmTree.get(nameToIndex.get(thisOb.get('from',''),0),{})
            toOb = glmTree.get(nameToIndex.get(thisOb.get('to',''),0),{})
            if toOb.get('object','') == 'triplex_meter' and 'latitude' in fromOb and 'longitude' in fromOb:
                toOb['latitude'] = str(float(fromOb['latitude']) + random.uniform(-10,10))
                toOb['longitude'] = str(float(fromOb['longitude']) + random.uniform(-10,10))
    for key in glmTree:
        thisOb = glmTree[key]
        if thisOb.get('object','') in ['triplex_node','load']:
            parentOb = glmTree.get(nameToIndex.get(thisOb.get('parent',''),0),{})
            if 'latitude' in parentOb and 'longitude' in parentOb:
                thisOb['latitude'] = str(float(parentOb['latitude']) + random.uniform(-5,5))
                thisOb['longitude'] = str(float(parentOb['longitude']) + random.uniform(-5,5))

    return glmTree, x_scale, y_scale


def _latCount(name):
    ''' Debug function to count up the meters and such and figure out whether we're lat/lon coding them correctly. '''
    nameCount, myLatCount = (0,0)
    for key in outGlm:
        if outGlm[key].get('object','')==name:
            nameCount += 1
            if 'latitude' in outGlm[key]:
                myLatCount += 1
    print name, 'COUNT', nameCount, 'LAT COUNT', latCount, 'SUCCESS RATE', 1.0*latCount/nameCount

def _tests(keepFiles=True):
    ''' Test convert every windmil feeder we have (in uploads). Return number of exceptions we hit. '''
    import os, json, traceback, shutil
    from solvers import gridlabd
    from matplotlib import pyplot as plt
    openPrefix = './uploads/'
    outPrefix = './scratch/milToGridlabTests/'
    try:
        os.mkdir(outPrefix)
    except:
        pass # Directory already there.
    exceptionCount = 0
    # testFiles = [('INEC-RENOIR.std','INEC.seq'), ('INEC-GRAHAM.std','INEC.seq'),
    #   ('Olin-Barre.std','Olin.seq'), ('Olin-Brown.std','Olin.seq'),
    #   ('ABEC-FRANK.std','ABEC.seq'), ('ABEC-COLUMBIA.std','ABEC.seq'),('OMF_Norfork1.std', 'OMF_Norfork1.seq')]
    testFiles = [('OMF_Norfork1.std', 'OMF_Norfork1.seq')]
    testAttachments = {'schedules.glm':''}
    # testAttachments = {'schedules.glm':'', 'climate.tmy2':open('./data/Climate/KY-LEXINGTON.tmy2','r').read()}
    for stdString, seqString in testFiles:
        try:
            # Convert the std+seq.
            with open(openPrefix + stdString,'r') as stdFile, open(openPrefix + seqString,'r') as seqFile:
                outGlm,x,y = convert(stdFile.read(),seqFile.read())
            with open(outPrefix + stdString.replace('.std','.glm'),'w') as outFile:
                outFile.write(feeder.sortedWrite(outGlm))
            print 'WROTE GLM FOR', stdString
            try:
                # Draw the GLM.
                myGraph = feeder.treeToNxGraph(outGlm)
                feeder.latLonNxGraph(myGraph, neatoLayout=False)
                plt.savefig(outPrefix + stdString.replace('.std','.png'))
                print 'DREW GLM OF', stdString
            except:
                exceptionCount += 1
                print 'FAILED DRAWING', stdString
            try:
                # Run powerflow on the GLM. HACK:blank attachments for now.
                output = gridlabd.runInFilesystem(outGlm, attachments=testAttachments, keepFiles=False)
                with open(outPrefix + stdString.replace('.std','.json'),'w') as outFile:
                    json.dump(output, outFile, indent=4)
                print 'RAN GRIDLAB ON', stdString
            except:
                exceptionCount += 1
                print 'POWERFLOW FAILED', stdString
        except:
            print 'FAILED CONVERTING', stdString
            exceptionCount += 1
            traceback.print_exc()
    if not keepFiles:
        shutil.rmtree(outPrefix)
    return exceptionCount

if __name__ == "__main__":
    _tests()
