from sscapi import PySSC
from math import ceil

''' 
based on pvsamv1_c3d_rescom.lk
runs 1 sub-array, cec 5 par module, snl inverter
'''

# Start by declaring the variables.

# Web service input variables.
latitude = 33
longitude = 104

# array parameters
ac_derate = 0.99
num_modules = 80

# module parameters
cec_area = 1.244
cec_alpha_sc = 2.651e-003
cec_beta_oc = -1.423e-001
cec_gamma_r = -4.070e-001
cec_i_mp_ref = 5.25
cec_i_sc_ref = 5.75
cec_n_s = 72
cec_t_noct = 49.2
cec_v_mp_ref = 41
cec_v_oc_ref = 47.7
cec_standoff = 6
cec_height = 0
cec_r_s = 0.105
cec_r_sh_ref = 160.48
cec_i_o_ref = 1.919e-010
cec_i_l_ref = 5.754
cec_adjust = 20.8
cec_a_ref = 1.9816

# inverter parameters
inv_snl_c0 = -6.57929e-006
inv_snl_c1 = 4.72925e-005
inv_snl_c2 = 0.00202195
inv_snl_c3 = 0.000285321
inv_snl_paco = 4000
inv_snl_pdco = 4186
inv_snl_pnt = 0.17
inv_snl_pso = 19.7391
inv_snl_vdco = 310.67
inv_snl_vdcmax = 0
inv_snl_vmin = 250
inv_snl_vmax = 480

tilt = 30
azimuth = 180
track_mode = 0
soiling = 0.95
dc_derate = 0.95558

# shading derate table
shading_mxh = [ [ 0,0,0,0,0,0,0,0,0.475,0.95,1,1,0.7875,0.2375,0.25,0.3625,0,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0,0,0,0.4875,1,1,1,0.925,0.6375,0.6625,0.225,0,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0,0,0.15,0.925,1,1,1,1,1,0.75,0.2,0,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0,0,0.45,0.9125,1,1,1,1,1,0.625,0.375,0,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0.075,0.05,0.7875,1,1,1,1,1,1,0.625,0.4875,0.025,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0.15,0.075,0.9,1,1,1,1,1,1,0.675,0.5,0.05,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0.1,0.0625,0.8375,1,1,1,1,1,1,0.6375,0.4875,0.025,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0,0,0.6625,0.9625,1,1,1,1,1,0.6125,0.4,0,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0,0,0.2,0.9125,1,1,1,1,1,0.7375,0.2125,0,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0,0,0.0625,0.7,1,1,1,0.9375,0.8,0.7,0.1875,0,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0,0,0,0.45,0.95,1,1,0.8125,0.3625,0.3625,0.375,0,0,0,0,0,0,0,0 ],
				[ 0,0,0,0,0,0,0,0.0125,0.525,0.95,1,0.9875,0.75,0.175,0.2125,0.275,0,0,0,0,0,0,0,0 ] ]

# out-years system performance
	  	  
analysis_years = 30
availability = 100
degradation = 0.5

# electric load input
elec_load = range(0,8760)
# projected escalation of load (%/year)
elec_load_escalation = 0

