# This function runs a .bat file that job handles multiple GridLAB-D files

import subprocess
import os
import stat

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

def create_shell_script(glm_folder):
	script = '{:s}/gld_job_handler.sh'.format(glm_folder)
	shell_script = open('{:s}/gld_job_handler.sh'.format(glm_folder),'w')
	shell_script.write('#i/bin/bash\n')
	shell_script.write('gridlabd -T 0 --job')
	shell_script.close()
	st = os.stat(script)
	os.chmod(script, st.st_mode | stat.S_IEXEC)
	return None

def run_shell_script(glm_folder):
	p = subprocess.Popen('{:s}/gld_job_handler.sh'.format(glm_folder), shell=True, cwd=glm_folder)
	stdout, stderr = p.communicate()
	return (stdout,stderr)

def main():
	#tests here
	glm_folder = '/home/afisher/OMFwork'
	create_shell_script(glm_folder)
	stdout, stderr = run_shell_script(glm_folder)
	
if __name__ ==  '__main__':
	main()