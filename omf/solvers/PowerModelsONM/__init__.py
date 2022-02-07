import os, platform, subprocess
from pathlib import Path

thisDir = os.path.abspath(os.path.dirname(__file__))

def check_instantiated():
	''' Check whether ONM was previously instantiated and working. '''
	return os.path.isfile(f'{thisDir}/instantiated.txt')

def install_onm(target='Darwin'):
	''' WARNING, WIP. TODO: OS check, linux support, license check, tests. '''
	try:
		os.system('sudo cat /Library/gurobi/gurobi.lic') # Fixme; check for '# Gurobi'.
	except:
		return('Please install valid license file in /Library/gurobi')
	os.system('HOMEBREW_NO_AUTO_UPDATE=1 brew install julia') # installs julia
	print('Julia installed')
	os.system('wget "https://packages.gurobi.com/9.1/gurobi9.1.2_mac64.pkg"') # d/l gurobi
	print('Downloaded Gurobi')
	os.system('sudo installer -pkg gurobi9.1.2_mac64.pkg -target /') # install gurobi
	os.system('echo "export GUROBI_HOME=/Library/gurobi912/mac64" >>  ~/.zshrc')
	os.system('echo "export PATH=/Library/gurobi912/mac64/bin:$PATH" >>  ~/.zshrc')
	os.system('echo "export LD_LIBRARY_PATH=/Library/gurobi912/mac64/lib" >>  ~/.zshrc')
	os.system('source ~/.zshrc')
	print('Environmental variables set')
	# Local julia project installs to contain both Gurobi and PowerModelsONM"
	os.system(f"julia --project={thisDir} -e 'import Pkg; Pkg.add(\"Gurobi\")'")
	print('Gurobi package added')
	os.system(f"julia --project={thisDir} -e 'import Pkg; Pkg.build(\"Gurobi\")'")
	print('Gurobi package built')
	os.system(f"julia --project={thisDir} -e 'import Pkg; Pkg.add(Pkg.PackageSpec(;name=\"PowerModelsONM\", rev=\"main\"));'") # TODO pin version
	print('PowerONM package added to Julia')
	os.system(f"julia --project={thisDir} -e 'import Pkg; Pkg.add(Pkg.PackageSpec(;name=\"PowerModelsDistribution\", rev=\"main\"));'") # TODO pin version
	print('PowerModelsDistribution package added to Julia')
	os.system(f'touch {thisDir}/instantiated.txt')

def build_settings_file(circuitPath='circuit.dss',settingsPath='settings.json', max_switch_actions=1, vm_lb_pu=0.9, vm_ub_pu=1.1, sbase_default=0.001, line_limit_mult=1.0E10, vad_deg=5.0):
	os.system(f"julia --project={thisDir} -e 'using PowerModelsONM; build_settings_file(\"{circuitPath}\", \"{settingsPath}\"; max_switch_actions={max_switch_actions}, vm_lb_pu={vm_lb_pu}, vm_ub_pu={vm_ub_pu}, sbase_default={sbase_default}, line_limit_mult={line_limit_mult}, vad_deg={vad_deg})'")

def run_onm(circuitPath='circuit.dss', settingsPath='settings.json', outputPath="onm_out.json", eventsPath="events.json", gurobi='true', verbose='true', optSwitchSolver="mip_solver", fixSmallNumbers='true', skipList='[\"faults\",\"stability\"]'):
	os.system(f"julia --project='{thisDir}' -e 'import Gurobi; using PowerModelsONM; args = Dict{{String,Any}}(\"network\"=>\"{circuitPath}\", \"settings\"=>\"{settingsPath}\", \"output\"=>\"{outputPath}\", \"events\"=>\"{eventsPath}\", \"gurobi\"=>{gurobi}, \"verbose\"=>{verbose}, \"opt-switch-solver\"=>\"{optSwitchSolver}\", \"fix-small-numbers\"=>{fixSmallNumbers}, \"skip\"=>{skipList}); entrypoint(args);'")

if __name__ == '__main__':
	# Basic Tests
	thisDirPath = Path(thisDir)
	omfDir = thisDirPath.parent.parent.absolute()
	build_settings_file(circuitPath=f'{omfDir}/scratch/RONM/circuit_onm_test.dss', settingsPath='./settings.json', max_switch_actions=1, vm_lb_pu=0.9, vm_ub_pu=1.1, sbase_default=0.001, line_limit_mult='Inf', vad_deg=5.0)
	run_onm(circuitPath=f'{omfDir}/scratch/RONM/circuit_onm_test.dss', settingsPath='./settings.json', outputPath="./onm_out.json", eventsPath=f'{omfDir}/scratch/RONM/events_onm_test.json', gurobi='true', verbose='true', optSwitchSolver="mip_solver", fixSmallNumbers='true', skipList='["faults","stability"]')