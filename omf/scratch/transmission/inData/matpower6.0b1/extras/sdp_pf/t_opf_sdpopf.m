function t_opf_sdpopf(quiet)
%T_OPF_SDPOPF  Tests for SDP-based AC optimal power flow.

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

num_tests = 36;

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

t0 = 'SDPOPF : ';
mpopt = mpoption('opf.violation', 1e-6);
mpopt = mpoption(mpopt, 'out.all', 0, 'verbose', verbose, ...
    'opf.ac.solver', 'SDPOPF', 'sdp_pf.eps_r', 0);

%% set up indices
ib_data     = [1:BUS_AREA BASE_KV:VMIN];
ib_voltage  = [VM VA];
ib_lam      = [LAM_P LAM_Q];
ib_mu       = [MU_VMAX MU_VMIN];
ig_data     = [GEN_BUS QMAX QMIN MBASE:APF];
ig_disp     = [PG QG VG];
ig_mu       = (MU_PMAX:MU_QMIN);
ibr_data    = (1:ANGMAX);
ibr_flow    = (PF:QT);
ibr_mu      = [MU_SF MU_ST];
ibr_angmu   = [MU_ANGMIN MU_ANGMAX];

%% get solved AC power flow case from MAT-file
load soln9mod_opf;     %% defines bus_soln, gen_soln, branch_soln, f_soln

%% run OPF
t = t0;
[baseMVA, bus, gen, gencost, branch, f, success, et] = runopf(casefile, mpopt);
t_ok(success, [t 'success']);
t_is(f, f_soln, 3, [t 'f']);
t_is(   bus(:,ib_data   ),    bus_soln(:,ib_data   ), 10, [t 'bus data']);
t_is(   bus(:,ib_voltage),    bus_soln(:,ib_voltage),  3, [t 'bus voltage']);
t_is(   bus(:,ib_lam    ),    bus_soln(:,ib_lam    ),  3, [t 'bus lambda']);
t_is(   bus(:,ib_mu     ),    bus_soln(:,ib_mu     ),  1, [t 'bus mu']);
t_is(   gen(:,ig_data   ),    gen_soln(:,ig_data   ), 10, [t 'gen data']);
t_is(   gen(:,ig_disp   ),    gen_soln(:,ig_disp   ),  2, [t 'gen dispatch']);
t_is(   gen(:,ig_mu     ),    gen_soln(:,ig_mu     ),  3, [t 'gen mu']);
t_is(branch(:,ibr_data  ), branch_soln(:,ibr_data  ), 10, [t 'branch data']);
t_is(branch(:,ibr_flow  ), branch_soln(:,ibr_flow  ),  2, [t 'branch flow']);
t_is(branch(:,ibr_mu    ), branch_soln(:,ibr_mu    ),  2, [t 'branch mu']);

%% run with automatic conversion of single-block pwl to linear costs
t = [t0 '(single-block PWL) : '];
mpc = loadcase(casefile);
mpc.gencost(3, NCOST) = 2;
[r, success] = runopf(mpc, mpopt);
[f, bus, gen, branch] = deal(r.f, r.bus, r.gen, r.branch);
t_ok(success, [t 'success']);
t_is(f, f_soln, 3, [t 'f']);
t_is(   bus(:,ib_data   ),    bus_soln(:,ib_data   ), 10, [t 'bus data']);
t_is(   bus(:,ib_voltage),    bus_soln(:,ib_voltage),  3, [t 'bus voltage']);
t_is(   bus(:,ib_lam    ),    bus_soln(:,ib_lam    ),  3, [t 'bus lambda']);
t_is(   bus(:,ib_mu     ),    bus_soln(:,ib_mu     ),  1, [t 'bus mu']);
t_is(   gen(:,ig_data   ),    gen_soln(:,ig_data   ), 10, [t 'gen data']);
t_is(   gen(:,ig_disp   ),    gen_soln(:,ig_disp   ),  2, [t 'gen dispatch']);
t_is(   gen(:,ig_mu     ),    gen_soln(:,ig_mu     ),  3, [t 'gen mu']);
t_is(branch(:,ibr_data  ), branch_soln(:,ibr_data  ), 10, [t 'branch data']);
t_is(branch(:,ibr_flow  ), branch_soln(:,ibr_flow  ),  2, [t 'branch flow']);
t_is(branch(:,ibr_mu    ), branch_soln(:,ibr_mu    ),  2, [t 'branch mu']);

%% get solved AC power flow case from MAT-file
load soln9mod_opf_Plim;       %% defines bus_soln, gen_soln, branch_soln, f_soln

%% run OPF with active power line limits
t = [t0 '(P line lim) : '];
mpopt1 = mpoption(mpopt, 'opf.flow_lim', 'P');
[baseMVA, bus, gen, gencost, branch, f, success, et] = runopf(casefile, mpopt1);
t_ok(success, [t 'success']);
t_is(f, f_soln, 3, [t 'f']);
t_is(   bus(:,ib_data   ),    bus_soln(:,ib_data   ), 10, [t 'bus data']);
t_is(   bus(:,ib_voltage),    bus_soln(:,ib_voltage),  3, [t 'bus voltage']);
t_is(   bus(:,ib_lam    ),    bus_soln(:,ib_lam    ),  3, [t 'bus lambda']);
t_is(   bus(:,ib_mu     ),    bus_soln(:,ib_mu     ),  1, [t 'bus mu']);
t_is(   gen(:,ig_data   ),    gen_soln(:,ig_data   ), 10, [t 'gen data']);
t_is(   gen(:,ig_disp   ),    gen_soln(:,ig_disp   ),  2, [t 'gen dispatch']);
t_is(   gen(:,ig_mu     ),    gen_soln(:,ig_mu     ),  3, [t 'gen mu']);
t_is(branch(:,ibr_data  ), branch_soln(:,ibr_data  ), 10, [t 'branch data']);
t_is(branch(:,ibr_flow  ), branch_soln(:,ibr_flow  ),  2, [t 'branch flow']);
t_is(branch(:,ibr_mu    ), branch_soln(:,ibr_mu    ),  2, [t 'branch mu']);

t_end;
