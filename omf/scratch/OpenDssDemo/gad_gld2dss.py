"""
"""

import re
import glob
import os
import math
import sys

SQRT3 = math.sqrt(3.0)

def parse_impedance(str):
    toks = re.split('[\+\-j]',str)
    toks = [t for t in toks if t]
    r = float(toks[0])
    x = float(toks[1])
    if str.startswith('-'):
        r *= -1.0
    if '-' in str[2:]:
        x *= -1.0
#    print (str, toks, r, x)
    return r, x

def parse_kvar(str):
    toks = str.split()
    val = float(toks[0])
    if len(toks) > 1:
        if 'MVAr' in toks[1]:
            val *= 1000.0
    else:
        val /= 1000.0
    return val

def parse_gmr_ft(str):
    toks = str.split()
    val = float(toks[0])
    if len(toks) > 1:
        if 'in' in toks[1]:
            val /= 12.0
    else:
        val *= 1.0
    return val

def parse_dist_ft(str):
    toks = str.split()
    val = float(toks[0])
    if len(toks) > 1:
        if 'in' in toks[1]:
            val /= 12.0
    else:
        val *= 1.0
    return val

def get_phnum(phstr):
    '''Convert a GLD phase letter to a DSS phase number'''
    if phstr == 'A' or phstr == 'AN':
        return '1'
    if phstr == 'B' or phstr == 'BN':
        return '2'
    if phstr == 'C' or phstr == 'CN':
        return '3'
    print('WARNING: "'+phstr+'" not recognized as a single phase.')
    return None

def get_phsfx(phstr):
    '''Build the OpenDSS bus suffix from the GridLAB-D phase field'''
    phsfx = ''
    if 'A' in phstr:
        phsfx += '.1'
    if 'B' in phstr:
        phsfx += '.2'
    if 'C' in phstr:
        phsfx += '.3'
    return phsfx

def count_ph(phstr):
    '''Count the number of phases from the GridLAB-D phase field'''
    count = 0
    if 'A' in phstr:
        count += 1
    if 'B' in phstr:
        count += 1
    if 'C' in phstr:
        count += 1
    return count

def obj(parent,model,line,itr,oidh,octr):
    '''
    Store an object in the model structure
    Inputs:
        parent: name of parent object (used for nested object defs)
        model: dictionary model structure
        line: glm line containing the object definition
        itr: iterator over the list of lines
        oidh: hash of object id's to object names
        octr: object counter
    '''
    octr += 1
    # Identify the object type
    m = re.search('object ([^:{\s]+)[:{\s]',line,re.IGNORECASE)
    type = m.group(1)
    # If the object has an id number, store it
    n = re.search('object ([^:]+:[^{\s]+)',line,re.IGNORECASE)
    if n:
        oid = n.group(1)
    line = next(itr)
    # Collect parameters
    oend = 0
    oname = None
    params = {}
    if parent is not None:
        params['parent'] = parent
        # print('nested '+type)
    while not oend:
        m = re.match('\s*(\S+) ([^;{]+)[;{]',line)
        if m:
            # found a parameter
            param = m.group(1)
            val = m.group(2)
            intobj = 0
            if param == 'name':
                oname = val
            elif param == 'object':
                # found a nested object
                intobj += 1
                if oname is None:
                    print('ERROR: nested object defined before parent name')
                    quit()
                line,octr = obj(oname,model,line,itr,oidh,octr)
            elif re.match('object',val):
                # found an inline object
                intobj += 1
                line,octr = obj(None,model,line,itr,oidh,octr)
                params[param] = 'OBJECT_'+str(octr)
            else:
                params[param] = val
        if re.search('}',line):
            if intobj:
                intobj -= 1
                line = next(itr)
            else:
                oend = 1
        else:
            line = next(itr)
    # If undefined, use a default name
    if oname is None:
        oname = 'OBJECT_'+str(octr)
    oidh[oname] = oname
    # Hash an object identifier to the object name
    if n:
        oidh[oid] = oname
    # Add the object to the model
    if type not in model:
        # New object type
        model[type] = {}
    model[type][oname] = {}
    for param in params:
        model[type][oname][param] = params[param]
    # Return the 
    return line,octr

