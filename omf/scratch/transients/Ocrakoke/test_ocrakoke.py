#!python3
#
# Copyright (C) 2014-2015 Julius Susanto. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""
PYPOWER-Dynamics
Classical Stability Test

"""
# Dynamic model classes
from pydyn.controller import controller
from pydyn.ext_grid import ext_grid
from pydyn.sym_order6a import sym_order6a
from pydyn.sym_order6b import sym_order6b
from pydyn.sym_order4 import sym_order4

# Simulation modules
from pydyn.events import events
from pydyn.recorder import recorder
from pydyn.run_sim import run_sim

# External modules
from pypower.loadcase import loadcase
import matplotlib.pyplot as plt
import numpy as np
from omf.scratch.transients import montefaults as mf
    
if __name__ == '__main__':
    
    #########
    # SETUP #
    #########
    
    print('----------------------------------------')
    print('PYPOWER-Dynamics - Classical 9 Bus Test')
    print('----------------------------------------')

    # Load PYPOWER case
    ppc = loadcase('ocrakoke.py')
    
    # Program options
    dynopt = {}
    dynopt['h'] = 0.001               # step length (s)
    dynopt['t_sim'] = 200.0             # simulation time (s)
    dynopt['max_err'] = 1e-6          # Maximum error in network iteration (voltage mismatches)
    dynopt['max_iter'] = 25           # Maximum number of network iterations
    dynopt['verbose'] = False         # option for verbose messages
    dynopt['fn'] = 60                 # Nominal system frequency (Hz)
    
    # Integrator option
    dynopt['iopt'] = 'mod_euler'
    #dynopt['iopt'] = 'runge_kutta'
    
    # Create dynamic model objects
    # oCtrl = controller('avr.dyn', dynopt)
    G1 = ext_grid('GEN1', 0, 0.0608, 23.64, dynopt)
    G2 = ext_grid('GEN2', 1, 0.1198, 6.01, dynopt)
    # G3 = ext_grid('GEN3', 2, 0.1813, 3.01, dynopt)
    # B1 = sym_order6b('B1.mach', dynopt)
    # B2 = sym_order6b('B2.mach', dynopt)
    # B3 = sym_order6b('B3.mach', dynopt)
    # B4 = sym_order6b('B4.mach', dynopt)
    
    # Create dictionary of elements
    elements = {}
    # elements[oCtrl.id] = oCtrl
    elements[G1.id] = G1
    elements[G2.id] = G2
    # elements[G3.id] = G3
    # elements[B1.id] = B1
    # elements[B2.id] = B2
    # elements[B3.id] = B3
    # elements[B4.id] = B4

    # Create event stack
    oEvents = events('events.evnt')
    # event1 = [10.3, 'LOAD', 2, -10, -10]
    # event2 = [10.35, 'LOAD', 2, -10, -10]
    # event3 = [1.38, 'LOAD',3, -100, -100]

    # oEvents.event_stack.append(event1)
    # oEvents.event_stack.append(event2)
    # oEvents.event_stack.append(event3)
    # oEvents = mf.addRandomEvents(ppc, oEvents, 5, dynopt['h'], dynopt['t_sim'], 0.05, 0.03)
    
    # Create recorder object
    oRecord = recorder('recorder.rcd')
    
    # Run simulation
    oRecord = run_sim(ppc,elements,dynopt,oEvents,oRecord)
    
    # # Calculate relative rotor angles
    # rel_delta01 = np.array(oRecord.results['GEN1:delta'])
    # rel_delta02 = np.array(oRecord.results['BUS1:delta'])
    # rel_delta11 = np.array(oRecord.results['GEN2:delta'])
    # rel_delta12 = np.array(oRecord.results['BUS2:delta'])
    # rel_delta21 = np.array(oRecord.results['GEN3:delta'])
    # rel_delta22 = np.array(oRecord.results['BUS3:delta'])
    # rel_delta31 = np.array(oRecord.results['GEN1:P'])
    # rel_delta32 = np.array(oRecord.results['BUS1:P'])
    # rel_delta42 = np.array(oRecord.results['BUS2:P'])
    # rel_delta52 = np.array(oRecord.results['BUS3:P'])
    # # Plot variables
    # plt.plot(oRecord.t_axis,rel_delta01 * 180 / np.pi, 'r-', oRecord.t_axis, rel_delta11 *180 / np.pi, 'b-', oRecord.t_axis, rel_delta21 *180 / np.pi, 'g-')
    # plt.xlabel('Time (s)')
    # plt.ylabel('Rotor Angles')
    # plt.show()
    # plt.plot(oRecord.t_axis,rel_delta02 * 180 / np.pi, 'r-', oRecord.t_axis, rel_delta12 *180 / np.pi, 'b-', oRecord.t_axis, rel_delta22 *180 / np.pi, 'g-')
    # plt.xlabel('Time (s)')
    # plt.ylabel('Rotor Angles')
    # plt.show()
    # plt.plot(oRecord.t_axis,rel_delta31)
    # plt.ylabel('Power of GEN1')
    # plt.show()
    # plt.plot(oRecord.t_axis,rel_delta32)
    # plt.ylabel('Power of BUS1')
    # plt.show()
    # plt.plot(oRecord.t_axis,rel_delta42)
    # plt.ylabel('Power of BUS2')
    # plt.show()
    # plt.plot(oRecord.t_axis,rel_delta52)
    # plt.ylabel('Power of BUS3')
    # plt.show()

    fig, axs = plt.subplots(3, 2)
    axs[0, 0].plot(oRecord.t_axis, np.array(oRecord.results['GEN1:delta']) * 180 / np.pi)
    axs[0, 0].set_title('Rotor Angle (GEN1)')
    axs[0, 0].set(ylabel='radians')
    axs[0, 1].plot(oRecord.t_axis, np.array(oRecord.results['GEN2:delta']) * 180 / np.pi, 'tab:orange')
    axs[0, 1].set_title('Rotor Angle (GEN2)')
    axs[0, 1].set(ylabel='radians')
    # axs[0, 2].plot(oRecord.t_axis, np.array(oRecord.results['GEN3:delta']) * 180 / np.pi, 'tab:green')
    # axs[0, 2].set_title('Rotor Angle (GEN3)')
    # axs[0, 2].set(ylabel='radians')
    axs[1, 0].plot(oRecord.t_axis, np.array(oRecord.results['GEN1:P']) * 100)
    axs[1, 0].set_title('Power (GEN1)')
    axs[1, 0].set(ylabel='MW')
    axs[1, 1].plot(oRecord.t_axis, np.array(oRecord.results['GEN2:P']) * 100, 'tab:orange')
    axs[1, 1].set_title('Power (GEN2)')
    axs[1, 1].set(ylabel='MW')
    # axs[1, 2].plot(oRecord.t_axis, np.array(oRecord.results['GEN3:P']) * 100, 'tab:green')
    # axs[1, 2].set_title('Power (GEN3)')
    # axs[1, 2].set(ylabel='MW')
    axs[2, 0].plot(oRecord.t_axis, np.array(oRecord.results['GEN1:omega']) * 180 / np.pi)
    axs[2, 0].set_title('Frequency (GEN1)')
    axs[2, 0].set(ylabel='Hz')
    axs[2, 1].plot(oRecord.t_axis, np.array(oRecord.results['GEN2:omega']) * 180 / np.pi, 'tab:orange')
    axs[2, 1].set_title('Frequency (GEN2)')
    axs[2, 1].set(ylabel='Hz')
    # axs[2, 2].plot(oRecord.t_axis, np.array(oRecord.results['GEN3:omega']) * 180 / np.pi, 'tab:green')
    # axs[2, 2].set_title('Frequency (GEN3)')
    # axs[2, 2].set(ylabel='Hz')
    for ax in axs.flat:
        ax.set(xlabel='time (s)')

    # Hide x labels and tick labels for top plots and y ticks for right plots.
    plt.show()
    
    # Write recorded variables to output file
    oRecord.write_output('output.csv')