%EXAMPLE_IEEE9 Examples of using maximum loadability limit (MLL) search with 
%   the IEEE 9

%   MATPOWER
%   Copyright (c) 2015-2016, Power Systems Engineering Research Center (PSERC)
%   by Camille Hamon
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%addpath('../');

% Loading the system and defining parameters
mpc = loadcase('case9'); % load ieee9
dir_mll = [0 0 0 0 0 0 1 0 0]'; % define direction of load increase

%% With reactive power limits (default)
% Running the search for MLL with verbose set to 1 to print the results.
results_mll = maxloadlim(mpc,dir_mll,'verbose',1); % 

%% Without enforcement of the reactive power limits.
% The reactive power limits are not enforced in the following example.
results_mll = maxloadlim(mpc,dir_mll,'verbose',1,'use_qlim',0);

% The same MLL point can be obtained by MATPOWER implementation of the CPF.
define_constants;
mpc_target = mpc;
nonzero_loads = mpc_target.bus(:,PD) ~= 0;
Q_P = mpc_target.bus(nonzero_loads,QD)./mpc_target.bus(nonzero_loads,PD);
mpc_target.bus(:,PD) = mpc_target.bus(:,PD)+2*dir_mll*mpc_target.baseMVA;
mpc_target.bus(nonzero_loads,QD) = Q_P.*mpc_target.bus(nonzero_loads,PD);
% Run the CPF with matpower
[results,~] = runcpf(mpc,mpc_target);