# utility rate input variables
rate_escalation = 0
ur_sell_eq_buy = 1
ur_monthly_fixed_charge = 0
ur_flat_buy_rate = 0.12
ur_flat_sell_rate = 0
ur_tou_enable = 0
ur_tou_p1_buy_rate = 0.12
ur_tou_p1_sell_rate = 0
ur_tou_p2_buy_rate = 0.12
ur_tou_p2_sell_rate = 0
ur_tou_p3_buy_rate = 0.12
ur_tou_p3_sell_rate = 0
ur_tou_p4_buy_rate = 0.12
ur_tou_p4_sell_rate = 0
ur_tou_p5_buy_rate = 0.12
ur_tou_p5_sell_rate = 0
ur_tou_p6_buy_rate = 0.12
ur_tou_p6_sell_rate = 0
ur_tou_p7_buy_rate = 0.12
ur_tou_p7_sell_rate = 0
ur_tou_p8_buy_rate = 0.12
ur_tou_p8_sell_rate = 0
ur_tou_p9_buy_rate = 0.12
ur_tou_p9_sell_rate = 0
ur_tou_sched_weekday = '111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111'
ur_tou_sched_weekend = '111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111'
ur_dc_enable = 0
ur_dc_fixed_m1 = 0
ur_dc_fixed_m2 = 0
ur_dc_fixed_m3 = 0
ur_dc_fixed_m4 = 0
ur_dc_fixed_m5 = 0
ur_dc_fixed_m6 = 0
ur_dc_fixed_m7 = 0
ur_dc_fixed_m8 = 0
ur_dc_fixed_m9 = 0
ur_dc_fixed_m10 = 0
ur_dc_fixed_m11 = 0
ur_dc_fixed_m12 = 0
ur_dc_p1 = 0
ur_dc_p2 = 0
ur_dc_p3 = 0
ur_dc_p4 = 0
ur_dc_p5 = 0
ur_dc_p6 = 0
ur_dc_p7 = 0
ur_dc_p8 = 0
ur_dc_p9 = 0
ur_dc_sched_weekday = '444444443333333333334444444444443333333333334444444444443333333333334444444444443333333333334444222222221111111111112222222222221111111111112222222222221111111111112222222222221111111111112222222222221111111111112222222222221111111111112222444444443333333333334444444444443333333333334444'
ur_dc_sched_weekend = '444444443333333333334444444444443333333333334444444444443333333333334444444444443333333333334444222222221111111111112222222222221111111111112222222222221111111111112222222222221111111111112222222222221111111111112222222222221111111111112222444444443333333333334444444444443333333333334444'
ur_tr_enable = 0
ur_tr_sell_mode = 1
ur_tr_sell_rate = 0
ur_tr_s1_energy_ub1 = 1e+099
ur_tr_s1_energy_ub2 = 1e+099
ur_tr_s1_energy_ub3 = 1e+099
ur_tr_s1_energy_ub4 = 1e+099
ur_tr_s1_energy_ub5 = 1e+099
ur_tr_s1_energy_ub6 = 1e+099
ur_tr_s1_rate1 = 0
ur_tr_s1_rate2 = 0
ur_tr_s1_rate3 = 0
ur_tr_s1_rate4 = 0
ur_tr_s1_rate5 = 0
ur_tr_s1_rate6 = 0
ur_tr_s2_energy_ub1 = 1e+099
ur_tr_s2_energy_ub2 = 1e+099
ur_tr_s2_energy_ub3 = 1e+099
ur_tr_s2_energy_ub4 = 1e+099
ur_tr_s2_energy_ub5 = 1e+099
ur_tr_s2_energy_ub6 = 1e+099
ur_tr_s2_rate1 = 0
ur_tr_s2_rate2 = 0
ur_tr_s2_rate3 = 0
ur_tr_s2_rate4 = 0
ur_tr_s2_rate5 = 0
ur_tr_s2_rate6 = 0
ur_tr_s3_energy_ub1 = 1e+099
ur_tr_s3_energy_ub2 = 1e+099
ur_tr_s3_energy_ub3 = 1e+099
ur_tr_s3_energy_ub4 = 1e+099
ur_tr_s3_energy_ub5 = 1e+099
ur_tr_s3_energy_ub6 = 1e+099
ur_tr_s3_rate1 = 0
ur_tr_s3_rate2 = 0
ur_tr_s3_rate3 = 0
ur_tr_s3_rate4 = 0
ur_tr_s3_rate5 = 0
ur_tr_s3_rate6 = 0
ur_tr_s4_energy_ub1 = 1e+099
ur_tr_s4_energy_ub2 = 1e+099
ur_tr_s4_energy_ub3 = 1e+099
ur_tr_s4_energy_ub4 = 1e+099
ur_tr_s4_energy_ub5 = 1e+099
ur_tr_s4_energy_ub6 = 1e+099
ur_tr_s4_rate1 = 0
ur_tr_s4_rate2 = 0
ur_tr_s4_rate3 = 0
ur_tr_s4_rate4 = 0
ur_tr_s4_rate5 = 0
ur_tr_s4_rate6 = 0
ur_tr_s5_energy_ub1 = 1e+099
ur_tr_s5_energy_ub2 = 1e+099
ur_tr_s5_energy_ub3 = 1e+099
ur_tr_s5_energy_ub4 = 1e+099
ur_tr_s5_energy_ub5 = 1e+099
ur_tr_s5_energy_ub6 = 1e+099
ur_tr_s5_rate1 = 0
ur_tr_s5_rate2 = 0
ur_tr_s5_rate3 = 0
ur_tr_s5_rate4 = 0
ur_tr_s5_rate5 = 0
ur_tr_s5_rate6 = 0
ur_tr_s6_energy_ub1 = 1e+099
ur_tr_s6_energy_ub2 = 1e+099
ur_tr_s6_energy_ub3 = 1e+099
ur_tr_s6_energy_ub4 = 1e+099
ur_tr_s6_energy_ub5 = 1e+099
ur_tr_s6_energy_ub6 = 1e+099
ur_tr_s6_rate1 = 0
ur_tr_s6_rate2 = 0
ur_tr_s6_rate3 = 0
ur_tr_s6_rate4 = 0
ur_tr_s6_rate5 = 0
ur_tr_s6_rate6 = 0
ur_tr_sched_m1 = 0
ur_tr_sched_m2 = 0
ur_tr_sched_m3 = 0
ur_tr_sched_m4 = 0
ur_tr_sched_m5 = 0
ur_tr_sched_m6 = 0
ur_tr_sched_m7 = 0
ur_tr_sched_m8 = 0
ur_tr_sched_m9 = 0
ur_tr_sched_m10 = 0
ur_tr_sched_m11 = 0
ur_tr_sched_m12 = 0

federal_tax_rate = 28
state_tax_rate = 7
property_tax_rate = 0
prop_tax_cost_assessed_percent = 100
prop_tax_assessed_decline = 0
sales_tax_rate = 5
real_discount_rate = 8
inflation_rate = 2.5
insurance_rate = 0
system_capacity = 17.22
system_heat_rate = 0
om_fixed = 0
om_fixed_escal = 0
om_production = 0
om_production_escal = 0
om_capacity = 20
om_capacity_escal = 0
om_fuel_cost = 0
om_fuel_cost_escal = 0
annual_fuel_usage = 0

# incentives

