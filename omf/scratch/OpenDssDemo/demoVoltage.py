import opendssdirect as dss
import networkx as nx
import matplotlib.pyplot as plt

def calculateGraph():

def plotGraph():


if __name__ == "__main__":
  get_ipython().magic('matplotlib inline')

  dss.run_command('Redirect ./short_circuit.dss')
  dss.run_command("New EnergyMeter.Main Line.650632 1")
  dss.run_command('Solve ./short_circuit.dss')

  lines = dss.utils.lines_to_dataframe()


