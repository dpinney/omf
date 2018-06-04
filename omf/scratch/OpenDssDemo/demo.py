import opendssdirect as dss
import types
import inspect

dss.run_command('Redirect ./short_circuit.dss')
dss.run_command('Solve ./short_circuit.dss')
print dss.utils.vsources_to_dataframe()

#dss.class_to_dataframe('Voltage')
