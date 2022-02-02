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
	# os.system(julia -e 'using Pkg; try Pkg.rm("gurobi"); catch; end')
	# os.system('julia -e \"using Pkg; Pkg.rm("gurobi")\"')
	# os.system(f'julia -e \"import Pkg; Pkg.add("gurobi")\"')
	os.system(f'julia --project="{thisDir}/PowerModelsONM.jl-1.1.0" -e \"using Pkg; Pkg.instantiate()\"')
	# os.system(f'julia --project="{thisDir}/PowerModelsONM.jl-1.0.1" -e \"using Pkg; Pkg.add("Gurobi"); Pkg.instantiate()\"')
	# Remember we instantiated.
	with open(f'{thisDir}/instantiated.txt','w+') as instant_file:
		instant_file.write('instantiated')

def run(dssPath, outPath, event_file):
	os.system(f'julia --project="{thisDir}/PowerModelsONM.jl-1.1.0" "{thisDir}/PowerModelsONM.jl-1.1.0/src/cli/entrypoint.jl" -n "{dssPath}" -o "{outPath}" --events "{event_file}" --gurobi')

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
		URL = 'https://github.com/lanl-ansi/PowerModelsONM.jl/releases/download/v1.1.0/' + FNAME
		os.system(f'wget -nv {URL} -P {ONM_DIR}')
		os.system(f'unzip {ONM_DIR}{FNAME} -d {ONM_DIR}')
		os.system(f'rm {ONM_DIR}{FNAME}')
		if platform.system() == "Darwin":
			# Disable quarantine.
			os.system(f'sudo xattr -dr com.apple.quarantine {ONM_DIR}')

def install_onm(target='Darwin'):
	''' WARNING, WIP. TODO: OS check, linux support, license check, tests. '''
	try: os.system('sudo cat /Library/gurobi/gurobi.lic') # Fixme; check for '# Gurobi'.
	except:
		return('Please install valid license file in /Library/gurobi')
	os.system('brew install julia') # installs julia
	print('Julia installed')
	os.system('pip3 install julia') # installs pyJulia
	print('installed pyJulia')
	os.system('wget "https://packages.gurobi.com/9.1/gurobi9.1.2_mac64.pkg"') # d/l gurobi
	print('Downloaded Gurobi')
	os.system('sudo installer -pkg gurobi9.1.2_mac64.pkg -target /') # install gurobi
	os.system('echo "export GUROBI_HOME=/Library/gurobi9.1.2" >>  ~/.zshrc')
	os.system('echo "export PATH=/Library/gurobi912/mac64/bin:$PATH" >>  ~/.zshrc')
	os.system('echo "export LD_LIBRARY_PATH=/Library/gurobi912/mac64lib" >>  ~/.zshrc')
	os.system('source ~/.zshrc')
	print('Environmental variables set')
	# Notebook notes "You should make a LOCAL project to contain both Gurobi and PowerModelsONM"; does this do that?
	os.system("julia --project=. -e 'import Pkg; Pkg.add(\"Gurobi\")'")
	print('Gurobi package added')
	os.system("julia --project=. -e 'import Pkg; Pkg.build(\"Gurobi\")'")
	print('Gurobi package built')
	os.system("julia --project=. -e 'import Pkg; Pkg.add(Pkg.PackageSpec(;name=\"PowerModelsONM\", rev=\"main\"));'") # TODO pin version
	print('PowerONM package added to Julia')
	os.system("julia --project=. -e 'import Pkg; Pkg.add(Pkg.PackageSpec(;name=\"PowerModelsDistribution\", rev=\"main\"));'") # TODO pin version
	print('PowerModelsDistribution package added to Julia')

def build_settings_file(circuitPath='circuit.dss',settingsPath='settings.json', max_switch_actions=1, vm_lb_pu=0.9, vm_ub_pu=1.1, sbase_default=0.001, line_limit_mult=1.0E10, vad_deg=5.0):
	os.system(f"julia --project=. -e 'using PowerModelsONM; build_settings_file(\"{circuitPath}\", \"{settingsPath}\"; max_switch_actions={max_switch_actions}, vm_lb_pu={vm_lb_pu}, vm_ub_pu={vm_ub_pu}, sbase_default={sbase_default}, line_limit_mult={line_limit_mult}, vad_deg={vad_deg})'")

def run_onm(circuitPath='circuit.dss', settingsPath='settings.json', outputPath="onm_out.json", eventsPath="events.json", gurobi='true', verbose='true', optSwitchSolver="mip_solver", fixSmallNumbers='true'):
	'''WARNING: WIP TODO: skip list'''
	os.system(f"julia --project=. -e 'import Gurobi; using PowerModelsONM; args = Dict{{String,Any}}(\"network\"=>\"{circuitPath}\", \"settings\"=>\"{settingsPath}\", \"output\"=>\"{outputPath}\", \"events\"=>\"{eventsPath}\", \"gurobi\"=>{gurobi}, \"verbose\"=>{verbose}, \"opt-switch-solver\"=>\"{optSwitchSolver}\", \"fix-small-numbers\"=>{fixSmallNumbers}, \"skip\"=>[\"faults\",\"stability\"]); entrypoint(args);'")

#instantiate()