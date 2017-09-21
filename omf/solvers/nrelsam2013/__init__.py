# #####################################################################
#
#   System Simulation Core (SSC) Python Wrapper using Classes
#   Author: Aron Dobos @ NREL and Steven Janzou @ NREL
#
# #####################################################################


import string, sys, struct, math, os
from ctypes import *

myDir = os.path.dirname(__file__)

c_number = c_float # must be c_double or c_float depending on how defined in sscapi.h
class SSCAPI():
	if sys.platform == 'win32' or sys.platform == 'cygwin':
		if 8*struct.calcsize("P") == 64:
			_dll = CDLL(os.path.join(myDir,"ssc64.dll")) 
		else:
			# HACK: Windows cannot import a DLL unless it's in the same directory as the process!
			cachedDir = os.getcwd()
			os.chdir(myDir)
			_dll = CDLL("ssc32.dll")
			os.chdir(cachedDir)
	elif sys.platform == 'darwin':
		_dll = CDLL(os.path.join(myDir,"ssc64.dylib"))
	elif sys.platform == 'linux2':
		_dll = CDLL(os.path.join(myDir,"ssc64.so"))
	else:
		print "Platform not supported ", sys.platform
	# print "\n   _dll chosen=", _dll, "(for ", sys.platform, ")"
	

	@staticmethod
	def ssc_version():
		SSCAPI._dll.ssc_version.restype = c_int
		return SSCAPI._dll.ssc_version()

	@staticmethod
	def ssc_build_info():
		SSCAPI._dll.ssc_build_info.restype = c_char_p
		return SSCAPI._dll.ssc_build_info()
	
	@staticmethod
	def ssc_data_create():
		SSCAPI._dll.ssc_data_create.restype = c_void_p
		return SSCAPI._dll.ssc_data_create()

	@staticmethod
	def ssc_data_free( p_data):
		SSCAPI._dll.ssc_data_free( c_void_p(p_data) )

	@staticmethod
	def ssc_data_clear( p_data):
		SSCAPI._dll.ssc_data_clear( c_void_p(p_data) )

	@staticmethod
	def ssc_data_unassign( p_data, name):
		SSCAPI._dll.ssc_data_unassign( c_void_p(p_data), c_char_p(name) )

	@staticmethod
	def ssc_data_query( p_data, name):
		SSCAPI._dll.ssc_data_query.restype = c_int
		return SSCAPI._dll.ssc_data_query( c_void_p(p_data), c_char_p(name) )

	@staticmethod
	def ssc_data_first( p_data):
		SSCAPI._dll.ssc_data_first.restype = c_char_p
		return SSCAPI._dll.ssc_data_first( c_void_p(p_data) )

	@staticmethod
	def ssc_data_next( p_data):
		SSCAPI._dll.ssc_data_next.restype = c_char_p
		return SSCAPI._dll.ssc_data_next( c_void_p(p_data) )

	@staticmethod
	def ssc_data_set_string( p_data, name, value):
		SSCAPI._dll.ssc_data_set_string( c_void_p(p_data), c_char_p(name), c_char_p(value) )

	@staticmethod
	def ssc_data_set_number( p_data, name, value):
		SSCAPI._dll.ssc_data_set_number( c_void_p(p_data), c_char_p(name), c_number(value) )

	@staticmethod
	def ssc_data_set_array(p_data,name,parr):
		count = len(parr)
		arr = (c_number*count)()
		for i in range(count):
			arr[i] = c_number(parr[i])
		return SSCAPI._dll.ssc_data_set_array( c_void_p(p_data), c_char_p(name),pointer(arr), c_int(count))

	@staticmethod
	def ssc_data_set_matrix(p_data,name,mat):
		nrows = len(mat)
		ncols = len(mat[0])
		size = nrows*ncols
		arr = (c_number*size)()
		idx=0
		for r in range(nrows):
			for c in range(ncols):
				arr[idx] = c_number(mat[r][c])
				idx=idx+1
		return SSCAPI._dll.ssc_data_set_matrix( c_void_p(p_data), c_char_p(name),pointer(arr), c_int(nrows), c_int(ncols))

	@staticmethod
	def ssc_data_set_table(p_data,name,table):
		SSCAPI._dll.ssc_data_set_table( c_void_p(p_data), c_char_p(name), c_void_p(table) )


	@staticmethod
	def ssc_data_get_string( p_data, name):
		SSCAPI._dll.ssc_data_get_string.restype = c_char_p
		return SSCAPI._dll.ssc_data_get_string( c_void_p(p_data), c_char_p(name) )

	@staticmethod
	def ssc_data_get_number( p_data, name):
		val = c_number(0)
		SSCAPI._dll.ssc_data_get_number( c_void_p(p_data), c_char_p(name), byref(val) )
		return val.value

	@staticmethod
	def ssc_data_get_array(p_data,name):
		count = c_int()
		SSCAPI._dll.ssc_data_get_array.restype = POINTER(c_number)
		parr = SSCAPI._dll.ssc_data_get_array( c_void_p(p_data), c_char_p(name), byref(count))
		arr = []
		for i in range(count.value):
			arr.append( float(parr[i]) )
		return arr

	@staticmethod
	def ssc_data_get_matrix(p_data,name):
		nrows = c_int()
		ncols = c_int()
		SSCAPI._dll.ssc_data_get_matrix.restype = POINTER(c_number)
		parr = SSCAPI._dll.ssc_data_get_matrix( c_void_p(p_data), c_char_p(name), byref(nrows), byref(ncols) )
		idx = 0
		mat = []
		for r in range(nrows.value):
			row = []
			for c in range(ncols.value):
				row.append( float(parr[idx]) )
				idx = idx + 1
			mat.append(row)
		return mat
	
	@staticmethod
	def ssc_data_get_table(p_data,name):
		SSCAPI._dll.ssc_data_get_table.restype = c_void_p
		return SSCAPI._dll.ssc_data_get_table( c_void_p(p_data), c_char_p(name) )
		

	@staticmethod
	def ssc_module_entry(index):
		SSCAPI._dll.ssc_module_entry.restype = c_void_p
		return SSCAPI._dll.ssc_module_entry( c_int(index) )

	@staticmethod
	def ssc_entry_name(p_entry):
		SSCAPI._dll.ssc_entry_name.restype = c_char_p
		return SSCAPI._dll.ssc_entry_name( c_void_p(p_entry) )

	@staticmethod
	def ssc_entry_description(p_entry):
		SSCAPI._dll.ssc_entry_description.restype = c_char_p
		return SSCAPI._dll.ssc_entry_description( c_void_p(p_entry) )

	@staticmethod
	def ssc_entry_version(p_entry):
		SSCAPI._dll.ssc_entry_version.restype = c_int
		return SSCAPI._dll.ssc_entry_version( c_void_p(p_entry) )

	@staticmethod
	def ssc_module_create(name):
		SSCAPI._dll.ssc_module_create.restype = c_void_p
		return SSCAPI._dll.ssc_module_create( c_char_p(name) )

	@staticmethod
	def ssc_module_free(p_mod):
		SSCAPI._dll.ssc_module_free( c_void_p(p_mod) )

	@staticmethod
	def ssc_module_var_info(p_mod,index):
		SSCAPI._dll.ssc_module_var_info.restype = c_void_p
		return SSCAPI._dll.ssc_module_var_info( c_void_p(p_mod), c_int(index) )

	@staticmethod
	def ssc_info_var_type( p_inf ):
		return SSCAPI._dll.ssc_info_var_type( c_void_p(p_inf) )

	@staticmethod
	def ssc_info_data_type( p_inf ):
		return SSCAPI._dll.ssc_info_data_type( c_void_p(p_inf) )

	@staticmethod
	def ssc_info_name( p_inf ):
		SSCAPI._dll.ssc_info_name.restype = c_char_p
		return SSCAPI._dll.ssc_info_name( c_void_p(p_inf) )

	@staticmethod
	def ssc_info_label( p_inf ):
		SSCAPI._dll.ssc_info_label.restype = c_char_p
		return SSCAPI._dll.ssc_info_label( c_void_p(p_inf) )

	@staticmethod
	def ssc_info_units( p_inf ):
		SSCAPI._dll.ssc_info_units.restype = c_char_p
		return SSCAPI._dll.ssc_info_units( c_void_p(p_inf) )

	@staticmethod
	def ssc_info_meta( p_inf ):
		SSCAPI._dll.ssc_info_meta.restype = c_char_p
		return SSCAPI._dll.ssc_info_meta( c_void_p(p_inf) )

	@staticmethod
	def ssc_info_group( p_inf ):
		SSCAPI._dll.ssc_info_group.restype = c_char_p
		return SSCAPI._dll.ssc_info_group( c_void_p(p_inf) )

	@staticmethod
	def ssc_info_uihint( p_inf ):
		SSCAPI._dll.ssc_info_uihint.restype = c_char_p
		return SSCAPI._dll.ssc_info_uihint( c_void_p(p_inf) )

	@staticmethod
	def ssc_module_exec( p_mod, p_data ):
		SSCAPI._dll.ssc_module_exec.restype = c_int
		return SSCAPI._dll.ssc_module_exec( c_void_p(p_mod), c_void_p(p_data) )

	@staticmethod
	def ssc_module_log( p_mod, index ):
		type = c_int()
		time = c_float()
		SSCAPI._dll.ssc_module_log.restype = c_char_p
		return SSCAPI._dll.ssc_module_log( c_void_p(p_mod), c_int(index), byref(type), byref(time) )
	
	
	
	
	
	
	
