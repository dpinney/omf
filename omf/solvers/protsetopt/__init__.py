import os, sys
import platform
#import json
import shutil
from urllib.request import urlretrieve as wget
from subprocess import check_output
from dss import DSS as dssObj

thisDir = os.path.abspath(os.path.dirname(__file__))

def pull_from_upstream():
	''' pull down the upstream package'''
	source_url = 'https://github.com/lilycatolson/Protection-settings-optimizer/archive/refs/heads/main.zip'
	wget(source_url, f'{thisDir}/pso_source.zip') #was: pso.zip 

def install_pso_env(clean=False, system : list = platform.system()):
    ''' create a venv for Protection Settings Optimizer and install there '''
    if not os.path.isfile(os.path.join(thisDir,"pso_source.zip")):
        pull_from_upstream()
    if clean:
        shutil.rmtree(f'{thisDir}/pso_env', ignore_errors=True)
    os.system(f'{sys.executable} -m venv "{thisDir}/pso_env"')
    os.system(f'unzip -o "{thisDir}/pso_source.zip" -d "{thisDir}/pso_env/"')
    os.system(f'source "{thisDir}/pso_env/bin/activate"; python -m pip install -r "{thisDir}/pso_env/Protection-settings-optimizer-main/requirements.txt"')

def install_pso_env_without_download(system : list = platform.system()):
    os.system(f'{sys.executable} -m venv "{thisDir}/pso_env"')
    os.system(f'source "{thisDir}/pso_env/bin/activate"; {sys.executable} -m pip install -e git+https://github.com/lilycatolson/Protection-settings-optimizer.git#egg=RSO_pack')

def install_pso(clean=False, system : list = platform.system()):
    ''' installs dependency for protsetopt'''
    instantiated_path = os.path.normpath(os.path.join(thisDir,"instantiated.txt"))
    if not os.path.isfile(instantiated_path):
        try:
            install_pso_env_without_download()
            #install_pso_env(clean=clean, system=system) #put back in once other version tested
            #os.system(f"{sys.executable} -m pip install -e git+https://github.com/lilycatolson/Protection-settings-optimizer.git#egg=RSO_pack")
            if system == "Windows":
                os.system(f'copy nul {instantiated_path}')
            else:
                os.system(f'touch "{instantiated_path}"')
            print(f'protsetopt installed - to reinstall remove file: {thisDir}/instantiated.txt')
        except Exception as e:
            print(e)
            print("error - unable to install protsetopt")

def run_venv_cmd(cmd=''):
    ''' Run a command against the venv. '''
    out = check_output([f'''source "{thisDir}/pso_env/bin/activate"; cd "{thisDir}"; pwd; python -c 'import RSO_pack; {cmd}' '''], shell=True)
    return out.decode('utf-8')

def run_pso(testPath, testFile):
    install_pso()
    try:
        import RSO_pack
    except (ImportError, ModuleNotFoundError):
        from . import RSO_pack

    RSO_pack.run(testPath, testFile)

def run_pso_venv(testPath, testFile):
    install_pso()
    run_venv_cmd(cmd=f'RSO_pack.run("{testPath}", "{testFile}")')

def _test():
    testPath = os.path.normpath(os.path.join(thisDir, 'testFiles'))
    testFile = 'IEEE34Test.dss'
    #run_pso(testPath, testFile)
    run_pso_venv(testPath, testFile)

if __name__ == "__main__":
    _test()
