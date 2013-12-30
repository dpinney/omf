import convert_cyme_model
import Milsoft_GridLAB_D_Feeder_Generation
import feeder

def main():
	
	## Inputs
	# conversion
	network_db = 'Duke_2407_Net.mdb'
	equipment_db = 'Duke_2407_Eq.mdb'
	feeder_id = None
	conductors_csv = 'duke_conductor_data.csv'
	# population
	case_flag = 0 # base case
	directory = ""
	calibration_config = None # use defaults
	feeder_config = None # use defaults (TODO: We don't actually have functionality in place for using custom feeder configuration (set point bins, etc))
	
	# Convert from CYME to GridLAB-D objects represented in a python dictionary (base GLM)
	gldDict = convert_cyme_model.convert_cyme_model(network_db, equipment_db, feeder_id, conductors_csv)
	print('conversion complete')
	# Populate base GLM
	final_dict, last_key = Milsoft_GridLAB_D_Feeder_Generation.GLD_Feeder(gldDict,case_flag,directory,calibration_config,feeder_config)
	print('population complete')
	# Write .glm file
	glm_string = feeder.sortedWrite(final_dict)
	file = open('output_populated.glm', 'w')
	file.write(glm_string)
	file.close()
	
if __name__ == '__main__':
	main()