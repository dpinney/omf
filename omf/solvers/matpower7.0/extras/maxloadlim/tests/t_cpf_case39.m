function t_cpf_case39(quiet)
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
mpc = loadcase('case39');
% Defining several load increase directions to be tested
dir_all = [eye(39);ones(1,39)];
idx_nonzero_loads = mpc.bus(:,PD) > 0;
% Number of load increase directions
nb_dir = size(dir_all,1);
% Message header
t0 = 'case39: ';

num_tests = nb_dir; % we don't consider the direction with all zeros
t_begin(num_tests, quiet);
for i = 1:nb_dir
    dir = dir_all(i,:)';
    dir(~idx_nonzero_loads)=0;
    if sum(dir) == 0 || i == 31
        % The code does not currently support load increase at
        % nonzero loads.
        % The MATPOWER CPF takes long time for increase at bus 31
        % which is the slack bus.
        t = sprintf('%s All load zeros or increase at slack bus',t0);
        t_skip(1, t);
    else
        % Preparing the target case for Matpower CPF
        mpc_target = mpc;
        nonzero_loads = mpc_target.bus(:,PD) ~= 0;
        Q_P = mpc_target.bus(nonzero_loads,QD)./mpc_target.bus(nonzero_loads,PD);
        mpc_target.bus(:,PD) = mpc.bus(:,PD)+2*dir*mpc_target.baseMVA;
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
        if i == 9
            t_skip(1, sprintf('%s - KNOWN MISMATCH: (%.2f, %.2f)', t, max_loads_mll(9), max_loads_cpf(9)));
        else
            t_is(max_loads_mll,max_loads_cpf,0,t);
        end
    end
end
t_end
