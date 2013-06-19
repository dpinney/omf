# About the inputs:
#import milToGridlab  
import Milsoft_GridLAB_D_Feeder_Generation
import calibrateFeeder
import processSCADA #TODO: write this function
import feeder
import AddTapeObjects
#import writeFeederConfig #TODO: future work (after June 1 deadline)

# MilSoft model ( milsoft = [stdPath, seqPath])
# Case Flag
# Feeder Info (region, ratings, etc) TBD
# SCADA Data
# feeder configuration file (user may input feeder configuration file as created by a previous calibration attempt on this feeder)
# feeder calibration file (user may input calibration file as created by a previous calibration attempt on this feeder)
# user_flag_to_calibrate (user may set to 0 to indicate they don't want to calibrate, just want general popualted model)

def createFeederDirectory(feederID):
	# check that this feederID is unique
	# create folder with all the fixin's for this model to be populated and/or calibrated and ran in GLD
	# TODO: directory needs to include subdirectory 'winners' for storing the best .glms from each calibration round
	# TODO: anything with suffix 'glm' might be deleted during calibration since we cleanup unecessary file between rounds. Put schedules, other .glms, etc into a subdirectory if we don't want them deleted. 
	directory = 'C:\\Users\\d3y051\\Documents\\NRECA_feeder_calibration_2-2013\\Calibration\\repository\\Feeder_Test'
	return directory
	
def OMFmain(milsoft, feeder_info, scada, case_flag, feeder_config, calibration_config, user_flag_to_calibrate=1):

	if milsoft is None:
		print ("Please input a MilSoft model to convert!")
		# error
		return
	else:
		internal_flag_to_calibrate = 0
		if feeder_config is None:
			if feeder_info is None:
				pass  # We'll use defaults.
			else:
				# use whatever feeder_info is to write a new feeder_config file that will populate Configuration.py appropriatly.
				feeder_config = writeFeederConfig(feeder_info)  #TODO: This function is in the future. 
		else:
			pass
			# We should check that this file is a valid feeder_config file for use inside Configuration.py. This is important if it's coming from the user incase they made change to the file that aren't compatible with our format. 
		if calibration_config is None:
			if scada is None:
				pass  # Well, we can't do any calibration but we can still pump out a populated model by using defaults.
			else:
				internal_flag_to_calibrate = 1
				days, SCADA = processSCADA.getValues(scada)
		else:
			pass
			# We'll check that this file is a valid calibration_config file for use inside Configuration.py. This is important if it's coming from the user incase they made change to the file that aren't compatible with our format.
			# This might be where we can find out if this is the final calibration file or if we're starting mid-calibration. To do this maybe:
			#  a. We could have another input to the script that is a flag indicating "yes, this is calibrated" or "no, this isn't finished yet".
			#  b. We could just run the script using this calbiration_config file and let the script determine whether it's calibrated -- this might take too long though. 
			#  c. There could be a flag within the calibration_config file that was set when it was previously determined to be the "best".
		
		# Create base .glm dictionary from milsoft model 
	
		# stdPath, seqPath = milsoft[0], milsoft[1]
		# outGlm = milToGridlab.convert(stdPath,seqPath)
		# directory = createFeederDirectory(milsoft)
		
		# testing with pre-made dictionary
		outGLM = milsoft
		directory = createFeederDirectory(None)
		
		if internal_flag_to_calibrate == 1 and user_flag_to_calibrate == 1:  # The user must want to calibrate (user_flag_to_calibrate = 1) and we must have SCADA input (internal_flag_to_calibrate = 1).
			# Send base .glm dictionary to calibration function
			final_calib_file, final_dict = calibrateFeeder.calibrateFeeder(outGLM, days, SCADA, case_flag,feeder_config, calibration_config, directory)
		else:
			# Populate the feeder. 
			print ("Either the user selected not to calibrate this feeder, the SCADA was not input, or this feeder has already been calibrated.")
			final_dict, last_key = Milsoft_GridLAB_D_Feeder_Generation.GLD_Feeder(outGLM,case_flag,calibration_config,feeder_config)
		#AddTapeObjects
		filename = 'test_feeder'
		if final_dict is not None:
			AddTapeObjects.add_recorders(final_dict,None,last_key,None,1,0,filename,None,0,0)
		
			#TODO: Turn final_dict into a .glm and return it to the user. 
			glmstring = feeder.sortedWrite(final_dict)
		
			file = open(directory+'\\'+filename+'.glm', 'w')
			file.write(glmstring)
			file.close()
		else:
			pass
		
