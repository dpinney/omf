#SOURCE
import os
from subprocess import check_output as sh
mods = [x[0:x.find('.dll')] for x in os.listdir('C:\Program Files\GridLAB-D\lib') if x.endswith('.dll')]
#print mods
for mod in mods:
    try:
        print sh('gridlabd --modhelp ' + mod)
    except:
        print 'FAILED on module name ' + mod

#MODULELIST
['assert', 'climate', 'generators', 'glsolvers', 'glxmatlab', 'market', 'msvcp80', 'msvcr80', 'network', 'powerflow', 'pthreadVC2', 'reliability', 'residential', 'tape', 'tape_file', 'tape_memory', 'tape_plot', 'test_extern_function', 'xerces-c_3_1']


'''
SAMPLEOUTPUT

class assert {
	enumeration {NONE=3, FALSE=2, TRUE=1} status; // desired outcome of assert test
	char1024 target; // the target property to test
	char32 part; // the target property part to test
	enumeration {outside=7, inside=6, !==3, >==2, >=5, <==1, <=4, ===0} relation; // the relation to use for the test
	char1024 value; // the value to compare with for binary tests
	char1024 within; // the bounds within which the value must bed compared
	char1024 lower; // the lower bound to compare with for interval tests
	char1024 upper; // the upper bound to compare with for interval tests
}

class assert {
	enumeration {NONE=3, FALSE=2, TRUE=1} status; // desired outcome of assert test
	char1024 target; // the target property to test
	char32 part; // the target property part to test
	enumeration {outside=7, inside=6, !==3, >==2, >=5, <==1, <=4, ===0} relation; // the relation to use for the test
	char1024 value; // the value to compare with for binary tests
	char1024 within; // the bounds within which the value must bed compared
	char1024 lower; // the lower bound to compare with for interval tests
	char1024 upper; // the upper bound to compare with for interval tests
}

class complex_assert {
	enumeration {ASSERT_NONE=3, ASSERT_FALSE=2, ASSERT_TRUE=1} status;
	enumeration {ONCE_DONE=2, ONCE_TRUE=1, ONCE_FALSE=0} once;
	enumeration {ANGLE=4, MAGNITUDE=3, IMAGINARY=2, REAL=1, FULL=0} operation;
	complex value;
	double within;
	char1024 target;
}

class double_assert {
	enumeration {ASSERT_NONE=3, ASSERT_FALSE=2, ASSERT_TRUE=1} status;
	enumeration {ONCE_DONE=2, ONCE_TRUE=1, ONCE_FALSE=0} once;
	enumeration {WITHIN_RATIO=1, WITHIN_VALUE=0} within_mode;
	double value;
	double within;
	char1024 target;
}

class enum_assert {
	enumeration {ASSERT_NONE=3, ASSERT_FALSE=2, ASSERT_TRUE=1} status;
	int32 value;
	char1024 target;
}


class climate {
	function calculate_solar_radiation_degrees();
	function calculate_solar_radiation_radians();
	function calculate_solar_radiation_shading_degrees();
	function calculate_solar_radiation_shading_radians();
	function calculate_solar_elevation();
	function calculate_solar_azimuth();
	function calc_solpos_radiation_shading_degrees();
	function calc_solpos_radiation_shading_radians();
	double solar_elevation;
	double solar_azimuth;
	char32 city;
	char1024 tmyfile;
	double temperature[degF];
	double humidity[%];
	double solar_flux[W/sf];
	double solar_direct[W/sf];
	double solar_diffuse[W/sf];
	double solar_global[W/sf];
	double extraterrestrial_direct_normal[W/sf];
	double pressure[mbar];
	double wind_speed[mph];
	double wind_dir[deg];
	double wind_gust[mph];
	double record.low[degF];
	int32 record.low_day;
	double record.high[degF];
	int32 record.high_day;
	double record.solar[W/sf];
	double rainfall[in/h];
	double snowdepth[in];
	enumeration {QUADRATIC=2, LINEAR=1, NONE=0} interpolate; // the interpolation mode used on the climate data
	double solar_horiz;
	double solar_north;
	double solar_northeast;
	double solar_east;
	double solar_southeast;
	double solar_south;
	double solar_southwest;
	double solar_west;
	double solar_northwest;
	double solar_raw[W/sf];
	double ground_reflectivity[pu];
	object reader;
	char1024 forecast; // forecasting specifications
}

class climate {
	function calculate_solar_radiation_degrees();
	function calculate_solar_radiation_radians();
	function calculate_solar_radiation_shading_degrees();
	function calculate_solar_radiation_shading_radians();
	function calculate_solar_elevation();
	function calculate_solar_azimuth();
	function calc_solpos_radiation_shading_degrees();
	function calc_solpos_radiation_shading_radians();
	double solar_elevation;
	double solar_azimuth;
	char32 city;
	char1024 tmyfile;
	double temperature[degF];
	double humidity[%];
	double solar_flux[W/sf];
	double solar_direct[W/sf];
	double solar_diffuse[W/sf];
	double solar_global[W/sf];
	double extraterrestrial_direct_normal[W/sf];
	double pressure[mbar];
	double wind_speed[mph];
	double wind_dir[deg];
	double wind_gust[mph];
	double record.low[degF];
	int32 record.low_day;
	double record.high[degF];
	int32 record.high_day;
	double record.solar[W/sf];
	double rainfall[in/h];
	double snowdepth[in];
	enumeration {QUADRATIC=2, LINEAR=1, NONE=0} interpolate; // the interpolation mode used on the climate data
	double solar_horiz;
	double solar_north;
	double solar_northeast;
	double solar_east;
	double solar_southeast;
	double solar_south;
	double solar_southwest;
	double solar_west;
	double solar_northwest;
	double solar_raw[W/sf];
	double ground_reflectivity[pu];
	object reader;
	char1024 forecast; // forecasting specifications
}

class csv_reader {
	int32 index;
	char32 city_name;
	char32 state_name;
	double lat_deg;
	double lat_min;
	double long_deg;
	double long_min;
	double low_temp;
	double high_temp;
	double peak_solar;
	int32 elevation;
	enumeration {ERROR=2, OPEN=1, INIT=0} status;
	char32 timefmt;
	char32 timezone;
	double timezone_offset;
	char256 columns;
	char256 filename;
}

class weather {
	double temperature[degF];
	double humidity[%];
	double solar_dir[W/sf];
	double solar_direct[W/sf];
	double solar_diff[W/sf];
	double solar_diffuse[W/sf];
	double solar_global[W/sf];
	double wind_speed[mph];
	double rainfall[in/h];
	double snowdepth[in];
	double pressure[mbar];
	int16 month;
	int16 day;
	int16 hour;
	int16 minute;
	int16 second;
}


class battery {
	enumeration {POWER_VOLTAGE_HYBRID=7, VOLTAGE_CONTROLLED=6, POWER_DRIVEN=5, SUPPLY_DRIVEN=4, CONSTANT_PF=3, CONSTANT_PQ=2, CONSTANT_V=1, UNKNOWN=0} generator_mode;
	enumeration {LINEAR_TEMPERATURE=1, NONE=0} additional_controls;
	enumeration {ONLINE=2, OFFLINE=1} generator_status;
	enumeration {LARGE=4, MED_HIGH_ENERGY=3, MED_COMMERCIAL=2, SMALL=1, HOUSEHOLD=5} rfb_size;
	enumeration {DC=1, AC=2} power_type;
	enumeration {CONFLICTED=5, EMPTY=4, FULL=3, WAITING=0, DISCHARGING=2, CHARGING=1} battery_state;
	double number_battery_state_changes;
	double monitored_power[W];
	double power_set_high[W];
	double power_set_low[W];
	double power_set_high_highT[W];
	double power_set_low_highT[W];
	double check_power_low[W];
	double check_power_high[W];
	double voltage_set_high[V];
	double voltage_set_low[V];
	double deadband[V];
	double sensitivity;
	double high_temperature;
	double midpoint_temperature;
	double low_temperature;
	double scheduled_power[W];
	double Rinternal[Ohm];
	double V_Max[V];
	complex I_Max[A];
	double E_Max[Wh];
	double P_Max[W];
	double power_factor;
	double Energy[Wh];
	double efficiency[unit];
	double base_efficiency[unit];
	double parasitic_power_draw[W];
	double Rated_kVA[kVA];
	complex V_Out[V];
	complex I_Out[A];
	complex VA_Out[VA];
	complex V_In[V];
	complex I_In[A];
	complex V_Internal[V];
	complex I_Internal[A];
	complex I_Prev[A];
	double power_transferred;
	bool use_internal_battery_model;
	enumeration {LEAD_ACID=2, LI_ION=1, UNKNOWON=0} battery_type;
	double nominal_voltage[V];
	double rated_power[W];
	double battery_capacity[Wh];
	double round_trip_efficiency[pu];
	double state_of_charge[pu];
	double battery_load[W];
	double reserve_state_of_charge[pu];
}

class dc_dc_converter {
	enumeration {BUCK_BOOST=2, BOOST=1, BUCK=0} dc_dc_converter_type;
	enumeration {SUPPLY_DRIVEN=5, CONSTANT_PF=4, CONSTANT_PQ=2, CONSTANT_V=1, UNKNOWN=0} generator_mode;
	complex V_Out[V];
	complex I_Out[A];
	complex Vdc[V];
	complex VA_Out[VA];
	double P_Out;
	double Q_Out;
	double service_ratio;
	complex V_In[V];
	complex I_In[A];
	complex VA_In[VA];
	set {S=112, N=8, C=4, B=2, A=1} phases;
}

class diesel_dg {
	function interupdate_gen_object();
	function postupdate_gen_object();
	enumeration {CONSTANTP=2, CONSTANTPQ=3, CONSTANTE=1, UNKNOWN=0} Gen_mode;
	enumeration {ONLINE=2, OFFLINE=1, UNKNOWN=0} Gen_status;
	enumeration {DYN_SYNCHRONOUS=3, SYNCHRONOUS=2, INDUCTION=1} Gen_type; // Dynamics-capable implementation of synchronous diesel generator
	double pf; // desired power factor
	double GenElecEff; // calculated electrical efficiency of generator
	complex TotalOutputPow[VA]; // total complex power generated
	double TotalRealPow[W]; // total real power generated
	double TotalReacPow[VAr]; // total reactive power generated
	double speed[1/min]; // speed of an engine
	double cylinders; // Total number of cylinders in a diesel engine
	double stroke; // category of internal combustion engines
	double torque[N]; // Net brake load
	double pressure[N/m^2]; // 
	double time_operation[min]; // 
	double fuel[kg]; // fuel consumption
	double w_coolingwater[kg]; // weight of cooling water supplied per minute
	double inlet_temperature[degC]; // Inlet temperature of cooling water in degC
	double outlet_temperature[degC]; // outlet temperature of cooling water in degC
	double air_fuel[kg]; // Air used per kg fuel
	double room_temperature[degC]; // Room temperature in degC
	double exhaust_temperature[degC]; // exhaust gas temperature in degC
	double cylinder_length[m]; // length of the cylinder, used in efficiency calculations
	double cylinder_radius[m]; // inner radius of cylinder, used in efficiency calculations
	double brake_diameter[m]; // diameter of brake, used in efficiency calculations
	double calotific_fuel[kJ/kg]; // calorific value of fuel
	double steam_exhaust[kg]; // steam formed per kg of fuel in the exhaust
	double specific_heat_steam[kJ/kg/K]; // specific heat of steam in exhaust
	double specific_heat_dry[kJ/kg/K]; // specific heat of dry exhaust gases
	double indicated_hp[W]; // Indicated horse power is the power developed inside the cylinder
	double brake_hp[W]; // brake horse power is the output of the engine at the shaft measured by a dynamometer
	double thermal_efficiency; // thermal efficiency or mechanical efiiciency of the engine is efined as bp/ip
	double energy_supplied[kJ]; // energy supplied during the trail
	double heat_equivalent_ip[kJ]; // heat equivalent of IP in a given time of operation
	double energy_coolingwater[kJ]; // energy carried away by cooling water
	double mass_exhaustgas[kg]; // mass of dry exhaust gas
	double energy_exhaustgas[kJ]; // energy carried away by dry exhaust gases
	double energy_steam[kJ]; // energy carried away by steam
	double total_energy_exhaustgas[kJ]; // total energy carried away by dry exhaust gases is the sum of energy carried away bt steam and energy carried away by dry exhaust gases
	double unaccounted_energyloss[kJ]; // unaccounted for energy loss
	double Pconv[kW]; // Converted power = Mechanical input - (F & W loasses + Stray losses + Core losses)
	double Rated_V[V]; // nominal line-line voltage in Volts
	double Rated_VA[VA]; // nominal capacity in VA
	complex power_out_A[VA]; // Output power of phase A
	complex power_out_B[VA]; // Output power of phase B
	complex power_out_C[VA]; // Output power of phase C
	double Rs; // internal transient resistance in p.u.
	double Xs; // internal transient impedance in p.u.
	double Rg; // grounding resistance in p.u.
	double Xg; // grounding impedance in p.u.
	complex voltage_A[V]; // voltage at generator terminal, phase A
	complex voltage_B[V]; // voltage at generator terminal, phase B
	complex voltage_C[V]; // voltage at generator terminal, phase C
	complex current_A[A]; // current generated at generator terminal, phase A
	complex current_B[A]; // current generated at generator terminal, phase B
	complex current_C[A]; // current generated at generator terminal, phase C
	complex EfA[V]; // induced voltage on phase A
	complex EfB[V]; // induced voltage on phase B
	complex EfC[V]; // induced voltage on phase C
	double omega_ref[rad/s]; // Reference frequency of generator (rad/s)
	double inertia; // Inertial constant (H) of generator
	double damping; // Damping constant (D) of generator
	double number_poles; // Number of poles in the generator
	double Ra[pu]; // Stator resistance (p.u.)
	double Xd[pu]; // d-axis reactance (p.u.)
	double Xq[pu]; // q-axis reactance (p.u.)
	double Xdp[pu]; // d-axis transient reactance (p.u.)
	double Xqp[pu]; // q-axis transient reactance (p.u.)
	double Xdpp[pu]; // d-axis subtransient reactance (p.u.)
	double Xqpp[pu]; // q-axis subtransient reactance (p.u.)
	double Xl[pu]; // Leakage reactance (p.u.)
	double Tdp[s]; // d-axis short circuit time constant (s)
	double Tdop[s]; // d-axis open circuit time constant (s)
	double Tqop[s]; // q-axis open circuit time constant (s)
	double Tdopp[s]; // d-axis open circuit subtransient time constant (s)
	double Tqopp[s]; // q-axis open circuit subtransient time constant (s)
	double Ta[s]; // Armature short-circuit time constant (s)
	complex X0[pu]; // Zero sequence impedance (p.u.)
	complex X2[pu]; // Negative sequence impedance (p.u.)
	double rotor_speed_convergence[rad]; // Convergence criterion on rotor speed used to determine when to exit deltamode
	double rotor_angle[rad]; // rotor angle state variable
	double rotor_speed[rad/s]; // machine speed state variable
	double field_voltage[pu]; // machine field voltage state variable
	double flux1d[pu]; // machine transient flux on d-axis state variable
	double flux2q[pu]; // machine subtransient flux on q-axis state variable
	complex EpRotated[pu]; // d-q rotated E-prime internal voltage state variable
	complex VintRotated[pu]; // d-q rotated Vint voltage state variable
	complex Eint_A[pu]; // Unrotated, unsequenced phase A internal voltage
	complex Eint_B[pu]; // Unrotated, unsequenced phase B internal voltage
	complex Eint_C[pu]; // Unrotated, unsequenced phase C internal voltage
	complex Irotated[pu]; // d-q rotated sequence current state variable
	complex pwr_electric[VA]; // Current electrical output of machine
	double pwr_mech[W]; // Current mechanical output of machine
	enumeration {SEXS=2, NO_EXC=1} Exciter_type; // Simplified Excitation System
	double KA[pu]; // Exciter gain (p.u.)
	double TA[s]; // Exciter time constant (seconds)
	double TB[s]; // Exciter transient gain reduction time constant (seconds)
	double TC[s]; // Exciter transient gain reduction time constant (seconds)
	double EMAX[pu]; // Exciter upper limit (p.u.)
	double EMIN[pu]; // Exciter lower limit (p.u.)
	double Vterm_max[pu]; // Upper voltage limit for super-second (p.u.)
	double Vterm_min[pu]; // Lower voltage limit for super-second (p.u.)
	double vset[pu]; // Exciter voltage set point state variable
	double bias; // Exciter bias state variable
	double xe; // Exciter state variable
	double xb; // Exciter state variable
	enumeration {DEGOV1=2, NO_GOV=1} Governor_type; // DEGOV1 Woodward Diesel Governor
	double R[pu]; // Governor droop constant (p.u.)
	double T1[s]; // Governor electric control box time constant (s)
	double T2[s]; // Governor electric control box time constant (s)
	double T3[s]; // Governor electric control box time constant (s)
	double T4[s]; // Governor actuator time constant (s)
	double T5[s]; // Governor actuator time constant (s)
	double T6[s]; // Governor actuator time constant (s)
	double K[pu]; // Governor actuator gain
	double TMAX[pu]; // Governor actuator upper limit (p.u.)
	double TMIN[pu]; // Governor actuator lower limit (p.u.)
	double TD[s]; // Governor combustion delay (s)
	double wref[pu]; // Governor reference frequency state variable
	double x1; // Governor electric box state variable
	double x2; // Governor electric box state variable
	double x4; // Governor electric box state variable
	double x5; // Governor electric box state variable
	double x6; // Governor electric box state variable
	double throttle; // Governor electric box state variable
	set {S=112, N=8, C=4, B=2, A=1} phases; // Specifies which phases to connect to - currently not supported and assumes three-phase connection
}

class diesel_dg {
	function interupdate_gen_object();
	function postupdate_gen_object();
	enumeration {CONSTANTP=2, CONSTANTPQ=3, CONSTANTE=1, UNKNOWN=0} Gen_mode;
	enumeration {ONLINE=2, OFFLINE=1, UNKNOWN=0} Gen_status;
	enumeration {DYN_SYNCHRONOUS=3, SYNCHRONOUS=2, INDUCTION=1} Gen_type; // Dynamics-capable implementation of synchronous diesel generator
	double pf; // desired power factor
	double GenElecEff; // calculated electrical efficiency of generator
	complex TotalOutputPow[VA]; // total complex power generated
	double TotalRealPow[W]; // total real power generated
	double TotalReacPow[VAr]; // total reactive power generated
	double speed[1/min]; // speed of an engine
	double cylinders; // Total number of cylinders in a diesel engine
	double stroke; // category of internal combustion engines
	double torque[N]; // Net brake load
	double pressure[N/m^2]; // 
	double time_operation[min]; // 
	double fuel[kg]; // fuel consumption
	double w_coolingwater[kg]; // weight of cooling water supplied per minute
	double inlet_temperature[degC]; // Inlet temperature of cooling water in degC
	double outlet_temperature[degC]; // outlet temperature of cooling water in degC
	double air_fuel[kg]; // Air used per kg fuel
	double room_temperature[degC]; // Room temperature in degC
	double exhaust_temperature[degC]; // exhaust gas temperature in degC
	double cylinder_length[m]; // length of the cylinder, used in efficiency calculations
	double cylinder_radius[m]; // inner radius of cylinder, used in efficiency calculations
	double brake_diameter[m]; // diameter of brake, used in efficiency calculations
	double calotific_fuel[kJ/kg]; // calorific value of fuel
	double steam_exhaust[kg]; // steam formed per kg of fuel in the exhaust
	double specific_heat_steam[kJ/kg/K]; // specific heat of steam in exhaust
	double specific_heat_dry[kJ/kg/K]; // specific heat of dry exhaust gases
	double indicated_hp[W]; // Indicated horse power is the power developed inside the cylinder
	double brake_hp[W]; // brake horse power is the output of the engine at the shaft measured by a dynamometer
	double thermal_efficiency; // thermal efficiency or mechanical efiiciency of the engine is efined as bp/ip
	double energy_supplied[kJ]; // energy supplied during the trail
	double heat_equivalent_ip[kJ]; // heat equivalent of IP in a given time of operation
	double energy_coolingwater[kJ]; // energy carried away by cooling water
	double mass_exhaustgas[kg]; // mass of dry exhaust gas
	double energy_exhaustgas[kJ]; // energy carried away by dry exhaust gases
	double energy_steam[kJ]; // energy carried away by steam
	double total_energy_exhaustgas[kJ]; // total energy carried away by dry exhaust gases is the sum of energy carried away bt steam and energy carried away by dry exhaust gases
	double unaccounted_energyloss[kJ]; // unaccounted for energy loss
	double Pconv[kW]; // Converted power = Mechanical input - (F & W loasses + Stray losses + Core losses)
	double Rated_V[V]; // nominal line-line voltage in Volts
	double Rated_VA[VA]; // nominal capacity in VA
	complex power_out_A[VA]; // Output power of phase A
	complex power_out_B[VA]; // Output power of phase B
	complex power_out_C[VA]; // Output power of phase C
	double Rs; // internal transient resistance in p.u.
	double Xs; // internal transient impedance in p.u.
	double Rg; // grounding resistance in p.u.
	double Xg; // grounding impedance in p.u.
	complex voltage_A[V]; // voltage at generator terminal, phase A
	complex voltage_B[V]; // voltage at generator terminal, phase B
	complex voltage_C[V]; // voltage at generator terminal, phase C
	complex current_A[A]; // current generated at generator terminal, phase A
	complex current_B[A]; // current generated at generator terminal, phase B
	complex current_C[A]; // current generated at generator terminal, phase C
	complex EfA[V]; // induced voltage on phase A
	complex EfB[V]; // induced voltage on phase B
	complex EfC[V]; // induced voltage on phase C
	double omega_ref[rad/s]; // Reference frequency of generator (rad/s)
	double inertia; // Inertial constant (H) of generator
	double damping; // Damping constant (D) of generator
	double number_poles; // Number of poles in the generator
	double Ra[pu]; // Stator resistance (p.u.)
	double Xd[pu]; // d-axis reactance (p.u.)
	double Xq[pu]; // q-axis reactance (p.u.)
	double Xdp[pu]; // d-axis transient reactance (p.u.)
	double Xqp[pu]; // q-axis transient reactance (p.u.)
	double Xdpp[pu]; // d-axis subtransient reactance (p.u.)
	double Xqpp[pu]; // q-axis subtransient reactance (p.u.)
	double Xl[pu]; // Leakage reactance (p.u.)
	double Tdp[s]; // d-axis short circuit time constant (s)
	double Tdop[s]; // d-axis open circuit time constant (s)
	double Tqop[s]; // q-axis open circuit time constant (s)
	double Tdopp[s]; // d-axis open circuit subtransient time constant (s)
	double Tqopp[s]; // q-axis open circuit subtransient time constant (s)
	double Ta[s]; // Armature short-circuit time constant (s)
	complex X0[pu]; // Zero sequence impedance (p.u.)
	complex X2[pu]; // Negative sequence impedance (p.u.)
	double rotor_speed_convergence[rad]; // Convergence criterion on rotor speed used to determine when to exit deltamode
	double rotor_angle[rad]; // rotor angle state variable
	double rotor_speed[rad/s]; // machine speed state variable
	double field_voltage[pu]; // machine field voltage state variable
	double flux1d[pu]; // machine transient flux on d-axis state variable
	double flux2q[pu]; // machine subtransient flux on q-axis state variable
	complex EpRotated[pu]; // d-q rotated E-prime internal voltage state variable
	complex VintRotated[pu]; // d-q rotated Vint voltage state variable
	complex Eint_A[pu]; // Unrotated, unsequenced phase A internal voltage
	complex Eint_B[pu]; // Unrotated, unsequenced phase B internal voltage
	complex Eint_C[pu]; // Unrotated, unsequenced phase C internal voltage
	complex Irotated[pu]; // d-q rotated sequence current state variable
	complex pwr_electric[VA]; // Current electrical output of machine
	double pwr_mech[W]; // Current mechanical output of machine
	enumeration {SEXS=2, NO_EXC=1} Exciter_type; // Simplified Excitation System
	double KA[pu]; // Exciter gain (p.u.)
	double TA[s]; // Exciter time constant (seconds)
	double TB[s]; // Exciter transient gain reduction time constant (seconds)
	double TC[s]; // Exciter transient gain reduction time constant (seconds)
	double EMAX[pu]; // Exciter upper limit (p.u.)
	double EMIN[pu]; // Exciter lower limit (p.u.)
	double Vterm_max[pu]; // Upper voltage limit for super-second (p.u.)
	double Vterm_min[pu]; // Lower voltage limit for super-second (p.u.)
	double vset[pu]; // Exciter voltage set point state variable
	double bias; // Exciter bias state variable
	double xe; // Exciter state variable
	double xb; // Exciter state variable
	enumeration {DEGOV1=2, NO_GOV=1} Governor_type; // DEGOV1 Woodward Diesel Governor
	double R[pu]; // Governor droop constant (p.u.)
	double T1[s]; // Governor electric control box time constant (s)
	double T2[s]; // Governor electric control box time constant (s)
	double T3[s]; // Governor electric control box time constant (s)
	double T4[s]; // Governor actuator time constant (s)
	double T5[s]; // Governor actuator time constant (s)
	double T6[s]; // Governor actuator time constant (s)
	double K[pu]; // Governor actuator gain
	double TMAX[pu]; // Governor actuator upper limit (p.u.)
	double TMIN[pu]; // Governor actuator lower limit (p.u.)
	double TD[s]; // Governor combustion delay (s)
	double wref[pu]; // Governor reference frequency state variable
	double x1; // Governor electric box state variable
	double x2; // Governor electric box state variable
	double x4; // Governor electric box state variable
	double x5; // Governor electric box state variable
	double x6; // Governor electric box state variable
	double throttle; // Governor electric box state variable
	set {S=112, N=8, C=4, B=2, A=1} phases; // Specifies which phases to connect to - currently not supported and assumes three-phase connection
}

class energy_storage {
	enumeration {SUPPLY_DRIVEN=4, CONSTANT_PF=3, CONSTANT_PQ=2, CONSTANT_V=1, UNKNOWN=0} generator_mode;
	enumeration {ONLINE=2, OFFLINE=1} generator_status;
	enumeration {DC=0, AC=1} power_type;
	double Rinternal;
	double V_Max[V];
	complex I_Max[A];
	double E_Max;
	double Energy;
	double efficiency;
	double Rated_kVA[kVA];
	complex V_Out[V];
	complex I_Out[A];
	complex VA_Out[VA];
	complex V_In[V];
	complex I_In[A];
	complex V_Internal[V];
	complex I_Internal[A];
	complex I_Prev[A];
	set {S=112, N=8, C=4, B=2, A=1} phases;
}

class inverter {
	enumeration {FOUR_QUADRANT=4, PWM=3, TWELVE_PULSE=2, SIX_PULSE=1, TWO_PULSE=0} inverter_type;
	enumeration {LOAD_FOLLOWING=5, CONSTANT_PF=2, CONSTANT_PQ=1, NONE=0} four_quadrant_control_mode;
	enumeration {ONLINE=2, OFFLINE=1} generator_status;
	enumeration {SUPPLY_DRIVEN=5, CONSTANT_PF=4, CONSTANT_PQ=2, CONSTANT_V=1, UNKNOWN=0} generator_mode;
	complex V_In[V];
	complex I_In[A];
	complex VA_In[VA];
	complex VA_Out[VA];
	complex Vdc[V];
	complex phaseA_V_Out[V];
	complex phaseB_V_Out[V];
	complex phaseC_V_Out[V];
	complex phaseA_I_Out[V];
	complex phaseB_I_Out[V];
	complex phaseC_I_Out[V];
	complex power_A[VA];
	complex power_B[VA];
	complex power_C[VA];
	double P_Out[VA];
	double Q_Out[VAr];
	double power_in[W];
	double rated_power[VA];
	double rated_battery_power[W];
	double inverter_efficiency;
	double battery_soc[pu];
	double soc_reserve[pu];
	double power_factor[unit];
	set {S=112, N=8, C=4, B=2, A=1} phases;
	bool use_multipoint_efficiency;
	enumeration {XANTREX=3, SMA=2, FRONIUS=1, NONE=0} inverter_manufacturer;
	double maximum_dc_power;
	double maximum_dc_voltage;
	double minimum_dc_power;
	double c_0;
	double c_1;
	double c_2;
	double c_3;
	object sense_object; // name of the object the inverter is trying to mitigate the load on (node/link) in LOAD_FOLLOWING
	double max_charge_rate[W]; // maximum rate the battery can be charged in LOAD_FOLLOWING
	double max_discharge_rate[W]; // maximum rate the battery can be discharged in LOAD_FOLLOWING
	double charge_on_threshold[W]; // power level at which the inverter should try charging the battery in LOAD_FOLLOWING
	double charge_off_threshold[W]; // power level at which the inverter should cease charging the battery in LOAD_FOLLOWING
	double discharge_on_threshold[W]; // power level at which the inverter should try discharging the battery in LOAD_FOLLOWING
	double discharge_off_threshold[W]; // power level at which the inverter should cease discharging the battery in LOAD_FOLLOWING
	double excess_input_power[W]; // Excess power at the input of the inverter that is otherwise just lost, or could be shunted to a battery
	double charge_lockout_time[s]; // Lockout time when a charging operation occurs before another LOAD_FOLLOWING dispatch operation can occur
	double discharge_lockout_time[s]; // Lockout time when a discharging operation occurs before another LOAD_FOLLOWING dispatch operation can occur
}

class microturbine {
	enumeration {SUPPLY_DRIVEN=5, CONSTANT_PF=4, CONSTANT_PQ=2, CONSTANT_V=1, UNKNOWN=0} generator_mode;
	enumeration {ONLINE=2, OFFLINE=1} generator_status;
	enumeration {DC=1, AC=2} power_type;
	double Rinternal;
	double Rload;
	double V_Max[V];
	complex I_Max[A];
	double frequency[Hz];
	double Max_Frequency[Hz];
	double Min_Frequency[Hz];
	double Fuel_Used[kVA];
	double Heat_Out[kVA];
	double KV;
	double Power_Angle;
	double Max_P[kW];
	double Min_P[kW];
	complex phaseA_V_Out[kV];
	complex phaseB_V_Out[kV];
	complex phaseC_V_Out[kV];
	complex phaseA_I_Out[A];
	complex phaseB_I_Out[A];
	complex phaseC_I_Out[A];
	complex power_A_Out;
	complex power_B_Out;
	complex power_C_Out;
	complex VA_Out;
	double pf_Out;
	complex E_A_Internal;
	complex E_B_Internal;
	complex E_C_Internal;
	double efficiency;
	double Rated_kVA[kVA];
	set {S=112, N=8, C=4, B=2, A=1} phases;
}

class power_electronics {
	enumeration {SUPPLY_DRIVEN=5, CONSTANT_PF=4, CONSTANT_PQ=2, CONSTANT_V=1, UNKNOWN=0} generator_mode;
	enumeration {ONLINE=2, OFFLINE=1} generator_status;
	enumeration {CURRENT_SOURCED=2, VOLTAGE_SOURCED=1} converter_type;
	enumeration {DARLINGTON=7, IBJT=6, JFET=5, SCR=4, MOSFET=3, BJT=2, IDEAL_SWITCH=1} switch_type;
	enumeration {BAND_PASS=4, BAND_STOP=3, HIGH_PASS=2, LOW_PASS=1} filter_type;
	enumeration {PARALLEL_RESONANT=5, SERIES_RESONANT=4, INDUCTIVE=3, CAPACITVE=2, IDEAL_FILTER=1} filter_implementation;
	enumeration {F240HZ=3, F180HZ=2, F120HZ=1} filter_frequency;
	enumeration {DC=1, AC=2} power_type;
	double Rated_kW[kW];
	double Max_P[kW];
	double Min_P[kW];
	double Rated_kVA[kVA];
	double Rated_kV[kV];
	set {S=112, N=8, C=4, B=2, A=1} phases;
}

class rectifier {
	enumeration {TWELVE_PULSE=4, SIX_PULSE=3, THREE_PULSE=2, TWO_PULSE=1, ONE_PULSE=0} rectifier_type;
	enumeration {SUPPLY_DRIVEN=5, CONSTANT_PF=4, CONSTANT_PQ=2, CONSTANT_V=1, UNKNOWN=0} generator_mode;
	complex V_Out[V];
	double V_Rated[V];
	complex I_Out[A];
	complex VA_Out[VA];
	double P_Out;
	double Q_Out;
	complex Vdc[V];
	complex voltage_A[V];
	complex voltage_B[V];
	complex voltage_C[V];
	complex current_A[V];
	complex current_B[V];
	complex current_C[V];
	complex power_A_In[VA];
	complex power_B_In[VA];
	complex power_C_In[VA];
	set {S=112, N=8, C=4, B=2, A=1} phases;
}

class solar {
	enumeration {SUPPLY_DRIVEN=5, CONSTANT_PF=4, CONSTANT_PQ=2, CONSTANT_V=1, UNKNOWN=0} generator_mode;
	enumeration {ONLINE=2, OFFLINE=1} generator_status;
	enumeration {CONCENTRATOR=5, THIN_FILM_GA_AS=4, AMORPHOUS_SILICON=3, MULTI_CRYSTAL_SILICON=2, SINGLE_CRYSTAL_SILICON=1} panel_type;
	enumeration {DC=1, AC=2} power_type;
	enumeration {GROUND_MOUNTED=2, ROOF_MOUNTED=1} INSTALLATION_TYPE;
	enumeration {PLAYERVALUE=2, SOLPOS=1, DEFAULT=0} SOLAR_TILT_MODEL; // solar tilt model used to compute insolation values
	enumeration {FLATPLATE=1, DEFAULT=0} SOLAR_POWER_MODEL;
	double a_coeff; // a coefficient for module temperature correction formula
	double b_coeff[s/m]; // b coefficient for module temperature correction formula
	double dT_coeff[m*m*degC/kW]; // Temperature difference coefficient for module temperature correction formula
	double T_coeff[%/degC]; // Maximum power temperature coefficient for module temperature correction formula
	double NOCT[degF];
	double Tmodule[degF];
	double Tambient[degC];
	double wind_speed[mph];
	double ambient_temperature[degF]; // Current ambient temperature of air
	double Insolation[W/sf];
	double Rinternal[Ohm];
	double Rated_Insolation[W/sf];
	double Pmax_temp_coeff;
	double Voc_temp_coeff;
	complex V_Max[V];
	complex Voc_Max[V];
	complex Voc[V];
	double efficiency[unit];
	double area[sf];
	double soiling[pu]; // Soiling of array factor - representing dirt on array
	double derating[pu]; // Panel derating to account for manufacturing variances
	double Tcell[degC];
	double Rated_kVA[kVA];
	complex P_Out[kW];
	complex V_Out[V];
	complex I_Out[A];
	complex VA_Out[VA];
	object weather;
	double shading_factor[pu]; // Shading factor for scaling solar power to the array
	double tilt_angle[deg]; // Tilt angle of PV array
	double orientation_azimuth[deg]; // Facing direction of the PV array
	bool latitude_angle_fix; // Fix tilt angle to installation latitude value
	enumeration {FIXED_AXIS=1, DEFAULT=0} orientation;
	set {S=112, N=8, C=4, B=2, A=1} phases;
}

class windturb_dg {
	enumeration {ONLINE=2, OFFLINE=1} Gen_status; // Generator is currently available to supply power
	enumeration {SYNCHRONOUS=2, INDUCTION=1} Gen_type; // Standard synchronous generator; is also used to 'fake' a doubly-fed induction generator for now
	enumeration {CONSTANTPQ=3, CONSTANTP=2, CONSTANTE=1} Gen_mode; // Maintains the real and reactive output at the terminals - currently unsupported
	enumeration {BERGEY_10kW=9, GE_25MW=8, VESTAS_V82=7, USER_DEFINED=6, GENERIC_IND_LARGE=5, GENERIC_IND_MID=4, GENERIC_IND_SMALL=3, GENERIC_SYNCH_LARGE=2, GENERIC_SYNCH_MID=1, GENERIC_SYNCH_SMALL=0} Turbine_Model; // Sets all defaults to represent the power output of a Bergey 10kW turbine
	double turbine_height[m]; // Describes the height of the wind turbine hub above the ground
	double roughness_length_factor; // European Wind Atlas unitless correction factor for adjusting wind speed at various heights above ground and terrain types, default=0.055
	double blade_diam[m]; // Diameter of blades
	double blade_diameter[m]; // Diameter of blades
	double cut_in_ws[m/s]; // Minimum wind speed for generator operation
	double cut_out_ws[m/s]; // Maximum wind speed for generator operation
	double ws_rated[m/s]; // Rated wind speed for generator operation
	double ws_maxcp[m/s]; // Wind speed at which generator reaches maximum Cp
	double Cp_max[pu]; // Maximum coefficient of performance
	double Cp_rated[pu]; // Rated coefficient of performance
	double Cp[pu]; // Calculated coefficient of performance
	double Rated_VA[VA]; // Rated generator power output
	double Rated_V[V]; // Rated generator terminal voltage
	double Pconv[W]; // Amount of electrical power converted from mechanical power delivered
	double P_converted[W]; // Amount of electrical power converted from mechanical power delivered
	double GenElecEff[%]; // Calculated generator electrical efficiency
	double generator_efficiency[%]; // Calculated generator electrical efficiency
	double TotalRealPow[W]; // Total real power output
	double total_real_power[W]; // Total real power output
	double TotalReacPow[VA]; // Total reactive power output
	double total_reactive_power[VA]; // Total reactive power output
	complex power_A[VA]; // Total complex power injected on phase A
	complex power_B[VA]; // Total complex power injected on phase B
	complex power_C[VA]; // Total complex power injected on phase C
	double WSadj[m/s]; // Speed of wind at hub height
	double wind_speed_adjusted[m/s]; // Speed of wind at hub height
	double Wind_Speed[m/s]; // Wind speed at 5-15m level (typical measurement height)
	double wind_speed[m/s]; // Wind speed at 5-15m level (typical measurement height)
	double air_density[kg/m^3]; // Estimated air density
	double R_stator[pu]; // Induction generator primary stator resistance in p.u.
	double X_stator[pu]; // Induction generator primary stator reactance in p.u.
	double R_rotor[pu]; // Induction generator primary rotor resistance in p.u.
	double X_rotor[pu]; // Induction generator primary rotor reactance in p.u.
	double R_core[pu]; // Induction generator primary core resistance in p.u.
	double X_magnetic[pu]; // Induction generator primary core reactance in p.u.
	double Max_Vrotor[pu]; // Induction generator maximum induced rotor voltage in p.u., e.g. 1.2
	double Min_Vrotor[pu]; // Induction generator minimum induced rotor voltage in p.u., e.g. 0.8
	double Rs[pu]; // Synchronous generator primary stator resistance in p.u.
	double Xs[pu]; // Synchronous generator primary stator reactance in p.u.
	double Rg[pu]; // Synchronous generator grounding resistance in p.u.
	double Xg[pu]; // Synchronous generator grounding reactance in p.u.
	double Max_Ef[pu]; // Synchronous generator maximum induced rotor voltage in p.u., e.g. 0.8
	double Min_Ef[pu]; // Synchronous generator minimum induced rotor voltage in p.u., e.g. 0.8
	double pf[pu]; // Desired power factor in CONSTANTP mode (can be modified over time)
	double power_factor[pu]; // Desired power factor in CONSTANTP mode (can be modified over time)
	complex voltage_A[V]; // Terminal voltage on phase A
	complex voltage_B[V]; // Terminal voltage on phase B
	complex voltage_C[V]; // Terminal voltage on phase C
	complex current_A[A]; // Calculated terminal current on phase A
	complex current_B[A]; // Calculated terminal current on phase B
	complex current_C[A]; // Calculated terminal current on phase C
	complex EfA[V]; // Synchronous generator induced voltage on phase A
	complex EfB[V]; // Synchronous generator induced voltage on phase B
	complex EfC[V]; // Synchronous generator induced voltage on phase C
	complex Vrotor_A[V]; // Induction generator induced voltage on phase A in p.u.
	complex Vrotor_B[V]; // Induction generator induced voltage on phase B in p.u.
	complex Vrotor_C[V]; // Induction generator induced voltage on phase C in p.u.
	complex Irotor_A[V]; // Induction generator induced current on phase A in p.u.
	complex Irotor_B[V]; // Induction generator induced current on phase B in p.u.
	complex Irotor_C[V]; // Induction generator induced current on phase C in p.u.
	set {S=112, N=8, C=4, B=2, A=1} phases; // Specifies which phases to connect to - currently not supported and assumes three-phase connection
}


FAILED on module name glsolvers
FAILED on module name glxmatlab
class auction {
	function submit_bid();
	function submit_bid_state();
	function get_market_for_time();
	function register_participant();
	char32 unit; // unit of quantity
	double period[s]; // interval of time between market clearings
	double latency[s]; // latency between market clearing and delivery
	int64 market_id; // unique identifier of market clearing
	object network; // the comm network used by object to talk to the market (if any)
	bool verbose; // enable verbose auction operations
	object linkref; // (DEPRECATED) reference to link object that has demand as power_out (only used when not all loads are bidding)
	double pricecap; // (DEPRECATED) the maximum price (magnitude) allowed
	double price_cap; // the maximum price (magnitude) allowed
	enumeration {BUYERS_ONLY=2, SELLERS_ONLY=1, NONE=0} special_mode;
	enumeration {OFF=1, ON=0} statistic_mode;
	double fixed_price;
	double fixed_quantity;
	object capacity_reference_object;
	char32 capacity_reference_property;
	double capacity_reference_bid_price;
	double max_capacity_reference_bid_quantity;
	double capacity_reference_bid_quantity;
	double init_price;
	double init_stdev;
	double future_mean_price;
	bool use_future_mean_price;
	timestamp current_market.start_time;
	timestamp current_market.end_time;
	double current_market.clearing_price;
	double current_market.clearing_quantity;
	enumeration {NULL=0, FAILURE=5, EXACT=4, MARGINAL_PRICE=3, MARGINAL_BUYER=2, MARGINAL_SELLER=1} current_market.clearing_type;
	double current_market.marginal_quantity_load;
	double current_market.marginal_quantity;
	double current_market.marginal_quantity_bid;
	double current_market.marginal_quantity_frac;
	double current_market.seller_total_quantity;
	double current_market.buyer_total_quantity;
	double current_market.seller_min_price;
	double current_market.buyer_total_unrep;
	double current_market.cap_ref_unrep;
	timestamp next_market.start_time;
	timestamp next_market.end_time;
	double next_market.clearing_price;
	double next_market.clearing_quantity;
	enumeration {NULL=0, FAILURE=5, EXACT=4, MARGINAL_PRICE=3, MARGINAL_BUYER=2, MARGINAL_SELLER=1} next_market.clearing_type;
	double next_market.marginal_quantity_load;
	double next_market.marginal_quantity_bid;
	double next_market.marginal_quantity_frac;
	double next_market.seller_total_quantity;
	double next_market.buyer_total_quantity;
	double next_market.seller_min_price;
	double next_market.cap_ref_unrep;
	timestamp past_market.start_time;
	timestamp past_market.end_time;
	double past_market.clearing_price;
	double past_market.clearing_quantity;
	enumeration {NULL=0, FAILURE=5, EXACT=4, MARGINAL_PRICE=3, MARGINAL_BUYER=2, MARGINAL_SELLER=1} past_market.clearing_type;
	double past_market.marginal_quantity_load;
	double past_market.marginal_quantity_bid;
	double past_market.marginal_quantity_frac;
	double past_market.seller_total_quantity;
	double past_market.buyer_total_quantity;
	double past_market.seller_min_price;
	double past_market.cap_ref_unrep;
	enumeration {PROB=2, DENY=1, NORMAL=0} margin_mode;
	int32 warmup;
	enumeration {TRUE=1, FALSE=0} ignore_pricecap;
	char256 transaction_log_file;
	int32 transaction_log_limit;
	char256 curve_log_file;
	int32 curve_log_limit;
	enumeration {EXTRA=1, NORMAL=0} curve_log_info;
}

class auction {
	function submit_bid();
	function submit_bid_state();
	function get_market_for_time();
	function register_participant();
	char32 unit; // unit of quantity
	double period[s]; // interval of time between market clearings
	double latency[s]; // latency between market clearing and delivery
	int64 market_id; // unique identifier of market clearing
	object network; // the comm network used by object to talk to the market (if any)
	bool verbose; // enable verbose auction operations
	object linkref; // (DEPRECATED) reference to link object that has demand as power_out (only used when not all loads are bidding)
	double pricecap; // (DEPRECATED) the maximum price (magnitude) allowed
	double price_cap; // the maximum price (magnitude) allowed
	enumeration {BUYERS_ONLY=2, SELLERS_ONLY=1, NONE=0} special_mode;
	enumeration {OFF=1, ON=0} statistic_mode;
	double fixed_price;
	double fixed_quantity;
	object capacity_reference_object;
	char32 capacity_reference_property;
	double capacity_reference_bid_price;
	double max_capacity_reference_bid_quantity;
	double capacity_reference_bid_quantity;
	double init_price;
	double init_stdev;
	double future_mean_price;
	bool use_future_mean_price;
	timestamp current_market.start_time;
	timestamp current_market.end_time;
	double current_market.clearing_price;
	double current_market.clearing_quantity;
	enumeration {NULL=0, FAILURE=5, EXACT=4, MARGINAL_PRICE=3, MARGINAL_BUYER=2, MARGINAL_SELLER=1} current_market.clearing_type;
	double current_market.marginal_quantity_load;
	double current_market.marginal_quantity;
	double current_market.marginal_quantity_bid;
	double current_market.marginal_quantity_frac;
	double current_market.seller_total_quantity;
	double current_market.buyer_total_quantity;
	double current_market.seller_min_price;
	double current_market.buyer_total_unrep;
	double current_market.cap_ref_unrep;
	timestamp next_market.start_time;
	timestamp next_market.end_time;
	double next_market.clearing_price;
	double next_market.clearing_quantity;
	enumeration {NULL=0, FAILURE=5, EXACT=4, MARGINAL_PRICE=3, MARGINAL_BUYER=2, MARGINAL_SELLER=1} next_market.clearing_type;
	double next_market.marginal_quantity_load;
	double next_market.marginal_quantity_bid;
	double next_market.marginal_quantity_frac;
	double next_market.seller_total_quantity;
	double next_market.buyer_total_quantity;
	double next_market.seller_min_price;
	double next_market.cap_ref_unrep;
	timestamp past_market.start_time;
	timestamp past_market.end_time;
	double past_market.clearing_price;
	double past_market.clearing_quantity;
	enumeration {NULL=0, FAILURE=5, EXACT=4, MARGINAL_PRICE=3, MARGINAL_BUYER=2, MARGINAL_SELLER=1} past_market.clearing_type;
	double past_market.marginal_quantity_load;
	double past_market.marginal_quantity_bid;
	double past_market.marginal_quantity_frac;
	double past_market.seller_total_quantity;
	double past_market.buyer_total_quantity;
	double past_market.seller_min_price;
	double past_market.cap_ref_unrep;
	enumeration {PROB=2, DENY=1, NORMAL=0} margin_mode;
	int32 warmup;
	enumeration {TRUE=1, FALSE=0} ignore_pricecap;
	char256 transaction_log_file;
	int32 transaction_log_limit;
	char256 curve_log_file;
	int32 curve_log_limit;
	enumeration {EXTRA=1, NORMAL=0} curve_log_info;
}

class controller {
	enumeration {DOUBLE_RAMP=6, WATERHEATER=5, HOUSE_PRECOOL=4, HOUSE_PREHEAT=3, HOUSE_COOL=2, HOUSE_HEAT=1, NONE=0} simple_mode;
	enumeration {OFF=0, ON=1} bid_mode;
	enumeration {ON=1, OFF=0} use_override;
	double ramp_low[degF]; // the comfort response below the setpoint
	double ramp_high[degF]; // the comfort response above the setpoint
	double range_low; // the setpoint limit on the low side
	double range_high; // the setpoint limit on the high side
	char32 target; // the observed property (e.g., air temperature)
	char32 setpoint; // the controlled property (e.g., heating setpoint)
	char32 demand; // the controlled load when on
	char32 load; // the current controlled load
	char32 total; // the uncontrolled load (if any)
	object market; // the market to bid into
	char32 state; // the state property of the controlled load
	char32 avg_target;
	char32 std_target;
	double bid_price; // the bid price
	double bid_quantity; // the bid quantity
	double set_temp[degF]; // the reset value
	double base_setpoint[degF];
	double market_price; // the current market clearing price seen by the controller.
	double period[s]; // interval of time between market clearings
	enumeration {DOUBLE_RAMP=1, RAMP=0} control_mode;
	enumeration {SLIDING=1, DEADBAND=0} resolve_mode;
	double slider_setting;
	double slider_setting_heat;
	double slider_setting_cool;
	char32 override;
	double heating_range_high[degF];
	double heating_range_low[degF];
	double heating_ramp_high;
	double heating_ramp_low;
	double cooling_range_high[degF];
	double cooling_range_low[degF];
	double cooling_ramp_high;
	double cooling_ramp_low;
	double heating_base_setpoint[degF];
	double cooling_base_setpoint[degF];
	char32 deadband;
	char32 heating_setpoint;
	char32 heating_demand;
	char32 cooling_setpoint;
	char32 cooling_demand;
	double sliding_time_delay[s]; // time interval desired for the sliding resolve mode to change from cooling or heating to off
	bool use_predictive_bidding;
	char32 average_target;
	char32 standard_deviation_target;
	int32 bid_delay;
}

class double_controller {
	enumeration {COOL=3, HEAT=2, OFF=1, INVALID=0} thermostat_mode;
	enumeration {COOL=3, HEAT=2, OFF=1, INVALID=0} last_mode;
	enumeration {STICKY=2, DEADBAND=1, NONE=0} resolve_mode;
	enumeration {HOUSE=1, NONE=0} setup_mode;
	enumeration {OFF=0, ON=1} bid_mode;
	int64 last_mode_timer;
	double cool_ramp_low;
	double cool_ramp_high;
	double cool_range_low;
	double cool_range_high;
	double cool_set_base;
	double cool_setpoint;
	double heat_ramp_low;
	double heat_ramp_high;
	double heat_range_low;
	double heat_range_high;
	double heat_set_base;
	double heat_setpoint;
	char32 temperature_name;
	char32 cool_setpoint_name;
	char32 cool_demand_name;
	char32 heat_setpoint_name;
	char32 heat_demand_name;
	char32 load_name;
	char32 total_load_name;
	char32 deadband_name;
	char32 state_name;
	object market; // the market to bid into
	double market_period;
	double bid_price; // the bid price
	double bid_quant; // the bid quantity
	char32 load; // the current controlled load
	char32 total; // the uncontrolled load (if any)
	double last_price;
	double temperature;
	double cool_bid;
	double heat_bid;
	double cool_demand;
	double heat_demand;
	double price;
	double avg_price;
	double stdev_price;
}

class generator_controller {
	enumeration {STARTING=2, RUNNING=1, OFF=0} generator_state; // Current generator state
	enumeration {LINEAR_BID=2, LINEAR_COST=1, EXPONENTIAL=0} amortization_type; // Amortization compounding method
	int32 generator_state_number; // Current generator state as numeric value
	object market; // Market the object will watch and bid into
	char1024 bid_curve; // Bidding curve text format
	char1024 bid_curve_file; // Bidding curve file name
	double bid_generator_rating[VA]; // Size of generator in VA for the bid curve
	bool update_curve; // Flag to force updating of bidding curve parse
	bool is_marginal_gen; // Flag to indicate if the generator is a marginal generator
	double generator_rating[VA]; // Size of generator in VA for the active bid
	double generator_output; // Current real power output of generator
	double input_unit_base[MW]; // Base multiplier for generator bid units
	double startup_cost; // Cost to start the generator from OFF status
	double shutdown_cost; // Cost to shut down the generator prematurely
	double minimum_runtime[s]; // Minimum time the generator should run to avoid shutdown cost
	double minimum_downtime[s]; // Minimum down time for the generator before it can bid again
	double capacity_factor; // Calculation of generator's current capacity factor based on the market period
	double amortization_factor[1/s]; // Exponential decay factor in 1/s for shutdown cost repayment
	double bid_delay; // Time before a market closes to bid
	enumeration {BUILDING=1, STANDALONE=0} generator_attachment; // Generator attachment type - determines interactions
	double building_load_curr; // Present building load value (if BUILDING attachment)
	double building_load_bid; // Expected building load value for currently bidding market period (if BUILDING attachment)
	double year_runtime_limit[h]; // Total number of hours the generator can run in a year
	double current_year_runtime[h]; // Total number of hours generator has run this year
	char1024 runtime_year_end; // Date and time the generator runtime year resets
	double scaling_factor[unit]; // scaling factor applied to license premium calculation
	double license_premium; // current value of the generator license premium calculated
	double hours_in_year[h]; // Number of hours assumed for the total year
	double op_and_maint_cost; // Operation and maintenance cost per runtime year
}

class passive_controller {
	int32 input_state;
	double input_setpoint;
	bool input_chained;
	double observation; // the observed value
	double mean_observation; // the observed mean value
	double stdev_observation; // the observed standard deviation value
	double expectation; // the observed expected value
	double sensitivity; // (DEPRECATED) the sensitivity of the control actuator to observation deviations
	double period[s]; // the cycle period for the controller logic
	char32 expectation_prop; // (DEPRECATED) the name of the property to observe for the expected value
	object expectation_obj; // (DEPRECATED) the object to watch for the expectation property
	char32 expectation_property; // the name of the property to observe for the expected value
	object expectation_object; // the object to watch for the expectation property
	char32 setpoint_prop; // (DEPRECATED) the name of the setpoint property in the parent object
	char32 setpoint; // the name of the setpoint property in the parent object
	char32 state_prop; // (DEPRECATED) the name of the actuator property in the parent object
	char32 state_property; // the name of the actuator property in the parent object
	object observation_obj; // (DEPRECATED) the object to observe
	char32 observation_prop; // (DEPRECATED) the name of the observation property
	object observation_object; // the object to observe
	char32 observation_property; // the name of the observation property
	char32 mean_observation_prop; // (DEPRECATED) the name of the mean observation property
	char32 stdev_observation_prop; // (DEPRECATED) the name of the standard deviation observation property
	char32 stdev_observation_property; // the name of the standard deviation observation property
	int32 cycle_length; // (DEPRECATED) length of time between processing cycles
	double base_setpoint; // the base setpoint to base control off of
	double critical_day; // used to switch between TOU and CPP days, 1 is CPP, 0 is TOU
	bool two_tier_cpp;
	double daily_elasticity;
	double sub_elasticity_first_second;
	double sub_elasticity_first_third;
	int32 second_tier_hours;
	int32 third_tier_hours;
	int32 first_tier_hours;
	double first_tier_price;
	double second_tier_price;
	double third_tier_price;
	double old_first_tier_price;
	double old_second_tier_price;
	double old_third_tier_price;
	double Percent_change_in_price;
	double Percent_change_in_peakoffpeak_ratio;
	double Percent_change_in_Criticalpeakoffpeak_ratio;
	bool linearize_elasticity;
	double price_offset;
	bool pool_pump_model; // Boolean flag for turning on the pool pump version of the DUTYCYCLE control
	double base_duty_cycle; // This is the duty cycle before modification due to the price signal
	enumeration {UNIFORM=2, EXPONENTIAL=1, NORMAL=0} distribution_type;
	double comfort_level;
	double range_high;
	double range_low;
	double ramp_high;
	double ramp_low;
	double prob_off;
	int32 output_state; // the target setpoint given the input observations
	double output_setpoint;
	enumeration {DIRECT_LOAD_CONTROL=7, ELASTICITY_MODEL=6, PROBABILITY_OFF=5, DUTYCYCLE=4, RAMP=1, NONE=0} control_mode; // the control mode to use for determining controller action
	enumeration {CYCLING=1, OFF=0} dlc_mode; // this mode is roughly designed to force cycle an AC unit
	double cycle_length_off[s];
	double cycle_length_on[s];
}

class stub_bidder {
	double bid_period[s];
	int16 count;
	object market;
	enumeration {SELLER=1, BUYER=0} role;
	double price;
	double quantity;
}

class stubauction {
	char32 unit; // unit of quantity
	double period[s]; // interval of time between market clearings
	double last.P; // last cleared price
	double current_market.clearing_price; // next cleared price
	double past_market.clearing_price; // last cleared price
	double next.P; // next cleared price
	double avg24; // daily average of price
	double std24; // daily stdev of price
	double avg72; // three day price average
	double std72; // three day price stdev
	double avg168; // weekly average of price
	double std168; // weekly stdev of price
	int64 market_id; // unique identifier of market clearing
	bool verbose; // enable verbose stubauction operations
	enumeration {DISABLED=1, NORMAL=0} control_mode; // the control mode to use for determining average and deviation calculations
}


FAILED on module name msvcp80
FAILED on module name msvcr80
FAILED on module name network
class billdump {
	char32 group; // the group ID to output data for (all nodes if empty)
	timestamp runtime; // the time to check voltage data
	char256 filename; // the file to dump the voltage data into
	int32 runcount; // the number of times the file has been written to
	enumeration {METER=1, TRIPLEX_METER=0} meter_type; // describes whether to collect from 3-phase or S-phase meters
}

class capacitor {
	parent node;
	class node {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		function delta_linkage_node();
		function interupdate_pwr_object();
		function delta_freq_pwr_object();
		enumeration {SWING=2, PV=1, PQ=0} bustype; // defines whether the node is a PQ, PV, or SWING node
		set {HASSOURCE=1} busflags; // flag indicates node has a source for voltage, i.e. connects to the swing node
		object reference_bus; // reference bus from which frequency is defined
		double maximum_voltage_error[V]; // convergence voltage limit or convergence criteria
		complex voltage_A[V]; // bus voltage, Phase A to ground
		complex voltage_B[V]; // bus voltage, Phase B to ground
		complex voltage_C[V]; // bus voltage, Phase C to ground
		complex voltage_AB[V]; // line voltages, Phase AB
		complex voltage_BC[V]; // line voltages, Phase BC
		complex voltage_CA[V]; // line voltages, Phase CA
		complex current_A[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex current_B[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex current_C[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex power_A[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex power_B[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex power_C[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex shunt_A[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		complex shunt_B[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		complex shunt_C[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} service_status; // In and out of service flag
		double service_status_double; // In and out of service flag - type double - will indiscriminately override service_status - useful for schedules
		double previous_uptime[min]; // Previous time between disconnects of node in minutes
		double current_uptime[min]; // Current time since last disconnect of node in minutes
		object topological_parent; // topological parent as per GLM configuration
	}

	set {N=8, D=256, C=4, B=2, A=1} pt_phase; // Phase(s) that the PT is on, used as measurement points for control
	set {N=8, D=256, C=4, B=2, A=1} phases_connected; // phases capacitors connected to
	enumeration {CLOSED=1, OPEN=0} switchA; // capacitor A switch open or close
	enumeration {CLOSED=1, OPEN=0} switchB; // capacitor B switch open or close
	enumeration {CLOSED=1, OPEN=0} switchC; // capacitor C switch open or close
	enumeration {CURRENT=4, VARVOLT=3, VOLT=2, VAR=1, MANUAL=0} control; // control operation strategy
	double cap_A_switch_count; // number of switch operations on Phase A
	double cap_B_switch_count; // number of switch operations on Phase B
	double cap_C_switch_count; // number of switch operations on Phase C
	double voltage_set_high[V]; // Turn off if voltage is above this set point
	double voltage_set_low[V]; // Turns on if voltage is below this set point
	double VAr_set_high[VAr]; // high VAR set point for VAR control (turn off)
	double VAr_set_low[VAr]; // low VAR set point for VAR control (turn on)
	double current_set_low[A]; // high current set point for current control mode (turn on)
	double current_set_high[A]; // low current set point for current control mode (turn off)
	double capacitor_A[VAr]; // Capacitance value for phase A or phase AB
	double capacitor_B[VAr]; // Capacitance value for phase B or phase BC
	double capacitor_C[VAr]; // Capacitance value for phase C or phase CA
	double cap_nominal_voltage[V]; // Nominal voltage for the capacitor. Used for calculation of capacitance value
	double time_delay[s]; // control time delay
	double dwell_time[s]; // Time for system to remain constant before a state change will be passed
	double lockout_time[s]; // Time for capacitor to remain locked out from further switching operations (VARVOLT control)
	object remote_sense; // Remote object for sensing values used for control schemes
	object remote_sense_B; // Secondary Remote object for sensing values used for control schemes (VARVOLT uses two)
	enumeration {INDIVIDUAL=1, BANK=0} control_level; // define bank or individual control
}

class currdump {
	char32 group; // the group ID to output data for (all links if empty)
	timestamp runtime; // the time to check current data
	char256 filename; // the file to dump the current data into
	int32 runcount; // the number of times the file has been written to
	enumeration {polar=1, rect=0} mode;
}

class emissions {
	double Nuclear_Order;
	double Hydroelectric_Order;
	double Solarthermal_Order;
	double Biomass_Order;
	double Wind_Order;
	double Coal_Order;
	double Naturalgas_Order;
	double Geothermal_Order;
	double Petroleum_Order;
	double Naturalgas_Max_Out[kWh];
	double Coal_Max_Out[kWh];
	double Biomass_Max_Out[kWh];
	double Geothermal_Max_Out[kWh];
	double Hydroelectric_Max_Out[kWh];
	double Nuclear_Max_Out[kWh];
	double Wind_Max_Out[kWh];
	double Petroleum_Max_Out[kWh];
	double Solarthermal_Max_Out[kWh];
	double Naturalgas_Out[kWh];
	double Coal_Out[kWh];
	double Biomass_Out[kWh];
	double Geothermal_Out[kWh];
	double Hydroelectric_Out[kWh];
	double Nuclear_Out[kWh];
	double Wind_Out[kWh];
	double Petroleum_Out[kWh];
	double Solarthermal_Out[kWh];
	double Naturalgas_Conv_Eff[Btu/kWh];
	double Coal_Conv_Eff[Btu/kWh];
	double Biomass_Conv_Eff[Btu/kWh];
	double Geothermal_Conv_Eff[Btu/kWh];
	double Hydroelectric_Conv_Eff[Btu/kWh];
	double Nuclear_Conv_Eff[Btu/kWh];
	double Wind_Conv_Eff[Btu/kWh];
	double Petroleum_Conv_Eff[Btu/kWh];
	double Solarthermal_Conv_Eff[Btu/kWh];
	double Naturalgas_CO2[lb/Btu];
	double Coal_CO2[lb/Btu];
	double Biomass_CO2[lb/Btu];
	double Geothermal_CO2[lb/Btu];
	double Hydroelectric_CO2[lb/Btu];
	double Nuclear_CO2[lb/Btu];
	double Wind_CO2[lb/Btu];
	double Petroleum_CO2[lb/Btu];
	double Solarthermal_CO2[lb/Btu];
	double Naturalgas_SO2[lb/Btu];
	double Coal_SO2[lb/Btu];
	double Biomass_SO2[lb/Btu];
	double Geothermal_SO2[lb/Btu];
	double Hydroelectric_SO2[lb/Btu];
	double Nuclear_SO2[lb/Btu];
	double Wind_SO2[lb/Btu];
	double Petroleum_SO2[lb/Btu];
	double Solarthermal_SO2[lb/Btu];
	double Naturalgas_NOx[lb/Btu];
	double Coal_NOx[lb/Btu];
	double Biomass_NOx[lb/Btu];
	double Geothermal_NOx[lb/Btu];
	double Hydroelectric_NOx[lb/Btu];
	double Nuclear_NOx[lb/Btu];
	double Wind_NOx[lb/Btu];
	double Petroleum_NOx[lb/Btu];
	double Solarthermal_NOx[lb/Btu];
	double Naturalgas_emissions_CO2[lb];
	double Naturalgas_emissions_SO2[lb];
	double Naturalgas_emissions_NOx[lb];
	double Coal_emissions_CO2[lb];
	double Coal_emissions_SO2[lb];
	double Coal_emissions_NOx[lb];
	double Biomass_emissions_CO2[lb];
	double Biomass_emissions_SO2[lb];
	double Biomass_emissions_NOx[lb];
	double Geothermal_emissions_CO2[lb];
	double Geothermal_emissions_SO2[lb];
	double Geothermal_emissions_NOx[lb];
	double Hydroelectric_emissions_CO2[lb];
	double Hydroelectric_emissions_SO2[lb];
	double Hydroelectric_emissions_NOx[lb];
	double Nuclear_emissions_CO2[lb];
	double Nuclear_emissions_SO2[lb];
	double Nuclear_emissions_NOx[lb];
	double Wind_emissions_CO2[lb];
	double Wind_emissions_SO2[lb];
	double Wind_emissions_NOx[lb];
	double Petroleum_emissions_CO2[lb];
	double Petroleum_emissions_SO2[lb];
	double Petroleum_emissions_NOx[lb];
	double Solarthermal_emissions_CO2[lb];
	double Solarthermal_emissions_SO2[lb];
	double Solarthermal_emissions_NOx[lb];
	double Total_emissions_CO2[lb];
	double Total_emissions_SO2[lb];
	double Total_emissions_NOx[lb];
	double Total_energy_out[kWh];
	double Region;
	double cycle_interval[s];
}

class fault_check {
	function reliability_alterations();
	function handle_sectionalizer();
	enumeration {ALL=2, ONCHANGE=1, SINGLE=0} check_mode; // Frequency of fault checks
	char1024 output_filename;
	bool reliability_mode;
	object eventgen_object;
}

class frequency_gen {
	enumeration {AUTO=1, OFF=0} Frequency_Mode; // Frequency object operations mode
	double Frequency[Hz]; // Instantaneous frequency value
	double FreqChange[Hz/s]; // Frequency change from last timestep
	double Deadband[Hz]; // Frequency deadband of the governor
	double Tolerance[%]; // % threshold a power difference must be before it is cared about
	double M[pu]; // Inertial constant of the system
	double D[%]; // Load-damping constant
	double Rated_power[W]; // Rated power of system (base power)
	double Gen_power[W]; // Mechanical power equivalent
	double Load_power[W]; // Last sensed load value
	double Gov_delay[s]; // Governor delay time
	double Ramp_rate[W/s]; // Ramp ideal ramp rate
	double Low_Freq_OI[Hz]; // Low frequency setpoint for GFA devices
	double High_Freq_OI[Hz]; // High frequency setpoint for GFA devices
	double avg24[Hz]; // Average of last 24 hourly instantaneous measurements
	double std24[Hz]; // Standard deviation of last 24 hourly instantaneous measurements
	double avg168[Hz]; // Average of last 168 hourly instantaneous measurements
	double std168[Hz]; // Standard deviation of last 168 hourly instantaneous measurements
	int32 Num_Resp_Eqs; // Total number of equations the response can contain
}

class fuse {
	parent link;
	class link {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		enumeration {OPEN=0, CLOSED=1} status; // 
		object from; // from_node - source node
		object to; // to_node - load node
		complex power_in[VA]; // power flow in (w.r.t from node)
		complex power_out[VA]; // power flow out (w.r.t to node)
		double power_out_real[W]; // power flow out (w.r.t to node), real
		complex power_losses[VA]; // power losses
		complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
		complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
		complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
		complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
		complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
		complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
		complex power_losses_A[VA]; // power losses, phase A
		complex power_losses_B[VA]; // power losses, phase B
		complex power_losses_C[VA]; // power losses, phase C
		complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
		complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
		complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
		complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
		complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
		complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
		complex fault_current_in_A[A]; // fault current flowing in, phase A
		complex fault_current_in_B[A]; // fault current flowing in, phase B
		complex fault_current_in_C[A]; // fault current flowing in, phase C
		complex fault_current_out_A[A]; // fault current flowing out, phase A
		complex fault_current_out_B[A]; // fault current flowing out, phase B
		complex fault_current_out_C[A]; // fault current flowing out, phase C
		set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
		double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
	}

	function change_fuse_state();
	function reliability_operation();
	function create_fault();
	function fix_fault();
	function change_fuse_faults();
	enumeration {GOOD=1, BLOWN=0} phase_A_status;
	enumeration {GOOD=1, BLOWN=0} phase_B_status;
	enumeration {GOOD=1, BLOWN=0} phase_C_status;
	enumeration {EXPONENTIAL=1, NONE=0} repair_dist_type;
	double current_limit[A];
	double mean_replacement_time[s];
}

class line {
	parent link;
	class link {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		enumeration {OPEN=0, CLOSED=1} status; // 
		object from; // from_node - source node
		object to; // to_node - load node
		complex power_in[VA]; // power flow in (w.r.t from node)
		complex power_out[VA]; // power flow out (w.r.t to node)
		double power_out_real[W]; // power flow out (w.r.t to node), real
		complex power_losses[VA]; // power losses
		complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
		complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
		complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
		complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
		complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
		complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
		complex power_losses_A[VA]; // power losses, phase A
		complex power_losses_B[VA]; // power losses, phase B
		complex power_losses_C[VA]; // power losses, phase C
		complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
		complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
		complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
		complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
		complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
		complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
		complex fault_current_in_A[A]; // fault current flowing in, phase A
		complex fault_current_in_B[A]; // fault current flowing in, phase B
		complex fault_current_in_C[A]; // fault current flowing in, phase C
		complex fault_current_out_A[A]; // fault current flowing out, phase A
		complex fault_current_out_B[A]; // fault current flowing out, phase B
		complex fault_current_out_C[A]; // fault current flowing out, phase C
		set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
		double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
	}

	object configuration;
	double length[ft];
}

class line_configuration {
	object conductor_A;
	object conductor_B;
	object conductor_C;
	object conductor_N;
	object spacing;
	complex z11[Ohm/mile];
	complex z12[Ohm/mile];
	complex z13[Ohm/mile];
	complex z21[Ohm/mile];
	complex z22[Ohm/mile];
	complex z23[Ohm/mile];
	complex z31[Ohm/mile];
	complex z32[Ohm/mile];
	complex z33[Ohm/mile];
}

class line_spacing {
	double distance_AB[ft];
	double distance_BC[ft];
	double distance_AC[ft];
	double distance_AN[ft];
	double distance_BN[ft];
	double distance_CN[ft];
	double distance_AE[ft]; // distance between phase A wire and earth
	double distance_BE[ft]; // distance between phase B wire and earth
	double distance_CE[ft]; // distance between phase C wire and earth
	double distance_NE[ft]; // distance between neutral wire and earth
}

class link {
	parent powerflow_object;
	class powerflow_object {
		set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
		double nominal_voltage[V];
	}

	enumeration {OPEN=0, CLOSED=1} status; // 
	object from; // from_node - source node
	object to; // to_node - load node
	complex power_in[VA]; // power flow in (w.r.t from node)
	complex power_out[VA]; // power flow out (w.r.t to node)
	double power_out_real[W]; // power flow out (w.r.t to node), real
	complex power_losses[VA]; // power losses
	complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
	complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
	complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
	complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
	complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
	complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
	complex power_losses_A[VA]; // power losses, phase A
	complex power_losses_B[VA]; // power losses, phase B
	complex power_losses_C[VA]; // power losses, phase C
	complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
	complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
	complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
	complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
	complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
	complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
	complex fault_current_in_A[A]; // fault current flowing in, phase A
	complex fault_current_in_B[A]; // fault current flowing in, phase B
	complex fault_current_in_C[A]; // fault current flowing in, phase C
	complex fault_current_out_A[A]; // fault current flowing out, phase A
	complex fault_current_out_B[A]; // fault current flowing out, phase B
	complex fault_current_out_C[A]; // fault current flowing out, phase C
	set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
	double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
	double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
	double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
}

class load {
	parent node;
	class node {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		function delta_linkage_node();
		function interupdate_pwr_object();
		function delta_freq_pwr_object();
		enumeration {SWING=2, PV=1, PQ=0} bustype; // defines whether the node is a PQ, PV, or SWING node
		set {HASSOURCE=1} busflags; // flag indicates node has a source for voltage, i.e. connects to the swing node
		object reference_bus; // reference bus from which frequency is defined
		double maximum_voltage_error[V]; // convergence voltage limit or convergence criteria
		complex voltage_A[V]; // bus voltage, Phase A to ground
		complex voltage_B[V]; // bus voltage, Phase B to ground
		complex voltage_C[V]; // bus voltage, Phase C to ground
		complex voltage_AB[V]; // line voltages, Phase AB
		complex voltage_BC[V]; // line voltages, Phase BC
		complex voltage_CA[V]; // line voltages, Phase CA
		complex current_A[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex current_B[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex current_C[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex power_A[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex power_B[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex power_C[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex shunt_A[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		complex shunt_B[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		complex shunt_C[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} service_status; // In and out of service flag
		double service_status_double; // In and out of service flag - type double - will indiscriminately override service_status - useful for schedules
		double previous_uptime[min]; // Previous time between disconnects of node in minutes
		double current_uptime[min]; // Current time since last disconnect of node in minutes
		object topological_parent; // topological parent as per GLM configuration
	}

	function delta_linkage_node();
	function interupdate_pwr_object();
	function delta_freq_pwr_object();
	enumeration {A=4, I=3, C=2, R=1, U=0} load_class; // Flag to track load type, not currently used for anything except sorting
	complex constant_power_A[VA]; // constant power load on phase A, specified as VA
	complex constant_power_B[VA]; // constant power load on phase B, specified as VA
	complex constant_power_C[VA]; // constant power load on phase C, specified as VA
	double constant_power_A_real[W]; // constant power load on phase A, real only, specified as W
	double constant_power_B_real[W]; // constant power load on phase B, real only, specified as W
	double constant_power_C_real[W]; // constant power load on phase C, real only, specified as W
	double constant_power_A_reac[VAr]; // constant power load on phase A, imaginary only, specified as VAr
	double constant_power_B_reac[VAr]; // constant power load on phase B, imaginary only, specified as VAr
	double constant_power_C_reac[VAr]; // constant power load on phase C, imaginary only, specified as VAr
	complex constant_current_A[A]; // constant current load on phase A, specified as Amps
	complex constant_current_B[A]; // constant current load on phase B, specified as Amps
	complex constant_current_C[A]; // constant current load on phase C, specified as Amps
	double constant_current_A_real[A]; // constant current load on phase A, real only, specified as Amps
	double constant_current_B_real[A]; // constant current load on phase B, real only, specified as Amps
	double constant_current_C_real[A]; // constant current load on phase C, real only, specified as Amps
	double constant_current_A_reac[A]; // constant current load on phase A, imaginary only, specified as Amps
	double constant_current_B_reac[A]; // constant current load on phase B, imaginary only, specified as Amps
	double constant_current_C_reac[A]; // constant current load on phase C, imaginary only, specified as Amps
	complex constant_impedance_A[Ohm]; // constant impedance load on phase A, specified as Ohms
	complex constant_impedance_B[Ohm]; // constant impedance load on phase B, specified as Ohms
	complex constant_impedance_C[Ohm]; // constant impedance load on phase C, specified as Ohms
	double constant_impedance_A_real[Ohm]; // constant impedance load on phase A, real only, specified as Ohms
	double constant_impedance_B_real[Ohm]; // constant impedance load on phase B, real only, specified as Ohms
	double constant_impedance_C_real[Ohm]; // constant impedance load on phase C, real only, specified as Ohms
	double constant_impedance_A_reac[Ohm]; // constant impedance load on phase A, imaginary only, specified as Ohms
	double constant_impedance_B_reac[Ohm]; // constant impedance load on phase B, imaginary only, specified as Ohms
	double constant_impedance_C_reac[Ohm]; // constant impedance load on phase C, imaginary only, specified as Ohms
	complex measured_voltage_A; // current measured voltage on phase A
	complex measured_voltage_B; // current measured voltage on phase B
	complex measured_voltage_C; // current measured voltage on phase C
	complex measured_voltage_AB; // current measured voltage on phases AB
	complex measured_voltage_BC; // current measured voltage on phases BC
	complex measured_voltage_CA; // current measured voltage on phases CA
	bool phase_loss_protection; // Trip all three phases of the load if a fault occurs
	double base_power_A[VA]; // in similar format as ZIPload, this represents the nominal power on phase A before applying ZIP fractions
	double base_power_B[VA]; // in similar format as ZIPload, this represents the nominal power on phase B before applying ZIP fractions
	double base_power_C[VA]; // in similar format as ZIPload, this represents the nominal power on phase C before applying ZIP fractions
	double power_pf_A[pu]; // in similar format as ZIPload, this is the power factor of the phase A constant power portion of load
	double current_pf_A[pu]; // in similar format as ZIPload, this is the power factor of the phase A constant current portion of load
	double impedance_pf_A[pu]; // in similar format as ZIPload, this is the power factor of the phase A constant impedance portion of load
	double power_pf_B[pu]; // in similar format as ZIPload, this is the power factor of the phase B constant power portion of load
	double current_pf_B[pu]; // in similar format as ZIPload, this is the power factor of the phase B constant current portion of load
	double impedance_pf_B[pu]; // in similar format as ZIPload, this is the power factor of the phase B constant impedance portion of load
	double power_pf_C[pu]; // in similar format as ZIPload, this is the power factor of the phase C constant power portion of load
	double current_pf_C[pu]; // in similar format as ZIPload, this is the power factor of the phase C constant current portion of load
	double impedance_pf_C[pu]; // in similar format as ZIPload, this is the power factor of the phase C constant impedance portion of load
	double power_fraction_A[pu]; // this is the constant power fraction of base power on phase A
	double current_fraction_A[pu]; // this is the constant current fraction of base power on phase A
	double impedance_fraction_A[pu]; // this is the constant impedance fraction of base power on phase A
	double power_fraction_B[pu]; // this is the constant power fraction of base power on phase B
	double current_fraction_B[pu]; // this is the constant current fraction of base power on phase B
	double impedance_fraction_B[pu]; // this is the constant impedance fraction of base power on phase B
	double power_fraction_C[pu]; // this is the constant power fraction of base power on phase C
	double current_fraction_C[pu]; // this is the constant current fraction of base power on phase C
	double impedance_fraction_C[pu]; // this is the constant impedance fraction of base power on phase C
}

class load_tracker {
	object target; // target object to track the load of
	char256 target_property; // property on the target object representing the load
	enumeration {ANGLE=3, MAGNITUDE=2, IMAGINARY=1, REAL=0} operation; // operation to perform on complex property types
	double full_scale; // magnitude of the load at full load, used for feed-forward control
	double setpoint; // load setpoint to track to
	double deadband; // percentage deadband
	double damping; // load setpoint to track to
	double output; // output scaling value
	double feedback; // the feedback signal, for reference purposes
}

class meter {
	parent node;
	class node {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		function delta_linkage_node();
		function interupdate_pwr_object();
		function delta_freq_pwr_object();
		enumeration {SWING=2, PV=1, PQ=0} bustype; // defines whether the node is a PQ, PV, or SWING node
		set {HASSOURCE=1} busflags; // flag indicates node has a source for voltage, i.e. connects to the swing node
		object reference_bus; // reference bus from which frequency is defined
		double maximum_voltage_error[V]; // convergence voltage limit or convergence criteria
		complex voltage_A[V]; // bus voltage, Phase A to ground
		complex voltage_B[V]; // bus voltage, Phase B to ground
		complex voltage_C[V]; // bus voltage, Phase C to ground
		complex voltage_AB[V]; // line voltages, Phase AB
		complex voltage_BC[V]; // line voltages, Phase BC
		complex voltage_CA[V]; // line voltages, Phase CA
		complex current_A[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex current_B[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex current_C[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex power_A[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex power_B[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex power_C[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex shunt_A[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		complex shunt_B[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		complex shunt_C[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} service_status; // In and out of service flag
		double service_status_double; // In and out of service flag - type double - will indiscriminately override service_status - useful for schedules
		double previous_uptime[min]; // Previous time between disconnects of node in minutes
		double current_uptime[min]; // Current time since last disconnect of node in minutes
		object topological_parent; // topological parent as per GLM configuration
	}

	function reset();
	function delta_linkage_node();
	function interupdate_pwr_object();
	function delta_freq_pwr_object();
	double measured_real_energy[Wh]; // metered real energy consumption, cummalitive
	double measured_reactive_energy[VAh]; // metered reactive energy consumption, cummalitive
	complex measured_power[VA]; // metered real power
	complex measured_power_A[VA]; // metered complex power on phase A
	complex measured_power_B[VA]; // metered complex power on phase B
	complex measured_power_C[VA]; // metered complex power on phase C
	double measured_demand[W]; // greatest metered real power during simulation
	double measured_real_power[W]; // metered real power
	double measured_reactive_power[VAr]; // metered reactive power
	complex meter_power_consumption[VA]; // metered power used for operating the meter; standby and communication losses
	complex measured_voltage_A[V]; // measured line-to-neutral voltage on phase A
	complex measured_voltage_B[V]; // measured line-to-neutral voltage on phase B
	complex measured_voltage_C[V]; // measured line-to-neutral voltage on phase C
	complex measured_voltage_AB[V]; // measured line-to-line voltage on phase AB
	complex measured_voltage_BC[V]; // measured line-to-line voltage on phase BC
	complex measured_voltage_CA[V]; // measured line-to-line voltage on phase CA
	complex measured_current_A[A]; // measured current on phase A
	complex measured_current_B[A]; // measured current on phase B
	complex measured_current_C[A]; // measured current on phase C
	bool customer_interrupted; // Reliability flag - goes active if the customer is in an 'interrupted' state
	bool customer_interrupted_secondary; // Reliability flag - goes active if the customer is in an 'secondary interrupted' state - i.e., momentary
	double monthly_bill; // Accumulator for the current month's bill
	double previous_monthly_bill; // Total monthly bill for the previous month
	double previous_monthly_energy[kWh]; // Total monthly energy for the previous month
	double monthly_fee; // Once a month flat fee for customer hook-up
	double monthly_energy[kWh]; // Accumulator for the current month's energy consumption
	enumeration {TIERED_RTP=4, HOURLY=3, TIERED=2, UNIFORM=1, NONE=0} bill_mode; // Billing structure desired
	object power_market; // Market (auction object) where the price is being received from
	int32 bill_day; // day of month bill is to be processed (currently limited to days 1-28)
	double price; // current price of electricity
	double price_base; // Used only in TIERED_RTP mode to describe the price before the first tier
	double first_tier_price; // price of electricity between first tier and second tier energy usage
	double first_tier_energy[kWh]; // switching point between base price and first tier price
	double second_tier_price; // price of electricity between second tier and third tier energy usage
	double second_tier_energy[kWh]; // switching point between first tier price and second tier price
	double third_tier_price; // price of electricity when energy usage exceeds third tier energy usage
	double third_tier_energy[kWh]; // switching point between second tier price and third tier price
}

class motor {
	parent node;
	class node {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		function delta_linkage_node();
		function interupdate_pwr_object();
		function delta_freq_pwr_object();
		enumeration {SWING=2, PV=1, PQ=0} bustype; // defines whether the node is a PQ, PV, or SWING node
		set {HASSOURCE=1} busflags; // flag indicates node has a source for voltage, i.e. connects to the swing node
		object reference_bus; // reference bus from which frequency is defined
		double maximum_voltage_error[V]; // convergence voltage limit or convergence criteria
		complex voltage_A[V]; // bus voltage, Phase A to ground
		complex voltage_B[V]; // bus voltage, Phase B to ground
		complex voltage_C[V]; // bus voltage, Phase C to ground
		complex voltage_AB[V]; // line voltages, Phase AB
		complex voltage_BC[V]; // line voltages, Phase BC
		complex voltage_CA[V]; // line voltages, Phase CA
		complex current_A[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex current_B[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex current_C[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex power_A[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex power_B[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex power_C[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex shunt_A[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		complex shunt_B[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		complex shunt_C[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} service_status; // In and out of service flag
		double service_status_double; // In and out of service flag - type double - will indiscriminately override service_status - useful for schedules
		double previous_uptime[min]; // Previous time between disconnects of node in minutes
		double current_uptime[min]; // Current time since last disconnect of node in minutes
		object topological_parent; // topological parent as per GLM configuration
	}

}

class node {
	parent powerflow_object;
	class powerflow_object {
		set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
		double nominal_voltage[V];
	}

	function delta_linkage_node();
	function interupdate_pwr_object();
	function delta_freq_pwr_object();
	enumeration {SWING=2, PV=1, PQ=0} bustype; // defines whether the node is a PQ, PV, or SWING node
	set {HASSOURCE=1} busflags; // flag indicates node has a source for voltage, i.e. connects to the swing node
	object reference_bus; // reference bus from which frequency is defined
	double maximum_voltage_error[V]; // convergence voltage limit or convergence criteria
	complex voltage_A[V]; // bus voltage, Phase A to ground
	complex voltage_B[V]; // bus voltage, Phase B to ground
	complex voltage_C[V]; // bus voltage, Phase C to ground
	complex voltage_AB[V]; // line voltages, Phase AB
	complex voltage_BC[V]; // line voltages, Phase BC
	complex voltage_CA[V]; // line voltages, Phase CA
	complex current_A[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
	complex current_B[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
	complex current_C[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
	complex power_A[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
	complex power_B[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
	complex power_C[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
	complex shunt_A[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
	complex shunt_B[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
	complex shunt_C[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
	double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
	enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} service_status; // In and out of service flag
	double service_status_double; // In and out of service flag - type double - will indiscriminately override service_status - useful for schedules
	double previous_uptime[min]; // Previous time between disconnects of node in minutes
	double current_uptime[min]; // Current time since last disconnect of node in minutes
	object topological_parent; // topological parent as per GLM configuration
}

class overhead_line {
	parent line;
	class line {
		parent link;
		class link {
			parent powerflow_object;
			class powerflow_object {
				set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
				double nominal_voltage[V];
			}

			enumeration {OPEN=0, CLOSED=1} status; // 
			object from; // from_node - source node
			object to; // to_node - load node
			complex power_in[VA]; // power flow in (w.r.t from node)
			complex power_out[VA]; // power flow out (w.r.t to node)
			double power_out_real[W]; // power flow out (w.r.t to node), real
			complex power_losses[VA]; // power losses
			complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
			complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
			complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
			complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
			complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
			complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
			complex power_losses_A[VA]; // power losses, phase A
			complex power_losses_B[VA]; // power losses, phase B
			complex power_losses_C[VA]; // power losses, phase C
			complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
			complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
			complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
			complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
			complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
			complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
			complex fault_current_in_A[A]; // fault current flowing in, phase A
			complex fault_current_in_B[A]; // fault current flowing in, phase B
			complex fault_current_in_C[A]; // fault current flowing in, phase C
			complex fault_current_out_A[A]; // fault current flowing out, phase A
			complex fault_current_out_B[A]; // fault current flowing out, phase B
			complex fault_current_out_C[A]; // fault current flowing out, phase C
			set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
			double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
			double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
			double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
		}

		object configuration;
		double length[ft];
	}

	function create_fault();
	function fix_fault();
}

class overhead_line_conductor {
	double geometric_mean_radius[ft]; // radius of the conductor
	double resistance[Ohm/mile]; // resistance in Ohms/mile of the conductor
	double diameter[in]; // Diameter of line for capacitance calculations
	double rating.summer.continuous[A]; // Continuous summer amp rating
	double rating.summer.emergency[A]; // Emergency summer amp rating
	double rating.winter.continuous[A]; // Continuous winter amp rating
	double rating.winter.emergency[A]; // Emergency winter amp rating
}

class power_metrics {
	function calc_metrics();
	function reset_interval_metrics();
	function reset_annual_metrics();
	function init_reliability();
	function logfile_extra();
	double SAIFI; // Displays annual SAIFI values as per IEEE 1366-2003
	double SAIFI_int; // Displays SAIFI values over the period specified by base_time_value as per IEEE 1366-2003
	double SAIDI; // Displays annual SAIDI values as per IEEE 1366-2003
	double SAIDI_int; // Displays SAIDI values over the period specified by base_time_value as per IEEE 1366-2003
	double CAIDI; // Displays annual CAIDI values as per IEEE 1366-2003
	double CAIDI_int; // Displays SAIDI values over the period specified by base_time_value as per IEEE 1366-2003
	double ASAI; // Displays annual AISI values as per IEEE 1366-2003
	double ASAI_int; // Displays AISI values over the period specified by base_time_value as per IEEE 1366-2003
	double MAIFI; // Displays annual MAIFI values as per IEEE 1366-2003
	double MAIFI_int; // Displays MAIFI values over the period specified by base_time_value as per IEEE 1366-2003
	double base_time_value[s]; // time period over which _int values are claculated
}

class powerflow_library {
}

class powerflow_object {
	set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
	double nominal_voltage[V];
}

class powerflow_object {
	set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
	double nominal_voltage[V];
}

class pqload {
	parent load;
	class load {
		parent node;
		class node {
			parent powerflow_object;
			class powerflow_object {
				set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
				double nominal_voltage[V];
			}

			function delta_linkage_node();
			function interupdate_pwr_object();
			function delta_freq_pwr_object();
			enumeration {SWING=2, PV=1, PQ=0} bustype; // defines whether the node is a PQ, PV, or SWING node
			set {HASSOURCE=1} busflags; // flag indicates node has a source for voltage, i.e. connects to the swing node
			object reference_bus; // reference bus from which frequency is defined
			double maximum_voltage_error[V]; // convergence voltage limit or convergence criteria
			complex voltage_A[V]; // bus voltage, Phase A to ground
			complex voltage_B[V]; // bus voltage, Phase B to ground
			complex voltage_C[V]; // bus voltage, Phase C to ground
			complex voltage_AB[V]; // line voltages, Phase AB
			complex voltage_BC[V]; // line voltages, Phase BC
			complex voltage_CA[V]; // line voltages, Phase CA
			complex current_A[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
			complex current_B[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
			complex current_C[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
			complex power_A[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
			complex power_B[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
			complex power_C[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
			complex shunt_A[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
			complex shunt_B[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
			complex shunt_C[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
			double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
			enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} service_status; // In and out of service flag
			double service_status_double; // In and out of service flag - type double - will indiscriminately override service_status - useful for schedules
			double previous_uptime[min]; // Previous time between disconnects of node in minutes
			double current_uptime[min]; // Current time since last disconnect of node in minutes
			object topological_parent; // topological parent as per GLM configuration
		}

		function delta_linkage_node();
		function interupdate_pwr_object();
		function delta_freq_pwr_object();
		enumeration {A=4, I=3, C=2, R=1, U=0} load_class; // Flag to track load type, not currently used for anything except sorting
		complex constant_power_A[VA]; // constant power load on phase A, specified as VA
		complex constant_power_B[VA]; // constant power load on phase B, specified as VA
		complex constant_power_C[VA]; // constant power load on phase C, specified as VA
		double constant_power_A_real[W]; // constant power load on phase A, real only, specified as W
		double constant_power_B_real[W]; // constant power load on phase B, real only, specified as W
		double constant_power_C_real[W]; // constant power load on phase C, real only, specified as W
		double constant_power_A_reac[VAr]; // constant power load on phase A, imaginary only, specified as VAr
		double constant_power_B_reac[VAr]; // constant power load on phase B, imaginary only, specified as VAr
		double constant_power_C_reac[VAr]; // constant power load on phase C, imaginary only, specified as VAr
		complex constant_current_A[A]; // constant current load on phase A, specified as Amps
		complex constant_current_B[A]; // constant current load on phase B, specified as Amps
		complex constant_current_C[A]; // constant current load on phase C, specified as Amps
		double constant_current_A_real[A]; // constant current load on phase A, real only, specified as Amps
		double constant_current_B_real[A]; // constant current load on phase B, real only, specified as Amps
		double constant_current_C_real[A]; // constant current load on phase C, real only, specified as Amps
		double constant_current_A_reac[A]; // constant current load on phase A, imaginary only, specified as Amps
		double constant_current_B_reac[A]; // constant current load on phase B, imaginary only, specified as Amps
		double constant_current_C_reac[A]; // constant current load on phase C, imaginary only, specified as Amps
		complex constant_impedance_A[Ohm]; // constant impedance load on phase A, specified as Ohms
		complex constant_impedance_B[Ohm]; // constant impedance load on phase B, specified as Ohms
		complex constant_impedance_C[Ohm]; // constant impedance load on phase C, specified as Ohms
		double constant_impedance_A_real[Ohm]; // constant impedance load on phase A, real only, specified as Ohms
		double constant_impedance_B_real[Ohm]; // constant impedance load on phase B, real only, specified as Ohms
		double constant_impedance_C_real[Ohm]; // constant impedance load on phase C, real only, specified as Ohms
		double constant_impedance_A_reac[Ohm]; // constant impedance load on phase A, imaginary only, specified as Ohms
		double constant_impedance_B_reac[Ohm]; // constant impedance load on phase B, imaginary only, specified as Ohms
		double constant_impedance_C_reac[Ohm]; // constant impedance load on phase C, imaginary only, specified as Ohms
		complex measured_voltage_A; // current measured voltage on phase A
		complex measured_voltage_B; // current measured voltage on phase B
		complex measured_voltage_C; // current measured voltage on phase C
		complex measured_voltage_AB; // current measured voltage on phases AB
		complex measured_voltage_BC; // current measured voltage on phases BC
		complex measured_voltage_CA; // current measured voltage on phases CA
		bool phase_loss_protection; // Trip all three phases of the load if a fault occurs
		double base_power_A[VA]; // in similar format as ZIPload, this represents the nominal power on phase A before applying ZIP fractions
		double base_power_B[VA]; // in similar format as ZIPload, this represents the nominal power on phase B before applying ZIP fractions
		double base_power_C[VA]; // in similar format as ZIPload, this represents the nominal power on phase C before applying ZIP fractions
		double power_pf_A[pu]; // in similar format as ZIPload, this is the power factor of the phase A constant power portion of load
		double current_pf_A[pu]; // in similar format as ZIPload, this is the power factor of the phase A constant current portion of load
		double impedance_pf_A[pu]; // in similar format as ZIPload, this is the power factor of the phase A constant impedance portion of load
		double power_pf_B[pu]; // in similar format as ZIPload, this is the power factor of the phase B constant power portion of load
		double current_pf_B[pu]; // in similar format as ZIPload, this is the power factor of the phase B constant current portion of load
		double impedance_pf_B[pu]; // in similar format as ZIPload, this is the power factor of the phase B constant impedance portion of load
		double power_pf_C[pu]; // in similar format as ZIPload, this is the power factor of the phase C constant power portion of load
		double current_pf_C[pu]; // in similar format as ZIPload, this is the power factor of the phase C constant current portion of load
		double impedance_pf_C[pu]; // in similar format as ZIPload, this is the power factor of the phase C constant impedance portion of load
		double power_fraction_A[pu]; // this is the constant power fraction of base power on phase A
		double current_fraction_A[pu]; // this is the constant current fraction of base power on phase A
		double impedance_fraction_A[pu]; // this is the constant impedance fraction of base power on phase A
		double power_fraction_B[pu]; // this is the constant power fraction of base power on phase B
		double current_fraction_B[pu]; // this is the constant current fraction of base power on phase B
		double impedance_fraction_B[pu]; // this is the constant impedance fraction of base power on phase B
		double power_fraction_C[pu]; // this is the constant power fraction of base power on phase C
		double current_fraction_C[pu]; // this is the constant current fraction of base power on phase C
		double impedance_fraction_C[pu]; // this is the constant impedance fraction of base power on phase C
	}

	object weather;
	double T_nominal[degF];
	double Zp_T[ohm/degF];
	double Zp_H[ohm/%];
	double Zp_S[ohm];
	double Zp_W[ohm/mph];
	double Zp_R[ohm];
	double Zp[ohm];
	double Zq_T[F/degF];
	double Zq_H[F/%];
	double Zq_S[F];
	double Zq_W[F/mph];
	double Zq_R[F];
	double Zq[F];
	double Im_T[A/degF];
	double Im_H[A/%];
	double Im_S[A];
	double Im_W[A/mph];
	double Im_R[A];
	double Im[A];
	double Ia_T[deg/degF];
	double Ia_H[deg/%];
	double Ia_S[deg];
	double Ia_W[deg/mph];
	double Ia_R[deg];
	double Ia[deg];
	double Pp_T[W/degF];
	double Pp_H[W/%];
	double Pp_S[W];
	double Pp_W[W/mph];
	double Pp_R[W];
	double Pp[W];
	double Pq_T[VAr/degF];
	double Pq_H[VAr/%];
	double Pq_S[VAr];
	double Pq_W[VAr/mph];
	double Pq_R[VAr];
	double Pq[VAr];
	double input_temp[degF];
	double input_humid[%];
	double input_solar[Btu/h];
	double input_wind[mph];
	double input_rain[in/h];
	double output_imped_p[Ohm];
	double output_imped_q[Ohm];
	double output_current_m[A];
	double output_current_a[deg];
	double output_power_p[W];
	double output_power_q[VAr];
	complex output_impedance[ohm];
	complex output_current[A];
	complex output_power[VA];
}

class recloser {
	parent switch;
	class switch {
		parent link;
		class link {
			parent powerflow_object;
			class powerflow_object {
				set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
				double nominal_voltage[V];
			}

			enumeration {OPEN=0, CLOSED=1} status; // 
			object from; // from_node - source node
			object to; // to_node - load node
			complex power_in[VA]; // power flow in (w.r.t from node)
			complex power_out[VA]; // power flow out (w.r.t to node)
			double power_out_real[W]; // power flow out (w.r.t to node), real
			complex power_losses[VA]; // power losses
			complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
			complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
			complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
			complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
			complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
			complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
			complex power_losses_A[VA]; // power losses, phase A
			complex power_losses_B[VA]; // power losses, phase B
			complex power_losses_C[VA]; // power losses, phase C
			complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
			complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
			complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
			complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
			complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
			complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
			complex fault_current_in_A[A]; // fault current flowing in, phase A
			complex fault_current_in_B[A]; // fault current flowing in, phase B
			complex fault_current_in_C[A]; // fault current flowing in, phase C
			complex fault_current_out_A[A]; // fault current flowing out, phase A
			complex fault_current_out_B[A]; // fault current flowing out, phase B
			complex fault_current_out_C[A]; // fault current flowing out, phase C
			set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
			double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
			double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
			double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
		}

		function change_switch_state();
		function reliability_operation();
		function create_fault();
		function fix_fault();
		function change_switch_faults();
		enumeration {CLOSED=1, OPEN=0} phase_A_state; // Defines the current state of the phase A switch
		enumeration {CLOSED=1, OPEN=0} phase_B_state; // Defines the current state of the phase B switch
		enumeration {CLOSED=1, OPEN=0} phase_C_state; // Defines the current state of the phase C switch
		enumeration {BANKED=1, INDIVIDUAL=0} operating_mode; // Defines whether the switch operates in a banked or per-phase control mode
	}

	function change_recloser_state();
	function recloser_reliability_operation();
	function change_recloser_faults();
	double retry_time[s]; // the amount of time in seconds to wait before the recloser attempts to close
	double max_number_of_tries; // the number of times the recloser will try to close before permanently opening
	double number_of_tries; // Current number of tries recloser has attempted
}

class regulator {
	parent link;
	class link {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		enumeration {OPEN=0, CLOSED=1} status; // 
		object from; // from_node - source node
		object to; // to_node - load node
		complex power_in[VA]; // power flow in (w.r.t from node)
		complex power_out[VA]; // power flow out (w.r.t to node)
		double power_out_real[W]; // power flow out (w.r.t to node), real
		complex power_losses[VA]; // power losses
		complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
		complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
		complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
		complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
		complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
		complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
		complex power_losses_A[VA]; // power losses, phase A
		complex power_losses_B[VA]; // power losses, phase B
		complex power_losses_C[VA]; // power losses, phase C
		complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
		complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
		complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
		complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
		complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
		complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
		complex fault_current_in_A[A]; // fault current flowing in, phase A
		complex fault_current_in_B[A]; // fault current flowing in, phase B
		complex fault_current_in_C[A]; // fault current flowing in, phase C
		complex fault_current_out_A[A]; // fault current flowing out, phase A
		complex fault_current_out_B[A]; // fault current flowing out, phase B
		complex fault_current_out_C[A]; // fault current flowing out, phase C
		set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
		double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
	}

	object configuration; // reference to the regulator_configuration object used to determine regulator properties
	int16 tap_A; // current tap position of tap A
	int16 tap_B; // current tap position of tap B
	int16 tap_C; // current tap position of tap C
	double tap_A_change_count; // count of all physical tap changes on phase A since beginning of simulation (plus initial value)
	double tap_B_change_count; // count of all physical tap changes on phase B since beginning of simulation (plus initial value)
	double tap_C_change_count; // count of all physical tap changes on phase C since beginning of simulation (plus initial value)
	object sense_node; // Node to be monitored for voltage control in remote sense mode
}

class regulator_configuration {
	enumeration {CLOSED_DELTA=5, OPEN_DELTA_CABA=4, OPEN_DELTA_BCAC=3, OPEN_DELTA_ABBC=2, WYE_WYE=1, UNKNOWN=0} connect_type; // Designation of connection style
	double band_center[V]; // band center setting of regulator control
	double band_width[V]; // band width setting of regulator control
	double time_delay[s]; // mechanical time delay between tap changes
	double dwell_time[s]; // time delay before a control action of regulator control
	int16 raise_taps; // number of regulator raise taps, or the maximum raise voltage tap position
	int16 lower_taps; // number of regulator lower taps, or the minimum lower voltage tap position
	double current_transducer_ratio[pu]; // primary rating of current transformer
	double power_transducer_ratio[pu]; // potential transformer rating
	double compensator_r_setting_A[V]; // Line Drop Compensation R setting of regulator control (in volts) on Phase A
	double compensator_r_setting_B[V]; // Line Drop Compensation R setting of regulator control (in volts) on Phase B
	double compensator_r_setting_C[V]; // Line Drop Compensation R setting of regulator control (in volts) on Phase C
	double compensator_x_setting_A[V]; // Line Drop Compensation X setting of regulator control (in volts) on Phase A
	double compensator_x_setting_B[V]; // Line Drop Compensation X setting of regulator control (in volts) on Phase B
	double compensator_x_setting_C[V]; // Line Drop Compensation X setting of regulator control (in volts) on Phase C
	set {C=4, B=2, A=1} CT_phase; // phase(s) monitored by CT
	set {C=4, B=2, A=1} PT_phase; // phase(s) monitored by PT
	double regulation; // regulation of voltage regulator in %
	enumeration {BANK=2, INDIVIDUAL=1} control_level; // Designates whether control is on per-phase or banked level
	enumeration {REMOTE_NODE=3, LINE_DROP_COMP=4, OUTPUT_VOLTAGE=2, MANUAL=1} Control; // Type of control used for regulating voltage
	enumeration {B=2, A=1} Type; // Defines regulator type
	int16 tap_pos_A; // initial tap position of phase A
	int16 tap_pos_B; // initial tap position of phase B
	int16 tap_pos_C; // initial tap position of phase C
}

class relay {
	parent link;
	class link {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		enumeration {OPEN=0, CLOSED=1} status; // 
		object from; // from_node - source node
		object to; // to_node - load node
		complex power_in[VA]; // power flow in (w.r.t from node)
		complex power_out[VA]; // power flow out (w.r.t to node)
		double power_out_real[W]; // power flow out (w.r.t to node), real
		complex power_losses[VA]; // power losses
		complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
		complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
		complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
		complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
		complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
		complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
		complex power_losses_A[VA]; // power losses, phase A
		complex power_losses_B[VA]; // power losses, phase B
		complex power_losses_C[VA]; // power losses, phase C
		complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
		complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
		complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
		complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
		complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
		complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
		complex fault_current_in_A[A]; // fault current flowing in, phase A
		complex fault_current_in_B[A]; // fault current flowing in, phase B
		complex fault_current_in_C[A]; // fault current flowing in, phase C
		complex fault_current_out_A[A]; // fault current flowing out, phase A
		complex fault_current_out_B[A]; // fault current flowing out, phase B
		complex fault_current_out_C[A]; // fault current flowing out, phase C
		set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
		double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
	}

	double time_to_change[s]; // time for state to change
	double recloser_delay[s]; // time delay before reclose (s)
	int16 recloser_tries; // number of times recloser has tried
	int16 recloser_limit; // maximum number of recloser tries
	bool recloser_event; // Flag for if we are in a reliabilty relay event or not
}

class restoration {
	int32 reconfig_attempts; // Number of reconfigurations/timestep to try before giving up
	int32 reconfig_iteration_limit; // Number of iterations to let PF go before flagging this as a bad reconfiguration
	bool populate_tree; // Flag to populate Parent/Child tree structure
}

class sectionalizer {
	parent switch;
	class switch {
		parent link;
		class link {
			parent powerflow_object;
			class powerflow_object {
				set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
				double nominal_voltage[V];
			}

			enumeration {OPEN=0, CLOSED=1} status; // 
			object from; // from_node - source node
			object to; // to_node - load node
			complex power_in[VA]; // power flow in (w.r.t from node)
			complex power_out[VA]; // power flow out (w.r.t to node)
			double power_out_real[W]; // power flow out (w.r.t to node), real
			complex power_losses[VA]; // power losses
			complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
			complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
			complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
			complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
			complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
			complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
			complex power_losses_A[VA]; // power losses, phase A
			complex power_losses_B[VA]; // power losses, phase B
			complex power_losses_C[VA]; // power losses, phase C
			complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
			complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
			complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
			complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
			complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
			complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
			complex fault_current_in_A[A]; // fault current flowing in, phase A
			complex fault_current_in_B[A]; // fault current flowing in, phase B
			complex fault_current_in_C[A]; // fault current flowing in, phase C
			complex fault_current_out_A[A]; // fault current flowing out, phase A
			complex fault_current_out_B[A]; // fault current flowing out, phase B
			complex fault_current_out_C[A]; // fault current flowing out, phase C
			set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
			double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
			double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
			double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
		}

		function change_switch_state();
		function reliability_operation();
		function create_fault();
		function fix_fault();
		function change_switch_faults();
		enumeration {CLOSED=1, OPEN=0} phase_A_state; // Defines the current state of the phase A switch
		enumeration {CLOSED=1, OPEN=0} phase_B_state; // Defines the current state of the phase B switch
		enumeration {CLOSED=1, OPEN=0} phase_C_state; // Defines the current state of the phase C switch
		enumeration {BANKED=1, INDIVIDUAL=0} operating_mode; // Defines whether the switch operates in a banked or per-phase control mode
	}

	function change_sectionalizer_state();
	function sectionalizer_reliability_operation();
	function change_sectionalizer_faults();
}

class series_reactor {
	parent link;
	class link {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		enumeration {OPEN=0, CLOSED=1} status; // 
		object from; // from_node - source node
		object to; // to_node - load node
		complex power_in[VA]; // power flow in (w.r.t from node)
		complex power_out[VA]; // power flow out (w.r.t to node)
		double power_out_real[W]; // power flow out (w.r.t to node), real
		complex power_losses[VA]; // power losses
		complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
		complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
		complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
		complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
		complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
		complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
		complex power_losses_A[VA]; // power losses, phase A
		complex power_losses_B[VA]; // power losses, phase B
		complex power_losses_C[VA]; // power losses, phase C
		complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
		complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
		complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
		complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
		complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
		complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
		complex fault_current_in_A[A]; // fault current flowing in, phase A
		complex fault_current_in_B[A]; // fault current flowing in, phase B
		complex fault_current_in_C[A]; // fault current flowing in, phase C
		complex fault_current_out_A[A]; // fault current flowing out, phase A
		complex fault_current_out_B[A]; // fault current flowing out, phase B
		complex fault_current_out_C[A]; // fault current flowing out, phase C
		set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
		double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
	}

	complex phase_A_impedance[Ohm]; // Series impedance of reactor on phase A
	double phase_A_resistance[Ohm]; // Resistive portion of phase A's impedance
	double phase_A_reactance[Ohm]; // Reactive portion of phase A's impedance
	complex phase_B_impedance[Ohm]; // Series impedance of reactor on phase B
	double phase_B_resistance[Ohm]; // Resistive portion of phase B's impedance
	double phase_B_reactance[Ohm]; // Reactive portion of phase B's impedance
	complex phase_C_impedance[Ohm]; // Series impedance of reactor on phase C
	double phase_C_resistance[Ohm]; // Resistive portion of phase C's impedance
	double phase_C_reactance[Ohm]; // Reactive portion of phase C's impedance
	double rated_current_limit[A]; // Rated current limit for the reactor
}

class substation {
	parent node;
	class node {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		function delta_linkage_node();
		function interupdate_pwr_object();
		function delta_freq_pwr_object();
		enumeration {SWING=2, PV=1, PQ=0} bustype; // defines whether the node is a PQ, PV, or SWING node
		set {HASSOURCE=1} busflags; // flag indicates node has a source for voltage, i.e. connects to the swing node
		object reference_bus; // reference bus from which frequency is defined
		double maximum_voltage_error[V]; // convergence voltage limit or convergence criteria
		complex voltage_A[V]; // bus voltage, Phase A to ground
		complex voltage_B[V]; // bus voltage, Phase B to ground
		complex voltage_C[V]; // bus voltage, Phase C to ground
		complex voltage_AB[V]; // line voltages, Phase AB
		complex voltage_BC[V]; // line voltages, Phase BC
		complex voltage_CA[V]; // line voltages, Phase CA
		complex current_A[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex current_B[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex current_C[A]; // bus current injection (in = positive), this an accumulator only, not a output or input variable
		complex power_A[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex power_B[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex power_C[VA]; // bus power injection (in = positive), this an accumulator only, not a output or input variable
		complex shunt_A[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		complex shunt_B[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		complex shunt_C[S]; // bus shunt admittance, this an accumulator only, not a output or input variable
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} service_status; // In and out of service flag
		double service_status_double; // In and out of service flag - type double - will indiscriminately override service_status - useful for schedules
		double previous_uptime[min]; // Previous time between disconnects of node in minutes
		double current_uptime[min]; // Current time since last disconnect of node in minutes
		object topological_parent; // topological parent as per GLM configuration
	}

	complex zero_sequence_voltage[V]; // The zero sequence representation of the voltage for the substation object.
	complex positive_sequence_voltage[V]; // The positive sequence representation of the voltage for the substation object.
	complex negative_sequence_voltage[V]; // The negative sequence representation of the voltage for the substation object.
	double base_power[VA]; // The 3 phase VA power rating of the substation.
	double power_convergence_value[VA]; // Default convergence criterion before power is posted to pw_load objects if connected, otherwise ignored
	enumeration {PHASE_C=2, PHASE_B=1, PHASE_A=0} reference_phase; // The reference phase for the positive sequence voltage.
	complex transmission_level_constant_power_load[VA]; // the average constant power load to be posted directly to the pw_load object.
	complex transmission_level_constant_current_load[A]; // the average constant current load at nominal voltage to be posted directly to the pw_load object.
	complex transmission_level_constant_impedance_load[Ohm]; // the average constant impedance load at nominal voltage to be posted directly to the pw_load object.
	complex average_distribution_load[VA]; // The average of the loads on all three phases at the substation object.
	complex distribution_power_A[VA];
	complex distribution_power_B[VA];
	complex distribution_power_C[VA];
	complex distribution_voltage_A[V];
	complex distribution_voltage_B[V];
	complex distribution_voltage_C[V];
	complex distribution_voltage_AB[V];
	complex distribution_voltage_BC[V];
	complex distribution_voltage_CA[V];
	complex distribution_current_A[A];
	complex distribution_current_B[A];
	complex distribution_current_C[A];
	double distribution_real_energy[Wh];
}

class switch {
	parent link;
	class link {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		enumeration {OPEN=0, CLOSED=1} status; // 
		object from; // from_node - source node
		object to; // to_node - load node
		complex power_in[VA]; // power flow in (w.r.t from node)
		complex power_out[VA]; // power flow out (w.r.t to node)
		double power_out_real[W]; // power flow out (w.r.t to node), real
		complex power_losses[VA]; // power losses
		complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
		complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
		complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
		complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
		complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
		complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
		complex power_losses_A[VA]; // power losses, phase A
		complex power_losses_B[VA]; // power losses, phase B
		complex power_losses_C[VA]; // power losses, phase C
		complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
		complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
		complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
		complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
		complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
		complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
		complex fault_current_in_A[A]; // fault current flowing in, phase A
		complex fault_current_in_B[A]; // fault current flowing in, phase B
		complex fault_current_in_C[A]; // fault current flowing in, phase C
		complex fault_current_out_A[A]; // fault current flowing out, phase A
		complex fault_current_out_B[A]; // fault current flowing out, phase B
		complex fault_current_out_C[A]; // fault current flowing out, phase C
		set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
		double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
	}

	function change_switch_state();
	function reliability_operation();
	function create_fault();
	function fix_fault();
	function change_switch_faults();
	enumeration {CLOSED=1, OPEN=0} phase_A_state; // Defines the current state of the phase A switch
	enumeration {CLOSED=1, OPEN=0} phase_B_state; // Defines the current state of the phase B switch
	enumeration {CLOSED=1, OPEN=0} phase_C_state; // Defines the current state of the phase C switch
	enumeration {BANKED=1, INDIVIDUAL=0} operating_mode; // Defines whether the switch operates in a banked or per-phase control mode
}

class transformer {
	parent link;
	class link {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		enumeration {OPEN=0, CLOSED=1} status; // 
		object from; // from_node - source node
		object to; // to_node - load node
		complex power_in[VA]; // power flow in (w.r.t from node)
		complex power_out[VA]; // power flow out (w.r.t to node)
		double power_out_real[W]; // power flow out (w.r.t to node), real
		complex power_losses[VA]; // power losses
		complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
		complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
		complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
		complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
		complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
		complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
		complex power_losses_A[VA]; // power losses, phase A
		complex power_losses_B[VA]; // power losses, phase B
		complex power_losses_C[VA]; // power losses, phase C
		complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
		complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
		complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
		complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
		complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
		complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
		complex fault_current_in_A[A]; // fault current flowing in, phase A
		complex fault_current_in_B[A]; // fault current flowing in, phase B
		complex fault_current_in_C[A]; // fault current flowing in, phase C
		complex fault_current_out_A[A]; // fault current flowing out, phase A
		complex fault_current_out_B[A]; // fault current flowing out, phase B
		complex fault_current_out_C[A]; // fault current flowing out, phase C
		set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
		double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
		double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
		double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
	}

	function power_calculation();
	object configuration; // Configuration library used for transformer setup
	object climate; // climate object used to describe thermal model ambient temperature
	double ambient_temperature[degC]; // ambient temperature in degrees C
	double top_oil_hot_spot_temperature[degC]; // top-oil hottest-spot temperature, degrees C
	double winding_hot_spot_temperature[degC]; // winding hottest-spot temperature, degrees C
	double percent_loss_of_life; // the percent loss of life
	double aging_constant; // the aging rate slope for the transformer insulation
	bool use_thermal_model; // boolean to enable use of thermal model
	double transformer_replacement_count; // counter of the number times the transformer has been replaced due to lifetime failure
	double aging_granularity[s]; // maximum timestep before updating thermal and aging model in seconds
}

class transformer_configuration {
	enumeration {SINGLE_PHASE_CENTER_TAPPED=5, SINGLE_PHASE=4, DELTA_GWYE=3, DELTA_DELTA=2, WYE_WYE=1, UNKNOWN=0} connect_type; // connect type enum: Wye-Wye, single-phase, etc.
	enumeration {VAULT=3, PADMOUNT=2, POLETOP=1, UNKNOWN=0} install_type; // Defines location of the transformer installation
	enumeration {DRY=2, MINERAL_OIL=1, UNKNOWN=0} coolant_type; // coolant type, used in life time model
	enumeration {DFOW=6, DFOA=5, NDFOW=4, NDFOA=3, FA=2, OA=1, UNKNOWN=0} cooling_type; // type of coolant fluid used in life time model
	double primary_voltage[V]; // primary voltage level in L-L value kV
	double secondary_voltage[V]; // secondary voltage level kV
	double power_rating[kVA]; // kVA rating of transformer, total
	double powerA_rating[kVA]; // kVA rating of transformer, phase A
	double powerB_rating[kVA]; // kVA rating of transformer, phase B
	double powerC_rating[kVA]; // kVA rating of transformer, phase C
	double resistance[pu]; // Series impedance, pu, real
	double reactance[pu]; // Series impedance, pu, imag
	complex impedance[pu]; // Series impedance, pu
	double resistance1[pu]; // Secondary series impedance (only used when you want to define each individual winding seperately, pu, real
	double reactance1[pu]; // Secondary series impedance (only used when you want to define each individual winding seperately, pu, imag
	complex impedance1[pu]; // Secondary series impedance (only used when you want to define each individual winding seperately, pu
	double resistance2[pu]; // Secondary series impedance (only used when you want to define each individual winding seperately, pu, real
	double reactance2[pu]; // Secondary series impedance (only used when you want to define each individual winding seperately, pu, imag
	complex impedance2[pu]; // Secondary series impedance (only used when you want to define each individual winding seperately, pu
	double shunt_resistance[pu]; // Shunt impedance on primary side, pu, real
	double shunt_reactance[pu]; // Shunt impedance on primary side, pu, imag
	complex shunt_impedance[pu]; // Shunt impedance on primary side, pu
	double core_coil_weight[lb]; // The weight of the core and coil assembly in pounds
	double tank_fittings_weight[lb]; // The weight of the tank and fittings in pounds
	double oil_volume[gal]; // The number of gallons of oil in the transformer
	double rated_winding_time_constant[h]; // The rated winding time constant in hours
	double rated_winding_hot_spot_rise[degC]; // winding hottest-spot rise over ambient temperature at rated load, degrees C
	double rated_top_oil_rise[degC]; // top-oil hottest-spot rise over ambient temperature at rated load, degrees C
	double no_load_loss[pu]; // Another method of specifying transformer impedances, defined as per unit power values (shunt)
	double full_load_loss[pu]; // Another method of specifying transformer impedances, defined as per unit power values (shunt and series)
	double reactance_resistance_ratio; // the reactance to resistance ratio (X/R)
	double installed_insulation_life[h]; // the normal lifetime of the transformer insulation at rated load, hours
}

class triplex_line {
	parent line;
	class line {
		parent link;
		class link {
			parent powerflow_object;
			class powerflow_object {
				set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
				double nominal_voltage[V];
			}

			enumeration {OPEN=0, CLOSED=1} status; // 
			object from; // from_node - source node
			object to; // to_node - load node
			complex power_in[VA]; // power flow in (w.r.t from node)
			complex power_out[VA]; // power flow out (w.r.t to node)
			double power_out_real[W]; // power flow out (w.r.t to node), real
			complex power_losses[VA]; // power losses
			complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
			complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
			complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
			complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
			complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
			complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
			complex power_losses_A[VA]; // power losses, phase A
			complex power_losses_B[VA]; // power losses, phase B
			complex power_losses_C[VA]; // power losses, phase C
			complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
			complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
			complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
			complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
			complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
			complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
			complex fault_current_in_A[A]; // fault current flowing in, phase A
			complex fault_current_in_B[A]; // fault current flowing in, phase B
			complex fault_current_in_C[A]; // fault current flowing in, phase C
			complex fault_current_out_A[A]; // fault current flowing out, phase A
			complex fault_current_out_B[A]; // fault current flowing out, phase B
			complex fault_current_out_C[A]; // fault current flowing out, phase C
			set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
			double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
			double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
			double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
		}

		object configuration;
		double length[ft];
	}

}

class triplex_line_conductor {
	double resistance[Ohm/mile]; // resistance of cable in ohm/mile
	double geometric_mean_radius[ft]; // geometric mean radius of the cable
	double rating.summer.continuous[A]; // amp ratings for the cable during continuous operation in summer
	double rating.summer.emergency[A]; // amp ratings for the cable during short term operation in summer
	double rating.winter.continuous[A]; // amp ratings for the cable during continuous operation in winter
	double rating.winter.emergency[A]; // amp ratings for the cable during short term operation in winter
}

class triplex_line_configuration {
	object conductor_1; // conductor type for phase 1
	object conductor_2; // conductor type for phase 2
	object conductor_N; // conductor type for phase N
	double insulation_thickness[in]; // thickness of insulation around cabling
	double diameter[in]; // total diameter of cable
	object spacing; // defines the line spacing configuration
	complex z11[Ohm/mile]; // phase 1 self-impedance, used for direct entry of impedance values
	complex z12[Ohm/mile]; // phase 1-2 induced impedance, used for direct entry of impedance values
	complex z21[Ohm/mile]; // phase 2-1 induced impedance, used for direct entry of impedance values
	complex z22[Ohm/mile]; // phase 2 self-impedance, used for direct entry of impedance values
}

class triplex_load {
	parent triplex_node;
	class triplex_node {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		enumeration {SWING=2, PV=1, PQ=0} bustype; // defines whether the node is a PQ, PV, or SWING node
		set {HASSOURCE=1} busflags; // flag indicates node has a source for voltage, i.e. connects to the swing node
		object reference_bus; // reference bus from which frequency is defined
		double maximum_voltage_error[V]; // convergence voltage limit or convergence criteria
		complex voltage_1[V]; // bus voltage, phase 1 to ground
		complex voltage_2[V]; // bus voltage, phase 2 to ground
		complex voltage_N[V]; // bus voltage, phase N to ground
		complex voltage_12[V]; // bus voltage, phase 1 to 2
		complex voltage_1N[V]; // bus voltage, phase 1 to N
		complex voltage_2N[V]; // bus voltage, phase 2 to N
		complex current_1[A]; // constant current load on phase 1, also acts as accumulator
		complex current_2[A]; // constant current load on phase 2, also acts as accumulator
		complex current_N[A]; // constant current load on phase N, also acts as accumulator
		double current_1_real[A]; // constant current load on phase 1, real
		double current_2_real[A]; // constant current load on phase 2, real
		double current_N_real[A]; // constant current load on phase N, real
		double current_1_reac[A]; // constant current load on phase 1, imag
		double current_2_reac[A]; // constant current load on phase 2, imag
		double current_N_reac[A]; // constant current load on phase N, imag
		complex current_12[A]; // constant current load on phase 1 to 2
		double current_12_real[A]; // constant current load on phase 1 to 2, real
		double current_12_reac[A]; // constant current load on phase 1 to 2, imag
		complex residential_nominal_current_1[A]; // posted current on phase 1 from a residential object, if attached
		complex residential_nominal_current_2[A]; // posted current on phase 2 from a residential object, if attached
		complex residential_nominal_current_12[A]; // posted current on phase 1 to 2 from a residential object, if attached
		double residential_nominal_current_1_real[A]; // posted current on phase 1, real, from a residential object, if attached
		double residential_nominal_current_1_imag[A]; // posted current on phase 1, imag, from a residential object, if attached
		double residential_nominal_current_2_real[A]; // posted current on phase 2, real, from a residential object, if attached
		double residential_nominal_current_2_imag[A]; // posted current on phase 2, imag, from a residential object, if attached
		double residential_nominal_current_12_real[A]; // posted current on phase 1 to 2, real, from a residential object, if attached
		double residential_nominal_current_12_imag[A]; // posted current on phase 1 to 2, imag, from a residential object, if attached
		complex power_1[VA]; // constant power on phase 1 (120V)
		complex power_2[VA]; // constant power on phase 2 (120V)
		complex power_12[VA]; // constant power on phase 1 to 2 (240V)
		double power_1_real[W]; // constant power on phase 1, real
		double power_2_real[W]; // constant power on phase 2, real
		double power_12_real[W]; // constant power on phase 1 to 2, real
		double power_1_reac[VAr]; // constant power on phase 1, imag
		double power_2_reac[VAr]; // constant power on phase 2, imag
		double power_12_reac[VAr]; // constant power on phase 1 to 2, imag
		complex shunt_1[S]; // constant shunt impedance on phase 1
		complex shunt_2[S]; // constant shunt impedance on phase 2
		complex shunt_12[S]; // constant shunt impedance on phase 1 to 2
		complex impedance_1[Ohm]; // constant series impedance on phase 1
		complex impedance_2[Ohm]; // constant series impedance on phase 2
		complex impedance_12[Ohm]; // constant series impedance on phase 1 to 2
		double impedance_1_real[Ohm]; // constant series impedance on phase 1, real
		double impedance_2_real[Ohm]; // constant series impedance on phase 2, real
		double impedance_12_real[Ohm]; // constant series impedance on phase 1 to 2, real
		double impedance_1_reac[Ohm]; // constant series impedance on phase 1, imag
		double impedance_2_reac[Ohm]; // constant series impedance on phase 2, imag
		double impedance_12_reac[Ohm]; // constant series impedance on phase 1 to 2, imag
		bool house_present; // boolean for detecting whether a house is attached, not an input
		enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} service_status; // In and out of service flag
		double service_status_double; // In and out of service flag - type double - will indiscriminately override service_status - useful for schedules
		double previous_uptime[min]; // Previous time between disconnects of node in minutes
		double current_uptime[min]; // Current time since last disconnect of node in minutes
		object topological_parent; // topological parent as per GLM configuration
	}

	enumeration {A=4, I=3, C=2, R=1, U=0} load_class; // Flag to track load type, not currently used for anything except sorting
	complex constant_power_1[VA]; // constant power load on split phase 1, specified as VA
	complex constant_power_2[VA]; // constant power load on split phase 2, specified as VA
	complex constant_power_12[VA]; // constant power load on split phase 12, specified as VA
	double constant_power_1_real[W]; // constant power load on spit phase 1, real only, specified as W
	double constant_power_2_real[W]; // constant power load on phase 2, real only, specified as W
	double constant_power_12_real[W]; // constant power load on phase 12, real only, specified as W
	double constant_power_1_reac[VAr]; // constant power load on phase 1, imaginary only, specified as VAr
	double constant_power_2_reac[VAr]; // constant power load on phase 2, imaginary only, specified as VAr
	double constant_power_12_reac[VAr]; // constant power load on phase 12, imaginary only, specified as VAr
	complex constant_current_1[A]; // constant current load on phase 1, specified as Amps
	complex constant_current_2[A]; // constant current load on phase 2, specified as Amps
	complex constant_current_12[A]; // constant current load on phase 12, specified as Amps
	double constant_current_1_real[A]; // constant current load on phase 1, real only, specified as Amps
	double constant_current_2_real[A]; // constant current load on phase 2, real only, specified as Amps
	double constant_current_12_real[A]; // constant current load on phase 12, real only, specified as Amps
	double constant_current_1_reac[A]; // constant current load on phase 1, imaginary only, specified as Amps
	double constant_current_2_reac[A]; // constant current load on phase 2, imaginary only, specified as Amps
	double constant_current_12_reac[A]; // constant current load on phase 12, imaginary only, specified as Amps
	complex constant_impedance_1[Ohm]; // constant impedance load on phase 1, specified as Ohms
	complex constant_impedance_2[Ohm]; // constant impedance load on phase 2, specified as Ohms
	complex constant_impedance_12[Ohm]; // constant impedance load on phase 12, specified as Ohms
	double constant_impedance_1_real[Ohm]; // constant impedance load on phase 1, real only, specified as Ohms
	double constant_impedance_2_real[Ohm]; // constant impedance load on phase 2, real only, specified as Ohms
	double constant_impedance_12_real[Ohm]; // constant impedance load on phase 12, real only, specified as Ohms
	double constant_impedance_1_reac[Ohm]; // constant impedance load on phase 1, imaginary only, specified as Ohms
	double constant_impedance_2_reac[Ohm]; // constant impedance load on phase 2, imaginary only, specified as Ohms
	double constant_impedance_12_reac[Ohm]; // constant impedance load on phase 12, imaginary only, specified as Ohms
	complex measured_voltage_1; // current measured voltage on phase 1
	complex measured_voltage_2; // current measured voltage on phase 2
	complex measured_voltage_12; // current measured voltage on phase 12
	double base_power_1[VA]; // in similar format as ZIPload, this represents the nominal power on phase 1 before applying ZIP fractions
	double base_power_2[VA]; // in similar format as ZIPload, this represents the nominal power on phase 2 before applying ZIP fractions
	double base_power_12[VA]; // in similar format as ZIPload, this represents the nominal power on phase 12 before applying ZIP fractions
	double power_pf_1[pu]; // in similar format as ZIPload, this is the power factor of the phase 1 constant power portion of load
	double current_pf_1[pu]; // in similar format as ZIPload, this is the power factor of the phase 1 constant current portion of load
	double impedance_pf_1[pu]; // in similar format as ZIPload, this is the power factor of the phase 1 constant impedance portion of load
	double power_pf_2[pu]; // in similar format as ZIPload, this is the power factor of the phase 2 constant power portion of load
	double current_pf_2[pu]; // in similar format as ZIPload, this is the power factor of the phase 2 constant current portion of load
	double impedance_pf_2[pu]; // in similar format as ZIPload, this is the power factor of the phase 2 constant impedance portion of load
	double power_pf_12[pu]; // in similar format as ZIPload, this is the power factor of the phase 12 constant power portion of load
	double current_pf_12[pu]; // in similar format as ZIPload, this is the power factor of the phase 12 constant current portion of load
	double impedance_pf_12[pu]; // in similar format as ZIPload, this is the power factor of the phase 12 constant impedance portion of load
	double power_fraction_1[pu]; // this is the constant power fraction of base power on phase 1
	double current_fraction_1[pu]; // this is the constant current fraction of base power on phase 1
	double impedance_fraction_1[pu]; // this is the constant impedance fraction of base power on phase 1
	double power_fraction_2[pu]; // this is the constant power fraction of base power on phase 2
	double current_fraction_2[pu]; // this is the constant current fraction of base power on phase 2
	double impedance_fraction_2[pu]; // this is the constant impedance fraction of base power on phase 2
	double power_fraction_12[pu]; // this is the constant power fraction of base power on phase 12
	double current_fraction_12[pu]; // this is the constant current fraction of base power on phase 12
	double impedance_fraction_12[pu]; // this is the constant impedance fraction of base power on phase 12
}

class triplex_meter {
	parent triplex_node;
	class triplex_node {
		parent powerflow_object;
		class powerflow_object {
			set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
			double nominal_voltage[V];
		}

		enumeration {SWING=2, PV=1, PQ=0} bustype; // defines whether the node is a PQ, PV, or SWING node
		set {HASSOURCE=1} busflags; // flag indicates node has a source for voltage, i.e. connects to the swing node
		object reference_bus; // reference bus from which frequency is defined
		double maximum_voltage_error[V]; // convergence voltage limit or convergence criteria
		complex voltage_1[V]; // bus voltage, phase 1 to ground
		complex voltage_2[V]; // bus voltage, phase 2 to ground
		complex voltage_N[V]; // bus voltage, phase N to ground
		complex voltage_12[V]; // bus voltage, phase 1 to 2
		complex voltage_1N[V]; // bus voltage, phase 1 to N
		complex voltage_2N[V]; // bus voltage, phase 2 to N
		complex current_1[A]; // constant current load on phase 1, also acts as accumulator
		complex current_2[A]; // constant current load on phase 2, also acts as accumulator
		complex current_N[A]; // constant current load on phase N, also acts as accumulator
		double current_1_real[A]; // constant current load on phase 1, real
		double current_2_real[A]; // constant current load on phase 2, real
		double current_N_real[A]; // constant current load on phase N, real
		double current_1_reac[A]; // constant current load on phase 1, imag
		double current_2_reac[A]; // constant current load on phase 2, imag
		double current_N_reac[A]; // constant current load on phase N, imag
		complex current_12[A]; // constant current load on phase 1 to 2
		double current_12_real[A]; // constant current load on phase 1 to 2, real
		double current_12_reac[A]; // constant current load on phase 1 to 2, imag
		complex residential_nominal_current_1[A]; // posted current on phase 1 from a residential object, if attached
		complex residential_nominal_current_2[A]; // posted current on phase 2 from a residential object, if attached
		complex residential_nominal_current_12[A]; // posted current on phase 1 to 2 from a residential object, if attached
		double residential_nominal_current_1_real[A]; // posted current on phase 1, real, from a residential object, if attached
		double residential_nominal_current_1_imag[A]; // posted current on phase 1, imag, from a residential object, if attached
		double residential_nominal_current_2_real[A]; // posted current on phase 2, real, from a residential object, if attached
		double residential_nominal_current_2_imag[A]; // posted current on phase 2, imag, from a residential object, if attached
		double residential_nominal_current_12_real[A]; // posted current on phase 1 to 2, real, from a residential object, if attached
		double residential_nominal_current_12_imag[A]; // posted current on phase 1 to 2, imag, from a residential object, if attached
		complex power_1[VA]; // constant power on phase 1 (120V)
		complex power_2[VA]; // constant power on phase 2 (120V)
		complex power_12[VA]; // constant power on phase 1 to 2 (240V)
		double power_1_real[W]; // constant power on phase 1, real
		double power_2_real[W]; // constant power on phase 2, real
		double power_12_real[W]; // constant power on phase 1 to 2, real
		double power_1_reac[VAr]; // constant power on phase 1, imag
		double power_2_reac[VAr]; // constant power on phase 2, imag
		double power_12_reac[VAr]; // constant power on phase 1 to 2, imag
		complex shunt_1[S]; // constant shunt impedance on phase 1
		complex shunt_2[S]; // constant shunt impedance on phase 2
		complex shunt_12[S]; // constant shunt impedance on phase 1 to 2
		complex impedance_1[Ohm]; // constant series impedance on phase 1
		complex impedance_2[Ohm]; // constant series impedance on phase 2
		complex impedance_12[Ohm]; // constant series impedance on phase 1 to 2
		double impedance_1_real[Ohm]; // constant series impedance on phase 1, real
		double impedance_2_real[Ohm]; // constant series impedance on phase 2, real
		double impedance_12_real[Ohm]; // constant series impedance on phase 1 to 2, real
		double impedance_1_reac[Ohm]; // constant series impedance on phase 1, imag
		double impedance_2_reac[Ohm]; // constant series impedance on phase 2, imag
		double impedance_12_reac[Ohm]; // constant series impedance on phase 1 to 2, imag
		bool house_present; // boolean for detecting whether a house is attached, not an input
		enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} service_status; // In and out of service flag
		double service_status_double; // In and out of service flag - type double - will indiscriminately override service_status - useful for schedules
		double previous_uptime[min]; // Previous time between disconnects of node in minutes
		double current_uptime[min]; // Current time since last disconnect of node in minutes
		object topological_parent; // topological parent as per GLM configuration
	}

	double measured_real_energy[Wh]; // metered real energy consumption
	double measured_reactive_energy[VAh]; // metered reactive energy consumption
	complex measured_power[VA]; // metered power
	complex indiv_measured_power_1[VA]; // metered power, phase 1
	complex indiv_measured_power_2[VA]; // metered power, phase 2
	complex indiv_measured_power_N[VA]; // metered power, phase N
	double measured_demand[W]; // metered demand (peak of power)
	double measured_real_power[W]; // metered real power
	double measured_reactive_power[VAr]; // metered reactive power
	complex meter_power_consumption[VA]; // power consumed by meter operation
	complex measured_voltage_1[V]; // measured voltage, phase 1 to ground
	complex measured_voltage_2[V]; // measured voltage, phase 2 to ground
	complex measured_voltage_N[V]; // measured voltage, phase N to ground
	complex measured_current_1[A]; // measured current, phase 1
	complex measured_current_2[A]; // measured current, phase 2
	complex measured_current_N[A]; // measured current, phase N
	bool customer_interrupted; // Reliability flag - goes active if the customer is in an interrupted state
	bool customer_interrupted_secondary; // Reliability flag - goes active if the customer is in a secondary interrupted state - i.e., momentary
	double monthly_bill; // Accumulator for the current month's bill
	double previous_monthly_bill; // Total monthly bill for the previous month
	double previous_monthly_energy[kWh]; // 
	double monthly_fee; // Total monthly energy for the previous month
	double monthly_energy[kWh]; // Accumulator for the current month's energy
	enumeration {TIERED_RTP=4, HOURLY=3, TIERED=2, UNIFORM=1, NONE=0} bill_mode; // Designates the bill mode to be used
	object power_market; // Designates the auction object where prices are read from for bill mode
	int32 bill_day; // Day bill is to be processed (assumed to occur at midnight of that day)
	double price; // Standard uniform pricing
	double price_base; // Used only in TIERED_RTP mode to describe the price before the first tier
	double first_tier_price; // first tier price of energy between first and second tier energy
	double first_tier_energy[kWh]; // price of energy on tier above price or price base
	double second_tier_price; // first tier price of energy between second and third tier energy
	double second_tier_energy[kWh]; // price of energy on tier above first tier
	double third_tier_price; // first tier price of energy greater than third tier energy
	double third_tier_energy[kWh]; // price of energy on tier above second tier
}

class triplex_node {
	parent powerflow_object;
	class powerflow_object {
		set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
		double nominal_voltage[V];
	}

	enumeration {SWING=2, PV=1, PQ=0} bustype; // defines whether the node is a PQ, PV, or SWING node
	set {HASSOURCE=1} busflags; // flag indicates node has a source for voltage, i.e. connects to the swing node
	object reference_bus; // reference bus from which frequency is defined
	double maximum_voltage_error[V]; // convergence voltage limit or convergence criteria
	complex voltage_1[V]; // bus voltage, phase 1 to ground
	complex voltage_2[V]; // bus voltage, phase 2 to ground
	complex voltage_N[V]; // bus voltage, phase N to ground
	complex voltage_12[V]; // bus voltage, phase 1 to 2
	complex voltage_1N[V]; // bus voltage, phase 1 to N
	complex voltage_2N[V]; // bus voltage, phase 2 to N
	complex current_1[A]; // constant current load on phase 1, also acts as accumulator
	complex current_2[A]; // constant current load on phase 2, also acts as accumulator
	complex current_N[A]; // constant current load on phase N, also acts as accumulator
	double current_1_real[A]; // constant current load on phase 1, real
	double current_2_real[A]; // constant current load on phase 2, real
	double current_N_real[A]; // constant current load on phase N, real
	double current_1_reac[A]; // constant current load on phase 1, imag
	double current_2_reac[A]; // constant current load on phase 2, imag
	double current_N_reac[A]; // constant current load on phase N, imag
	complex current_12[A]; // constant current load on phase 1 to 2
	double current_12_real[A]; // constant current load on phase 1 to 2, real
	double current_12_reac[A]; // constant current load on phase 1 to 2, imag
	complex residential_nominal_current_1[A]; // posted current on phase 1 from a residential object, if attached
	complex residential_nominal_current_2[A]; // posted current on phase 2 from a residential object, if attached
	complex residential_nominal_current_12[A]; // posted current on phase 1 to 2 from a residential object, if attached
	double residential_nominal_current_1_real[A]; // posted current on phase 1, real, from a residential object, if attached
	double residential_nominal_current_1_imag[A]; // posted current on phase 1, imag, from a residential object, if attached
	double residential_nominal_current_2_real[A]; // posted current on phase 2, real, from a residential object, if attached
	double residential_nominal_current_2_imag[A]; // posted current on phase 2, imag, from a residential object, if attached
	double residential_nominal_current_12_real[A]; // posted current on phase 1 to 2, real, from a residential object, if attached
	double residential_nominal_current_12_imag[A]; // posted current on phase 1 to 2, imag, from a residential object, if attached
	complex power_1[VA]; // constant power on phase 1 (120V)
	complex power_2[VA]; // constant power on phase 2 (120V)
	complex power_12[VA]; // constant power on phase 1 to 2 (240V)
	double power_1_real[W]; // constant power on phase 1, real
	double power_2_real[W]; // constant power on phase 2, real
	double power_12_real[W]; // constant power on phase 1 to 2, real
	double power_1_reac[VAr]; // constant power on phase 1, imag
	double power_2_reac[VAr]; // constant power on phase 2, imag
	double power_12_reac[VAr]; // constant power on phase 1 to 2, imag
	complex shunt_1[S]; // constant shunt impedance on phase 1
	complex shunt_2[S]; // constant shunt impedance on phase 2
	complex shunt_12[S]; // constant shunt impedance on phase 1 to 2
	complex impedance_1[Ohm]; // constant series impedance on phase 1
	complex impedance_2[Ohm]; // constant series impedance on phase 2
	complex impedance_12[Ohm]; // constant series impedance on phase 1 to 2
	double impedance_1_real[Ohm]; // constant series impedance on phase 1, real
	double impedance_2_real[Ohm]; // constant series impedance on phase 2, real
	double impedance_12_real[Ohm]; // constant series impedance on phase 1 to 2, real
	double impedance_1_reac[Ohm]; // constant series impedance on phase 1, imag
	double impedance_2_reac[Ohm]; // constant series impedance on phase 2, imag
	double impedance_12_reac[Ohm]; // constant series impedance on phase 1 to 2, imag
	bool house_present; // boolean for detecting whether a house is attached, not an input
	enumeration {OUT_OF_SERVICE=0, IN_SERVICE=1} service_status; // In and out of service flag
	double service_status_double; // In and out of service flag - type double - will indiscriminately override service_status - useful for schedules
	double previous_uptime[min]; // Previous time between disconnects of node in minutes
	double current_uptime[min]; // Current time since last disconnect of node in minutes
	object topological_parent; // topological parent as per GLM configuration
}

class underground_line {
	parent line;
	class line {
		parent link;
		class link {
			parent powerflow_object;
			class powerflow_object {
				set {A=1, B=2, C=4, D=256, N=8, S=112, G=128} phases;
				double nominal_voltage[V];
			}

			enumeration {OPEN=0, CLOSED=1} status; // 
			object from; // from_node - source node
			object to; // to_node - load node
			complex power_in[VA]; // power flow in (w.r.t from node)
			complex power_out[VA]; // power flow out (w.r.t to node)
			double power_out_real[W]; // power flow out (w.r.t to node), real
			complex power_losses[VA]; // power losses
			complex power_in_A[VA]; // power flow in (w.r.t from node), phase A
			complex power_in_B[VA]; // power flow in (w.r.t from node), phase B
			complex power_in_C[VA]; // power flow in (w.r.t from node), phase C
			complex power_out_A[VA]; // power flow out (w.r.t to node), phase A
			complex power_out_B[VA]; // power flow out (w.r.t to node), phase B
			complex power_out_C[VA]; // power flow out (w.r.t to node), phase C
			complex power_losses_A[VA]; // power losses, phase A
			complex power_losses_B[VA]; // power losses, phase B
			complex power_losses_C[VA]; // power losses, phase C
			complex current_out_A[A]; // current flow out of link (w.r.t. to node), phase A
			complex current_out_B[A]; // current flow out of link (w.r.t. to node), phase B
			complex current_out_C[A]; // current flow out of link (w.r.t. to node), phase C
			complex current_in_A[A]; // current flow to link (w.r.t from node), phase A
			complex current_in_B[A]; // current flow to link (w.r.t from node), phase B
			complex current_in_C[A]; // current flow to link (w.r.t from node), phase C
			complex fault_current_in_A[A]; // fault current flowing in, phase A
			complex fault_current_in_B[A]; // fault current flowing in, phase B
			complex fault_current_in_C[A]; // fault current flowing in, phase C
			complex fault_current_out_A[A]; // fault current flowing out, phase A
			complex fault_current_out_B[A]; // fault current flowing out, phase B
			complex fault_current_out_C[A]; // fault current flowing out, phase C
			set {CN=768, CR=512, CF=256, BN=48, BR=32, BF=16, AN=3, AR=2, AF=1, UNKNOWN=0} flow_direction; // flag used for describing direction of the flow of power
			double mean_repair_time[s]; // Time after a fault clears for the object to be back in service
			double continuous_rating[A]; // Continuous rating for this link object (set individual line segments
			double emergency_rating[A]; // Emergency rating for this link object (set individual line segments
		}

		object configuration;
		double length[ft];
	}

	function create_fault();
	function fix_fault();
}

class underground_line_conductor {
	double outer_diameter[in]; // Outer diameter of conductor and sheath
	double conductor_gmr[ft]; // Geometric mean radius of the conductor
	double conductor_diameter[in]; // Diameter of conductor
	double conductor_resistance[Ohm/mile]; // Resistance of conductor in ohm/mile
	double neutral_gmr[ft]; // Geometric mean radius of the neutral conductor
	double neutral_diameter[in]; // Diameter of the neutral conductor
	double neutral_resistance[Ohm/mile]; // Resistance of netural conductor in ohm/mile
	int16 neutral_strands; // Number of cable strands in neutral conductor
	double insulation_relative_permitivitty[unit]; // Permitivitty of insulation, relative to air
	double shield_gmr[ft]; // Geometric mean radius of shielding sheath
	double shield_resistance[Ohm/mile]; // Resistance of shielding sheath in ohms/mile
	double rating.summer.continuous[A]; // amp rating in summer, continuous
	double rating.summer.emergency[A]; // amp rating in summer, short term
	double rating.winter.continuous[A]; // amp rating in winter, continuous
	double rating.winter.emergency[A]; // amp rating in winter, short term
}

class volt_var_control {
	enumeration {STANDBY=0, ACTIVE=1} control_method; // IVVC activated or in standby
	double capacitor_delay[s]; // Default capacitor time delay - overridden by local defintions
	double regulator_delay[s]; // Default regulator time delay - overriden by local definitions
	double desired_pf; // Desired power-factor magnitude at the substation transformer or regulator
	double d_max; // Scaling constant for capacitor switching on - typically 0.3 - 0.6
	double d_min; // Scaling constant for capacitor switching off - typically 0.1 - 0.4
	object substation_link; // Substation link, transformer, or regulator to measure power factor
	set {C=4, B=2, A=1} pf_phase; // Phase to include in power factor monitoring
	char1024 regulator_list; // List of voltage regulators for the system, separated by commas
	char1024 capacitor_list; // List of controllable capacitors on the system separated by commas
	char1024 voltage_measurements; // List of voltage measurement devices, separated by commas
	char1024 minimum_voltages; // Minimum voltages allowed for feeder, separated by commas
	char1024 maximum_voltages; // Maximum voltages allowed for feeder, separated by commas
	char1024 desired_voltages; // Desired operating voltages for the regulators, separated by commas
	char1024 max_vdrop; // Maximum voltage drop between feeder and end measurements for each regulator, separated by commas
	char1024 high_load_deadband; // High loading case voltage deadband for each regulator, separated by commas
	char1024 low_load_deadband; // Low loading case voltage deadband for each regulator, separated by commas
	bool pf_signed; // Set to true to consider the sign on the power factor.  Otherwise, it just maintains the deadband of +/-desired_pf
}

class voltdump {
	char32 group; // the group ID to output data for (all nodes if empty)
	timestamp runtime; // the time to check voltage data
	char256 filename; // the file to dump the voltage data into
	char256 file; // the file to dump the voltage data into
	int32 runcount; // the number of times the file has been written to
	enumeration {polar=1, rect=0} mode; // dumps the voltages in either polar or rectangular notation
}


FAILED on module name pthreadVC2
class eventgen {
	function add_event();
	char1024 target_group;
	char256 fault_type;
	enumeration {TRIANGLE=10, BETA=9, GAMMA=8, WEIBULL=7, RAYLEIGH=6, EXPONENTIAL=5, PARETO=4, BERNOULLI=3, LOGNORMAL=2, NORMAL=1, UNIFORM=0} failure_dist;
	enumeration {TRIANGLE=10, BETA=9, GAMMA=8, WEIBULL=7, RAYLEIGH=6, EXPONENTIAL=5, PARETO=4, BERNOULLI=3, LOGNORMAL=2, NORMAL=1, UNIFORM=0} restoration_dist;
	double failure_dist_param_1;
	double failure_dist_param_2;
	double restoration_dist_param_1;
	double restoration_dist_param_2;
	char1024 manual_outages;
	double max_outage_length[s];
	int32 max_simultaneous_faults;
}

class metrics {
	char1024 report_file;
	char1024 customer_group;
	object module_metrics_object;
	char1024 metrics_of_interest;
	double metric_interval[s];
	double report_interval[s];
}

class metrics {
	char1024 report_file;
	char1024 customer_group;
	object module_metrics_object;
	char1024 metrics_of_interest;
	double metric_interval[s];
	double report_interval[s];
}


class ZIPload {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double heat_fraction; // fraction of ZIPload that is transferred as heat
	double base_power[kW]; // base real power of the overall load
	double power_pf; // power factor for constant power portion
	double current_pf; // power factor for constant current portion
	double impedance_pf; // power factor for constant impedance portion
	bool is_240; // load is 220/240 V (across both phases)
	double breaker_val[A]; // Amperage of connected breaker
	complex actual_power[kVA]; // variable to pull actual load as function of voltage
	double multiplier; // this variable is used to modify the base power as a function of multiplier x base_power
	bool heatgain_only; // allows the zipload to generate heat only (no kW), not activated by default
	bool demand_response_mode; // Activates equilibrium dynamic representation of demand response
	int16 number_of_devices; // Number of devices to model - base power is the total load of all devices
	int16 thermostatic_control_range; // Range of the thermostat's control operation
	double number_of_devices_off; // Total number of devices that are off
	double number_of_devices_on; // Total number of devices that are on
	double rate_of_cooling[K/h]; // rate at which devices cool down
	double rate_of_heating[K/h]; // rate at which devices heat up
	int16 temperature; // temperature of the device's controlled media (eg air temp or water temp)
	double phi; // duty cycle of the device
	double demand_rate[1/h]; // consumer demand rate that prematurely turns on a device or population
	double nominal_power; // the rated amount of power demanded by devices that are on
	double duty_cycle[pu]; // fraction of time in the on state
	double recovery_duty_cycle[pu]; // fraction of time in the on state, while in recovery interval
	double period[h]; // time interval to apply duty cycle
	double phase[pu]; // initial phase of load; duty will be assumed to occur at beginning of period
}

class appliance {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	complex_array powers;
	complex_array impedances;
	complex_array currents;
	double_array durations;
	double_array transitions;
	double_array heatgains;
}

class clotheswasher {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double motor_power[kW];
	double circuit_split;
	double queue[unit]; // the total laundry accumulated
	double demand[unit/day]; // the amount of laundry accumulating daily
	complex energy_meter[kWh];
	double stall_voltage[V];
	double start_voltage[V];
	double clothesWasherPower;
	complex stall_impedance[Ohm];
	double trip_delay[s];
	double reset_delay[s];
	double Is_on;
	double normal_perc;
	double perm_press_perc;
	double NORMAL_PREWASH_POWER;
	double NORMAL_WASH_POWER;
	double NORMAL_SPIN_LOW_POWER;
	double NORMAL_SPIN_MEDIUM_POWER;
	double NORMAL_SPIN_HIGH_POWER;
	double NORMAL_SMALLWASH_POWER;
	double NORMAL_PREWASH_ENERGY;
	double NORMAL_WASH_ENERGY;
	double NORMAL_SPIN_LOW_ENERGY;
	double NORMAL_SPIN_MEDIUM_ENERGY;
	double NORMAL_SPIN_HIGH_ENERGY;
	double NORMAL_SMALLWASH_ENERGY;
	double PERMPRESS_PREWASH_POWER;
	double PERMPRESS_WASH_POWER;
	double PERMPRESS_SPIN_LOW_POWER;
	double PERMPRESS_SPIN_MEDIUM_POWER;
	double PERMPRESS_SPIN_HIGH_POWER;
	double PERMPRESS_SMALLWASH_POWER;
	double PERMPRESS_PREWASH_ENERGY;
	double PERMPRESS_WASH_ENERGY;
	double PERMPRESS_SPIN_LOW_ENERGY;
	double PERMPRESS_SPIN_MEDIUM_ENERGY;
	double PERMPRESS_SPIN_HIGH_ENERGY;
	double PERMPRESS_SMALLWASH_ENERGY;
	double GENTLE_PREWASH_POWER;
	double GENTLE_WASH_POWER;
	double GENTLE_SPIN_LOW_POWER;
	double GENTLE_SPIN_MEDIUM_POWER;
	double GENTLE_SPIN_HIGH_POWER;
	double GENTLE_SMALLWASH_POWER;
	double GENTLE_PREWASH_ENERGY;
	double GENTLE_WASH_ENERGY;
	double GENTLE_SPIN_LOW_ENERGY;
	double GENTLE_SPIN_MEDIUM_ENERGY;
	double GENTLE_SPIN_HIGH_ENERGY;
	double GENTLE_SMALLWASH_ENERGY;
	double queue_min[unit];
	double queue_max[unit];
	double clotheswasher_run_prob;
	enumeration {SPIN4=9, SPIN3=8, SPIN2=7, SPIN1=6, WASH=5, PREWASH=4, STOPPED=0} state;
	enumeration {SMALLWASH=4, SPIN_WASH=3, SPIN_HIGH=2, SPIN_MEDIUM=1, SPIN_LOW=0} spin_mode;
	enumeration {GENTLE=2, PERM_PRESS=1, NORMAL=0} wash_mode;
}

class dishwasher {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double control_power[W];
	double dishwasher_coil_power_1[W];
	double dishwasher_coil_power_2[W];
	double dishwasher_coil_power_3[W];
	double motor_power[W];
	double circuit_split;
	double queue[unit]; // number of loads accumulated
	double stall_voltage[V];
	double start_voltage[V];
	complex stall_impedance[Ohm];
	double trip_delay[s];
	double reset_delay[s];
	double total_power[W];
	enumeration {HEATEDDRY_ONLY=7, CONTROL_ONLY=6, COIL_ONLY=3, MOTOR_COIL_ONLY=4, MOTOR_ONLY=5, TRIPPED=2, STALLED=1, STOPPED=0} state;
	double energy_baseline[kWh];
	double energy_used[kWh];
	bool control_check1;
	bool control_check2;
	bool control_check3;
	bool control_check4;
	bool control_check5;
	bool control_check6;
	bool control_check7;
	bool control_check8;
	bool control_check9;
	bool control_check10;
	bool control_check11;
	bool control_check12;
	bool control_check_temp;
	bool motor_only_check1;
	bool motor_only_check2;
	bool motor_only_check3;
	bool motor_only_check4;
	bool motor_only_check5;
	bool motor_only_check6;
	bool motor_only_check7;
	bool motor_only_check8;
	bool motor_only_check9;
	bool motor_only_temp1;
	bool motor_only_temp2;
	bool motor_coil_only_check1;
	bool motor_coil_only_check2;
	bool heateddry_check1;
	bool heateddry_check2;
	bool coil_only_check1;
	bool coil_only_check2;
	bool coil_only_check3;
	bool Heateddry_option_check;
	double queue_min[unit];
	double queue_max[unit];
	double pulse_interval_1[s];
	double pulse_interval_2[s];
	double pulse_interval_3[s];
	double pulse_interval_4[s];
	double pulse_interval_5[s];
	double pulse_interval_6[s];
	double pulse_interval_7[s];
	double pulse_interval_8[s];
	double pulse_interval_9[s];
	double pulse_interval_10[s];
	double pulse_interval_11[s];
	double pulse_interval_12[s];
	double pulse_interval_13[s];
	double pulse_interval_14[s];
	double pulse_interval_15[s];
	double pulse_interval_16[s];
	double pulse_interval_17[s];
	double pulse_interval_18[s];
	double pulse_interval_19[s];
	double dishwasher_run_prob;
	double energy_needed[kWh];
	double dishwasher_demand[kWh];
	double daily_dishwasher_demand[kWh];
	double actual_dishwasher_demand[kWh];
	double motor_on_off;
	double motor_coil_on_off;
	bool is_240; // load is 220/240 V (across both phases)
}

class dryer {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double motor_power[W];
	double dryer_coil_power[W];
	double controls_power[W];
	double circuit_split;
	double queue[unit]; // number of loads accumulated
	double queue_min[unit];
	double queue_max[unit];
	double stall_voltage[V];
	double start_voltage[V];
	complex stall_impedance[Ohm];
	double trip_delay[s];
	double reset_delay[s];
	double total_power[W];
	enumeration {CONTROL_ONLY=5, MOTOR_COIL_ONLY=3, MOTOR_ONLY=4, TRIPPED=2, STALLED=1, STOPPED=0} state;
	double energy_baseline[kWh];
	double energy_used[kWh];
	double next_t;
	bool control_check;
	bool motor_only_check1;
	bool motor_only_check2;
	bool motor_only_check3;
	bool motor_only_check4;
	bool motor_only_check5;
	bool motor_only_check6;
	bool dryer_on;
	bool dryer_ready;
	bool dryer_check;
	bool motor_coil_only_check1;
	bool motor_coil_only_check2;
	bool motor_coil_only_check3;
	bool motor_coil_only_check4;
	bool motor_coil_only_check5;
	bool motor_coil_only_check6;
	double dryer_run_prob;
	double dryer_turn_on;
	double pulse_interval_1[s];
	double pulse_interval_2[s];
	double pulse_interval_3[s];
	double pulse_interval_4[s];
	double pulse_interval_5[s];
	double pulse_interval_6[s];
	double pulse_interval_7[s];
	double energy_needed[kWh];
	double daily_dryer_demand[kWh];
	double actual_dryer_demand[kWh];
	double motor_on_off;
	double motor_coil_on_off;
	bool is_240; // load is 220/240 V (across both phases)
}

class evcharger {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	enumeration {HIGH=2, MEDIUM=1, LOW=0} charger_type;
	enumeration {HYBRID=1, ELECTRIC=0} vehicle_type;
	enumeration {WORK=1, HOME=0, UNKNOWN=4294967295} state;
	double p_go_home[unit/h];
	double p_go_work[unit/h];
	double work_dist[mile];
	double capacity[kWh];
	double charge[unit];
	bool charge_at_work;
	double charge_throttle[unit];
	double charger_efficiency[unit]; // Efficiency of the charger in terms of energy in to battery stored
	double power_train_efficiency[mile/kWh]; // Miles per kWh of battery charge
	double mileage_classification[mile]; // Miles expected range on battery only
	char1024 demand_profile;
}

class evcharger_det {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double charge_rate[W]; // Current demanded charge rate of the vehicle
	double variation_mean[s]; // Mean of normal variation of schedule variation
	double variation_std_dev[s]; // Standard deviation of normal variation of schedule times
	double variation_trip_mean[mile]; // Mean of normal variation of trip distance variation
	double variation_trip_std_dev[mile]; // Standard deviation of normal variation of trip distance
	double mileage_classification[mile]; // Mileage classification of electric vehicle
	bool work_charging_available; // Charging available when at work
	char1024 data_file; // Path to .CSV file with vehicle travel information
	int32 vehicle_index; // Index of vehicles in file this particular vehicle's data
	enumeration {DRIVING_WORK=4, DRIVING_HOME=3, WORK=2, HOME=1, UNKNOWN=0} vehicle_location;
	double travel_distance[mile]; // Distance vehicle travels from home to home
	double arrival_at_work; // Time vehicle arrives at work - HHMM
	double duration_at_work[s]; // Duration the vehicle remains at work
	double arrival_at_home; // Time vehicle arrives at home - HHMM
	double duration_at_home[s]; // Duration the vehicle remains at home
	double battery_capacity[kWh]; // Current capacity of the battery in kWh
	double battery_SOC[%]; // State of charge of battery
	double battery_size[kWh]; // Full capacity of battery
	double mileage_efficiency[mile/kWh]; // Efficiency of drive train in mile/kWh
	double maximum_charge_rate[W]; // Maximum output rate of charger in kW
	double charging_efficiency[unit]; // Efficiency of charger (ratio) when charging
}

class freezer {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double size[cf];
	double rated_capacity[Btu/h];
	double temperature[degF];
	double setpoint[degF];
	double deadband[degF];
	timestamp next_time;
	double output;
	double event_temp;
	double UA[Btu];
	enumeration {ON=1, OFF=0} state;
}

class house {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	function attach_enduse();
	object weather; // reference to the climate object
	double floor_area[sf]; // home conditioned floor area
	double gross_wall_area[sf]; // gross outdoor wall area
	double ceiling_height[ft]; // average ceiling height
	double aspect_ratio; // aspect ratio of the home's footprint
	double envelope_UA[Btu/degF]; // overall UA of the home's envelope
	double window_wall_ratio; // ratio of window area to wall area
	double number_of_doors; // ratio of door area to wall area
	double exterior_wall_fraction; // ratio of exterior wall ratio to wall area
	double interior_exterior_wall_ratio; // ratio of interior to exterior walls
	double exterior_ceiling_fraction; // ratio of external ceiling sf to floor area
	double exterior_floor_fraction; // ratio of floor area used in UA calculation
	double window_shading; // transmission coefficient through window due to glazing
	double window_exterior_transmission_coefficient; // coefficient for the amount of energy that passes through window
	double solar_heatgain_factor; // product of the window area, window transmitivity, and the window exterior transmission coefficient
	double airchange_per_hour; // number of air-changes per hour
	double airchange_UA[Btu/degF]; // additional UA due to air infiltration
	double UA[Btu/degF]; // the total UA
	double internal_gain[Btu/h]; // internal heat gains
	double solar_gain[Btu/h]; // solar heat gains
	double incident_solar_radiation[Btu/h]; // average incident solar radiation hitting the house
	double heat_cool_gain[Btu/h]; // system heat gains(losses)
	set {W=16, S=8, E=4, N=2, H=1, NONE=0} include_solar_quadrant; // bit set for determining which solar incidence quadrants should be included in the solar heatgain
	double horizontal_diffuse_solar_radiation[Btu/h]; // incident solar radiation hitting the top of the house
	double north_incident_solar_radiation[Btu/h]; // incident solar radiation hitting the north side of the house
	double northwest_incident_solar_radiation[Btu/h]; // incident solar radiation hitting the northwest side of the house
	double west_incident_solar_radiation[Btu/h]; // incident solar radiation hitting the west side of the house
	double southwest_incident_solar_radiation[Btu/h]; // incident solar radiation hitting the southwest side of the house
	double south_incident_solar_radiation[Btu/h]; // incident solar radiation hitting the south side of the house
	double southeast_incident_solar_radiation[Btu/h]; // incident solar radiation hitting the southeast side of the house
	double east_incident_solar_radiation[Btu/h]; // incident solar radiation hitting the east side of the house
	double northeast_incident_solar_radiation[Btu/h]; // incident solar radiation hitting the northeast side of the house
	enumeration {CURVED=3, LINEAR=2, FLAT=1, DEFAULT=0} heating_cop_curve; // Defines the function type to use for the adjusted heating COP as a function of outside air temperature.
	enumeration {CURVED=3, LINEAR=2, FLAT=1, DEFAULT=0} heating_cap_curve; // Defines the function type to use for the adjusted heating capacity as a function of outside air temperature.
	enumeration {CURVED=3, LINEAR=2, FLAT=1, DEFAULT=0} cooling_cop_curve; // Defines the function type to use for the adjusted cooling COP as a function of outside air temperature.
	enumeration {CURVED=3, LINEAR=2, FLAT=1, DEFAULT=0} cooling_cap_curve; // Defines the function type to use for the adjusted cooling capacity as a function of outside air temperature.
	bool use_latent_heat; // Boolean for using the heat latency of the air to the humidity when cooling.
	bool include_fan_heatgain; // Boolean to choose whether to include the heat generated by the fan in the ETP model.
	double thermostat_deadband[degF]; // deadband of thermostat control
	double dlc_offset[degF]; // used as a cap to offset the thermostat deadband for direct load control applications
	int16 thermostat_cycle_time; // minimum time in seconds between thermostat updates
	int16 thermostat_off_cycle_time; // the minimum amount of time the thermostat cycle must stay in the off state
	int16 thermostat_on_cycle_time; // the minimum amount of time the thermostat cycle must stay in the on state
	timestamp thermostat_last_cycle_time; // last time the thermostat changed state
	double heating_setpoint[degF]; // thermostat heating setpoint
	double cooling_setpoint[degF]; // thermostat cooling setpoint
	double design_heating_setpoint[degF]; // system design heating setpoint
	double design_cooling_setpoint[degF]; // system design cooling setpoint
	double over_sizing_factor; // over sizes the heating and cooling system from standard specifications (0.2 ='s 120% sizing)
	double design_heating_capacity[Btu/h]; // system heating capacity
	double design_cooling_capacity[Btu/h]; // system cooling capacity
	double cooling_design_temperature[degF]; // system cooling design temperature
	double heating_design_temperature[degF]; // system heating design temperature
	double design_peak_solar[Btu/h]; // system design solar load
	double design_internal_gains[W/sf]; // system design internal gains
	double air_heat_fraction[pu]; // fraction of heat gain/loss that goes to air (as opposed to mass)
	double mass_solar_gain_fraction[pu]; // fraction of the heat gain/loss from the solar gains that goes to the mass
	double mass_internal_gain_fraction[pu]; // fraction of heat gain/loss from the internal gains that goes to the mass
	double auxiliary_heat_capacity[Btu/h]; // installed auxiliary heating capacity
	double aux_heat_deadband[degF]; // temperature offset from standard heat activation to auxiliary heat activation
	double aux_heat_temperature_lockout[degF]; // temperature at which auxiliary heat will not engage above
	double aux_heat_time_delay[s]; // time required for heater to run until auxiliary heating engages
	double cooling_supply_air_temp[degF]; // temperature of air blown out of the cooling system
	double heating_supply_air_temp[degF]; // temperature of air blown out of the heating system
	double duct_pressure_drop[inH2O]; // end-to-end pressure drop for the ventilation ducts, in inches of water
	double fan_design_power[W]; // designed maximum power draw of the ventilation fan
	double fan_low_power_fraction[pu]; // fraction of ventilation fan power draw during low-power mode (two-speed only)
	double fan_power[kW]; // current ventilation fan power draw
	double fan_design_airflow[cfm]; // designed airflow for the ventilation system
	double fan_impedance_fraction[pu]; // Impedance component of fan ZIP load
	double fan_power_fraction[pu]; // Power component of fan ZIP load
	double fan_current_fraction[pu]; // Current component of fan ZIP load
	double fan_power_factor[pu]; // Power factor of the fan load
	double heating_demand; // the current power draw to run the heating system
	double cooling_demand; // the current power draw to run the cooling system
	double heating_COP[pu]; // system heating performance coefficient
	double cooling_COP[Btu/kWh]; // system cooling performance coefficient
	double air_temperature[degF]; // indoor air temperature
	double outdoor_temperature[degF]; // outdoor air temperature
	double outdoor_rh[%]; // outdoor relative humidity
	double mass_heat_capacity[Btu/degF]; // interior mass heat capacity
	double mass_heat_coeff[Btu/degF]; // interior mass heat exchange coefficient
	double mass_temperature[degF]; // interior mass temperature
	double air_volume[cf]; // air volume
	double air_mass[lb]; // air mass
	double air_heat_capacity[Btu/degF]; // air thermal mass
	double latent_load_fraction[pu]; // fractional increase in cooling load due to latent heat
	double total_thermal_mass_per_floor_area[Btu/degF];
	double interior_surface_heat_transfer_coeff[Btu/h];
	double number_of_stories; // number of stories within the structure
	double is_AUX_on; // logic statement to determine population statistics - is the AUX on? 0 no, 1 yes
	double is_HEAT_on; // logic statement to determine population statistics - is the HEAT on? 0 no, 1 yes
	double is_COOL_on; // logic statement to determine population statistics - is the COOL on? 0 no, 1 yes
	double thermal_storage_present; // logic statement for determining if energy storage is present
	double thermal_storage_in_use; // logic statement for determining if energy storage is being utilized
	set {RESISTIVE=16, TWOSTAGE=8, FORCEDAIR=4, AIRCONDITIONING=2, GAS=1} system_type; // heating/cooling system type/options
	set {LOCKOUT=4, TIMER=2, DEADBAND=1, NONE=0} auxiliary_strategy; // auxiliary heating activation strategies
	enumeration {AUX=3, COOL=4, OFF=1, HEAT=2, UNKNOWN=0} system_mode; // heating/cooling system operation state
	enumeration {AUX=3, COOL=4, OFF=1, HEAT=2, UNKNOWN=0} last_system_mode; // heating/cooling system operation state
	enumeration {RESISTANCE=4, HEAT_PUMP=3, GAS=2, NONE=1} heating_system_type;
	enumeration {HEAT_PUMP=2, ELECTRIC=2, NONE=1} cooling_system_type;
	enumeration {ELECTRIC=2, NONE=1} auxiliary_system_type;
	enumeration {TWO_SPEED=3, ONE_SPEED=2, NONE=1} fan_type;
	enumeration {UNKNOWN=7, VERY_GOOD=6, GOOD=5, ABOVE_NORMAL=4, NORMAL=3, BELOW_NORMAL=2, LITTLE=1, VERY_LITTLE=0} thermal_integrity_level; // default envelope UA settings
	enumeration {LOW_E_GLASS=2, GLASS=1, OTHER=0} glass_type; // glass used in the windows
	enumeration {INSULATED=4, WOOD=3, THERMAL_BREAK=2, ALUMINIUM=1, ALUMINUM=1, NONE=0} window_frame; // type of window frame
	enumeration {HIGH_S=5, LOW_S=4, REFL=3, ABS=2, CLEAR=1, OTHER=0} glazing_treatment; // the treatment to increase the reflectivity of the exterior windows
	enumeration {OTHER=4, THREE=3, TWO=2, ONE=1} glazing_layers; // number of layers of glass in each window
	enumeration {FULL=2, BASIC=1, NONE=0} motor_model; // indicates the level of detail used in modelling the hvac motor parameters
	enumeration {VERY_GOOD=4, GOOD=3, AVERAGE=2, POOR=1, VERY_POOR=0} motor_efficiency; // when using motor model, describes the efficiency of the motor
	int64 last_mode_timer;
	double hvac_motor_efficiency[unit]; // when using motor model, percent efficiency of hvac motor
	double hvac_motor_loss_power_factor[unit]; // when using motor model, power factor of motor losses
	double Rroof[degF]; // roof R-value
	double Rwall[degF]; // wall R-value
	double Rfloor[degF]; // floor R-value
	double Rwindows[degF]; // window R-value
	double Rdoors[degF]; // door R-value
	double hvac_breaker_rating[A]; // determines the amount of current the HVAC circuit breaker can handle
	double hvac_power_factor[unit]; // power factor of hvac
	double hvac_load; // heating/cooling system load
	double last_heating_load; // stores the previous heating/cooling system load
	double last_cooling_load; // stores the previous heating/cooling system load
	complex hvac_power; // describes hvac load complex power consumption
	double total_load; // total panel enduse load
	enduse panel; // the enduse load description
	complex panel.energy[kVAh]; // the total energy consumed since the last meter reading
	complex panel.power[kVA]; // the total power consumption of the load
	complex panel.peak_demand[kVA]; // the peak power consumption since the last meter reading
	double panel.heatgain[Btu/h]; // the heat transferred from the enduse to the parent
	double panel.cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
	double panel.heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
	double panel.current_fraction[pu]; // the fraction of total power that is constant current
	double panel.impedance_fraction[pu]; // the fraction of total power that is constant impedance
	double panel.power_fraction[pu]; // the fraction of the total power that is constant power
	double panel.power_factor; // the power factor of the load
	complex panel.constant_power[kVA]; // the constant power portion of the total load
	complex panel.constant_current[kVA]; // the constant current portion of the total load
	complex panel.constant_admittance[kVA]; // the constant admittance portion of the total load
	double panel.voltage_factor[pu]; // the voltage change factor
	double panel.breaker_amps[A]; // the rated breaker amperage
	set {IS220=1} panel.configuration; // the load configuration options
	double design_internal_gain_density[W/sf]; // average density of heat generating devices in the house
	bool compressor_on;
	int64 compressor_count;
	timestamp hvac_last_on;
	timestamp hvac_last_off;
	double hvac_period_length;
	double hvac_duty_cycle;
	enumeration {NONE=2, BAND=1, FULL=0} thermostat_control; // determine level of internal thermostatic control
}

class lights {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	enumeration {HID=4, SSL=3, CFL=2, FLUORESCENT=1, INCANDESCENT=0} type; // lighting type (affects power_factor)
	enumeration {OUTDOOR=1, INDOOR=0} placement; // lighting location (affects where heatgains go)
	double installed_power[kW]; // installed lighting capacity
	double power_density[W/sf]; // installed power density
	double curtailment[pu]; // lighting curtailment factor
	double demand[pu]; // the current lighting demand
	complex actual_power[kVA]; // actual power demand of lights object
}

class microwave {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double installed_power[kW]; // rated microwave power level
	double standby_power[kW]; // standby microwave power draw (unshaped only)
	double circuit_split;
	enumeration {ON=1, OFF=0} state; // on/off state of the microwave
	double cycle_length[s]; // length of the combined on/off cycle between uses
	double runtime[s]; // 
	double state_time[s]; // 
}

class occupantload {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	int32 number_of_occupants;
	double occupancy_fraction[unit];
	double heatgain_per_person[Btu/h];
}

class plugload {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double circuit_split;
	double demand[unit];
	double installed_power[kW]; // installed plugs capacity
	complex actual_power[kVA]; // actual power demand
}

class range {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double oven_volume[gal]; // the volume of the oven
	double oven_UA[Btu]; // the UA of the oven (surface area divided by R-value)
	double oven_diameter[ft]; // the diameter of the oven
	double oven_demand[gpm]; // the hot food take out from the oven
	double heating_element_capacity[kW]; // the power of the heating element
	double inlet_food_temperature[degF]; // the inlet temperature of the food
	enumeration {GASHEAT=1, ELECTRIC=0} heat_mode; // the energy source for heating the oven
	enumeration {GARAGE=1, INSIDE=0} location; // whether the range is inside or outside
	double oven_setpoint[degF]; // the temperature around which the oven will heat its contents
	double thermostat_deadband[degF]; // the degree to heat the food in the oven, when needed
	double temperature[degF]; // the outlet temperature of the oven
	double height[ft]; // the height of the oven
	double food_density; // food density
	double specificheat_food;
	double queue_cooktop[unit]; // number of loads accumulated
	double queue_oven[unit]; // number of loads accumulated
	double queue_min[unit];
	double queue_max[unit];
	double time_cooktop_operation;
	double time_cooktop_setting;
	double cooktop_run_prob;
	double oven_run_prob;
	double cooktop_coil_setting_1[kW];
	double cooktop_coil_setting_2[kW];
	double cooktop_coil_setting_3[kW];
	double total_power_oven[kW];
	double total_power_cooktop[kW];
	double total_power_range[kW];
	double demand_cooktop[unit/day]; // number of loads accumulating daily
	double demand_oven[unit/day]; // number of loads accumulating daily
	double stall_voltage[V];
	double start_voltage[V];
	complex stall_impedance[Ohm];
	double trip_delay[s];
	double reset_delay[s];
	double time_oven_operation[s];
	double time_oven_setting[s];
	enumeration {CT_TRIPPED=6, CT_STALLED=5, STAGE_8_ONLY=4, STAGE_7_ONLY=3, STAGE_6_ONLY=2, CT_STOPPED=1} state_cooktop;
	double cooktop_energy_baseline[kWh];
	double cooktop_energy_used;
	double Toff;
	double Ton;
	double cooktop_interval_setting_1[s];
	double cooktop_interval_setting_2[s];
	double cooktop_interval_setting_3[s];
	double cooktop_energy_needed[kWh];
	bool heat_needed;
	bool oven_check;
	bool remainon;
	bool cooktop_check;
	double actual_load[kW]; // the actual load based on the current voltage across the coils
	double previous_load[kW]; // the actual load based on current voltage stored for use in controllers
	complex actual_power[kVA]; // the actual power based on the current voltage across the coils
	double is_range_on; // simple logic output to determine state of range (1-on, 0-off)
}

class refrigerator {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double size[cf]; // volume of the refrigerator
	double rated_capacity[Btu/h];
	double temperature[degF];
	double setpoint[degF];
	double deadband[degF];
	double cycle_time[s];
	double output;
	double event_temp;
	double UA[Btu];
	double compressor_off_normal_energy;
	double compressor_off_normal_power[W];
	double compressor_on_normal_energy;
	double compressor_on_normal_power[W];
	double defrost_energy;
	double defrost_power[W];
	double icemaking_energy;
	double icemaking_power[W];
	double ice_making_probability;
	int32 FF_Door_Openings;
	int32 door_opening_energy;
	int32 door_opening_power;
	double DO_Thershold;
	double dr_mode_double;
	double energy_needed;
	double energy_used;
	double refrigerator_power;
	bool icemaker_running;
	int32 check_DO;
	bool is_240;
	double defrostDelayed;
	bool long_compressor_cycle_due;
	double long_compressor_cycle_time;
	double long_compressor_cycle_power;
	double long_compressor_cycle_energy;
	double long_compressor_cycle_threshold;
	enumeration {COMPRESSOR_TIME=3, DOOR_OPENINGS=2, TIMED=1} defrost_criterion;
	bool run_defrost;
	double door_opening_criterion;
	double compressor_defrost_time;
	double delay_defrost_time;
	int32 daily_door_opening;
	enumeration {COMPRESSSOR_ON_NORMAL=3, COMPRESSSOR_ON_LONG=4, COMPRESSSOR_OFF_NORMAL=2, DEFROST=1} state;
}

class residential_enduse {
	loadshape shape;
	enduse load; // the enduse load description
	complex energy[kVAh]; // the total energy consumed since the last meter reading
	complex power[kVA]; // the total power consumption of the load
	complex peak_demand[kVA]; // the peak power consumption since the last meter reading
	double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
	double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
	double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
	double current_fraction[pu]; // the fraction of total power that is constant current
	double impedance_fraction[pu]; // the fraction of total power that is constant impedance
	double power_fraction[pu]; // the fraction of the total power that is constant power
	double power_factor; // the power factor of the load
	complex constant_power[kVA]; // the constant power portion of the total load
	complex constant_current[kVA]; // the constant current portion of the total load
	complex constant_admittance[kVA]; // the constant admittance portion of the total load
	double voltage_factor[pu]; // the voltage change factor
	double breaker_amps[A]; // the rated breaker amperage
	set {IS220=1} configuration; // the load configuration options
	enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
	enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
}

class residential_enduse {
	loadshape shape;
	enduse load; // the enduse load description
	complex energy[kVAh]; // the total energy consumed since the last meter reading
	complex power[kVA]; // the total power consumption of the load
	complex peak_demand[kVA]; // the peak power consumption since the last meter reading
	double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
	double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
	double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
	double current_fraction[pu]; // the fraction of total power that is constant current
	double impedance_fraction[pu]; // the fraction of total power that is constant impedance
	double power_fraction[pu]; // the fraction of the total power that is constant power
	double power_factor; // the power factor of the load
	complex constant_power[kVA]; // the constant power portion of the total load
	complex constant_current[kVA]; // the constant current portion of the total load
	complex constant_admittance[kVA]; // the constant admittance portion of the total load
	double voltage_factor[pu]; // the voltage change factor
	double breaker_amps[A]; // the rated breaker amperage
	set {IS220=1} configuration; // the load configuration options
	enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
	enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
}

class thermal_storage {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double total_capacity[Btu]; // total storage capacity of unit
	double stored_capacity[Btu]; // amount of capacity that is stored
	double recharge_power[kW]; // installed compressor power usage
	double discharge_power[kW]; // installed pump power usage
	double recharge_pf; // installed compressor power factor
	double discharge_pf; // installed pump power factor
	enumeration {EXTERNAL=1, INTERNAL=0} discharge_schedule_type; // Scheduling method for discharging
	enumeration {EXTERNAL=1, INTERNAL=0} recharge_schedule_type; // Scheduling method for charging
	double recharge_time; // Flag indicating if recharging is available at the current time (1 or 0)
	double discharge_time; // Flag indicating if discharging is available at the current time (1 or 0)
	double discharge_rate[Btu/h]; // rating of discharge or cooling
	double SOC[%]; // state of charge as percentage of total capacity
	double k[W/m/K]; // coefficient of thermal conductivity (W/m/K)
}

class waterheater {
	parent residential_enduse;
	class residential_enduse {
		loadshape shape;
		enduse load; // the enduse load description
		complex energy[kVAh]; // the total energy consumed since the last meter reading
		complex power[kVA]; // the total power consumption of the load
		complex peak_demand[kVA]; // the peak power consumption since the last meter reading
		double heatgain[Btu/h]; // the heat transferred from the enduse to the parent
		double cumulative_heatgain[Btu]; // the cumulative heatgain from the enduse to the parent
		double heatgain_fraction[pu]; // the fraction of the heat that goes to the parent
		double current_fraction[pu]; // the fraction of total power that is constant current
		double impedance_fraction[pu]; // the fraction of total power that is constant impedance
		double power_fraction[pu]; // the fraction of the total power that is constant power
		double power_factor; // the power factor of the load
		complex constant_power[kVA]; // the constant power portion of the total load
		complex constant_current[kVA]; // the constant current portion of the total load
		complex constant_admittance[kVA]; // the constant admittance portion of the total load
		double voltage_factor[pu]; // the voltage change factor
		double breaker_amps[A]; // the rated breaker amperage
		set {IS220=1} configuration; // the load configuration options
		enumeration {OFF=4294967295, NORMAL=0, ON=1} override;
		enumeration {ON=1, OFF=0, UNKNOWN=4294967295} power_state;
	}

	double tank_volume[gal]; // the volume of water in the tank when it is full
	double tank_UA[Btu]; // the UA of the tank (surface area divided by R-value)
	double tank_diameter[ft]; // the diameter of the water heater tank
	double water_demand[gpm]; // the hot water draw from the water heater
	double heating_element_capacity[kW]; // the power of the heating element
	double inlet_water_temperature[degF]; // the inlet temperature of the water tank
	enumeration {GASHEAT=1, ELECTRIC=0} heat_mode; // the energy source for heating the water heater
	enumeration {GARAGE=1, INSIDE=0} location; // whether the water heater is inside or outside
	double tank_setpoint[degF]; // the temperature around which the water heater will heat its contents
	double thermostat_deadband[degF]; // the degree to heat the water tank, when needed
	double temperature[degF]; // the outlet temperature of the water tank
	double height[ft]; // the height of the hot water column within the water tank
	double demand[gpm]; // the water consumption
	double actual_load[kW]; // the actual load based on the current voltage across the coils
	double previous_load[kW]; // the actual load based on current voltage stored for use in controllers
	complex actual_power[kVA]; // the actual power based on the current voltage across the coils
	double is_waterheater_on; // simple logic output to determine state of waterheater (1-on, 0-off)
	double gas_fan_power[kW]; // load of a running gas waterheater
	double gas_standby_power[kW]; // load of a gas waterheater in standby
}


class collector {
	char1024 property;
	char32 trigger;
	char1024 file;
	int32 limit;
	char256 group;
	double interval[s];
}

class group_recorder {
	char256 file; // output file name
	char1024 group; // group definition string
	double interval[s]; // recordering interval (0 'every iteration', -1 'on change')
	double flush_interval[s]; // file flush interval (0 never, negative on samples)
	bool strict; // causes the group_recorder to stop the simulation should there be a problem opening or writing with the group_recorder
	bool print_units; // flag to append units to each written value, if applicable
	char256 property; // property to record
	int32 limit; // the maximum number of lines to write to the file
	enumeration {ANG_RAD=5, ANG_DEG=4, MAG=3, IMAG=2, REAL=1, NONE=0} complex_part; // the complex part to record if complex properties are gathered
}

class histogram {
	char1024 filename; // the name of the file to write
	char8 filetype; // the format to output a histogram in
	char32 mode; // the mode of file output
	char1024 group; // the GridLAB-D group expression to use for this histogram
	char1024 bins; // the specific bin values to use
	char256 property; // the property to sample
	double min; // the minimum value of the auto-sized bins to use
	double max; // the maximum value of the auto-sized bins to use
	double samplerate[s]; // the rate at which samples are read
	double countrate[s]; // the reate at which bins are counted and written
	int32 bin_count; // the number of auto-sized bins to use
	int32 limit; // the number of samples to write
}

class multi_recorder {
	double interval[s];
	char1024 property;
	char32 trigger;
	char1024 file;
	char8 filetype;
	char32 mode;
	char1024 multifile;
	int32 limit;
	char1024 plotcommands;
	char32 xdata;
	char32 columns;
	enumeration {SVG=6, PNG=5, PDF=4, JPG=3, GIF=2, EPS=1, SCREEN=0} output;
	enumeration {NONE=2, ALL=1, DEFAULT=0} header_units;
	enumeration {NONE=2, ALL=1, DEFAULT=0} line_units;
}

class player {
	char256 property;
	char1024 file;
	char8 filetype;
	char32 mode;
	int32 loop;
}

class player {
	char256 property;
	char1024 file;
	char8 filetype;
	char32 mode;
	int32 loop;
}

class recorder {
	char1024 property;
	char32 trigger;
	char1024 file;
	char8 filetype;
	char32 mode;
	char1024 multifile;
	int32 limit;
	char1024 plotcommands;
	char32 xdata;
	char32 columns;
	double interval[s];
	enumeration {SVG=6, PNG=5, PDF=4, JPG=3, GIF=2, EPS=1, SCREEN=0} output;
	enumeration {NONE=2, ALL=1, DEFAULT=0} header_units;
	enumeration {NONE=2, ALL=1, DEFAULT=0} line_units;
}

class shaper {
	char1024 file;
	char8 filetype;
	char32 mode;
	char256 group;
	char256 property;
	double magnitude;
	double events;
}

'''