class API:
	# constants for return value of Info.VarType() (see sscapi.h)
	INPUT=1
	OUTPUT=2
	INOUT=3

	# constants for out integer type in Module.Log() method (see sscapi.h)
	NOTICE = 1
	WARNING = 2
	ERROR = 3


	# constants for return value of Data.Query() and Info.DataType() (see sscapi.h)
	INVALID=0
	STRING=1
	NUMBER=2
	ARRAY=3
	MATRIX=4
	TABLE=5

	
	
	def version(self):
		return SSCAPI.ssc_version()
	
	def build_info(self):
		return SSCAPI.ssc_build_info()
	
	
	

	
class Entry:

	def __init__(self):
		self._idx = 0
		
	def reset(self):
		self._idx = 0
	
	def get(self):
		self._entry = SSCAPI.ssc_module_entry(self._idx)
		if (self._entry is None):
			self.reset()
			return False
		else:
			self._idx += 1
			return True
	
	def name(self):
		if (self._entry is not None):
			return SSCAPI.ssc_entry_name(self._entry)
		else: 
			return None
	
	def description(self):
		if (self._entry is not None):
			return SSCAPI.ssc_entry_description(self._entry)
		else:
			return null
	
	def version(self):
		if (self._entry is not None):
			return SSCAPI.ssc_entry_version(self._entry)
		else:
			return -1

	

