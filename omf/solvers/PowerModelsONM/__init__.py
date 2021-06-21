import os, platform, subprocess

thisDir = os.path.abspath(os.path.dirname(__file__))

def check_instantiated():
	''' Check whether ONM was previously instantiated and working. '''
	return os.path.isfile(f'{thisDir}/instantiated.txt')

def instantiate():
	''' Instantiate (set up) the ONM library locally. '''
	# Check for Julia.
	try:
		subprocess.check_call(['julia','--version'])
	except:
		raise Exception('Julia not installed. ONM requires Julia v1.6.')
	# Instantiate
	os.system('julia -e \"using Pkg; Pkg.rm("gurobi")\"')
	os.system(f'julia --project="{thisDir}/PowerModelsONM.jl-0.4.0" -e \"using Pkg; Pkg.instantiate()\"')
	# Remember we instantiated.
	with open(f'{thisDir}/instantiated.txt','w+') as instant_file:
		instant_file.write('instantiated')

def run(dssPath, outPath, event_file):
	os.system(f'julia --project="{thisDir}/PowerModelsONM.jl-0.4.0" "{thisDir}/PowerModelsONM.jl-0.4.0/src/cli/entrypoint.jl" -n "{dssPath}" -o "{outPath}" --events "{event_file}"')

def binary_install():
	''' WARNING: DEPRECATED '''
	if platform.system() == "Linux":
		FNAME = 'PowerModelsONM_ubuntu-latest_x64.zip'
	elif platform.system() == "Windows":
		FNAME = 'PowerModelsONM_windows-latest_x64.zip'
	elif platform.system() == "Darwin":
		FNAME = 'PowerModelsONM_macOS-latest_x64.zip'
	else:
		raise Exception('Unsupported ONM platform.')
	if not os.path.isdir(f'{ONM_DIR}build'):
		URL = 'https://github.com/lanl-ansi/PowerModelsONM.jl/releases/download/v0.4.0/' + FNAME
		os.system(f'wget -nv {URL} -P {ONM_DIR}')
		os.system(f'unzip {ONM_DIR}{FNAME} -d {ONM_DIR}')
		os.system(f'rm {ONM_DIR}{FNAME}')
		if platform.system() == "Darwin":
			# Disable quarantine.
			os.system(f'sudo xattr -dr com.apple.quarantine {ONM_DIR}')

#instantiate()