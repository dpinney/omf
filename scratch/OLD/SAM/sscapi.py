# #####################################################################
#
#   System Simulation Core (SSC) Python Wrapper
#   Author: Aron Dobos @ NREL
#
# #####################################################################


import string, sys
from ctypes import *

c_number = c_float # must be c_double or c_float depending on how defined in sscapi.h
class PySSC:
	def __init__(self):
		self.pdll = CDLL("ssc32.dll")

	INVALID=0
	STRING=1
	NUMBER=2
	ARRAY=3
	MATRIX=4

	INPUT=1
	OUTPUT=2
	INOUT=3

	def version(self):
		self.pdll.ssc_version.restype = c_int
		return self.pdll.ssc_version()

	def data_create(self):
		self.pdll.ssc_data_create.restype = c_void_p
		return self.pdll.ssc_data_create()

	def data_free(self, p_data):
		self.pdll.ssc_data_free( c_void_p(p_data) )

	def data_clear(self, p_data):
		self.pdll.ssc_data_clear( c_void_p(p_data) )

	def data_unassign(self, p_data, name):
		self.pdll.ssc_data_unassign( c_void_p(p_data), c_char_p(name) )

	def data_query(self, p_data, name):
		self.pdll.ssc_data_query.restype = c_int
		return self.pdll.ssc_data_query( c_void_p(p_data), c_char_p(name) )

	def data_first(self, p_data):
		self.pdll.ssc_data_first.restype = c_char_p
		return self.pdll.ssc_data_first( c_void_p(p_data) )

	def data_next(self, p_data):
		self.pdll.ssc_data_next.restype = c_char_p
		return self.pdll.ssc_data_next( c_void_p(p_data) )

	def data_set_string(self, p_data, name, value):
		self.pdll.ssc_data_set_string( c_void_p(p_data), c_char_p(name), c_char_p(value) )

	def data_set_number(self, p_data, name, value):
		self.pdll.ssc_data_set_number( c_void_p(p_data), c_char_p(name), c_number(value) )

	def data_set_array(self,p_data,name,parr):
		count = len(parr)
		arr = (c_number*count)()
		for i in range(count):
			arr[i] = c_number(parr[i])
		return self.pdll.ssc_data_set_array( c_void_p(p_data), c_char_p(name),pointer(arr), c_int(count))

	def data_set_matrix(self,p_data,name,mat):
		nrows = len(mat)
		ncols = len(mat[0])
		size = nrows*ncols
		arr = (c_number*size)()
		idx=0
		for r in range(nrows):
			for c in range(ncols):
				arr[idx] = c_number(mat[r][c])
				idx=idx+1
		return self.pdll.ssc_data_set_matrix( c_void_p(p_data), c_char_p(name),pointer(arr), c_int(nrows), c_int(ncols))


	def data_get_string(self, p_data, name):
		self.pdll.ssc_data_get_string.restype = c_char_p
		return self.pdll.ssc_data_get_string( c_void_p(p_data), c_char_p(name) )

	def data_get_number(self, p_data, name):
		val = c_number(0)
		self.pdll.ssc_data_get_number( c_void_p(p_data), c_char_p(name), byref(val) )
		return val.value

	def data_get_array(self,p_data,name):
		count = c_int()
		self.pdll.ssc_data_get_array.restype = POINTER(c_number)
		parr = self.pdll.ssc_data_get_array( c_void_p(p_data), c_char_p(name), byref(count))
		arr = []
		for i in range(count.value):
			arr.append( float(parr[i]) )
		return arr

	def data_get_matrix(self,p_data,name):
		nrows = c_int()
		ncols = c_int()
		self.pdll.ssc_data_get_matrix.restype = POINTER(c_number)
		parr = self.pdll.ssc_data_get_matrix( c_void_p(p_data), c_char_p(name), byref(nrows), byref(ncols) )
		idx = 0
		mat = []
		for r in range(nrows.value):
			row = []
			for c in range(ncols.value):
				row.append( float(parr[idx]) )
				idx = idx + 1
			mat.append(row)
		return mat

	def module_entry(self,index):
		self.pdll.ssc_module_entry.restype = c_void_p
		return self.pdll.ssc_module_entry( c_int(index) )

	def entry_name(self,p_entry):
		self.pdll.ssc_entry_name.restype = c_char_p
		return self.pdll.ssc_entry_name( c_void_p(p_entry) )

	def entry_description(self,p_entry):
		self.pdll.ssc_entry_description.restype = c_char_p
		return self.pdll.ssc_entry_description( c_void_p(p_entry) )

	def entry_version(self,p_entry):
		self.pdll.ssc_entry_version.restype = c_int
		return self.pdll.ssc_entry_version( c_void_p(p_entry) )

	def module_create(self,name):
		self.pdll.ssc_module_create.restype = c_void_p
		return self.pdll.ssc_module_create( c_char_p(name) )

	def module_free(self,p_mod):
		self.pdll.ssc_module_free( c_void_p(p_mod) )

	def module_var_info(self,p_mod,index):
		self.pdll.ssc_module_var_info.restype = c_void_p
		return self.pdll.ssc_module_var_info( c_void_p(p_mod), c_int(index) )

	def info_var_type( self, p_inf ):
		return self.pdll.ssc_info_var_type( c_void_p(p_inf) )

	def info_data_type( self, p_inf ):
		return self.pdll.ssc_info_data_type( c_void_p(p_inf) )

	def info_name( self, p_inf ):
		self.pdll.ssc_info_name.restype = c_char_p
		return self.pdll.ssc_info_name( c_void_p(p_inf) )

	def info_label( self, p_inf ):
		self.pdll.ssc_info_label.restype = c_char_p
		return self.pdll.ssc_info_label( c_void_p(p_inf) )

	def info_units( self, p_inf ):
		self.pdll.ssc_info_units.restype = c_char_p
		return self.pdll.ssc_info_units( c_void_p(p_inf) )

	def info_meta( self, p_inf ):
		self.pdll.ssc_info_meta.restype = c_char_p
		return self.pdll.ssc_info_meta( c_void_p(p_inf) )

	def info_group( self, p_inf ):
		self.pdll.ssc_info_group.restype = c_char_p
		return self.pdll.ssc_info_group( c_void_p(p_inf) )

	def info_uihint( self, p_inf ):
		self.pdll.ssc_info_uihint.restype = c_char_p
		return self.pdll.ssc_info_uihint( c_void_p(p_inf) )

	def module_exec( self, p_mod, p_data ):
		self.pdll.ssc_module_exec.restype = c_int
		return self.pdll.ssc_module_exec( c_void_p(p_mod), c_void_p(p_data) )

	def module_log( self, p_mod, index ):
		type = c_int()
		time = c_float()
		self.pdll.ssc_module_log.restype = c_char_p
		return self.pdll.ssc_module_log( c_void_p(p_mod), c_int(index), byref(type), byref(time) )