class Data:
		
	def __init__(self, data = None):
		if (data is None):
			self._data = SSCAPI.ssc_data_create()
			self._owned = True
		else: # be careful of cyclic references - can use weakref.ref(data)
			self._data = data
			self._owned = False
		
		
		
	def __del__(self):
		if (self._owned) and (self._data != None):
			SSCAPI.ssc_data_free(self._data)
		
	def clear(self):
		SSCAPI.ssc_data_clear(self._data)
		
	def first(self):
		p = SSCAPI.ssc_data_first(self._data)
		if (p is not None) and (len(p)>0):
			return p
		else:
			return None
		
	def next(self):
		p = SSCAPI.ssc_data_next(self._data)
		if (p is not None) and (len(p)>0):
			return p
		else:
			return None
	
	def query(self, name):
		return SSCAPI.ssc_data_query(self._data, name)
		
	def set_number(self, name, value):
		SSCAPI.ssc_data_set_number(self._data, name, value)
		
	def get_number(self, name):
		val = float('nan')
		val = SSCAPI.ssc_data_get_number(self._data, name)
		return val
		
	def set_string(self, name, value):
		SSCAPI.ssc_data_set_string(self._data, name, value)
		
	def get_string(self, name):
		return SSCAPI.ssc_data_get_string(self._data, name)
		
	def set_array(self, name, data):
		SSCAPI.ssc_data_set_array(self._data, name, data)
		
	def get_array(self, name):
		return SSCAPI.ssc_data_get_array(self._data, name)
		
	def set_matrix(self, name, mat):
		SSCAPI.ssc_data_set_matrix(self._data, name, mat)
		
	def get_matrix(self, name):
		return SSCAPI.ssc_data_get_matrix(self._data, name)
		
	def set_table(self, name, table):
		SSCAPI.ssc_data_set_table(self._data, name, table)
		
	def get_table(self, name):
		return SSCAPI.ssc_data_get_table(self._data, name)
		
	def get_data_handle(self):
		return self._data



class Info:
	
	def __init__(self, module):
		self._mod = module
		self._idx = 0
		
		
	def reset(self):
		self._idx = 0
		
	def get(self):
		self._inf = SSCAPI.ssc_module_var_info(self._mod.get_module_handle(), self._idx)
		if (self._inf is None):
			self.reset()
			return False
		else:
			self._idx += 1
			return True
		
	def name(self):
		if (self._inf is None):
			return None
		else:
			return SSCAPI.ssc_info_name(self._inf)
	
	def var_type(self):
		if (self._inf is None):
			return -1
		else:
			return SSCAPI.ssc_info_var_type(self._inf)
	
	def data_type(self):
		if (self._inf is None):
			return -1
		else:
			return SSCAPI.ssc_info_data_type(self._inf)
	 
	def label(self):
		if (self._inf is None):
			return None
		else:
			return SSCAPI.ssc_info_label(self._inf)
	
	def units(self):
		if (self._inf is None):
			return None
		else:
			return SSCAPI.ssc_info_units(self._inf)
	
	def meta(self):
		if (self._inf is None):
			return None
		else:
			return SSCAPI.ssc_info_meta(self._inf)
	
	def group(self):
		if (self._inf is None):
			return None
		else:
			return SSCAPI.ssc_info_group(self._inf)
	
	def required(self):
		if (self._inf is None):
			return None
		else:
			return SSCAPI.ssc_info_required(self._inf)
	
	def constraints(self):
		if (self._inf is None):
			return None
		else:
			return SSCAPI.ssc_info_constraints(self._inf)



class Module:
	
	def __init__(self, name):
		self._mod = SSCAPI.ssc_module_create(name)
		
		
		
	def __del__(self):
		if (self._mod is not None):
			SSCAPI.ssc_module_free(self._mod)
		

	def is_ok(self):
		return self._mod is not None

	def get_module_handle(self):
		return self._mod

	def exec_(self, data):
		return (SSCAPI.ssc_module_exec(self._mod, data.get_data_handle()) != 0);

	def log(self, idx):
		msg = SSCAPI.ssc_module_log(self._mod, idx)
		return msg
	
