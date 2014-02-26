'''
Created on Feb 24, 2014

@author: afisher
'''
import add_glm_object_dictionary
import math
import cmath
import random

def create(lf, rp):
	random.seed(10)
	f4 = {}
	
	nodes = []
	swing= []
	loads = []
	ohls = []
	xfmrs = []
	lcfgs = []
	tcfgs = []
	lsps = []
	olcs = []
	
	nodep = [None]*7
	meterp = [None]*10
	loadp = [None]*38
	ohlp = [None]*8
	xfmrp = [None]*11
	lcfgp = [None]*17
	tcfgp = [None]*25
	lspp = [None]*13
	olcp = [None]*10
	
	primary_volt = 12470/math.sqrt(3)
	secondary_volt = 4160/math.sqrt(3)
	
	def calculate_load(rated_load, voltage, load_multiplier, load_type):
		load = complex(0,0)
		if load_type == 'power':
			load = rated_load*load_multiplier
		elif load_type == 'current':
			load = complex.conjugate((rated_load*load_multiplier)/voltage)
		elif load_type == 'impedance':
			load = complex.conjugate((abs(voltage))**2/(rated_load*load_multiplier))
		else:
			raise RuntimeError("Invalid load_type. Please select power, current, or impedance.")
		if load.imag >= 0:
			load_str = '{:0.6f}+{:0.6f}j'.format(load.real, load.imag)
		else:
			load_str = '{:0.6f}-{:0.6f}j'.format(load.real, abs(load.imag))
			
		return load_str
	
	def classify_loads(load_list, res_pen):
		num_res = math.ceil(len(load_list)*res_pen)
		if num_res < 0:
			num_res = 0
		elif num_res > len(load_list):
			num_res = len(load_list)	
		num_com = len(load_list) - res_pen
		
		rloads = 0
		cloads = 0
		for load in load_list:
			if rloads == num_res:
				load[6] = 'C'
				cloads += 1
			elif cloads == num_com:
				load[6] = 'R'
				rloads += 1
			else:
				q = random.random
				if q <= res_pen:
					load[6] = 'R'
					rloads += 1
				else:
					load[6] = 'C'
					cloads += 1
		pass
#------------------------------------------------------------------------------ Store swing node
	swing.append(meterp)
	swing[0][0] = 'n1'
	swing[0][1] = 'distribution_nodes'
	swing[0][3] = 'SWING'
	swing[0][4] = 'ABCN'
	swing[0][5] = '{:0.6f}'.format(primary_volt)
#------------------------------------------------------------------------------ Store nodes
	n_names = ['n2', 'n3', 'n4']
	for name in n_names:
		nodes.append(nodep)
		index = len(nodes) - 1
		nodes[index][0] = name
		nodes[index][1] = 'distribution_nodes'
		nodes[index][4] = 'ABCN'
		nodes[index][5] ='{:0.6f}'.format(secondary_volt)
		if name == 'n2':
			nodes[index][5] ='{:0.6f}'.format(primary_volt)
#------------------------------------------------------------------------------ Store loads
	loads.append(loadp)
	loads[0][0] = 'l4'
	loads[0][2] = 'n4'
	loads[0][4] = 'ABCN'
	loads[0][5] = '{:0.6f}'.format(secondary_volt)
	loads[0][7] = calculate_load(1275000, secondary_volt*cmath.rect(1, 0), lf, 'power')
	loads[0][8] = calculate_load(1800000, secondary_volt*cmath.rect(1, -2*math.pi/3), lf, 'power')
	loads[0][9] = calculate_load(2375000, secondary_volt*cmath.rect(1, 2*math.pi/3), lf, 'power')
#------------------------------------------------------------------------------ Classify the loads
	classify_loads(loads, rp)
#------------------------------------------------------------------------------ Store overhead lines
	ohl_names = ['ohl_n1_n2','ohl_n3_n4']
	for name in ohl_names:
		ohls.append(ohlp)
		index = len(ohls) - 1
		ohls[index][0] = name
		ohls[index][1] = 'distribution_lines'
		ohls[index][2] = 'ABCN'
		ohls[index][6] = 'lcfg1'
		if name == 'ohl_n1_n2': 
			ohls[index][3] = 'n1'
			ohls[index][4] = 'n2'
			ohls[index][5] = '2000'
		elif name == 'ohl_n3_n4':
			ohls[index][3] = 'n3'
			ohls[index][4] = 'n4'
			ohls[index][5] = '2500'
