import opendssdirect as dss
import pandas as pd

dss.run_command("Redirect ./short_circuit.dss")
dss.run_command('Solve')
#print dss.Circuit.YCurrents()
print dss.Meters.CalcCurrent()
print dss.Isource.AllNames()
print dss.Fuses.RatedCurrent()
print dss.CktElement.CplxSeqCurrents()
print dss.CktElement.Currents()
print dss.CktElement.CurrentsMagAng()
print dss.CktElement.Residuals()
print dss.CktElement.SeqCurrents()
#print dss.Sensors.Currents()
