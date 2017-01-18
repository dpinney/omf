function [BL2, BL1, BL0] = makeBloss(mpc)
% [BL2, BL1, BL0] = MAKEBLOSS(MPC)
%
%   MPC must have consecutive bus numbering (i.e. internal bus numbering)
%
%   LOSS = (0.5 * Pg' * BL2 * Pg + BL1' * Pg + BL0 )
%
%   Example:
%       mpc = loadcase('case30');
%       results = rundcopf(mpc);
%       Pg = results.gen(:, PG);
%       [BL2, BL1, BL0] = makeBloss2(mpc);
%       loss = (0.5 * Pg' * BL2 * Pg + BL1' * Pg + BL0 )
%
%       Pf = results.branch(:, PF) / mpc.baseMVA;
%       r = mpc.branch(:, BR_R);
%       loss2 = sum( Pf .^ 2 .* r ) * mpc.baseMVA

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% define named indices into data matrices
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, ...
    RATE_C, TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST] = idx_brch;
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, ...
    GEN_STATUS, PMAX, PMIN, MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN] = idx_gen;

if ischar(mpc)
    mpc = loadcase(mpc);
end
[Bbus, Bf, Pbusinj, Pfinj] = makeBdc(mpc.baseMVA, mpc.bus, mpc.branch);

%% form generator connection matrix: element i,j is 1 if gen j at bus i is ON
nb = size(mpc.bus, 1);
ng = size(mpc.gen, 1);
nl = size(mpc.branch, 1);
Cg = sparse(mpc.gen(:, GEN_BUS), (1:ng)', ones(ng, 1), nb, ng);

%% get indices k of non-reference buses
ref = find(mpc.bus(:, BUS_TYPE) == REF);
ref = ref(1);
k = (1:nb)';
k(ref) = [];

%% Pbus = Cg * Pg - Pd - Ps
%% Pbus(k) = Cg(k,:) * Pg - Pd(k) - Ps(k)
%% Pbus(k) = Bbus(k,k) * Va(k) + Pbusinj(k)
%% Va(k) = inv( Bbus(k,k) ) * (Pbus(k) - Pbusinj(k))
%% Pf = Bf * Va + Pfinj
%% Pf = Bf(:,k) * Va(k) + Bf(:,ref) * Va(ref) + Pfinj
%%    = Bf(:,k) * inv( Bbus(k,k) ) * (Pbus(k) - Pbusinj(k)) + Bf(:,ref) * Va(ref) + Pfinj
%%    = W * (Pbus(k) - Pbusinj(k)) + Bf(:,ref) * Va(ref) + Pfinj
%%    = W * (Cg(k,:) * Pg - Pd(k) - Ps(k) - Pbusinj(k)) + Bf(:,ref) * Va(ref) + Pfinj
%%    = Wg * Pg + Pz;
%% W = Bf(:,k) * inv( Bbus(k,k) );
%% Wg = W * Cg(k,:);
%% Pz = Bf(:,ref) * Va(ref) + Pfinj - W * (Pd(k) + Ps(k) + Pbusinj(k));
%% loss = Pf' * R * Pf
%%      = (Wg * Pg + Pz)' * R * (Wg * Pg + Pz)
%%      = Pg' * Wg' * R * Wg * Pg
%%        + 2 * Pz' * R * Wg * Pg
%%        + Pz' * R * Pz

r = mpc.branch(:, BR_R);
Varef = mpc.bus(ref, VA) * pi/180;
Pd = mpc.bus(:, PD) / mpc.baseMVA;
Ps = mpc.bus(:, GS) / mpc.baseMVA;
W = Bf(:, k) / Bbus(k, k);          %% = Bf(:, k) * inv(Bbus(k, k))
Wg = W * Cg(k,:);
Pz = Bf(:,ref) * Varef + Pfinj - W * (Pd(k) + Ps(k) + Pbusinj(k));
R = sparse(1:nl, 1:nl, r, nl, nl);  %% nl x nl matrix w/ line resistences on diag

%% form B coefficients
BL2 = 2 * Wg' * R * Wg / mpc.baseMVA;
BL1 = 2 * Wg' * R * Pz;
BL0 = Pz' * R * Pz * mpc.baseMVA;