#------------------------------------------------------------------------------ Store transformers
	xfmrs.append(xfmrp)
	xfmrs[0][0] = 'xfmr_n2_n3'
	xfmrs[0][1] = 'distribution_transformers'
	xfmrs[0][2] = 'ABC'
	xfmrs[0][3] = 'n2'
	xfmrs[0][4] = 'n3'
	xfmrs[0][5] = 'tcfg1'
#------------------------------------------------------------------------------ Store line configurations
	lcfgs.append(lcfgp)
	lcfgs[0][0] = 'lcfg1'
	lcfgs[0][2] = 'olc1'
	lcfgs[0][3] = 'olc1'
	lcfgs[0][4] = 'olc1'
	lcfgs[0][5] = 'olc2'
	lcfgs[0][6] = 'lsp1'
#------------------------------------------------------------------------------ Store transformer configurations
	tcfgs.append(tcfgp)
	tcfgs[0][0] = 'tcfg1'
	tcfgs[0][2] = 'WYE_WYE'
	tcfgs[0][6] = '12470'
	tcfgs[0][7] = '4160'
	tcfgs[0][8] = '6000'
	tcfgs[0][9] = '1380'
	tcfgs[0][10] = '1980'
	tcfgs[0][11] = '2640'
	tcfgs[0][12] = '0.01+0.06j'
#------------------------------------------------------------------------------ Store line spacings
	lsps.append(lspp)
	lsps[0][0] = 'lsp1'
	lsps[0][2] = '2.5'
	lsps[0][3] = '7.0'
	lsps[0][4] = '{:0.6f}'.format(math.sqrt(4**2 + 4**2))
	lsps[0][5] = '28.0'
	lsps[0][6] = '4.5'
	lsps[0][7] = '{:0.6f}'.format(math.sqrt(1.5**2 + 4**2))
	lsps[0][8] = '28.0'
	lsps[0][9] = '5.0'
	lsps[0][10] = '28.0'
	lsps[0][11] = '24.0'
#------------------------------------------------------------------------------ Store overhead line conductors
	olc_names = ['olc1', 'olc2']
	for name in olc_names:
		olcs.append(olcp)
		index = len(olcs) - 1
		olcs[index][0] = name
		if name == 'olc1':
			olcs[index][2] = '0.306'
			olcs[index][3] = '0.0244'
			olcs[index][4] = '0.721'
			olcs[index][5] = '530'
			olcs[index][9] = '// 336,400 26/7 ACSR'
		elif name == 'olc2':
			olcs[index][2] = '0.592'
			olcs[index][3] = '0.00814'
			olcs[index][4] = '0.563'
			olcs[index][5] = '340'
			olcs[index][9] = '// 4/0 6/1 ACSR'
#------------------------------------------------------------------------------ Add overhead line conductor dictionaries
	for olc in olcs:
		f4 = add_glm_object_dictionary.create_glm_object_dictionary(f4, 'overhead_line_conductor', olc)
#------------------------------------------------------------------------------ Add line spacing dictionaries
	for lsp in lsps:
		f4 = add_glm_object_dictionary.create_glm_object_dictionary(f4, 'line_spacing', lsp)
#------------------------------------------------------------------------------ Add line configuration dictionaries
	for lcfg in lcfgs:
		f4 = add_glm_object_dictionary.create_glm_object_dictionary(f4, 'line_configuration', lcfg)
#------------------------------------------------------------------------------ Add transformer configuration dictionaries
	for tcfg in tcfgs:
		f4 = add_glm_object_dictionary.create_glm_object_dictionary(f4, 'transformer_configuration', tcfg)
#------------------------------------------------------------------------------ Add swing dictionary
	for sw in swing:
		f4 = add_glm_object_dictionary.create_glm_object_dictionary(f4, 'meter', sw)
#------------------------------------------------------------------------------ Add node dictionaries
	for node in nodes:
		f4 = add_glm_object_dictionary.create_glm_object_dictionary(f4, 'node', node)
#------------------------------------------------------------------------------ Add load dictionaries
	for load in loads:
		f4 = add_glm_object_dictionary.create_glm_object_dictionary(f4, 'load', load)
#------------------------------------------------------------------------------ Add overhead line dictionaries
	for ohl in ohls:
		f4 = add_glm_object_dictionary.create_glm_object_dictionary(f4, 'overhead_line', ohl)
#------------------------------------------------------------------------------ Add overhead line dictionaries
	for xfmr in xfmrs:
		f4 = add_glm_object_dictionary.create_glm_object_dictionary(f4, 'transformer', xfmr)

	return f4

def main():
	import pprint
	IEEE_4 = create(1, 1)
	pprint.pprint(IEEE_4)
	pass
if __name__ == '__main__':
	main()