itc_fed_amount = 0
itc_fed_amount_deprbas_fed = 0
itc_fed_amount_deprbas_sta = 0
itc_sta_amount = 0
itc_sta_amount_deprbas_fed = 0
itc_sta_amount_deprbas_sta = 0
itc_fed_percent = 30
itc_fed_percent_maxvalue = 1e+099
itc_fed_percent_deprbas_fed = 0
itc_fed_percent_deprbas_sta = 0
itc_sta_percent = 0
itc_sta_percent_maxvalue = 1e+099
itc_sta_percent_deprbas_fed = 0
itc_sta_percent_deprbas_sta = 0
ptc_fed_amount = 0
ptc_fed_term = 10
ptc_fed_escal = 2
ptc_sta_amount = 0
ptc_sta_term = 10
ptc_sta_escal = 2
ibi_fed_amount = 0
ibi_fed_amount_tax_fed = 1
ibi_fed_amount_tax_sta = 1
ibi_fed_amount_deprbas_fed = 0
ibi_fed_amount_deprbas_sta = 0
ibi_sta_amount = 0
ibi_sta_amount_tax_fed = 1
ibi_sta_amount_tax_sta = 1
ibi_sta_amount_deprbas_fed = 0
ibi_sta_amount_deprbas_sta = 0
ibi_uti_amount = 0
ibi_uti_amount_tax_fed = 1
ibi_uti_amount_tax_sta = 1
ibi_uti_amount_deprbas_fed = 0
ibi_uti_amount_deprbas_sta = 0
ibi_oth_amount = 0
ibi_oth_amount_tax_fed = 1
ibi_oth_amount_tax_sta = 1
ibi_oth_amount_deprbas_fed = 0
ibi_oth_amount_deprbas_sta = 0
ibi_fed_percent = 0
ibi_fed_percent_maxvalue = 1e+099
ibi_fed_percent_tax_fed = 1
ibi_fed_percent_tax_sta = 1
ibi_fed_percent_deprbas_fed = 0
ibi_fed_percent_deprbas_sta = 0
ibi_sta_percent = 0
ibi_sta_percent_maxvalue = 1e+099
ibi_sta_percent_tax_fed = 1
ibi_sta_percent_tax_sta = 1
ibi_sta_percent_deprbas_fed = 0
ibi_sta_percent_deprbas_sta = 0
ibi_uti_percent = 0
ibi_uti_percent_maxvalue = 1e+099
ibi_uti_percent_tax_fed = 1
ibi_uti_percent_tax_sta = 1
ibi_uti_percent_deprbas_fed = 0
ibi_uti_percent_deprbas_sta = 0
ibi_oth_percent = 0
ibi_oth_percent_maxvalue = 1e+099
ibi_oth_percent_tax_fed = 1
ibi_oth_percent_tax_sta = 1
ibi_oth_percent_deprbas_fed = 0
ibi_oth_percent_deprbas_sta = 0
cbi_fed_amount = 0
cbi_fed_maxvalue = 1e+099
cbi_fed_tax_fed = 1
cbi_fed_tax_sta = 1
cbi_fed_deprbas_fed = 0
cbi_fed_deprbas_sta = 0
cbi_sta_amount = 0
cbi_sta_maxvalue = 1e+099
cbi_sta_tax_fed = 1
cbi_sta_tax_sta = 1
cbi_sta_deprbas_fed = 0
cbi_sta_deprbas_sta = 0
cbi_uti_amount = 0
cbi_uti_maxvalue = 1e+099
cbi_uti_tax_fed = 1
cbi_uti_tax_sta = 1
cbi_uti_deprbas_fed = 0
cbi_uti_deprbas_sta = 0
cbi_oth_amount = 0
cbi_oth_maxvalue = 1e+099
cbi_oth_tax_fed = 1
cbi_oth_tax_sta = 1
cbi_oth_deprbas_fed = 0
cbi_oth_deprbas_sta = 0
pbi_fed_amount = 0
pbi_fed_term = 0
pbi_fed_escal = 0
pbi_fed_tax_fed = 1
pbi_fed_tax_sta = 1
pbi_sta_amount = 0
pbi_sta_term = 0
pbi_sta_escal = 0
pbi_sta_tax_fed = 1
pbi_sta_tax_sta = 1
pbi_uti_amount = 0
pbi_uti_term = 0
pbi_uti_escal = 0
pbi_uti_tax_fed = 1
pbi_uti_tax_sta = 1
pbi_oth_amount = 0
pbi_oth_term = 0
pbi_oth_escal = 0
pbi_oth_tax_fed = 1
pbi_oth_tax_sta = 1
total_installed_cost = 99621.1
salvage_percentage = 0

loan_debt = 100
loan_term = 30
loan_rate = 7.5
is_mortgage = 0 # true/false

is_commercial = 0
# Enable MACRS depreciation true/false (commercial only)
depr_fed_macrs = 1
depr_sta_macrs = 1

# internal calculations to determine array electrical wiring
mod_power = cec_v_mp_ref * cec_i_mp_ref
num_series = 0.5 * (inv_snl_vmin + inv_snl_vmax) / cec_v_mp_ref

if inv_snl_vdcmax > 0:
	while num_series > 0 and num_series * cec_v_oc_ref > inv_snl_vdcmax:
		num_series -= 1

if num_series < 1:
	num_series = 1
num_series = int(num_series)

num_parallel = num_modules / num_series
if num_parallel < 1:
	num_parallel = 1

num_inverters = ceil(num_series * num_parallel * mod_power / inv_snl_paco)
if num_inverters < 1:
	num_inverters = 1

num_parallel = int(num_parallel)
num_inverters = int(num_inverters)

print 'num_parallel: ' + str(num_parallel)
print 'num_series: ' + str(num_series)
print 'num_inverters: ' + str(num_inverters)


#Shoehorn the variables into the SAM data container.

ssc = PySSC()
dat = ssc.data_create()

ssc.data_set_string(dat, 'weather_file', 'C:/Users/dwp0/Dropbox/OMF/omf/scratch/systemAdvisoryModel/examples/abilene.tm2')

