function [data, topo] = sgvm_mpc2data(mpc)
%SGVM_MPC2DATA create VARIATIONS MODE inputs from MATPOWER case
%   [DATA, TOPO] = SGVM_MPC2DATA(MPC)
%
%   Converts a MATPOWER structure to a data structure that is suitable for
%   sampling via the SGVM_DATA2MPC function. This is essentially a function
%   that strips out the used data from the MPC structure.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

%% some initializations
define_constants;
data = struct();
nb = size(mpc.bus, 1);

%% if not consecutive numbering use ext2int
if ~all(mpc.bus(:,BUS_I)  == (1:nb).')
    mpc = ext2int(mpc);
end

%% power base
data.baseMVA = mpc.baseMVA;

%% branch
data.branch = mpc.branch(:, [BR_R, BR_X, BR_B, RATE_A, TAP, SHIFT]);
topo        = mpc.branch(:, [F_BUS, T_BUS]);
%% load
data.load   = mpc.bus(:, [PD, QD]);

%% gen
data.gen    = mpc.gen(:, [GEN_BUS, QMAX, QMIN, PMAX, PMIN]);

%% gencost
if isfield(mpc, 'gencost')
    data.gencost = mpc.gencost;
end
