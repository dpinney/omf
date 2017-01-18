function [v, f, hn, gn, Al, Au, xl, xu] = check_feasibility(mpc, mpopt)
%CHECK_FEASIBILITY  Returns the maximum constraint violation in p.u.
%   V = CHECK_FEASIBILITY(MPC)
%   [V, F, HN, GN, AL, AU, XL, XU] = CHECK_FEASIBILITY(MPC, MPOPT)
%
%   Not thoroughly tested.

%   MATPOWER
%   Copyright (c) 2010-2016, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%%----- initialization -----
%% define named indices into data matrices
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, ...
    TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST, ...
    ANGMIN, ANGMAX, MU_ANGMIN, MU_ANGMAX] = idx_brch;
[PW_LINEAR, POLYNOMIAL, MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;

if nargin < 2
    mpopt = mpoption;
end

[mpc, mpopt] = opf_args(mpc, mpopt);
mpc = ext2int(mpc);
om = opf_setup(mpc, mpopt);
om = build_cost_params(om);

%% unpack data
mpc = get_mpc(om);
[vv, ll, nn] = get_idx(om);

%% problem dimensions
nb = size(mpc.bus, 1);      %% number of buses
nl = size(mpc.branch, 1);   %% number of branches
ny = getN(om, 'var', 'y');  %% number of piece-wise linear costs

%% linear constraints
[A, l, u] = linear_constraints(om);

%% bounds on optimization vars
[x, xmin, xmax] = getv(om);

%% build admittance matrices
[Ybus, Yf, Yt] = makeYbus(mpc.baseMVA, mpc.bus, mpc.branch);

%% set y variables (ONLY IMPLEMENTED FOR PG)
if ny > 0
    ipwl = find(mpc.gencost(:, MODEL) == PW_LINEAR);
    ig = vv.i1.Pg:vv.iN.Pg;
    x(vv.i1.y:vv.iN.y) = totcost(mpc.gencost(ipwl, :), x(ig(ipwl)) * mpc.baseMVA);
end

%% find branches with flow limits
il = find(mpc.branch(:, RATE_A) ~= 0 & mpc.branch(:, RATE_A) < 1e10);
nl2 = length(il);           %% number of constrained lines

%%-----  run opf  -----
f_fcn = @(x)opf_costfcn(x, om);
gh_fcn = @(x)opf_consfcn(x, om, Ybus, Yf(il,:), Yt(il,:), mpopt, il);
hess_fcn = @(x, lambda, cost_mult)opf_hessfcn(x, lambda, cost_mult, om, Ybus, Yf(il,:), Yt(il,:), mpopt, il);

[f, df, d2f] = f_fcn(x);
[hn, gn, dhn, dgn] = gh_fcn(x);

Ax = A * x;
Au = Ax - u;
Al = l - Ax;

xu = x - xmax;
xl = xmin - x;

v = max([hn; abs(gn); Au; Al; xu; xl]);
