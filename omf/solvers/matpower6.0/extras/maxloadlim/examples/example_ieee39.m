%EXAMPLE_IEEE39 Examples of using maximum loadability limit (MLL) search with 
%   the IEEE 39

%   MATPOWER
%   Copyright (c) 2015-2016, Power Systems Engineering Research Center (PSERC)
%   by Camille Hamon
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%addpath('../');
%clear,clc;

% Loading the system and defining parameters
mpc = loadcase('case39'); % load ieee9
dir_mll = zeros(39,1); % define direction of load increase
dir_mll(9) = 1;

%% First, run a CPF
define_constants;
mpc_target = mpc;
nonzero_loads = mpc_target.bus(:,PD) ~= 0;
Q_P = mpc_target.bus(nonzero_loads,QD)./mpc_target.bus(nonzero_loads,PD);
mpc_target.bus(:,PD) = mpc_target.bus(:,PD)+2*dir_mll*mpc_target.baseMVA;
mpc_target.bus(nonzero_loads,QD) = Q_P.*mpc_target.bus(nonzero_loads,PD);
% Run the CPF with matpower
[results,~] = runcpf(mpc,mpc_target);

%% Without enforcement of the reactive power limits.
% The reactive power limits are not enforced in the following example.
results_mll = maxloadlim(mpc,dir_mll,'verbose',1,'use_qlim',0);
mpopt = mpoption('out.lim.all',1,'out.lim.v',1,...
    'out.lim.line',1,'out.lim.pg',1,'out.lim.qg',1);
printpf(results_mll,1,mpopt);

% Try to increase the load a bit at bus 9
% results_mll.bus(9,PD) = 1.1*results_mll.bus(9,PD);
% results_mll.bus(nonzero_loads,QD) = Q_P.*results_mll.bus(nonzero_loads,PD);
% results_pf = runpf(results_mll);
% mpc_pf.version = results_pf.version;
% mpc_pf.baseMVA = results_pf.baseMVA;
% mpc_pf.bus = results_pf.bus;
% mpc_pf.gen = results_pf.gen(:,1:21);
% mpc_pf.branch = results_pf.branch;
% mpc_pf.gencost = results_pf.gencost;
% results_mll = maxloadlim(mpc_pf,dir_mll,'verbose',1,'use_qlim',0);