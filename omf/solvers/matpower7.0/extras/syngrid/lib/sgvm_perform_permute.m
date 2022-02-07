function mpc = sgvm_perform_permute(mpc, v, permORnmap)
%SGVM_PERFORM_PERMUTE perform node property permutation on MPC
%   MPC = SGVM_PERFORM_PERMUTE(MPC, V, PERMORNMAP)
%
%   Vector V is *either* PERM: a mapping that permutes *properties*
%                         or
%   Vector V is NMAP: a mapping of node numbers.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

define_constants;
nb = size(mpc.bus, 1);

switch permORnmap
case 'perm'
    perm = v;
    nmap = full(sparse(perm, 1, 1:nb));
case 'nmap'
    nmap = v;
    perm = full(sparse(nmap,1, 1:nb));
end
% node property vector x is permuted as x(perm)
% bus numbers , BUS_I or GEN_BUS can be mapped with nmap(GEN_BUS)
% for bus matrix we use perm, for gen matrix nmap.
mpc.bus = [mpc.bus(:,BUS_I), mpc.bus(perm,2:end)];
mpc.gen = [nmap(mpc.gen(:,GEN_BUS)), mpc.gen(:,2:end)];
