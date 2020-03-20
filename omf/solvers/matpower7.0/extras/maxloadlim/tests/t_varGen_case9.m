function t_varGen_case9(quiet)
% This function tests the implementation of the variable generators in the
% IEEE 9 bus system

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
dir_var_gen_all = [0 1 0;
    0 0 1;
    0 1 1];
idx_nonzero_loads = mpc.bus(:,PD) > 0;
% Number of load increase directions
nb_dir_load = size(dir_all,1);
nb_dir_gen = size(dir_var_gen_all,1);
% Message header
t0 = 'case9: ';

num_tests = nb_dir_load*nb_dir_gen; % we don't consider the direction with all zeros
t_begin(num_tests, quiet);
for i = 1:nb_dir_load
    dir_load = dir_all(i,:)';
    dir_load(~idx_nonzero_loads)=0;
    for j = 1:nb_dir_gen
        dir_var_gen = dir_var_gen_all(j,:)';
        idx_var_gen = find(dir_var_gen);
        dir_var_gen = dir_var_gen(idx_var_gen);
        % Normalizing with respect to both loads and gens
        gen_load_dir = [dir_load;dir_var_gen];
        dir_load = dir_load/norm(gen_load_dir);
        dir_var_gen = dir_var_gen/norm(gen_load_dir);
        % Find MLL in the direction of load and gen increase
        results_with_gens = maxloadlim(mpc,dir_load,'verbose',0,'idx_var_gen',idx_var_gen,'dir_var_gen',dir_var_gen);
        % Set gens to their values in previous results and re-run in
        % load space only
        mpc2 = mpc;
        mpc2.gen(:,PG) = results_with_gens.gen(:,PG);
        dir_load2 = dir_load/norm(dir_load);
        % Find MLL in the direction of load and gen increase
        results_without_gens = maxloadlim(mpc2,dir_load2,'verbose',0);
        % Compare the maximum loads
        mll_with_gen = results_with_gens.bus(:,PD);
        mll_without_gen = results_without_gens.bus(:,PD);
        % We compare with a precision of 1MW
        t = sprintf('%sLOAD: %s   GEN: %s',t0,mat2str(dir_load),mat2str(dir_var_gen));
        t_is(mll_with_gen,mll_without_gen,0,t);
    end
end
t_end