ssc.data_set_number(dat, 'ac_derate', ac_derate)
ssc.data_set_number(dat, 'modules_per_string', num_series)
ssc.data_set_number(dat, 'strings_in_parallel', num_parallel)
ssc.data_set_number(dat, 'inverter_count', num_inverters)
ssc.data_set_number(dat, 'subarray1_tilt', tilt)
ssc.data_set_number(dat, 'subarray1_azimuth', azimuth)
ssc.data_set_number(dat, 'subarray1_track_mode', track_mode)
ssc.data_set_matrix(dat, 'subarray1_shading_mxh', shading_mxh)
ssc.data_set_array(dat, 'subarray1_soiling', [soiling, soiling, soiling, soiling, soiling, soiling, soiling, soiling, soiling, soiling, soiling, soiling ])
ssc.data_set_number(dat, 'subarray1_derate', dc_derate)

# set up values for other sub arrays - not used (currently)
ssc.data_set_number(dat, 'subarray2_tilt', 0)
ssc.data_set_number(dat, 'subarray3_tilt', 0)
ssc.data_set_number(dat, 'subarray4_tilt', 0)

ssc.data_set_number(dat, 'module_model', 1)

ssc.data_set_number(dat, 'cec_area', cec_area)
ssc.data_set_number(dat, 'cec_a_ref', cec_a_ref)
ssc.data_set_number(dat, 'cec_adjust', cec_adjust)
ssc.data_set_number(dat, 'cec_alpha_sc', cec_alpha_sc)
ssc.data_set_number(dat, 'cec_beta_oc', cec_beta_oc)
ssc.data_set_number(dat, 'cec_gamma_r', cec_gamma_r)
ssc.data_set_number(dat, 'cec_i_l_ref', cec_i_l_ref)
ssc.data_set_number(dat, 'cec_i_mp_ref', cec_i_mp_ref)
ssc.data_set_number(dat, 'cec_i_o_ref', cec_i_o_ref)
ssc.data_set_number(dat, 'cec_i_sc_ref', cec_i_sc_ref)
ssc.data_set_number(dat, 'cec_n_s', cec_n_s)
ssc.data_set_number(dat, 'cec_r_s', cec_r_s)
ssc.data_set_number(dat, 'cec_r_sh_ref', cec_r_sh_ref)
ssc.data_set_number(dat, 'cec_t_noct', cec_t_noct)
ssc.data_set_number(dat, 'cec_v_mp_ref', cec_v_mp_ref)
ssc.data_set_number(dat, 'cec_v_oc_ref', cec_v_oc_ref)
ssc.data_set_number(dat, 'cec_temp_corr_mode', 0)
ssc.data_set_number(dat, 'cec_standoff', cec_standoff)
ssc.data_set_number(dat, 'cec_height', cec_height)

ssc.data_set_number(dat, 'inverter_model', 1)

ssc.data_set_number(dat, 'inv_snl_c0', inv_snl_c0)
ssc.data_set_number(dat, 'inv_snl_c1', inv_snl_c1)
ssc.data_set_number(dat, 'inv_snl_c2', inv_snl_c2)
ssc.data_set_number(dat, 'inv_snl_c3', inv_snl_c3)
ssc.data_set_number(dat, 'inv_snl_paco', inv_snl_paco)
ssc.data_set_number(dat, 'inv_snl_pdco', inv_snl_pdco)
ssc.data_set_number(dat, 'inv_snl_pnt', inv_snl_pnt)
ssc.data_set_number(dat, 'inv_snl_pso', inv_snl_pso)
ssc.data_set_number(dat, 'inv_snl_vdco', inv_snl_vdco)
ssc.data_set_number(dat, 'inv_snl_vdcmax', inv_snl_vdcmax)

# all variables have been set up for pvsamv1. Run!
mod = ssc.module_create('pvsamv1')
returnStatus = ssc.module_exec(mod, dat)


# process results
# if ssc.module_exec(mod, dat) == 0:
# 	print "pvsamv1 simulation error"
# 	idx = 1
# 	msg = ssc.module_log(mod, 0)
# 	while (msg != None):
# 		print "\t: " + msg
# 		msg = ssc.module_log(mod, idx)
# 		idx = idx + 1
# else:
# 	#return the relevant outputs desired
# 	ac_hourly = var('hourly_ac_net');
# 	ac_monthly = var('monthly_ac_net');
# 	ac_annual = var('annual_ac_net');
# 	print 'ac_hourly (kWh) = ' + str(ac_hourly)
# 	print 'ac_monthly (kWh) = ' + str(ac_monthly)
# 	print 'ac_annual (kWh) = ' + str(ac_annual)


