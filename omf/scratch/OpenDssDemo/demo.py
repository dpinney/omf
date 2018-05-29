import opendssdirect as dss
import types
import inspect

for name, module in inspect.getmembers(dss):
    if isinstance(module, types.ModuleType) and not name.startswith('_'):
        print 'dss.{%s}' % name


# All buses.

for bus in dss.Circuit.AllBusNames():
  print bus

# Pandas interface.
'''
dss.utils.loads_to_dataframe()
dss.utils.transformers_to_dataframe()
dss.utils.capacitors_to_dataframe()
dss.utils.fuses_to_dataframe()
dss.utils.generators_to_dataframe()
dss.utils.isource_to_dataframe()
dss.utils.lines_to_dataframe()
dss.utils.loads_to_dataframe()
dss.utils.loadshape_to_dataframe()
dss.utils.meters_to_dataframe()
dss.utils.monitors_to_dataframe()
dss.utils.pvsystems_to_dataframe()
dss.utils.reclosers_to_dataframe()
dss.utils.regcontrols_to_dataframe()
dss.utils.relays_to_dataframe()
dss.utils.sensors_to_dataframe()
dss.utils.transformers_to_dataframe()
dss.utils.vsources_to_dataframe()
dss.utils.xycurves_to_dataframe()
'''

dss.run_command('Redirect IEEE123Master.dss')
dss.run_command('Compile IEEE123Master.dss') 

dss.run_command(
    "New Storage.{bus_name} Bus1={bus_name} phases=1 kV=2.2 kWRated={rating} kWhRated={kwh_rating} kWhStored={initial_state} %IdlingkW=0 %reserve=0 %EffCharge=100 %EffDischarge=100 State=CHARGING".format(
    bus_name='675',
    rating=20,
    kwh_rating=20,
    initial_state=20
    ))


dss.run_command(
    "New Storage.{bus_name} Bus1={bus_name} phases=1 kV=2.2 kWRated={rating} kWhRated={kwh_rating} kWhStored={initial_state} %IdlingkW=0 %reserve=0 %EffCharge=100 %EffDischarge=100 State=CHARGING".format(
    bus_name='611',
    rating=20,
    kwh_rating=20,
    initial_state=20
    ))

dss.run_command('Solve');

print dss.utils.class_to_dataframe('Storage')
