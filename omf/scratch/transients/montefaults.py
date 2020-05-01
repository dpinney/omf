# Dynamic model classes
from pydyn.controller import controller
from pydyn.sym_order6a import sym_order6a
from pydyn.sym_order6b import sym_order6b
from pydyn.sym_order4 import sym_order4
from pydyn.ext_grid import ext_grid

# Simulation modules
from pydyn.events import events
from pydyn.recorder import recorder
from pydyn.run_sim import run_sim

# External modules
from pypower.loadcase import loadcase
import matplotlib.pyplot as plt
import numpy as np
import random
import scipy
import scipy.stats
import math

def addRandomEvents(ppc, oEvents, n, stepLength, simTime, meanDuration, stdDuration):
    busIndex = list(ppc.keys()).index('bus')
    buses = list(ppc.values())[busIndex]
    numberOfBuses = len(buses)

    index = 0
    while index < n:
        busIndex = random.randint(0,numberOfBuses-2)
        newBus = str(int(buses[busIndex][0]))
        roundTo = abs(int(math.log10(stepLength)))
        newFaultStart = round(random.uniform(0.0, simTime), roundTo)
        newDuration = -1
        while newDuration < 0:
            newDuration = round(scipy.stats.norm.rvs(meanDuration, stdDuration), roundTo)

        event1 = [newFaultStart, 'FAULT', newBus, '0', '0']
        event2 = [round(newFaultStart + newDuration, roundTo), 'CLEAR_FAULT', newBus]
        oEvents.event_stack.append(event1)
        oEvents.event_stack.append(event2)

        index += 1

    oEvents.event_stack.sort()

    return oEvents

# def changeLoads():