def process_one_model(inf, modeldir, dotfile, vbase_str, circuit_name):

    toks = vbase_str.split(',')
    srcekv = float(toks[0])
    print ('voltage bases are {:s} and source voltage is {:.2f} for {:s}'.format (vbase_str, srcekv, circuit_name))

    #-----------------------
    # Pull Model Into Memory
    #-----------------------
    lines = []
    line = inf.readline()
    while line is not '':
        while re.match('\s*//',line) or re.match('\s+$',line):
            # skip comments and white space
            line = inf.readline()
        lines.append(line)
        line = inf.readline()
    inf.close()
    
    #--------------------------
    # Build the model structure
    #--------------------------
    octr = 0;
    model = {}
    h = {}      # OID hash
    clock = {}
    modules = {}
    classes = {}
    directives = []
    itr = iter(lines)
    for line in itr:
        # Look for objects
        if re.search('object',line):
            line,octr = obj(None,model,line,itr,h,octr)
        # Look for # directives
        if re.match('#\s?\w',line):
            directives.append(line)
        # Look for the clock
        m_clock = re.match('clock\s*([;{])',line,re.IGNORECASE)
        if (m_clock):
            # Clock found: look for parameters
            if m_clock.group(1) == '{':
                # multi-line clock definition
                oend = 0
                while not oend:
                    line = next(itr)
                    m_param = re.search('(\w+)\s+([^;\n]+)',line)
                    if m_param:
                        # Parameter found
                        clock[m_param.group(1)]=m_param.group(2)
                    if re.search('}',line):
                        # End of the clock definition
                        oend = 1
        # Look for module definitions
        m_mtype = re.search('module\s+(\w+)\s*([;{])',line,re.IGNORECASE)
        if (m_mtype):
            # Module found: look for parameters
            modules[m_mtype.group(1)] = {}
            if m_mtype.group(2) == '{':
                # multi-line module definition
                oend = 0
                while not oend:
                    line = next(itr)
                    m_param = re.search('(\w+)\s+([^;\n]+)',line)
                    if m_param:
                        # Parameter found
                        modules[m_mtype.group(1)][m_param.group(1)] =\
                                m_param.group(2)
                    if re.search('}',line):
                        # End of the module
                        oend = 1
        # Look for class definitions
        m_ctype = re.search('class\W+(\w+)\s*([;{])',line,re.IGNORECASE)
        if (m_ctype):
            # Class found: look for parameters
            classes[m_ctype.group(1)] = {}
            if m_ctype.group(2) == '{':
                # multi-line class definition
                oend = 0
                while not oend:
                    line = next(itr)
                    m_param = re.search('(\w+)\s+([^;\n]+)',line)
                    if m_param:
                        # Parameter found
                        classes[m_ctype.group(1)][m_param.group(1)] =\
                                m_param.group(2)
                    if re.search('}',line):
                        # End of the class
                        oend = 1
    
    # Print the oid hash
    # print('oidh:')
    # for x in h:
        # print(x+'->'+h[x])
    # print('end oidh')
    
    # Print the model structure
    # for t in model:
        # print(t+':')
        # for o in model[t]:
            # print('\t'+o+':')
            # for p in model[t][o]:
                # if ':' in model[t][o][p]:
                    # print('\t\t'+p+'\t-->\t'+h[model[t][o][p]])
                # else:
                    # print('\t\t'+p+'\t-->\t'+model[t][o][p])



    # -----------------------
    # Print the OpenDSS Model
    # -----------------------
    redirects = []
    kvbases = set([])
    
    # BREAKERS
    if 'breaker' in model:
        redirects.append('Breakers.dss')
        breakerf = open(modeldir+'/Breakers.dss', 'w');
        breakerf.write('!Breaker Definitions:\n\n');
        for breaker in model['breaker']:
            row = model['breaker'][breaker]
            name = str(breaker)
            bus1 = str(row['from'])
            bus2 = str(row['to'])
            phsfx = get_phsfx(row['phases'])
            phqty = str(count_ph(row['phases']))
            breakerf.write('new line.' + name       +\
                    ' bus1=' + bus1 + phsfx         +\
                    ' bus2=' + bus2 + phsfx         +\
                    ' phases=' + phqty              +\
                    ' switch=y')
            if row['status'] == 'OPEN':
                breakerf.write(' enabled=false')
            breakerf.write('\n');
        breakerf.close()


    # CAPACITORS AND CAPACITOR CONFIGURATOINS
    if 'capacitor' in model:
        redirects.append('Capacitors.dss')
        capacitorf = open(modeldir+'/Capacitors.dss', 'w')
        capacitorf.write('! Capacitor Definitions \n\n')
        redirects.append('CapControls.dss')
        capctrlf = open(modeldir+'/CapControls.dss','w')
        capctrlf.write('! Capacitor Controls \n\n')
        for cap in model['capacitor']:
            row = model['capacitor'][cap]
            # First, write to the capacitor file
            name = str(cap)                         # name of the capacitor
            bus1 = str(cap)                         # (always?) decended from a node
            phsfx = get_phsfx(row['phases'])        # DSS phase suffix
            phqty = str(count_ph(row['phases']))    # 
            if 'cap_nominal_voltage' in row:
                kvln_tok = 'cap_nominal_voltage'
            else:
                kvln_tok = 'nominal_voltage'
            kvLN = float(row[kvln_tok])/1000.0; # node voltage is LN
            kvbases.update([round(kvLN*SQRT3,2)])
            kv = '{:.3f}'.format(kvLN if phqty == '1' else kvLN*SQRT3)
            kvar = 0
            if 'capacitor_A' in row: 
                kvar += parse_kvar(row['capacitor_A'])
            if 'capacitor_B' in row:
                kvar += parse_kvar(row['capacitor_B'])
            if 'capacitor_C' in row:
                kvar += parse_kvar(row['capacitor_C'])
            kvar = str(kvar)
            conn = 'wye' # capacitors are always wye in gld
            capacitorf.write('new capacitor.' + name    +\
                ' bus1=' + bus1 + phsfx                 +\
                ' phases=' + phqty                      +\
                ' kv=' + kv                             +\
                ' kvar=' + kvar                         +\
                ' conn=wye'                             +\
                '\n')
            # Second, write to the cap control file
            if 'control' not in row:
                continue
            if row['control'] == 'VOLT':
                capctrlf.write('new capcontrol.' + name + '_ctrl ' +\
                    'capacitor=' + name + ' ')
                capctrlf.write('type=voltage'                       +\
                    ' element=' + 'capacitor.' + name               +\
                    ' terminal=' + '1'                              +\
                    ' ptphase=' + get_phnum(row['pt_phase'])        +\
                    ' ptratio=' + '1'                               +\
                    ' offsetting=' + str(row['voltage_set_high'])   +\
                    ' onsetting=' + str(row['voltage_set_low'])     +\
                    ' delay=' + str(row['time_delay'])              +\
                    ' delayoff=' + str(row['dwell_time'])           +\
                    ' deadtime=' + '0'                              +\
                    '\n')
            elif row['control'] == 'MANUAL':
                capctrlf.write('!manual control for '+name+'\n')
            else:
                # unrecognized control type: disable the controller
                print('Warning: "'+row['control']+'" cap control not implemented')
                capctrlf.write('enabled=false\n')
        capacitorf.close()
        capctrlf.close()


    # SWITCHES
    if 'switch' in model:
        redirects.append('Switches.dss')
        switchf = open(modeldir+'/Switches.dss','w')
        switchf.write('! Switch Definitions\n')
        for switch in model['switch']:
            row = model['switch'][switch]
            name = switch
            bus1 = str(row['from'])
            bus2 = str(row['to'])
            phsfx = get_phsfx(row['phases'])
            phqty = str(count_ph(row['phases']))
            switchf.write('new line.' + name        +\
                    ' bus1=' + bus1 + phsfx         +\
                    ' bus2=' + bus2 + phsfx         +\
                    ' phases=' + phqty              +\
                    ' switch=y')
            if row['status'] == 'OPEN':
                switchf.write(' enabled=false')
            switchf.write('\n');
        switchf.close()



    # LINES
    # Note: GridLAB-D uses incomplete line geometry - we will create the primitive
    # Z-matrix for an OpenDSS linecode using the same method as GridLAB-D.
    # GridLAB-D uses modified Carson's equations: Kersting (3rd) 4.39 and 4.40
    #   - Earth Resistivity is defined in line.h as 100 ohm-m
    #   - Here, we will assume a system frequency of 60 Hz
    rterm = 0.00158836*60
    icoef = 0.00202237*60
    iterm = math.log(100/60)/2 + 7.6786


    # LINE CODES (two variants, one with spacings and conductors, the other with impedances)
    if 'line_configuration' in model:
        redirects.append('LineCodes.dss')
        wirehash = {}
        if 'overhead_line_conductor' in model:
            wirehash.update(model['overhead_line_conductor'])
        if 'underground_line_conductor' in model:
            wirehash.update(model['underground_line_conductor'])
        if 'line_spacing' in model:
            spacehash = model['line_spacing']
        lcodef = open(modeldir+'/LineCodes.dss','w')
        lcodef.write('! Linecodes\n')
        for code in model['line_configuration']:
            row = model['line_configuration'][code]
            # Populate the following list vectors for existing phases
            ri = []
            GMR = []
            Dij = []
            idx = 0
            neutflag = 0
            phases = 0;
            # Check phase A
            if 'conductor_A' in row:
                phases += 1
                if 'overhead_line_conductor' in model:
                    if h[row['conductor_A']] in model['overhead_line_conductor']:
                        ri.append(float(wirehash[h[row['conductor_A']]]['resistance']))
                        GMR.append(parse_gmr_ft(wirehash[h[row['conductor_A']]]['geometric_mean_radius']))
                if 'underground_line_conductor' in model:
                    if h[row['conductor_A']] in model['underground_line_conductor']:
                        ri.append(float(wirehash[h[row['conductor_A']]]['conductor_resistance']))
                        GMR.append(parse_gmr_ft(wirehash[h[row['conductor_A']]]['conductor_gmr']))
                Dij.append([])
                Dij[idx].append(0)
                if 'conductor_B' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_AB'])
                    Dij[idx].append(D if D > 0 else 0.001)
                if 'conductor_C' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_AC'])
                    Dij[idx].append(D if D > 0 else 0.001)
                if 'conductor_N' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_AN'])
                    Dij[idx].append(D if D > 0 else 0.001)
                idx += 1
            # Check phase B
            if 'conductor_B' in row:
                phases += 1
                if 'overhead_line_conductor' in model:
                    if h[row['conductor_B']] in model['overhead_line_conductor']:
                        ri.append(float(wirehash[h[row['conductor_B']]]['resistance']))
                        GMR.append(parse_gmr_ft(wirehash[h[row['conductor_B']]]['geometric_mean_radius']))
                if 'underground_line_conductor' in model:
                    if h[row['conductor_B']] in model['underground_line_conductor']:
                        ri.append(float(wirehash[h[row['conductor_B']]]['conductor_resistance']))
                        GMR.append(parse_gmr_ft(wirehash[h[row['conductor_B']]]['conductor_gmr']))
                Dij.append([])
                if 'conductor_A' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_AB'])
                    Dij[idx].append(D if D > 0 else 0.001)
                Dij[idx].append(0)
                if 'conductor_C' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_BC'])
                    Dij[idx].append(D if D > 0 else 0.001)
                if 'conductor_N' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_BN'])
                    Dij[idx].append(D if D > 0 else 0.001)
                idx += 1
            # Check phase C
            if 'conductor_C' in row:
                phases += 1
                if 'overhead_line_conductor' in model:
                    if h[row['conductor_C']] in model['overhead_line_conductor']:
                        ri.append(float(wirehash[h[row['conductor_C']]]['resistance']))
                        GMR.append(parse_gmr_ft(wirehash[h[row['conductor_C']]]['geometric_mean_radius']))
                if 'underground_line_conductor' in model:
                    if h[row['conductor_C']] in model['underground_line_conductor']:
                        ri.append(float(wirehash[h[row['conductor_C']]]['conductor_resistance']))
                        GMR.append(parse_gmr_ft(wirehash[h[row['conductor_C']]]['conductor_gmr']))
                Dij.append([])
                if 'conductor_A' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_AC'])
                    Dij[idx].append(D if D > 0 else 0.001)
                if 'conductor_B' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_BC'])
                    Dij[idx].append(D if D > 0 else 0.001)
                Dij[idx].append(0)
                if 'conductor_N' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_CN'])
                    Dij[idx].append(D if D > 0 else 0.001)
                idx += 1
            # Check phase N
            if 'conductor_N' in row:
                neutflag = 1
                if 'overhead_line_conductor' in model:
                    if h[row['conductor_N']] in model['overhead_line_conductor']:
                        ri.append(float(wirehash[h[row['conductor_N']]]['resistance']))
                        GMR.append(parse_gmr_ft(wirehash[h[row['conductor_N']]]['geometric_mean_radius']))
                if 'underground_line_conductor' in model:
                    if h[row['conductor_N']] in model['underground_line_conductor']:
                        ri.append(float(wirehash[h[row['conductor_N']]]['conductor_resistance']))
                        GMR.append(parse_gmr_ft(wirehash[h[row['conductor_N']]]['conductor_gmr']))
                Dij.append([])
                if 'conductor_A' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_AN'])
                    Dij[idx].append(D if D > 0 else 0.001)
                if 'conductor_B' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_BN'])
                    Dij[idx].append(D if D > 0 else 0.001)
                if 'conductor_C' in row:
                    D = parse_dist_ft(spacehash[h[row['spacing']]]['distance_CN'])
                    Dij[idx].append(D if D > 0 else 0.001)
                Dij[idx].append(0)
                idx += 1
                        
            # Calculate the primitive impedance matrix from conductor data (assumes idx still good)
            if phases > 0:
                rprim = []
                xprim = []
                for ii in range(0,idx):
                    rprim.append([])
                    xprim.append([])
                    for jj in range(0,idx):
                        if ii == jj:
                            rprim[ii].append(ri[ii]+rterm)
                            xprim[ii].append(icoef*(math.log(1/GMR[ii])+iterm))
                        else:
                            rprim[ii].append(rterm)
                            if Dij[ii][jj] == 0:
                                print('ERROR: line configuration '+code+' has zero distance')
                            xprim[ii].append(icoef*(math.log(1/Dij[ii][jj])+iterm))
                # Write the line codes
                name = str(code)
                condqty = len(rprim)
                rmat = '[ '
                xmat = '[ '
                for ii in range(0,len(rprim)):
                    for jj in range(0,ii+1):
                        rmat += '{:.6f}'.format(rprim[ii][jj])
                        xmat += '{:.6f}'.format(xprim[ii][jj])
                        if jj < ii:
                            rmat += ' '
                            xmat += ' '
                    if ii < (len(rprim)-1):
                        rmat += ' | '
                        xmat += ' | '
                    else:
                        rmat += ' ]'
                        xmat += ' ]'
                # OpenDSS reduces the last conductor by default
                print ('new linecode.{:s} nphases={:d} units=mi'.format (name, condqty), file=lcodef)
                if neutflag:
                    print ('~ neutral={:d} kron=yes'.format(condqty), file=lcodef)
                print ('~ rmatrix={:s}'.format (rmat), file=lcodef)
                print ('~ xmatrix={:s}'.format (xmat), file=lcodef)
            else: # if we didn't find any conductors, look for the matrix elements
                if 'z11' in row:
                    phases += 1
                if 'z22' in row:
                    phases += 1
                if 'z33' in row:
                    phases += 1
                rfull = [[0 for i in range(phases)] for j in range(phases)]
                xfull = [[0 for i in range(phases)] for j in range(phases)]
                cfull = [[0 for i in range(phases)] for j in range(phases)]
                i = 0
                if 'z11' in row:
                    rfull[i][i], xfull[i][i] = parse_impedance (row['z11'])
                    if 'c11' in row:
                        cfull[i][i] = float(row['c11'])
                    i += 1
                if 'z22' in row:
                    rfull[i][i], xfull[i][i] = parse_impedance (row['z22'])
                    if 'c22' in row:
                        cfull[i][i] = float(row['c22'])
                    j = i-1
                    if 'z12' in row:
                        rfull[j][i], xfull[j][i] = parse_impedance (row['z12'])
                        rfull[i][j] = rfull[j][i]
                        xfull[i][j] = xfull[j][i]
                    if 'c12' in row:
                        cfull[j][i] = float(row['c12'])
                        cfull[i][j] = cfull[j][i]
                    i += 1
                if 'z33' in row:
                    rfull[i][i], xfull[i][i] = parse_impedance (row['z33'])
                    if 'c33' in row:
                        cfull[i][i] = float(row['c33'])
                    ## fill in the diagonals
                    j = i-1
                    if 'c23' in row:
                        cfull[j][i] = float(row['c23'])
                        cfull[i][j] = cfull[j][i]
                    if 'z23' in row:
                        rfull[j][i], xfull[j][i] = parse_impedance (row['z23'])
                        rfull[i][j] = rfull[j][i]
                        xfull[i][j] = xfull[j][i]
                        j -= 1
                    if 'z13' in row:
                        rfull[j][i], xfull[j][i] = parse_impedance (row['z13'])
                        rfull[i][j] = rfull[j][i]
                        xfull[i][j] = xfull[j][i]
                    if 'c13' in row:
                        cfull[j][i] = float(row['c13'])
                        cfull[i][j] = cfull[j][i]
                # write this line code in triangular form
                rmat = '['
                xmat = '['
                cmat = '['
                for ii in range(phases):
                    for jj in range(ii+1):
                        rmat += '{:.6f}'.format(rfull[ii][jj])
                        xmat += '{:.6f}'.format(xfull[ii][jj])
                        cmat += '{:.6f}'.format(cfull[ii][jj])
                        if jj < ii:
                            rmat += ' '
                            xmat += ' '
                            cmat += ' '
                    if ii < (phases-1):
                        rmat += ' | '
                        xmat += ' | '
                        cmat += ' | '
                    else:
                        rmat += ']'
                        xmat += ']'
                        cmat += ']'
                lcodef.write('new linecode.' + str(code)      +\
                        ' nphases='+str(phases) + ' units=mi' +\
                        '\n~ rmatrix=' + rmat                 +\
                        '\n~ xmatrix=' + xmat                 +\
                        '\n~ cmatrix=' + cmat                 +\
                        '\n')
        lcodef.close()
    
    # OVERHEAD LINES
    if 'overhead_line' in model:
        redirects.append('OverheadLines.dss')
        olf = open(modeldir+'/OverheadLines.dss','w')
        olf.write('! Overhead Line Definitions\n')
        for ol in model['overhead_line']:
            row = model['overhead_line'][ol]
            name = str(ol)
            bus1 = str(row['from'])
            bus2 = str(row['to'])
            phsfx = get_phsfx(row['phases'])
            phqty = str(count_ph(row['phases']))
            linecode = str(h[row['configuration']])
            length = str(row['length'])
            olf.write('new line.' + name        +\
                    ' bus1=' + bus1 + phsfx     +\
                    ' bus2=' + bus2 + phsfx     +\
                    ' phases=' + phqty          +\
                    ' linecode=' + linecode     +\
                    ' length=' + length         +\
                    ' units=Ft'                 +\
                    '\n')
        olf.close()
    
    
    # UNDERGROUND CABLES
    if 'underground_line' in model:
        redirects.append('UndergroundLines.dss')
        ugf = open(modeldir+'/UndergroundLines.dss','w')
        ugf.write('! Underground Line Definitions\n')
        for ol in model['underground_line']:
            row = model['underground_line'][ol]
            name = str(ol)
            bus1 = str(row['from'])
            bus2 = str(row['to'])
            phsfx = get_phsfx(row['phases'])
            phqty = str(count_ph(row['phases']))
            linecode = str(h[row['configuration']])
            length = str(row['length'])
            ugf.write('new line.' + name        +\
                    ' bus1=' + bus1 + phsfx     +\
                    ' bus2=' + bus2 + phsfx     +\
                    ' phases=' + phqty          +\
                    ' linecode=' + linecode     +\
                    ' length=' + length         +\
                    ' units=Ft'                 +\
                    '\n')
        ugf.close()
    
    
    # TRIPLEX LINES (two variants, one with spacing/conductor, other with impedances)
    # triplex_line_conductor: wire - resistance and gmr defined
    # triplex_line: linecode - distances defined as follows:
    #   distances = 2*diameter/2 + 2*insulation_thickness
    #   number and type of conductors is fixed
    if 'triplex_line_configuration' in model:
        redirects.append('TpxLineCodes.dss')
        if 'triplex_line_conductor' in model:
            wirehash = model['triplex_line_conductor']
        tpxcodef = open(modeldir+'/TpxLineCodes.dss','w')
        tpxcodef.write('! Triplex linecodes\n')
        for code in model['triplex_line_configuration']:
            row = model['triplex_line_configuration'][code]
            neutflag = False
            if 'z11' in row:
                r11, x11 = parse_impedance(row['z11'])
                r12, x12 = parse_impedance(row['z12'])
                r21, x21 = parse_impedance(row['z21'])
                r22, x22 = parse_impedance(row['z22'])
                rprim = [[r11, r12],[r21, r22]]
                xprim = [[x11, x12],[x21, x22]]
            else:
                # Populate the following list vectors for existing phases
                ri = []
                GMR = []
                Dij = []
                # Phase 1
                ri.append(float(wirehash[h[row['conductor_1']]]['resistance']))
                GMR.append(float(wirehash[h[row['conductor_1']]]['geometric_mean_radius']))
                Dij.append([])
                Dij[0].append(0)
                Dij[0].append(float(row['diameter'])+2*float(row['insulation_thickness']))
                Dij[0].append(float(row['diameter'])+2*float(row['insulation_thickness']))
                # Phase 2
                ri.append(float(wirehash[h[row['conductor_2']]]['resistance']))
                GMR.append(float(wirehash[h[row['conductor_2']]]['geometric_mean_radius']))
                Dij.append([])
                Dij[1].append(float(row['diameter'])+2*float(row['insulation_thickness']))
                Dij[1].append(0)
                Dij[1].append(float(row['diameter'])+2*float(row['insulation_thickness']))
                # Phase N
                ri.append(float(wirehash[h[row['conductor_N']]]['resistance']))
                GMR.append(float(wirehash[h[row['conductor_N']]]['geometric_mean_radius']))
                Dij.append([])
                Dij[2].append(float(row['diameter'])+2*float(row['insulation_thickness']))
                Dij[2].append(float(row['diameter'])+2*float(row['insulation_thickness']))
                Dij[2].append(0)
                neutflag = True
            
                # Calculate the primitive impedance matrix
                rprim = []
                xprim = []
                for ii in range(0,3):
                    rprim.append([])
                    xprim.append([])
                    for jj in range(0,3):
                        if ii == jj:
                            rprim[ii].append(ri[ii]+rterm)
                            xprim[ii].append(icoef*(math.log(1/GMR[ii])+iterm))
                        else:
                            rprim[ii].append(rterm)
                            xprim[ii].append(icoef*(math.log(1/Dij[ii][jj])+iterm))
            
            # Write the triplex line codes
            name = code
            rmat = '[ '
            xmat = '[ '
            for ii in range(0,len(rprim)):
                for jj in range(0,ii+1):
                    rmat += '{:.6f}'.format(rprim[ii][jj])
                    xmat += '{:.6f}'.format(xprim[ii][jj])
                    if jj < ii:
                        rmat += ' '
                        xmat += ' '
                if ii < (len(rprim)-1):
                    rmat += ' | '
                    xmat += ' | '
                else:
                    rmat += ' ]'
                    xmat += ' ]'
            # OpenDSS reduces the last conductor by default
            if neutflag:
                tpxcodef.write('new linecode.' + name    +\
                        ' nphases=3 units=mi'            +\
                        ' neutral=3 kron=yes'            +\
                        '\n~ rmatrix=' + rmat            +\
                        '\n~ xmatrix=' + xmat            +\
                        '\n')
            else:
                tpxcodef.write('new linecode.' + name    +\
                        ' nphases=2 units=mi'            +\
                        '\n~ rmatrix=' + rmat            +\
                        '\n~ xmatrix=' + xmat            +\
                        '\n')
        tpxcodef.close()
    
    
    
    # TRIPLEX LINES
    if 'triplex_line' in model:
        redirects.append('TriplexLines.dss')
        tpxf = open(modeldir+'/TriplexLines.dss','w')
        tpxf.write('! Triplex Line Definitions\n')
        for tpl in model['triplex_line']:
            row = model['triplex_line'][tpl]
            name = str(tpl)
            bus1 = str(row['from'])
            bus2 = str(row['to'])
            phsfx = '.1.2'
            phqty = str(2)
            linecode = str(h[row['configuration']])
            length = str(row['length'])
            tpxf.write('new line.' + name       +\
                    ' bus1=' + bus1 + phsfx     +\
                    ' bus2=' + bus2 + phsfx     +\
                    ' phases=' + phqty          +\
                    ' linecode=' + linecode     +\
                    ' length=' + length         +\
                    ' units=Ft'                 +\
                    '\n')
        tpxf.close()
    

    # TRANSFORMERS
    if 'transformer' in model:
        redirects.append('Transformers.dss')
        xff = open(modeldir+'/Transformers.dss','w')
        xff.write('! Transformer Definitions\n')
        for xfcode in model['transformer_configuration']:
            row = model['transformer_configuration'][xfcode]
            phct = 0
            if 'powerA_rating' in row:
                if float(row['powerA_rating']) > 0.0:
                    phct += 1
            if 'powerB_rating' in row:
                if float(row['powerB_rating']) > 0.0:
                    phct += 1
            if 'powerC_rating' in row:
                if float(row['powerC_rating']) > 0.0:
                    phct +=1
            if phct == 0 and 'power_rating' in row:
                if row['connect_type'] == 'SINGLE_PHASE_CENTER_TAPPED':
                    phct = 1
                else:
                    phct = 3
            kvastr = ' kva='+str(row['power_rating'])
            xff.write('new xfmrcode.xfcode_'+str(xfcode))
            if row['connect_type'] == 'SINGLE_PHASE_CENTER_TAPPED':
                xff.write(' windings=3')
            else:
                xff.write(' windings=2')
            xff.write(' phases='+str(phct))
            xff.write('\n\t~')
            if 'shunt_resistance' in row:
                nll_pct = '{:.3f}'.format(1/float(row['shunt_resistance'])*100)
                xff.write(' %noloadloss='+nll_pct)
            if 'shunt_reactance' in row:
                imag_pct = '{:.3f}'.format(1/float(row['shunt_reactance'])*100)
                xff.write(' %imag='+imag_pct)
            if ('shunt_resistance' in row) or ('shunt_reactance' in row):
                xff.write('\n\t~')
            # Implementation depends on the connection type
            if row['connect_type'] == 'SINGLE_PHASE_CENTER_TAPPED':
                if 'impedance' in row:
                    rwdg1, xgld = parse_impedance (row['impedance'])
                    if ('impedance1' in row) and ('imedance2' in row):
                        r1, x1 = parse_impedance (row['impedance1'])
                        r2, x2 = parse_impedance (row['impedance2'])
                        xhl = 100.0 * (xgld + x1)
                        xht = 100.0 * (xgld + x2)
                        xll = 100.0 * (x1 + x2)
                        rwdg1 *= 100.0
                        rwdg2 = 100.0 * r1
                        rwdg3 = 100.0 * r2
                    else:
                        xhl = 1.2 * 100.0 * xgld
                        xht = xhl
                        xlt = xhl * 0.8 / 1.2
                        rwdg1 *= 100.0 * 0.5
                        rwdg2 = 2 * rwdg1
                        rwdg3 = rwdg2
                else: # separate Reactance and Resistance definitions
                    xgld = 100.0 * float(row['reactance'])
                    if ('reactance1' in row) and ('reactance2' in row):
                        xgld1 = 100.0 * float(row['reactance1'])
                        xgld2 = 100.0 * float(row['reactance2'])
                        xhl = xgld + xgld1
                        xht = xgld + xgld2
                        xlt = xgld1 + xgld2
                    else: # GLD file contains the star-equivalent reactances
                        xhl = 1.2 * xgld
                        xht = 1.2 * xgld
                        xlt = 0.8 * xgld
                    rwdg1 = 100.0 * float(row['resistance'])
                    if ('resistance1' in row) and ('resistance2' in row):
                        rwdg2 = 100.0 * float(row['resistance1'])
                        rwdg3 = 100.0 * float(row['resistance2'])
                    else: # GLD file contains the winding resistances
                        rwdg2 = rwdg1
                        rwdg3 = rwdg1
                        rwdg1 *= 0.5
                # write the parsed short-circuit reactance data
                xff.write(' xhl='+'{:.3f}'.format(xhl))
                xff.write(' xht='+'{:.3f}'.format(xht))
                xff.write(' xlt='+'{:.3f}'.format(xlt))
                # Primary winding
                xff.write('\n\t~ wdg=1')
                xff.write(' conn=wye')
                xff.write(kvastr)
                xff.write(' kv='+'{:.3f}'.format(float(row['primary_voltage'])/1000))
                kvbases.update([round(float(row['primary_voltage'])/1000*SQRT3,2)])
                xff.write(' %R='+'{:.3f}'.format(rwdg1))
                # Secondary winding
                xff.write('\n\t~ wdg=2')
                xff.write(' conn=wye')
                xff.write(kvastr)
                xff.write(' kv=.120')
                kvbases.update([0.120])
                kvbases.update([0.240])
                xff.write(' %R='+'{:.3f}'.format(rwdg2))
                # Tertiary winding
                xff.write('\n\t~ wdg=3')
                xff.write(' conn=wye')
                xff.write(kvastr)
                xff.write(' kv=.120')
                xff.write(' %R='+'{:.3f}'.format(rwdg3))
            else:
                kv1 = float(row['primary_voltage']) / 1000
                kv2 = float(row['secondary_voltage']) / 1000
                if row['connect_type'] == 'WYE_WYE':
                    conn1 = 'wye'
                    conn2 = 'wye'
                    kvbases.update([round(kv1*SQRT3,2)])
                    kvbases.update([round(kv2*SQRT3,2)])
                    if phct == 1:
                        kv1 /= SQRT3
                        kv2 /= SQRT3
                elif row['connect_type'] == 'DELTA_GWYE':
                    conn1 = 'delta'
                    conn2 = 'wye'
                    kvbases.update([round(kv1,2)])
                    kvbases.update([round(kv2*SQRT3,2)])
                    if phct == 1:
                        kv2 /= SQRT3
                elif row['connect_type'] == 'DELTA_DELTA':
                    conn1 = 'delta'
                    conn2 = 'delta'
                    kvbases.update([round(kv1,2)])
                    kvbases.update([round(kv2,2)])
                # Impedance
                xff.write(' %loadloss='+'{:.3f}'.format(float(row['resistance'])*100))
                xff.write(' xhl='+str(float(row['reactance'])*100))
                # Primary winding
                xff.write('\n\t~ wdg=1')
                xff.write(' conn='+conn1)
                xff.write(kvastr)
                xff.write(' kv='+'{:.3f}'.format(kv1))
                # Secondary winding
                xff.write('\n\t~ wdg=2')
                xff.write(' conn='+conn2)
                xff.write(kvastr)
                xff.write(' kv='+'{:.3f}'.format(kv2))
            xff.write('\n');
        for xfmr in model['transformer']:
            row = model['transformer'][xfmr]
            bus1=str(row['from'])
            bus2=str(row['to'])
            phsfx = ''
            phases = row['phases']
            if 'A' in phases:
                phsfx += '.1'
            if 'B' in phases:
                phsfx += '.2'
            if 'C' in phases:
                phsfx += '.3'
            xff.write('new transformer.transformer_'+str(xfmr) + ' xfmrcode=xfcode_' 
                      + str(row['configuration']))
            if 'S' in phases:
                xff.write(' buses=[' + bus1 + phsfx + ' ' + bus2 + '.1.0 ' + bus2 + '.0.2]')
            else:
                xff.write(' buses=[' + bus1 + phsfx + ' ' + bus2 + phsfx + ']')
            xff.write('\n');
        xff.close()

    
    # NON-SPLIT-PHASE LOADS
    if 'load' in model:
        redirects.append('Loads.dss')
        loadf = open(modeldir+'/Loads.dss', 'w')
        loadf.write('! Load Definitions \n\n')
        for load in model['load']:
            row = model['load'][load]
            name = str(load)
            bus1 = str(load)
            phqty = count_ph(row['phases'])
            if 'constant_power_A' in row:
                toks = re.split('[\+j]',row['constant_power_A'])
                PA = float(toks[0])
                QA = float(toks[1])
                loadf.write('new load.'+name+'_phA')
                loadf.write(' phases=1')
                if 'connection_type' in row:
                    if row['connection_type'] == 'WYE-GND':
                        loadf.write(' bus1='+bus1+'.1')
                        loadf.write(' conn=wye')
                    if row['connection_type'] == 'DELTA':
                        loadf.write(' bus1='+bus1+'.1.2')
                        loadf.write(' conn=delta')
                else:
                    loadf.write(' bus1='+bus1+'.1')
                    loadf.write(' conn=wye')
                # assuming gld voltage is LL for delta loads and LN for wye loads
                loadf.write(' kv='+'{:.3f}'.format(float(row['nominal_voltage'])/1000))
                loadf.write(' kw='+'{:.3f}'.format(PA/1000))
                loadf.write(' kvar='+'{:.3f}'.format(QA/1000))
                loadf.write('\n')
            if 'constant_power_B' in row:
                toks = re.split('[\+j]',row['constant_power_B'])
                PB = float(toks[0])
                QB = float(toks[1])
                loadf.write('new load.'+name+'_phB')
                loadf.write(' phases=1')
                if 'connection_type' in row:
                    if row['connection_type'] == 'WYE-GND':
                        loadf.write(' bus1='+bus1+'.2')
                        loadf.write(' conn=wye')
                    if row['connection_type'] == 'DELTA':
                        loadf.write(' bus1='+bus1+'.2.3')
                        loadf.write(' conn=delta')
                else:
                    loadf.write(' bus1='+bus1+'.2')
                    loadf.write(' conn=wye')
                # assuming gld voltage is LL for delta loads and LN for wye loads
                loadf.write(' kv='+'{:.3f}'.format(float(row['nominal_voltage'])/1000))
                loadf.write(' kw='+'{:.3f}'.format(PB/1000))
                loadf.write(' kvar='+'{:.3f}'.format(QB/1000))
                loadf.write('\n')
            if 'constant_power_C' in row:
                toks = re.split('[\+j]',row['constant_power_C'])
                PC = float(toks[0])
                QC = float(toks[1])
                loadf.write('new load.'+name+'_phC')
                loadf.write(' phases=1')
                if 'connection_type' in row:
                    if row['connection_type'] == 'WYE-GND':
                        loadf.write(' bus1='+bus1+'.3')
                        loadf.write(' conn=wye')
                    if row['connection_type'] == 'DELTA':
                        loadf.write(' bus1='+bus1+'.2.3')
                        loadf.write(' conn=delta')
                else:
                    loadf.write(' bus1='+bus1+'.3')
                    loadf.write(' conn=wye')
                # assuming gld voltage is LL for delta loads and LN for wye loads
                loadf.write(' kv='+'{:.3f}'.format(float(row['nominal_voltage'])/1000))
                loadf.write(' kw='+'{:.3f}'.format(PC/1000))
                loadf.write(' kvar='+'{:.3f}'.format(QC/1000))
                loadf.write('\n')
    
    
    # TRIPLEX LOADS
    if 'triplex_node' in model: 
        redirects.append('TpxLoads.dss')
        loadf = open(modeldir+'/TpxLoads.dss', 'w')
        loadf.write('! Triplex Load Definitions \n\n')
        for node in model['triplex_node']:
            row = model['triplex_node'][node]
            name = str(node)
            bus1 = str(node)
            if 'power_12' in row:
                toks = re.split('[\+j]',row['power_12'])
                P = float(toks[0])
                Q = float(toks[1])
                # Balanced 240-V load - follow the pattern of IEEE 8500 example distributed with OpenDSS
                loadf.write('new load.'+name+'_240v')
                loadf.write(' phases=2')
                loadf.write(' bus1='+bus1+'.1.2')
                loadf.write(' conn=wye')
                loadf.write(' kv=0.208')
                loadf.write(' kw='+'{:.3f}'.format(P/1000))
                loadf.write(' kvar='+'{:.3f}'.format(Q/1000))
                loadf.write('\n')
            if 'power_1' in row:
                toks = re.split('[\+j]',row['power_1'])
                P = float(toks[0])
                Q = float(toks[1])
                # Unbalanced load on phase 1
                loadf.write('new load.'+name+'_120v1')
                loadf.write(' phases=1')
                loadf.write(' bus1='+bus1+'.1')
                loadf.write(' conn=wye')
                loadf.write(' kv=0.120')
                loadf.write(' kw='+'{:.3f}'.format(P/1000))
                loadf.write(' kvar='+'{:.3f}'.format(Q/1000))
                loadf.write('\n')
            if 'power_2' in row:
                toks = re.split('[\+j]',row['power_2'])
                P = float(toks[0])
                Q = float(toks[1])
                # Unbalanced load on phase 2
                loadf.write('new load.'+name+'_120v2')
                loadf.write(' phases=1')
                loadf.write(' bus1='+bus1+'.2')
                loadf.write(' conn=wye')
                loadf.write(' kv=0.120')
                loadf.write(' kw='+'{:.3f}'.format(P/1000))
                loadf.write(' kvar='+'{:.3f}'.format(Q/1000))
                loadf.write('\n')
        loadf.close()
    
    
    
    # -----------------------------------------------------------------------------
    # Reclosers
    # -----------------------------------------------------------------------------
    if 'recloser' in model:
        redirects.append('Reclosers.dss')
        recloserf = open(modeldir+'/Reclosers.dss', 'w');
        recloserf.write('!Recloser Definitions:\n\n');
        for recloser in model['recloser']:
            row = model['recloser'][recloser]
            name = recloser
            bus1 = str(row['from'])
            bus2 = str(row['to'])
            phsfx = get_phsfx(row['phases'])
            phqty = str(count_ph(row['phases']))
            recloserf.write('new line.' + name      +\
                    ' bus1=' + bus1 + phsfx         +\
                    ' bus2=' + bus2 + phsfx         +\
                    ' phases=' + phqty              +\
                    ' switch=y')
            if row['status'] == 'OPEN':
                recloserf.write(' enabled=false')
            recloserf.write('\n');
        recloserf.close()

    

    # FUSES
    if 'fuse' in model:
        redirects.append('Fuses.dss')
        fusef = open(modeldir+'/Fuses.dss', 'w');
        fusef.write('!Fuse Definitions:\n\n');
        for fuse in model['fuse']:
            row = model['fuse'][fuse]
            name = fuse
            bus1 = str(row['from'])
            bus2 = str(row['to'])
            phsfx = get_phsfx(row['phases'])
            phqty = str(count_ph(row['phases']))
            fusef.write('new line.' + name      +\
                    ' bus1=' + bus1 + phsfx         +\
                    ' bus2=' + bus2 + phsfx         +\
                    ' phases=' + phqty              +\
                    ' switch=y')
            if row['status'] == 'OPEN':
                fusef.write(' enabled=false')
            fusef.write('\n');
        fusef.close()


    
    # REGULATORS
    regnum = 0 # we need to assign a bank to each regulator so they can be collected after DSS==>CIM==>GLD
    if 'regulator' in model:
        redirects.append('Regulators.dss')
        regf = open(modeldir+'/Regulators.dss', 'w');
        regf.write('!Regulator Definitions:\n\n');
        for reg in model['regulator']:
            row = {**model['regulator'][reg],\
                **model['regulator_configuration']\
                [h[model['regulator'][reg]['configuration']]]}
            name = reg
            bus1 = str(row['from'])
            bus2 = str(row['to'])
            phsfx = get_phsfx(row['phases'])
            phqty = str(count_ph(row['phases']))
            numtaps = str(float(row['raise_taps'])+float(row['lower_taps']))
            if 'band_center' in row:
                vbase = str(row['band_center'])
            else:
                vbase = '120'
            kvbase = str(float(vbase)/1000)
            if 'band_width' in row:
                vband = str(row['band_width'])
            else:
                vband = '2'
            maxtap = str(1+float(row['regulation']))
            mintap = str(1-float(row['regulation']))
            if 'time_delay' in row:
                delay = str(row['time_delay'])
            else:
                delay = '30'
            if 'power_transducer_ratio' in row:
                ptratio = str(row['power_transducer_ratio'])
                if 'band_center' not in row:
                    kvbase = str(float(ptratio)*120/1000)
            else:
                ptratio = '1'
            regnum = regnum + 1
            regbank = str(regnum)
            if 'A' in row['phases']:
                regf.write('new transformer.' + name + '_A' +\
                        ' bank=vreg' + regbank              +\
                        ' phases=1'                         +\
                        ' numtaps=' + numtaps               +\
                        ' wdg=1'                            +\
                        ' kva=100000'                       +\
                        ' kv=' + kvbase                     +\
                        ' bus=' + bus1 + '.1'               +\
                        ' wdg=2'                            +\
                        ' kva=100000'                       +\
                        ' kv=' + kvbase                     +\
                        ' bus=' + bus2 + '.1'               +\
                        '\n')
                regf.write('new regcontrol.' + name + '_regA'   +\
                        ' transformer=' + name + '_A'           +\
                        ' winding=2'                            +\
                        ' ptratio=' + ptratio                   +\
                        ' vreg=' + vbase                        +\
                        ' band=' + vband                        +\
                        ' delay=' + delay                       +\
                        '\n')
            if 'B' in row['phases']:
                regf.write('new transformer.' + name + '_B' +\
                        ' bank=vreg' + regbank              +\
                        ' phases=1'                         +\
                        ' numtaps=' + numtaps               +\
                        ' wdg=1'                            +\
                        ' kva=100000'                       +\
                        ' kv=' + kvbase                     +\
                        ' bus=' + bus1 + '.2'               +\
                        ' wdg=2'                            +\
                        ' kva=100000'                       +\
                        ' kv=' + kvbase                     +\
                        ' bus=' + bus2 + '.2'               +\
                        '\n')
                regf.write('new regcontrol.' + name + '_regB'   +\
                        ' transformer=' + name + '_B'           +\
                        ' winding=2'                            +\
                        ' ptratio=' + ptratio                   +\
                        ' vreg=' + vbase                        +\
                        ' band=' + vband                        +\
                        ' delay=' + delay                       +\
                        '\n')
            if 'C' in row['phases']:
                regf.write('new transformer.' + name + '_C' +\
                        ' bank=vreg' + regbank              +\
                        ' phases=1'                         +\
                        ' numtaps=' + numtaps               +\
                        ' wdg=1'                            +\
                        ' kva=100000'                       +\
                        ' kv=' + kvbase                     +\
                        ' bus=' + bus1 + '.3'               +\
                        ' wdg=2'                            +\
                        ' kva=100000'                       +\
                        ' kv=' + kvbase                     +\
                        ' bus=' + bus2 + '.3'               +\
                        '\n')
                regf.write('new regcontrol.' + name + '_regC'   +\
                        ' transformer=' + name + '_C'           +\
                        ' winding=2'                            +\
                        ' ptratio=' + ptratio                   +\
                        ' vreg=' + vbase                        +\
                        ' band=' + vband                        +\
                        ' delay=' + delay                       +\
                        '\n')
    regf.close()

    
    
    # JUMPERS
    # cursor.execute ( "SELECT * FROM networknode")
    # Hash nodes to their parents
    # h = {}
    # for row in cursor.fetchall():
        # node = row['name']
        # if row['parent'] is not None:
            # h[node] = row['parent']
        # else:
            # h[node] = node
    # Rehash nodes to the their oldest ancestor
    # for node in h:
        # tmp = node
        # while tmp != h[tmp]:
            # tmp = h[tmp]
        # h[node] = tmp
    # print(h)

    # Write Jumpers.dss
    redirects.append('Jumpers.dss')
    jumpf = open(modeldir+'/Jumpers.dss','w')
    ctr = 0
    for t in {'node','meter','capacitor','load'}:
        if t in model:
            for o in model[t]:
                if 'parent' in model[t][o]:
                    ctr += 1
                    jname = 'j'+str(ctr)
                    bus1 = str(o)
                    bus2 = str(model[t][o]['parent'])
                    phqty = count_ph(model[t][o]['phases'])
                    phsfx = get_phsfx(model[t][o]['phases'])
                    jumpf.write('new line.' + jname     +\
                            ' phases=' + str(phqty)     +\
                            ' bus1=' + bus1 + phsfx     +\
                            ' bus2=' + bus2 + phsfx     +\
                            ' switch=yes'               +\
                            '\n')
    for t in {'triplex_meter','triplex_node'}:
        if t in model:
            for o in model[t]:
                if 'parent' in model[t][o]:
                    ctr += 1
                    jname = 'j'+str(ctr)
                    bus1 = str(o)
                    bus2 = str(model[t][o]['parent'])
                    jumpf.write('new line.' + jname     +\
                            ' phases=2'                 +\
                            ' bus1=' + bus1 + '.1.2'    +\
                            ' bus2=' + bus2 + '.1.2'    +\
                            ' switch=yes'               +\
                            '\n')
    jumpf.close()


    # SUBSTATION
    sourcef = open(modeldir+'/VSource.dss','w')
    sourcef.write('new circuit.{:s} bus1=sourcebus phases=3 MVAsc3=50000 basekv={:.2f}\n'.format(circuit_name, srcekv))
    sourcef.write('new line.trunk bus1=sourcebus bus2=rootbus phases=3 switch=yes\n')
    sourcef.write('new energymeter.feeder element=line.trunk terminal=1\n')
    feederhead = '' # starting bus as defined by PNNL
    for t in model:
        if t == 'node' or\
                t == 'meter' or\
                t == 'capacitor' or\
                t == 'load' or\
                t == 'triplex_meter' or\
                t == 'substation' or\
                t == 'triplex_node':
            for o in model[t]:
                if 'bustype' in model[t][o]:
                    if model[t][o]['bustype'] == 'SWING':
                        # Connect gld swing bus to the source bus
                        feederhead = str(o)
                        sourcef.write('new transformer.source_'+str(o))
                        sourcef.write(' phases=3')
                        sourcef.write(' %noloadloss=0.0001')
                        sourcef.write(' %imag=0.0001')
                        sourcef.write(' %loadloss=0.0001')
                        sourcef.write(' xhl=0.0001')
                        sourcef.write(' windings=2')
                        sourcef.write(' wdg=1 kva=100000 kv={:.2f}'.format(srcekv))
                        sourcef.write(' bus=rootbus')
                        sourcef.write(' wdg=2 kva=100000 kv='+\
                            '{:.3f}'.format(float(model[t][o]['nominal_voltage'])/1000*1.73205))
                        kvbases.update([round(float(\
                            model[t][o]['nominal_voltage'])/1000*1.73205,2)])
                        sourcef.write(' bus='+feederhead)
                        sourcef.write('\n')
    sourcef.close()
    
    
    
    # COORDINATES
    # coordinates from visualizations by Michael A. Cohen
    coordh = {}
    if len(dotfile) > 0:
        vf = open(dotfile)
        line = vf.readline()
        while line is not '':
            m = re.search(r'^\s*(\S+)\s+\[',line)
            if m:
                # Found an object
                o = m.group(1)
                coordh[o] = {}
                coordh[o]['x'] = None
                coordh[o]['y'] = None
                # look for coordinates
                while not re.search(']',line):
                    line = vf.readline()
                    n = re.search(r'pos\s*=\s*"\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*"',line)
                    if n:
                        # print('\tx is '+n.group(1))
                        # print('\ty is '+n.group(2))
                        coordh[o]['x'] = n.group(1)
                        coordh[o]['y'] = n.group(2)
                if coordh[o]['x'] is None or coordh[o]['y'] is None:
                    # object had no coordinates or coordinates were invalid
                    # print('No valid coordinates for '+o)
                    del coordh[o]
            line = vf.readline()
        vf.close()
    coordf = open(modeldir+'/Buscoords.csv','w')
    for t in {'node','meter','capacitor','load','triplex_meter','triplex_node'}:
        if t in model:
            for node in model[t]:
                m = re.search(r'_(\w+)_(\d+)',node)
                if m:
                    nde = m.group(1)+m.group(2)
                    if nde in coordh:
                        xde = coordh[nde]['x']
                        yde = coordh[nde]['y']
                        yhead = float(yde)
                    else:
                        xde = '0'
                        yde = '0'
