function mpc = case2local
%CASE2LOCAL    Power flow data for 2-bus system used in [1].
%   Please see CASEFORMAT for details on the case file format.
%
%   The semidefinite relaxation of the OPF problem fails to solve
%   case2local for upper limits on bus two voltage magnitude between 
%   0.985 and 1.04. See [1] for more details.
%
%   [1] W. Bukhsh, A. Grothey, K. McKinnon, and P. Trodden, "Local
%       Solutions of Optimal power Flow," Tech. Report. ERGO-11-017,
%       University of Edinburgh School of Mathematics, Edinburgh Research
%       Group in Optimization, 2011. [Online]. Available:
%       https://www.maths.ed.ac.uk/ERGO/pubs/ERGO-11-017.html

t = 17.625;

%% MATPOWER Case Format : Version 2
mpc.version = '2';

%%-----  Power Flow Data  -----%%
%% system MVA base
mpc.baseMVA = 100;

%% bus data
%	bus_i	type	Pd	Qd	Gs	Bs	area	Vm	Va	baseKV	zone	Vmax	Vmin
mpc.bus = [
	1	3	0	0	0	0	1	0.9703	0	345	1	1.05	0.95;
	2	1	20*t	-20.3121*t	0	0	1	1.03	-64.3755	345	1	1.03	0.95;
];

%% generator data
%	bus	Pg	Qg	Qmax	Qmin	Vg	mBase	status	Pmax	Pmin	Pc1	Pc2	Qc1min	Qc1max	Qc2min	Qc2max	ramp_agc	ramp_10	ramp_30	ramp_q	apf
mpc.gen = [
	1	447.67	153.55	900	-900	0.9703	100	1	900	0	0	0	0	0	0	0	0	0	0	0	0;
];

%% branch data
%	fbus	tbus	r	x	b	rateA	rateB	rateC	ratio	angle	status	angmin	angmax
mpc.branch = [
	1	2	0.04	0.20	0.0	900	900	900	0	0	1	-360	360;
];

%%-----  OPF Data  -----%%
%% area data
%	area	refbus
mpc.areas = [
	1	1;
];

%% generator cost data
%	1	startup	shutdown	n	x1	y1	...	xn	yn
%	2	startup	shutdown	n	c(n-1)	...	c0
mpc.gencost = [
	2	1500	0	3	0	1	0;
];