'''



// start economic analysis

// calculate annualized output of the system for each year of its life

// setup curtailment schedule (no curtailment, factor=1)
curtailment = alloc( 12,24 );
for (r=0;r<12;r++)
	for (c=0;c<24;c++)
		curtailment[r][c] = 1;


var( 'analysis_years', analysis_years );
var( 'energy_availability', [ availability ] ); // 100% availability
var( 'energy_degradation', [ degradation ] ); // 0.5% per year
var( 'energy_curtailment', curtailment );
var( 'system_use_lifetime_output', 0 );
var( 'energy_net_hourly', ac_hourly );

run( 'annualoutput' );

outln( 'annual e_net_delivered (kWh) = ' + var('annual_e_net_delivered') );

// calculate annual revenue from utility rate
var( 'analysis_years', analysis_years );
var( 'system_availability', [ availability ] );
var( 'system_degradation', [ degradation ] );
var( 'rate_escalation', [ rate_escalation+inflation_rate ] );
var( 'ur_sell_eq_buy', ur_sell_eq_buy );
var( 'ur_monthly_fixed_charge', ur_monthly_fixed_charge );
var( 'ur_flat_buy_rate', ur_flat_buy_rate );
var( 'ur_flat_sell_rate', ur_flat_sell_rate );
var( 'ur_tou_enable', ur_tou_enable );
var( 'ur_tou_p1_buy_rate', ur_tou_p1_buy_rate );
var( 'ur_tou_p1_sell_rate', ur_tou_p1_sell_rate );
var( 'ur_tou_p2_buy_rate', ur_tou_p2_buy_rate );
var( 'ur_tou_p2_sell_rate', ur_tou_p2_sell_rate );
var( 'ur_tou_p3_buy_rate', ur_tou_p3_buy_rate );
var( 'ur_tou_p3_sell_rate', ur_tou_p3_sell_rate );
var( 'ur_tou_p4_buy_rate', ur_tou_p4_buy_rate );
var( 'ur_tou_p4_sell_rate', ur_tou_p4_sell_rate );
var( 'ur_tou_p5_buy_rate', ur_tou_p5_buy_rate );
var( 'ur_tou_p5_sell_rate', ur_tou_p5_sell_rate );
var( 'ur_tou_p6_buy_rate', ur_tou_p6_buy_rate );
var( 'ur_tou_p6_sell_rate', ur_tou_p6_sell_rate );
var( 'ur_tou_p7_buy_rate', ur_tou_p7_buy_rate );
var( 'ur_tou_p7_sell_rate', ur_tou_p7_sell_rate );
var( 'ur_tou_p8_buy_rate', ur_tou_p8_buy_rate );
var( 'ur_tou_p8_sell_rate', ur_tou_p8_sell_rate );
var( 'ur_tou_p9_buy_rate', ur_tou_p9_buy_rate );
var( 'ur_tou_p9_sell_rate', ur_tou_p9_sell_rate );
var( 'ur_tou_sched_weekday', ur_tou_sched_weekday );
var( 'ur_tou_sched_weekend', ur_tou_sched_weekend );
var( 'ur_dc_enable', ur_dc_enable );
var( 'ur_dc_fixed_m1', ur_dc_fixed_m1 );
var( 'ur_dc_fixed_m2', ur_dc_fixed_m2 );
var( 'ur_dc_fixed_m3', ur_dc_fixed_m3 );
var( 'ur_dc_fixed_m4', ur_dc_fixed_m4 );
var( 'ur_dc_fixed_m5', ur_dc_fixed_m5 );
var( 'ur_dc_fixed_m6', ur_dc_fixed_m6 );
var( 'ur_dc_fixed_m7', ur_dc_fixed_m7 );
var( 'ur_dc_fixed_m8', ur_dc_fixed_m8 );
var( 'ur_dc_fixed_m9', ur_dc_fixed_m9 );
var( 'ur_dc_fixed_m10', ur_dc_fixed_m10 );
var( 'ur_dc_fixed_m11', ur_dc_fixed_m11 );
var( 'ur_dc_fixed_m12', ur_dc_fixed_m12 );
var( 'ur_dc_p1', ur_dc_p1 );
var( 'ur_dc_p2', ur_dc_p2 );
var( 'ur_dc_p3', ur_dc_p3 );
var( 'ur_dc_p4', ur_dc_p4 );
var( 'ur_dc_p5', ur_dc_p5 );
var( 'ur_dc_p6', ur_dc_p6 );
var( 'ur_dc_p7', ur_dc_p7 );
var( 'ur_dc_p8', ur_dc_p8 );
var( 'ur_dc_p9', ur_dc_p9 );
var( 'ur_dc_sched_weekday', ur_dc_sched_weekday );
var( 'ur_dc_sched_weekend', ur_dc_sched_weekend );
var( 'ur_tr_enable', ur_tr_enable );
var( 'ur_tr_sell_mode', ur_tr_sell_mode );
var( 'ur_tr_sell_rate', ur_tr_sell_rate );
var( 'ur_tr_s1_energy_ub1', ur_tr_s1_energy_ub1 );
var( 'ur_tr_s1_energy_ub2', ur_tr_s1_energy_ub2 );
var( 'ur_tr_s1_energy_ub3', ur_tr_s1_energy_ub3 );
var( 'ur_tr_s1_energy_ub4', ur_tr_s1_energy_ub4 );
var( 'ur_tr_s1_energy_ub5', ur_tr_s1_energy_ub5 );
var( 'ur_tr_s1_energy_ub6', ur_tr_s1_energy_ub6 );
var( 'ur_tr_s1_rate1', ur_tr_s1_rate1 );
var( 'ur_tr_s1_rate2', ur_tr_s1_rate2 );
var( 'ur_tr_s1_rate3', ur_tr_s1_rate3 );
var( 'ur_tr_s1_rate4', ur_tr_s1_rate4 );
var( 'ur_tr_s1_rate5', ur_tr_s1_rate5 );
var( 'ur_tr_s1_rate6', ur_tr_s1_rate6 );
var( 'ur_tr_s2_energy_ub1', ur_tr_s2_energy_ub1 );
var( 'ur_tr_s2_energy_ub2', ur_tr_s2_energy_ub2 );
var( 'ur_tr_s2_energy_ub3', ur_tr_s2_energy_ub3 );
var( 'ur_tr_s2_energy_ub4', ur_tr_s2_energy_ub4 );
var( 'ur_tr_s2_energy_ub5', ur_tr_s2_energy_ub5 );
var( 'ur_tr_s2_energy_ub6', ur_tr_s2_energy_ub6 );
var( 'ur_tr_s2_rate1', ur_tr_s2_rate1 );
var( 'ur_tr_s2_rate2', ur_tr_s2_rate2 );
var( 'ur_tr_s2_rate3', ur_tr_s2_rate3 );
var( 'ur_tr_s2_rate4', ur_tr_s2_rate4 );
var( 'ur_tr_s2_rate5', ur_tr_s2_rate5 );
var( 'ur_tr_s2_rate6', ur_tr_s2_rate6 );
var( 'ur_tr_s3_energy_ub1', ur_tr_s3_energy_ub1 );
var( 'ur_tr_s3_energy_ub2', ur_tr_s3_energy_ub2 );
var( 'ur_tr_s3_energy_ub3', ur_tr_s3_energy_ub3 );
var( 'ur_tr_s3_energy_ub4', ur_tr_s3_energy_ub4 );
var( 'ur_tr_s3_energy_ub5', ur_tr_s3_energy_ub5 );
var( 'ur_tr_s3_energy_ub6', ur_tr_s3_energy_ub6 );
var( 'ur_tr_s3_rate1', ur_tr_s3_rate1 );
var( 'ur_tr_s3_rate2', ur_tr_s3_rate2 );
var( 'ur_tr_s3_rate3', ur_tr_s3_rate3 );
var( 'ur_tr_s3_rate4', ur_tr_s3_rate4 );
var( 'ur_tr_s3_rate5', ur_tr_s3_rate5 );
var( 'ur_tr_s3_rate6', ur_tr_s3_rate6 );
var( 'ur_tr_s4_energy_ub1', ur_tr_s4_energy_ub1 );
var( 'ur_tr_s4_energy_ub2', ur_tr_s4_energy_ub2 );
var( 'ur_tr_s4_energy_ub3', ur_tr_s4_energy_ub3 );
var( 'ur_tr_s4_energy_ub4', ur_tr_s4_energy_ub4 );
var( 'ur_tr_s4_energy_ub5', ur_tr_s4_energy_ub5 );
var( 'ur_tr_s4_energy_ub6', ur_tr_s4_energy_ub6 );
var( 'ur_tr_s4_rate1', ur_tr_s4_rate1 );
var( 'ur_tr_s4_rate2', ur_tr_s4_rate2 );
var( 'ur_tr_s4_rate3', ur_tr_s4_rate3 );
var( 'ur_tr_s4_rate4', ur_tr_s4_rate4 );
var( 'ur_tr_s4_rate5', ur_tr_s4_rate5 );
var( 'ur_tr_s4_rate6', ur_tr_s4_rate6 );
var( 'ur_tr_s5_energy_ub1', ur_tr_s5_energy_ub1 );
var( 'ur_tr_s5_energy_ub2', ur_tr_s5_energy_ub2 );
var( 'ur_tr_s5_energy_ub3', ur_tr_s5_energy_ub3 );
var( 'ur_tr_s5_energy_ub4', ur_tr_s5_energy_ub4 );
var( 'ur_tr_s5_energy_ub5', ur_tr_s5_energy_ub5 );
var( 'ur_tr_s5_energy_ub6', ur_tr_s5_energy_ub6 );
var( 'ur_tr_s5_rate1', ur_tr_s5_rate1 );
var( 'ur_tr_s5_rate2', ur_tr_s5_rate2 );
var( 'ur_tr_s5_rate3', ur_tr_s5_rate3 );
var( 'ur_tr_s5_rate4', ur_tr_s5_rate4 );
var( 'ur_tr_s5_rate5', ur_tr_s5_rate5 );
var( 'ur_tr_s5_rate6', ur_tr_s5_rate6 );
var( 'ur_tr_s6_energy_ub1', ur_tr_s6_energy_ub1 );
var( 'ur_tr_s6_energy_ub2', ur_tr_s6_energy_ub2 );
var( 'ur_tr_s6_energy_ub3', ur_tr_s6_energy_ub3 );
var( 'ur_tr_s6_energy_ub4', ur_tr_s6_energy_ub4 );
var( 'ur_tr_s6_energy_ub5', ur_tr_s6_energy_ub5 );
var( 'ur_tr_s6_energy_ub6', ur_tr_s6_energy_ub6 );
var( 'ur_tr_s6_rate1', ur_tr_s6_rate1 );
var( 'ur_tr_s6_rate2', ur_tr_s6_rate2 );
var( 'ur_tr_s6_rate3', ur_tr_s6_rate3 );
var( 'ur_tr_s6_rate4', ur_tr_s6_rate4 );
var( 'ur_tr_s6_rate5', ur_tr_s6_rate5 );
var( 'ur_tr_s6_rate6', ur_tr_s6_rate6 );
var( 'ur_tr_sched_m1', ur_tr_sched_m1 );
var( 'ur_tr_sched_m2', ur_tr_sched_m2 );
var( 'ur_tr_sched_m3', ur_tr_sched_m3 );
var( 'ur_tr_sched_m4', ur_tr_sched_m4 );
var( 'ur_tr_sched_m5', ur_tr_sched_m5 );
var( 'ur_tr_sched_m6', ur_tr_sched_m6 );
var( 'ur_tr_sched_m7', ur_tr_sched_m7 );
var( 'ur_tr_sched_m8', ur_tr_sched_m8 );
var( 'ur_tr_sched_m9', ur_tr_sched_m9 );
var( 'ur_tr_sched_m10', ur_tr_sched_m10 );
var( 'ur_tr_sched_m11', ur_tr_sched_m11 );
var( 'ur_tr_sched_m12', ur_tr_sched_m12 );


// set up energy generation and load
var( 'e_with_system', ac_hourly ); // electric generation (PV, kWh)
var( 'e_without_system', elec_load ); // electric load (kWh), negative value indicates draw from grid
var( 'load_escalation', [ elec_load_escalation ] );

run( 'utilityrate' );

outln( 'energy value ($) = ' + var('energy_value' ) );


// set up financial variables
var( 'analysis_years', analysis_years );
var( 'federal_tax_rate', federal_tax_rate );
var( 'state_tax_rate', state_tax_rate );
var( 'property_tax_rate', property_tax_rate );
var( 'prop_tax_cost_assessed_percent', prop_tax_cost_assessed_percent );
var( 'prop_tax_assessed_decline', prop_tax_assessed_decline );
var( 'sales_tax_rate', sales_tax_rate );
var( 'real_discount_rate', real_discount_rate );
var( 'inflation_rate', inflation_rate );
var( 'insurance_rate', insurance_rate );
var( 'system_capacity', system_capacity );
var( 'system_heat_rate', system_heat_rate );
var( 'om_fixed', [ om_fixed ] );
var( 'om_fixed_escal', om_fixed_escal );
var( 'om_production', [ om_production ] );
var( 'om_production_escal', om_production_escal );
var( 'om_capacity', [ om_capacity ] );
var( 'om_capacity_escal', om_capacity_escal );
var( 'om_fuel_cost', [ om_fuel_cost ] );
var( 'om_fuel_cost_escal', om_fuel_cost_escal );
var( 'annual_fuel_usage', annual_fuel_usage );
var( 'itc_fed_amount', itc_fed_amount );
var( 'itc_fed_amount_deprbas_fed', itc_fed_amount_deprbas_fed );
var( 'itc_fed_amount_deprbas_sta', itc_fed_amount_deprbas_sta );
var( 'itc_sta_amount', itc_sta_amount );
var( 'itc_sta_amount_deprbas_fed', itc_sta_amount_deprbas_fed );
var( 'itc_sta_amount_deprbas_sta', itc_sta_amount_deprbas_sta );
var( 'itc_fed_percent', itc_fed_percent );
var( 'itc_fed_percent_maxvalue', itc_fed_percent_maxvalue );
var( 'itc_fed_percent_deprbas_fed', itc_fed_percent_deprbas_fed );
var( 'itc_fed_percent_deprbas_sta', itc_fed_percent_deprbas_sta );
var( 'itc_sta_percent', itc_sta_percent );
var( 'itc_sta_percent_maxvalue', itc_sta_percent_maxvalue );
var( 'itc_sta_percent_deprbas_fed', itc_sta_percent_deprbas_fed );
var( 'itc_sta_percent_deprbas_sta', itc_sta_percent_deprbas_sta );
var( 'ptc_fed_amount', [ ptc_fed_amount ] );
var( 'ptc_fed_term', ptc_fed_term );
var( 'ptc_fed_escal', ptc_fed_escal );
var( 'ptc_sta_amount', [ ptc_sta_amount ] );
var( 'ptc_sta_term', ptc_sta_term );
var( 'ptc_sta_escal', ptc_sta_escal );
var( 'ibi_fed_amount', ibi_fed_amount );
var( 'ibi_fed_amount_tax_fed', ibi_fed_amount_tax_fed );
var( 'ibi_fed_amount_tax_sta', ibi_fed_amount_tax_sta );
var( 'ibi_fed_amount_deprbas_fed', ibi_fed_amount_deprbas_fed );
var( 'ibi_fed_amount_deprbas_sta', ibi_fed_amount_deprbas_sta );
var( 'ibi_sta_amount', ibi_sta_amount );
var( 'ibi_sta_amount_tax_fed', ibi_sta_amount_tax_fed );
var( 'ibi_sta_amount_tax_sta', ibi_sta_amount_tax_sta );
var( 'ibi_sta_amount_deprbas_fed', ibi_sta_amount_deprbas_fed );
var( 'ibi_sta_amount_deprbas_sta', ibi_sta_amount_deprbas_sta );
var( 'ibi_uti_amount', ibi_uti_amount );
var( 'ibi_uti_amount_tax_fed', ibi_uti_amount_tax_fed );
var( 'ibi_uti_amount_tax_sta', ibi_uti_amount_tax_sta );
var( 'ibi_uti_amount_deprbas_fed', ibi_uti_amount_deprbas_fed );
var( 'ibi_uti_amount_deprbas_sta', ibi_uti_amount_deprbas_sta );
var( 'ibi_oth_amount', ibi_oth_amount );
var( 'ibi_oth_amount_tax_fed', ibi_oth_amount_tax_fed );
var( 'ibi_oth_amount_tax_sta', ibi_oth_amount_tax_sta );
var( 'ibi_oth_amount_deprbas_fed', ibi_oth_amount_deprbas_fed );
var( 'ibi_oth_amount_deprbas_sta', ibi_oth_amount_deprbas_sta );
var( 'ibi_fed_percent', ibi_fed_percent );
var( 'ibi_fed_percent_maxvalue', ibi_fed_percent_maxvalue );
var( 'ibi_fed_percent_tax_fed', ibi_fed_percent_tax_fed );
var( 'ibi_fed_percent_tax_sta', ibi_fed_percent_tax_sta );
var( 'ibi_fed_percent_deprbas_fed', ibi_fed_percent_deprbas_fed );
var( 'ibi_fed_percent_deprbas_sta', ibi_fed_percent_deprbas_sta );
var( 'ibi_sta_percent', ibi_sta_percent );
var( 'ibi_sta_percent_maxvalue', ibi_sta_percent_maxvalue );
var( 'ibi_sta_percent_tax_fed', ibi_sta_percent_tax_fed );
var( 'ibi_sta_percent_tax_sta', ibi_sta_percent_tax_sta );
var( 'ibi_sta_percent_deprbas_fed', ibi_sta_percent_deprbas_fed );
var( 'ibi_sta_percent_deprbas_sta', ibi_sta_percent_deprbas_sta );
var( 'ibi_uti_percent', ibi_uti_percent );
var( 'ibi_uti_percent_maxvalue', ibi_uti_percent_maxvalue );
var( 'ibi_uti_percent_tax_fed', ibi_uti_percent_tax_fed );
var( 'ibi_uti_percent_tax_sta', ibi_uti_percent_tax_sta );
var( 'ibi_uti_percent_deprbas_fed', ibi_uti_percent_deprbas_fed );
var( 'ibi_uti_percent_deprbas_sta', ibi_uti_percent_deprbas_sta );
var( 'ibi_oth_percent', ibi_oth_percent );
var( 'ibi_oth_percent_maxvalue', ibi_oth_percent_maxvalue );
var( 'ibi_oth_percent_tax_fed', ibi_oth_percent_tax_fed );
var( 'ibi_oth_percent_tax_sta', ibi_oth_percent_tax_sta );
var( 'ibi_oth_percent_deprbas_fed', ibi_oth_percent_deprbas_fed );
var( 'ibi_oth_percent_deprbas_sta', ibi_oth_percent_deprbas_sta );
var( 'cbi_fed_amount', cbi_fed_amount );
var( 'cbi_fed_maxvalue', cbi_fed_maxvalue );
var( 'cbi_fed_tax_fed', cbi_fed_tax_fed );
var( 'cbi_fed_tax_sta', cbi_fed_tax_sta );
var( 'cbi_fed_deprbas_fed', cbi_fed_deprbas_fed );
var( 'cbi_fed_deprbas_sta', cbi_fed_deprbas_sta );
var( 'cbi_sta_amount', cbi_sta_amount );
var( 'cbi_sta_maxvalue', cbi_sta_maxvalue );
var( 'cbi_sta_tax_fed', cbi_sta_tax_fed );
var( 'cbi_sta_tax_sta', cbi_sta_tax_sta );
var( 'cbi_sta_deprbas_fed', cbi_sta_deprbas_fed );
var( 'cbi_sta_deprbas_sta', cbi_sta_deprbas_sta );
var( 'cbi_uti_amount', cbi_uti_amount );
var( 'cbi_uti_maxvalue', cbi_uti_maxvalue );
var( 'cbi_uti_tax_fed', cbi_uti_tax_fed );
var( 'cbi_uti_tax_sta', cbi_uti_tax_sta );
var( 'cbi_uti_deprbas_fed', cbi_uti_deprbas_fed );
var( 'cbi_uti_deprbas_sta', cbi_uti_deprbas_sta );
var( 'cbi_oth_amount', cbi_oth_amount );
var( 'cbi_oth_maxvalue', cbi_oth_maxvalue );
var( 'cbi_oth_tax_fed', cbi_oth_tax_fed );
var( 'cbi_oth_tax_sta', cbi_oth_tax_sta );
var( 'cbi_oth_deprbas_fed', cbi_oth_deprbas_fed );
var( 'cbi_oth_deprbas_sta', cbi_oth_deprbas_sta );
var( 'pbi_fed_amount', [ pbi_fed_amount ] );
var( 'pbi_fed_term', pbi_fed_term );
var( 'pbi_fed_escal', pbi_fed_escal );
var( 'pbi_fed_tax_fed', pbi_fed_tax_fed );
var( 'pbi_fed_tax_sta', pbi_fed_tax_sta );
var( 'pbi_sta_amount', [ pbi_sta_amount ] );
var( 'pbi_sta_term', pbi_sta_term );
var( 'pbi_sta_escal', pbi_sta_escal );
var( 'pbi_sta_tax_fed', pbi_sta_tax_fed );
var( 'pbi_sta_tax_sta', pbi_sta_tax_sta );
var( 'pbi_uti_amount', [ pbi_uti_amount ] );
var( 'pbi_uti_term', pbi_uti_term );
var( 'pbi_uti_escal', pbi_uti_escal );
var( 'pbi_uti_tax_fed', pbi_uti_tax_fed );
var( 'pbi_uti_tax_sta', pbi_uti_tax_sta );
var( 'pbi_oth_amount', [ pbi_oth_amount ] );
var( 'pbi_oth_term', pbi_oth_term );
var( 'pbi_oth_escal', pbi_oth_escal );
var( 'pbi_oth_tax_fed', pbi_oth_tax_fed );
var( 'pbi_oth_tax_sta', pbi_oth_tax_sta );
var( 'total_installed_cost', total_installed_cost );
var( 'salvage_percentage', salvage_percentage );

var( 'loan_debt', loan_debt );
var( 'loan_rate', loan_rate );
var( 'loan_term', loan_term );

if ( is_commercial )
{
	var( 'market', 1 ); // commercial
	var( 'depr_fed_type', depr_fed_macrs );
	var( 'depr_sta_type', depr_sta_macrs );	
}
else
{
	var( 'market', 0 ); // residential
	var( 'mortgage', is_mortgage );
}

run( 'cashloan' );

outln( 'lcoe_real = ' + var('lcoe_real') );
outln( 'lcoe_nominal = ' + var('lcoe_nom') );
outln( 'npv = ' + var('npv') );

'''