#                        print('No coordinates for '+node)
                    coordf.write(node+','+xde+','+yde+'\n')
                    if node == feederhead:
                        yhead = float (yde)
                        coordf.write('rootbus,'+xde+',{:.2f}\n'.format(yhead-1))
                        coordf.write('sourcebus,'+xde+',{:.2f}\n'.format(yhead-2))
    coordf.close()
    
    # -----------------------------------------------------------------------------
    # Master File
    # -----------------------------------------------------------------------------
    masterf = open(modeldir+'/Master.dss','w')
    masterf.write('clear\n')
    masterf.write('redirect VSource.dss\n')
    for f in redirects:
        masterf.write('redirect '+f+'\n')
    # Voltage bases should be built dynamically
    masterf.write('set voltagebases="{:s}"\n'.format(vbase_str))
    # ctr = 0
    # for kvbase in kvbases:
        # ctr += 1
        # masterf.write(str(kvbase))
        # print(kvbase)
        # masterf.write(',' if ctr < len(# kvbases) else '"\n')
    masterf.write('calcv\n')
    masterf.write('buscoords Buscoords.csv\n')
    print ('batchedit load..* model=5 // 1=P, 2=Z, 5=I', file=masterf)
    print ('AddBusMarker Bus={:s} code=34 color=Green size=5'.format (feederhead), file=masterf)
    print ('set markcapacitors=yes', file=masterf)
    print ('set capmarkercode=38', file=masterf)
    print ('set capmarkersize=1', file=masterf)
    print ('set markfuses=no', file=masterf)
    print ('set fusemarkercode=12', file=masterf)
    print ('set markreclosers=yes', file=masterf)
    print ('set reclosermarkercode=26', file=masterf)
    print ('set reclosermarkersize=2', file=masterf)
    print ('set markregulators=yes', file=masterf)
    print ('set regmarkercode=34', file=masterf)
    print ('set regmarkersize=1', file=masterf)
    print ('set markswitches=no', file=masterf)
    print ('set switchmarkercode=12', file=masterf)
    print ('set marktransformers=no', file=masterf)
    print ('set transmarkercode=25', file=masterf)
    print ('set transmarkersize=1', file=masterf)
    print ('set DaisySize=1.0', file=masterf)
    masterf.close()

