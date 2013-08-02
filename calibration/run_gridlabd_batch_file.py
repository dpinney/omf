# This function runs a .bat file that job handles multiple GridLAB-D files

import subprocess
#C:\Projects\GridLAB-D_Builds\trunk\test\input\batch test\13_node_fault2.glm
def create_batch_file(glm_folder,batch_name):
	batch_file = open('{:s}'.format(batch_name),'w')
	batch_file.write('gridlabd.exe -T 0 --job\n')
	#batch_file.write('pause\n')
	batch_file.close()
	return None

def run_batch_file(glm_folder,batch_name):
	p = subprocess.Popen('{:s}'.format(batch_name),cwd=glm_folder)
	code = p.wait()
	#print(code)
	return None
	
def main():
	#tests here
	glm_folder = 'C:\\Projects\\GridLAB-D_Builds\\trunk\\test\\input\\batch_test'
	batch_name = 'C:\\Projects\\GridLAB-D_Builds\\trunk\\test\\input\\batch_test\\calibration_batch_file.bat'
	create_batch_file(glm_folder,batch_name)
	run_batch_file(batch_name)
	
if __name__ ==  '__main__':
	main()
