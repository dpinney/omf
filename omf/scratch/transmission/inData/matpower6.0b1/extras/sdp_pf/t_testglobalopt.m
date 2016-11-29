function t_testglobalopt(quiet)
%T_TESTGLOBALOPT  Test for Global Optimality Condition

%   MATPOWER
%   Copyright (c) 2013-2016 by Power System Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%   and Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

if nargin < 1
    quiet = 0;
end

num_tests = 6;

t_begin(num_tests, quiet);

[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, ...
    TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST, ...
    ANGMIN, ANGMAX, MU_ANGMIN, MU_ANGMAX] = idx_brch;
[PW_LINEAR, POLYNOMIAL, MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;

casefile = 't_case9mod_opf';
if quiet
    verbose = 0;
else
    verbose = 0;
end

t0 = 'TESTGLOALOPT : ';

%% get saved solution with apparent power limits
load soln9mod_opf;     %% defines bus_soln, gen_soln, branch_soln, f_soln, Apsd_soln, comp_soln, globalopt_soln

res = loadcase(casefile);
res.bus = bus_soln;
res.gen = gen_soln;
res.branch = branch_soln;

mpopt = mpoption('out.all', 0, 'verbose', verbose);

%% get test results with apparent power limits
t = t0;
[globalopt,comp,Apsd] = testGlobalOpt(res, mpopt);
t_ok(globalopt, [t 'global optimum verification']);
t_is(comp, comp_soln, 3, [t 'complimentarity conditions']);
t_ok(Apsd, [t 'A is positive semidefinite']);

%% get saved solution with active power limits
load soln9mod_opf_Plim;     %% defines bus_soln, gen_soln, branch_soln, f_soln, Apsd_soln, comp_soln, globalopt_soln

res = loadcase(casefile);
res.bus = bus_soln;
res.gen = gen_soln;
res.branch = branch_soln;

mpopt1 = mpoption(mpopt, 'opf.flow_lim', 'P');

%% get test results with active power limits
t = [t0 '(P line lim) : '];
[globalopt,comp,Apsd] = testGlobalOpt(res, mpopt1);
t_ok(globalopt, [t 'global optimum verification']);
t_is(comp, comp_soln, 3, [t 'complimentarity conditions']);
t_ok(Apsd, [t 'A is positive semidefinite']);

t_end;
