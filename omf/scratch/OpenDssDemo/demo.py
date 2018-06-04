import opendssdirect as dss
import types
import inspect

dss.run_command('Redirect ./short_circuit.dss')
dss.run_command('Solve ./short_circuit.dss')
print dss.utils.vsources_to_dataframe()

'''
print dss.utils.capacitors_to_dataframe()
print dss.utils.fuses_to_dataframe()
print dss.utils.generators_to_dataframe()
print dss.utils.isource_to_dataframe()
print dss.utils.lines_to_dataframe()
print dss.utils.loads_to_dataframe()
print dss.utils.loadshape_to_dataframe()
print dss.utils.meters_to_dataframe()
print dss.utils.monitors_to_dataframe()
print dss.utils.pvsystems_to_dataframe()
print dss.utils.reclosers_to_dataframe()
print dss.utils.regcontrols_to_dataframe()
print dss.utils.relays_to_dataframe()
print dss.utils.sensors_to_dataframe()
print dss.utils.transformers_to_dataframe()
print dss.utils.xycurves_to_dataframe()
'''

