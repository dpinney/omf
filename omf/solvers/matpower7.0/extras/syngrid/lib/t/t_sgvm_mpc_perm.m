function [mpc_array, status] = t_sgvm_mpc_perm(quiet)
%T_MPC_PERM

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if nargin < 1
    quiet = 0;
end
%rng(seed, 'twister'); % for reproducibility
%rng('default');

num_tests = 1;
t_begin(num_tests, quiet);
define_constants;
%% create data sample
%mpcsamp = loadcase('case_ACTIVSg10k');
% mpcsamp = loadcase('case_ACTIVSg2000');
mpcsamp = loadcase('case118');
% mpctop  = loadcase('case3375wp');
mpopt = mpoption('opf.ac.solver', 'MIPS');
% smpl_opt = struct('node', 'direct');
smpl_opt = struct('node', 'kde');

opt   = struct('ea', struct('generations', 10, 'inds', 5, 'select', 5, 'randnew', 0, 'initfill', 1),...
        'mpopt', mpopt, 'smpl_opt', smpl_opt, ...
        'parallel', struct('use', 0, 'numcores', 20),'verbose', 0,...
        'nodeperm', struct('verbose', 0, 'niter', 1),...
        'branchperm', struct('verbose',0,'niter', 2),...
        'shunts', struct('verbose', 1));
% opt = struct('verbose', 2, 'nodeperm', struct('verbose', 1),'branchperm', struct('verbose', 1));
% data = sgvm_mpc2data(mpcsamp);
[~, topo] = sgvm_mpc2data(mpcsamp);
%N = 3000;
% have_fcn('ipopt', 0);
%[mpc_array, status] = syngrid(topo, mpcsamp);%, opt);
[mpc_array, status] = syngrid(topo, mpcsamp, struct('verbose', 1));
