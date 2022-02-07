function t_insolvablepfsos_limitQ(quiet)
%T_INSOLVABLEPF  Test for power flow insolvability condition

%   MATPOWER
%   Copyright (c) 2013-2019, Power Systems Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%   and Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER/mx-sdp_pf.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-sdp_pf/ for more info.

if nargin < 1
    quiet = 0;
end

num_tests = 2;

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

if have_fcn('octave')
    if have_fcn('octave', 'vnum') >= 4
        file_in_path_warn_id = 'Octave:data-file-in-path';
    else
        file_in_path_warn_id = 'Octave:load-file-in-path';
    end
    s1 = warning('query', file_in_path_warn_id);
    warning('off', file_in_path_warn_id);
end

t0 = 'INSOLVABLEPF : ';

%% test an insolvable case
load soln9mod_opf;     %% defines bus_soln, gen_soln, branch_soln, Vslack_min_soln, sigma_soln, etacomp_soln

res = loadcase(casefile);
res.bus = bus_soln;
res.gen = gen_soln;
res.branch = branch_soln;

% Make the case insolvable
mult = 10;
res.bus(:,PD) = mult*res.bus(:,PD);
res.bus(:,QD) = mult*res.bus(:,QD);
res.gen(:,PG) = mult*res.gen(:,PG);

mpopt = mpoption('out.all', 0, 'verbose', verbose);

%% get test results for insolvable case
t = [t0 '(insolvable case) :'];
insolvable = insolvablepfsos_limitQ(res,mpopt);
t_ok(insolvable, [t ' insolvable']);


%% test a solvable case
load soln9mod_opf;     %% defines bus_soln, gen_soln, branch_soln, Vslack_min_soln, sigma_soln, etacomp_soln

res = loadcase(casefile);
res.bus = bus_soln;
res.gen = gen_soln;
res.branch = branch_soln;

%% get test results for insolvable case
t = [t0 '(solvable case) :'];
insolvable = insolvablepfsos_limitQ(res,mpopt);
t_ok(~insolvable, [t ' solvable']);

if have_fcn('octave')
    warning(s1.state, file_in_path_warn_id);
end

t_end;
