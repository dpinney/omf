from omf import feeder

feed = feeder.parse('./Taxonomy_Feeders-solar/GC-12.47-1-solarAdd.glm')
feeder.attachRecorders(feed, 'Inverter', 'object', 'inverter')

output = open('./taxo_temp/GC-12.47-1-solarAdd.glm', 'w')
output.write(feeder.write(feed))
output.close()

# phaseA_V_Out, phaseB_V_Out, phaseC_V_Out, phaseA_I_Out, phaseB_I_Out, phaseC_I_Out;