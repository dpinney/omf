function mpc = case3sc
%CASE3SC    Power flow data for 3-bus system used in [1].
%   Please see CASEFORMAT for details on the case file format.
%
%   The semidefinite relaxation of the OPF problem successfully solves 
%   case3sc with a value of 60 MVA for the line-flow limit on the line from
%   bus 3 to bus 2. The semidefinite relaxation fails to give a physically
%   meaningful solution to case3sc with a value of 50 MVA for the line-flow
%   limit on this line. See [1] for further details.
%
%   [1] B.C. Lesieutre, D.K. Molzahn, A.R. Borden, and C.L. DeMarco,
%       "Examining the Limits of the Application of Semidefinite 
%       Programming to Power Flow Problems," In 49th Annual Allerton 
%       Conference on Communication, Control, and Computing, 2011,
%       September 28-30 2011.

mpc.version = '2';

%-----  Power Flow Data  -----%%
% system MVA base
mpc.baseMVA = 100;
    
% bus data
%	bus_i	type	Pd	Qd	Gs	Bs	area	Vm	Va	baseKV	zone	Vmax	Vmin
mpc.bus = [
	1	3	110	40	0	0	1	1	0	345	1	1.1	0.9;
	2	2	110	40	0	0	1	1	0	345	1	1.1	0.9;
	3	2	95	50	0	0	1	1	0	345	1	1.1	0.9;
];

% generator data
%	bus	Pg	Qg	Qmax	Qmin	Vg	mBase	status	Pmax	Pmin	Pc1	Pc2	Qc1min	Qc1max	Qc2min	Qc2max	ramp_agc	ramp_10	ramp_30	ramp_q	apf
mpc.gen = [
	1	0	0	300	-300	1	100	1	1e3	0	0	0	0	0	0	0	0	0	0	0	0;
	2	0	0	300	-300	1	100	1	1e3	0	0	0	0	0	0	0	0	0	0	0	0;
    3	0	0	300	-300	1	100	1	0.0001	-0.0001	0	0	0	0	0	0	0	0	0	0	0; % Synchronous condensor
];

% branch data
%	fbus	tbus	r	x	b	rateA	rateB	rateC	ratio	angle	status	angmin	angmax
mpc.branch = [
    1	3	0.065	0.62	0.45	250	250	250	0	0	1	-360	360;
	3	2	0.025	0.75	0.7    50	300	300	0	0	1	-360	360; % <-- change this line-flow limit to change satisfaction of semidefinite rank constraint
    1	2	0.042	0.900	0.3	250	250	250	0	0	1	-360	360;
];

% area data
%	area	refbus
mpc.areas = [
	1	1;
];

% generator cost data
%	1	startup	shutdown	n	x1	y1	...	xn	yn
%	2	startup	shutdown	n	c(n-1)	...	c0
mpc.gencost = [
	2	1500	0	3	0.11	5	0;
	2	2000	0	3	0.085	1.2	0;
    2	2000	0	3	0	0	0; % Synchronous condensor
];
