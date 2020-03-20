function t_cpf_case9(quiet)
% This function tests the maxloadlim extension to the OPF in MATPOWER
% against MATPOWER implementation of a CPF

%   MATPOWER
%   Copyright (c) 2015-2016, Power Systems Engineering Research Center (PSERC)
%   by Camille Hamon
%
%   This file is part of MATPOWER/mx-maxloadlim.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-maxloadlim/ for more info.

if nargin < 1
    quiet = 0;
end
define_constants;
% Loading the case
mpc = loadcase('case9');
% Defining several load increase directions to be tested
dir_all = [0 0 0 0 1 0 0 0 0;
    0 0 0 0 0 0 1 0 0;
    0 0 0 0 0 0 0 0 1;
    0 0 0 0 1 0 1 0 1;
    0 0 0 0 1 0 1 0 0;
    0 0 0 0 1 0 0 0 1;
    0 0 0 0 0 0 1 0 1];
% Number of load increase directions
nb_dir = size(dir_all,1);
% Message header
t0 = 'case9: ';

num_tests = nb_dir; % we don't consider the direction with all zeros
t_begin(num_tests, quiet);
for i = 1:nb_dir
    % Preparing the target case for Matpower CPF
    dir = dir_all(i,:)';
    mpc_target = mpc;
    nonzero_loads = mpc_target.bus(:,PD) ~= 0;
    Q_P = mpc_target.bus(nonzero_loads,QD)./mpc_target.bus(nonzero_loads,PD);
    mpc_target.bus(:,PD) = mpc_target.bus(:,PD)+2*dir*mpc_target.baseMVA;
    mpc_target.bus(nonzero_loads,QD) = Q_P.*mpc_target.bus(nonzero_loads,PD);
    % Run the CPF with matpower
    [results,~] = runcpf(mpc,mpc_target,mpoption('out.all',0,'verbose',0));
    % Extract the maximum loads
    max_loads_cpf = results.bus(:,PD);
    % Solve the maximum loadability limit without considering
    % reactive power limits
    results_mll = maxloadlim(mpc,dir,'use_qlim',0,'verbose',0);
    % Extract the maximum loads
    max_loads_mll = results_mll.bus(:,PD);
    % We compare with a precision of 1MW
    t = sprintf('%sdirection: %s',t0,mat2str(dir));
    t_is(max_loads_cpf,max_loads_mll,0,t);
end
t_end