# ----------------------------------
# Process all of the taxonomy models
#-----------------------------------

def process_taxonomy():
    vbase_str = '100,34.5,24.9,22.9,13.8,12.47,0.48,0.208'
    for ifn in glob.glob("base_taxonomy/new*.glm"):
        wd = os.getcwd()
        if sys.platform == 'win32':
            m = re.match(r'base_taxonomy\\(.+).glm',ifn)
        else:
            m = re.match(r'base_taxonomy/(.+).glm',ifn)
        if m:
            modelname = re.sub('[-\.]','_',m.group(1))
        else:
            modelname = 'default'
        if 'GC-12.47-1' in ifn:
            taxname = 'GC-12.47-1'
        else:
            taxname = 'default'
        n = re.search(r'(R\d-\d\d\.\d\d-\d).glm',ifn)
        if n:
            taxname = n.group(1)
        print("Processing "+taxname+"... "+ifn)
        inf = open(ifn,'r')
        if sys.platform == 'win32':
            modeldir = wd + '\\' + modelname
        else:
            modeldir = wd + '/' + modelname
        if modelname not in glob.glob('*'):
            os.system('mkdir '+modeldir)

        dotfile = wd+'/visualizations/'+taxname+'.dot'
        process_one_model (inf, modeldir, dotfile, vbase_str, 'sourceckt')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        fp = open(fname, 'r')
        if len(sys.argv) > 2:
            vbase_str = sys.argv[2].strip('"')
        else:
            vbase_str = '12.47,0.48,0.208'
        if len(sys.argv) > 3:
            ckt_name = sys.argv[3]
        else:
            ckt_name = 'substation'
        process_one_model (fp, '.', '', vbase_str, ckt_name)
        fp.close()
    else:
        process_taxonomy()