def main():
	# test run with pre-made dictionary simuating output from milToGridlab.py. All other parameters are None. Note that SCADA input just needs to be not None for this test-- the values are imput directily into processSCADA.py rather than actually being taken from a file right now.
	glm_object_dict = {}
	glm_object_dict[0] = {'object' : 'overhead_line_conductor',
						  'name' : 'ohlc_100',
						  'geometric_mean_radius' : '0.0244',
						  'resistance' : '0.306'}

	glm_object_dict[1] = {'object' : 'overhead_line_conductor',
						  'name' : 'ohlc_101',
						  'geometric_mean_radius' : '0.00814',
						  'resistance' : '0.592'}

	glm_object_dict[2] = {'object' : 'line_spacing',
						  'name' : 'ls_200',
						  'distance_AB' : '2.5',
						  'distance_BC' : '4.5',
						  'distance_AC' : '7.0',
						  'distance_AN' : '5.656854',
						  'distance_BN' : '4.272002',
						  'distance_CN' : '5.0'}

	glm_object_dict[3] = {'object' : 'line_configuration',
						  'name' : 'lc_300',
						  'conductor_A' : 'ohlc_100',
						  'conductor_B' : 'ohlc_100',
						  'conductor_C' : 'ohlc_100',
						  'conductor_N' : 'ohlc_101',
						  'spacing' : 'ls_200'}

	glm_object_dict[4] = {'object' : 'transformer_configuration',
						  'name' : 'tc_400',
						  'connect_type' : '1',
						  'power_rating' : '1666.7',
						  'powerA_rating' : '666.7',
						  'powerB_rating' : '500',
						  'powerC_rating' : '500',
						  'primary_voltage' : '12470',
						  'secondary_voltage' : '4160',
						  'resistance' : '0.01',
						  'reactance' : '0.06'}

	glm_object_dict[5] = {'object' : 'transformer_configuration',
						  'name' : 'SPCT_config_A_500k',
						  'connect_type' : 'SINGLE_PHASE_CENTER_TAPPED',
						  'install_type' : 'PADMOUNT',
						  'primary_voltage' : '2400',
						  'secondary_voltage' : '120',
						  'power_rating' : '500',
						  'powerA_rating' : '500',
						  'impedance' : '0.015+0.0675j'}

	glm_object_dict[6] = {'object' : 'transformer_configuration',
						  'name' : 'SPCT_config_B_500k',
						  'connect_type' : 'SINGLE_PHASE_CENTER_TAPPED',
						  'install_type' : 'PADMOUNT',
						  'primary_voltage' : '2400',
						  'secondary_voltage' : '120',
						  'power_rating' : '500',
						  'powerB_rating' : '500',
						  'impedance' : '0.015+0.0675j'}

	glm_object_dict[7] = {'object' : 'transformer_configuration',
						  'name' : 'SPCT_config_C_667k',
						  'connect_type' : 'SINGLE_PHASE_CENTER_TAPPED',
						  'install_type' : 'PADMOUNT',
						  'primary_voltage' : '2400',
						  'secondary_voltage' : '120',
						  'power_rating' : '666.7',
						  'powerC_rating' : '666.7',
						  'impedance' : '0.015+0.0675j'}

	glm_object_dict[8] = {'object' : 'node',
						  'name' : 'node1',
						  'phases' : 'ABCN',
                          'bustype' : 'SWING',
						  'voltage_A' : '+7199.558+0.000j',
						  'voltage_B' : '-3599.779-6235.000j',
						  'voltage_C' : '-3599.779+6235.000j',
						  'nominal_voltage' : '7200'}

	glm_object_dict[9] = {'object' : 'overhead_line',
						  'name' : 'oh_12',
						  'phases' : 'ABCN',
						  'from' : 'node1',
						  'to' : 'node2',
						  'length' : '2000',
						  'configuration' : 'lc_300'}

	glm_object_dict[10] = {'object' : 'node',
						  'name' : 'node2',
						  'phases' : 'ABCN',
						  'voltage_A' : '+7199.558+0.000j',
						  'voltage_B' : '-3599.779-6235.000j',
						  'voltage_C' : '-3599.779+6235.000j',
						  'nominal_voltage' : '7200'}

	glm_object_dict[11] = {'object' : 'transformer',
						  'name' : 't_23',
						  'phases' : 'ABCN',
						  'from' : 'node2',
						  'to' : 'node3',
						  'configuration' : 'tc_400'}

	glm_object_dict[12] = {'object' : 'node',
						  'name' : 'node3',
						  'phases' : 'ABCN',
						  'voltage_A' : '+2401.777+0.000j',
						  'voltage_B' : '-1200.889-2080.000j',
						  'voltage_C' : '-1200.889+2080.000j',
						  'nominal_voltage' : '2400'}

	glm_object_dict[13] = {'object' : 'overhead_line',
						  'name' : 'oh_34',
						  'phases' : 'ABCN',
						  'from' : 'node3',
						  'to' : 'node4',
						  'length' : '2500',
						  'configuration' : 'lc_300'}

	glm_object_dict[14] = {'object' : 'node',
						  'name' : 'node4',
						  'phases' : 'ABCN',
						  'voltage_A' : '+2401.777+0.000j',
						  'voltage_B' : '-1200.889-2080.000j',
						  'voltage_C' : '-1200.889+2080.000j',
						  'nominal_voltage' : '2400'}

	glm_object_dict[15] = {'object' : 'transformer',
						  'name' : 'SPCT_A_n4-tn4',
						  'phases' : 'AS',
						  'from' : 'node4',
						  'to' : 'tn4A',
						  'configuration' : 'SPCT_config_A_500k'}

	glm_object_dict[16] = {'object' : 'transformer',
						  'name' : 'SPCT_B_n4-tn4',
						  'phases' : 'BS',
						  'from' : 'node4',
						  'to' : 'tn4B',
						  'configuration' : 'SPCT_config_B_500k'}

	glm_object_dict[17] = {'object' : 'transformer',
						  'name' : 'SPCT_C_n4-tn4',
						  'phases' : 'CS',
						  'from' : 'node4',
						  'to' : 'tn4C',
						  'configuration' : 'SPCT_config_C_667k'}

	glm_object_dict[18] = {'object' : 'triplex_node',
						  'name' : 'tn4A',
						  'phases' : 'AS',
						  'power_12' : '318750.000+197544.508j',
						  'nominal_voltage' : '120'}

	glm_object_dict[19] = {'object' : 'triplex_node',
						  'name' : 'tn4B',
						  'phases' : 'BS',
						  'power_12' : '450000.000+217945.947j',
						  'nominal_voltage' : '120'}

	glm_object_dict[20] = {'object' : 'triplex_node',
						  'name' : 'tn4C',
						  'phases' : 'CS',
						  'power_12' : '593750.000+195156.187j',
						  'nominal_voltage' : '120'}

	milsoft = glm_object_dict
	feeder_info = None # place holder for future feeder information input from the user. 
	scada = 'make_believe_scada_file.xlsx' # place holder for file with scada that will be processed for certain values. 
	case_flag = 0 # base case, do not put None
	feeder_config = None # only used in the case that the user already has a feeder configuration .py file that works (i.e. they've calibrated feeder  or at least part of it)
	calibration_config = None # same as for feeder_config
	
	OMFmain(milsoft, feeder_info, scada, case_flag, feeder_config, calibration_config,1) 
if __name__ ==  '__main__':
	main();