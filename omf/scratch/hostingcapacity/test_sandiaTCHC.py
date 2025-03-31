import omf
from pathlib import Path
from omf.solvers import mohca_cl
import pandas as pd
import unittest

xf_lookup = pd.DataFrame(columns=['kVA', 'R_ohms_LV', 'X_ohms_LV'])
xf_lookup['kVA'] = [50]
xf_lookup['R_ohms_LV'] = [0.0135936]
xf_lookup['X_ohms_LV'] = [0.0165888]

# 12, True, buscoords -> works
# This is default in the hosting capacity model rn
# This gives good output :)
# None, True, None -> TypeError
# 12, False, buscoords -> works
# None, True, buscoords -> list.remove(x) x not in list
# None, False, buscoords -> list.remove(x) not in list
# Note, if there are no transformers, make sure the other 2 variables match that, otherwise it breaks.

class TestSandiaTCHC(unittest.TestCase):

	def __init__(self, methodName: str = "TestSandiaTCHC"):
		super().__init__(methodName)

		self.testDir = Path.cwd()
		self.testFilesDir = Path(omf.omfDir, 'static', 'testFiles', 'hostingCapacity')
		self.mohca_input = Path(self.testFilesDir, "input_mohcaData.csv")
		self.buscoords = Path(self.testFilesDir, "input_bus_coords.csv")
		self.min_xfmr = 12
		self.overload_constraint = 1.2

	def test12TrueNone(self):
		'''
		Testing 12, True, None
		'''
		mohca_cl.isu_transformerCustMapping(input_meter_data_fp=self.mohca_input, grouping_output_fp=Path(self.testDir, "transPairing_12_True_None_output.csv"), minimum_xfmr_n=self.min_xfmr, fmr_n_is_exact=True, bus_coords_fp=None )

		# None, 0 None
		# 12, True, None
		# Both produce files with no bus_coords. Both break sandiaTCHC => KEYERROR
		mohca_cl.sandiaTCHC( in_path=self.mohca_input, out_path=Path(self.testDir, "tchc_12_True_None.csv"), final_results=pd.read_csv("transPairing_12_True_None_output.csv"), der_pf=1.0, vv_x=None, vv_y=None, overload_constraint=self.overload_constraint, xf_lookup=xf_lookup )

	def testNoneFalseNone(self):
		mohca_cl.isu_transformerCustMapping(input_meter_data_fp=self.mohca_input, grouping_output_fp=Path(self.testDir, "transPairing_None_False_None_output.csv"), minimum_xfmr_n=None, fmr_n_is_exact=False, bus_coords_fp=None )
		mohca_cl.sandiaTCHC( in_path=self.mohca_input, out_path=Path(self.testDir, "tchc_None_False_None.csv"), final_results=pd.read_csv("transPairing_None_False_None_output.csv"), der_pf=1.0, vv_x=None, vv_y=None, overload_constraint=self.overload_constraint, xf_lookup=xf_lookup )

	def test15TrueBus(self):
		mohca_cl.isu_transformerCustMapping(input_meter_data_fp=self.mohca_input, grouping_output_fp=Path(self.testDir, "transPairing_15_True_bus.csv"), minimum_xfmr_n=15, fmr_n_is_exact=True, bus_coords_fp=self.buscoords )
		mohca_cl.sandiaTCHC( in_path=self.mohca_input, out_path=Path(self.testDir, "tchc_15_True_bus.csv"), final_results=pd.read_csv("transPairing_15_True_bus.csv"), der_pf=1.0, vv_x=None, vv_y=None, overload_constraint=self.overload_constraint, xf_lookup=xf_lookup )

	def test15FalseBus(self):
		mohca_cl.isu_transformerCustMapping(input_meter_data_fp=self.mohca_input, grouping_output_fp=Path(self.testDir, "transPairing_15_False_bus.csv"), minimum_xfmr_n=15, fmr_n_is_exact=False, bus_coords_fp=self.buscoords )
		mohca_cl.sandiaTCHC( in_path=self.mohca_input, out_path=Path(self.testDir, "tchc_15_False_bus.csv"), final_results=pd.read_csv("transPairing_15_False_bus.csv"), der_pf=1.0, vv_x=None, vv_y=None, overload_constraint=self.overload_constraint, xf_lookup=xf_lookup )

if __name__ == "__main__":
	unittest.main()
