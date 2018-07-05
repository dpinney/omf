import opendssdirect as dss

dss.run_command('Redirect IEEE37.dss')
dss.run_command('Export Circuit circuits.csv')