if __name__ == "__main__":

	def arr_to_str(a):
		s = ''
		for i in range(len(a)):
			s += str(a[i])
			if i<len(a)-1:
				s += ' '
		return s

	def mat_to_str(m):
		s = ''
		ncols = len(m[0])
		for r in range(len(m)):
			for c in range(ncols):
				s += str(m[r][c])
				if c < ncols-1:
					s += ' '
			if r < len(m)-1:
				s += ' | '
		return s


	def print_data(d):
		print 'data set:'
		name = ssc.data_first(d)
		while (name != None):
			type = ssc.data_query(d,name)
			outstr = '\t'
			if type == PySSC.STRING:
				outstr += ' str: ' + name + '    \'' + ssc.data_get_string(d,name) + '\''
			elif type == PySSC.NUMBER:
				outstr += ' num: ' + name + '    ' + str(ssc.data_get_number(d,name))
			elif type == PySSC.ARRAY:
				outstr += ' arr: ' + name + '    [ ' + arr_to_str( ssc.data_get_array(d,name) ) + ' ]'
			elif type == PySSC.MATRIX:
				outstr += ' mat: ' + name + '    [ ' + mat_to_str( ssc.data_get_matrix(d,name) ) + ' ]'
			else:
				outstr += ' inv! ' + name

			print outstr
			name = ssc.data_next(d)

	def simtest():
		ssc = PySSC()
		dat = ssc.data_create()
		
		i=0
		while (1):
			x = ssc.module_entry(i)
			if x == None:
				break;
			print 'module: "' + ssc.entry_name(x) + '" ver: ', ssc.entry_version(x)
			print '\t\t' + ssc.entry_description(x) 
			m = ssc.module_create( ssc.entry_name(x) )
			k=0
			while (1):
				inf = ssc.module_var_info( m, k )
				if inf == None:
					break;
				
				if ( ssc.info_var_type(inf) == PySSC.INPUT ):
					print '\tInput: \'' + ssc.info_name(inf) + '\' type(' + str(ssc.info_data_type(inf)) + ')  ' + ssc.info_label(inf) + '  (' + ssc.info_units(inf) + ')'
				else:
					print '\tOutput: \'' + ssc.info_name(inf) + '\' type(' + str(ssc.info_data_type(inf)) + ')  ' + ssc.info_label(inf) + '  (' + ssc.info_units(inf) + ')'
			
				k=k+1
				
			ssc.module_free(m)
			i=i+1

		ssc.data_set_string(dat, 'file_name', 'daggett.tm2')
		ssc.data_set_number(dat, 'system_size', 4)
		ssc.data_set_number(dat, 'derate', 0.77)
		ssc.data_set_number(dat, 'track_mode', 0)
		ssc.data_set_number(dat, 'azimuth', 180)
		ssc.data_set_number(dat, 'tilt_eq_lat', 1)


		# run PV system simulation
		mod = ssc.module_create("pvwattsv1")
		if ssc.module_exec(mod, dat) == 0:
			print 'PVWatts V1 simulation error'
			idx = 1
			msg = ssc.module_log(mod, 0)
			while (msg != None):
				print '\t: ' + msg
				msg = ssc.module_log(mod, idx)
				idx = idx + 1
		else:
			ann = 0
			ac = ssc.data_get_array(dat, "ac")
			for i in range(len(ac)):
				ac[i] = ac[i]/1000
				ann += ac[i]
			print 'PVWatts V1 Simulation ok, e_net (annual kW)=', ann
			ssc.data_set_array(dat, "e_with_system", ac) # copy over ac

		ssc.module_free(mod)

		mod = ssc.module_create("utilityrate")

		# calculate value of energy based on utility rate
		ssc.data_set_array(dat, "system_degradation", [0.5])

		ssc.data_set_array(dat,  "load_escalation", [0.9])
		ssc.data_set_array(dat, "rate_escalation", [1.5])
		ssc.data_set_number(dat, "ur_monthly_fixed_charge", 50)
		ssc.data_set_number(dat, "analysis_years", 30)
		ssc.data_set_number(dat, "ur_flat_buy_rate", 0.12)

		ssc.data_set_number(dat, "ur_tou_enable",1)
		ssc.data_set_number(dat, "ur_tou_p1_buy_rate", 0.12)
		ssc.data_set_number(dat, "ur_tou_p2_buy_rate", 0.556)
		ssc.data_set_number(dat, "ur_tou_p3_buy_rate", 0.75)
		ssc.data_set_number(dat, "ur_tou_p4_buy_rate", 0.99)
		ssc.data_set_string(dat, "ur_tou_sched_weekday", "111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111222222222222222222222222222222224444444442222222222222224444444442222222333333334444444443333333333333333333333333333333111111111111111111111111111111111111111111111111")
		ssc.data_set_string(dat, "ur_tou_sched_weekend", "111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111222222222222222222222222222222222222222222222222222222222222222222222222111111111111111111111111111111111111111111111111111111111111111111111111")

		if ssc.module_exec(mod, dat) == 0:
			print 'UtilityRate simulation error'
			idx = 1
			msg = ssc.module_log(mod, 0)
			while (msg != None):
				print '\t: ' + msg
				msg = ssc.module_log(mod, idx)
				idx = idx + 1
		else:
			print 'UtilityRate Simulation ok, year1_energy_value=  ($) ', ssc.data_get_array(dat, "energy_value")[0]

		ssc.module_free(mod)

		# calculate 30 year financial cashflow based on net energy and energy value in each year
		mod = ssc.module_create('cashloan')

		ssc.data_set_number(dat, "federal_tax_rate", 35.0)
		ssc.data_set_number(dat, "state_tax_rate", 8.0)
		ssc.data_set_number(dat, "real_discount_rate", 11.0)
		ssc.data_set_number(dat, "insurance_rate", 0.5)
		ssc.data_set_number(dat, "property_tax_rate", 2.0)
		ssc.data_set_number(dat, "sales_tax_rate", 3.2)
		ssc.data_set_number(dat, "inflation_rate", 3)
		ssc.data_set_number(dat, "system_capacity", 250)
		ssc.data_set_number(dat, "total_installed_cost", 110810)
		ssc.data_set_number(dat, "percent_of_cost_subject_sales_tax", 90)

		ssc.data_set_number(dat, "market", 0) #0=residential, 1=commercial
		ssc.data_set_number(dat, "mortgage", 0) # boolean

		ssc.data_set_number(dat, "loan_term", 30)
		ssc.data_set_number(dat, "loan_rate", 4.95)
		ssc.data_set_number(dat, "loan_debt", 80)
		ssc.data_set_number(dat, "itc_fed_percent", 30)

		if ssc.module_exec(mod, dat) == 0:
			print 'CashLoan simulation error'
			idx = 1
			msg = ssc.module_log(mod, 0)
			while (msg != None):
				print '\t: ' + msg
				msg = ssc.module_log(mod, idx)
				idx = idx + 1
		else:
			print 'CashLoan Simulation ok, lcoe_nom= ', ssc.data_get_number(dat, "lcoe_nom")

		ssc.module_free(mod)


		# Test windwatts with skystream 2.4
		ssc.data_set_string(dat, 'file_name', 'rocksprings.tm2')
		ssc.data_set_number(dat, 'ctl_mode', 2)
		ssc.data_set_number(dat, 'cutin', 4)
		ssc.data_set_number(dat, 'hub_ht', 13)
		ssc.data_set_number(dat, 'lossc', 0)
		ssc.data_set_number(dat, 'lossp', 0)
		ssc.data_set_array(dat, 'pc_wind', [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39])
		ssc.data_set_array(dat, 'pc_power', [0,0,0,0,0.08,0.02,0.35,0.6,1,1.6,2,2.25,2.35,2.4,2.4,2.37,2.3,2.09,2,2,2,2,2,1.98,1.95,1.8,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
		ssc.data_set_number(dat, 'rotor_di', 3.7)
		ssc.data_set_number(dat, 'shear', 0.14)
		ssc.data_set_number(dat, 'turbul', 0.1)
		ssc.data_set_array(dat, 'wt_x', [0])
		ssc.data_set_array(dat, 'wt_y', [0])


		# run wind system simulation
		mod = ssc.module_create("windwatts")
		if ssc.module_exec(mod, dat) == 0:
			print 'WindWatts simulation error'
			idx = 1
			msg = ssc.module_log(mod, 0)
			while (msg != None):
				print '\t: ' + msg
				msg = ssc.module_log(mod, idx)
				idx = idx + 1
		else:
			ann = 0
			ac = ssc.data_get_array(dat, "farmpwr")
			for i in range(len(ac)):
				ann += ac[i]
			print 'WindWatts Simulation ok, e_net (annual kW)=', ann

		ssc.module_free(mod)

		ssc.data_free(dat)


# ############################################################
# Test program 'main'

	print 'Hello, PySSC'
	ssc = PySSC()
	print 'Version: {0}'.format(ssc.version())

	dat = ssc.data_create()

	ssc.data_set_string(dat, 'first_name', 'Aron')
	ssc.data_set_string(dat, 'last_name', 'Dobos')
	ssc.data_set_number(dat, 'sizekw', 3.4)
	ssc.data_set_number(dat, 'derate', 0.77)
	ssc.data_set_number(dat, 'track_mode', 1)

	ssc.data_set_array(dat, 'mysched', [ 1, 5, 6, 2, 123, 41 ] )
	ssc.data_set_matrix(dat, 'mymat', [ [3, 5, 2], [2, 1, 1], [4, 5, 6] ] )
	print_data(dat)

	idx=1
	e = ssc.module_entry(0)
	while(e != None):
		print 'Module: ' + ssc.entry_name(e) + '  ver(' + str(ssc.entry_version(e)) + ')'
		e = ssc.module_entry(idx)
		idx=idx+1

	mod = ssc.module_create('easywatts')
	idx = 1
	inf = ssc.module_var_info(mod, 0)
	while (inf != None):
		if (ssc.info_var_type(inf) == PySSC.INPUT):
			print '\tInput: \'' + ssc.info_name(inf) + '\' type(' + str(ssc.info_data_type(inf)) + ')'

		inf = ssc.module_var_info(mod, idx)
		idx = idx+1

	ssc.module_free(mod)
	ssc.data_free(dat)

	print ''
	print 'basic api ok, now running simulation tests'
	print ''
	simtest()




