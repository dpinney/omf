import omf.cosim

glw = omf.cosim.GridLabWorld('6267', 'localhost', 'GC-solarAdd.glm', '2000-01-01 0:00:00')
glw.start()
print (glw.readClock())
# Changing solar gen status.
print (glw.read('test_solar', 'generator_status'))
glw.write('test_solar','generator_status', 'OFFLINE')
print ('Switched off solar')
print (glw.read('test_solar', 'generator_status'))
# Changing reactive power output.
print (glw.read('test_solar_inverter', 'Q_Out'))
glw.write('test_solar_inverter','Q_Out', '1000')
print ('Change Q_Out')
print (glw.read('test_solar_inverter', 'Q_Out'))
#glw.waitUntil('2000-01-01 0:30:00')
#print ('Stepped ahead 12 hours')
print (glw.readClock())
glw.resume()
print (glw.readClock())
glw.shutdown()