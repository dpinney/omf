function [Ainc] = makeIncidence(bus, branch)
%MAKEINCIDENCE   Builds the bus incidence matrix.
%   [Ainc] = MAKEINCIDENCE(MPC)
%   [Ainc] = MAKEINCIDENCE(BUS, BRANCH)
%
%   Builds the bus incidence matrix. This matrix has size nline by nbus,
%   with each row having two nonzero elements: +1 in the entry for the 
%   "from" bus of the corresponding line and -1 in the entry for the "to"
%   bus of the corresponding line.
%
%   Inputs:
%       MPC : MATPOWER case variable with internal indexing.
%
%   Outputs:
%       AINC : An nline by nbus size bus incidence matrix.

%   MATPOWER
%   Copyright (c) 2013-2019, Power Systems Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%   and Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER/mx-sdp_pf.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-sdp_pf/ for more info.

if nargin < 2
    mpc     = bus;
    bus     = mpc.bus;
    branch  = mpc.branch;
end

%% constants
nb = size(bus, 1);          %% number of buses
nl = size(branch, 1);       %% number of lines

%% define named indices into bus, branch matrices
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, ...
    TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST, ...
    ANGMIN, ANGMAX, MU_ANGMIN, MU_ANGMAX] = idx_brch;

%% check that bus numbers are equal to indices to bus (one set of bus numbers)
if any(bus(:, BUS_I) ~= (1:nb)')
    error('makeIncidence: buses must be numbered consecutively in bus matrix; use ext2int() to convert to internal ordering')
end

%% build connection matrices
f = branch(:, F_BUS);                           %% list of "from" buses
t = branch(:, T_BUS);                           %% list of "to" buses
Cf = sparse(1:nl, f, ones(nl, 1), nl, nb);      %% connection matrix for line & from buses
Ct = sparse(1:nl, t, ones(nl, 1), nl, nb);      %% connection matrix for line & to buses

Ainc = Cf - Ct;
