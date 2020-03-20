function t_sg_options(quiet)
%T_SG_OPTIONS  Tests for sg_options().

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if nargin < 1
    quiet = 0;
end

t_begin(93, quiet);

t = 'sg_options() : ';
sgopt = sg_options();
t_is(sgopt.verbose, 0, 12, [t 'verbose']);
t_is(sgopt.bm.refsys, 2, 12, [t 'bm.refsys']);
t_ok(isequal(sgopt.bm.loading, 'D'), [t 'bm.loading']);
t_is(sgopt.bm.br2b_ratio, 1.5, 12, [t 'bm.br2b_ratio']);
t_is(sgopt.bm.br_overload, 0, 12, [t 'bm.br_overload']);
t_is(sgopt.bm.bta_method, 0, 12, [t 'bm.bta_method']);
t_is(sgopt.bm.cost_model, 2, 12, [t 'bm.cost_model']);
t_ok(sgopt.mpoptprint == 0, [t 'mpoptprint']);
t_ok(isempty(sgopt.vm.opflogpath), [t 'vm.opflogpath']);
t_is(sgopt.vm.ea.generations, 5, 12, [t 'vm.ea.generations'])
t_is(sgopt.vm.ea.inds, 4, 12, [t 'vm.ea.inds'])
t_is(sgopt.vm.ea.select, 5, 12, [t 'vm.ea.select'])
t_is(sgopt.vm.ea.randnew, 0, 12, [t 'vm.ea.randnew'])
t_is(sgopt.vm.ea.initfill, 0, 12, [t 'vm.ea.initfill'])
t_is(sgopt.vm.parallel.use, 0, 12, [t 'vm.parallel.use'])
t_is(sgopt.vm.parallel.numcores, 0, 12, [t 'vm.parallel.numcores'])
t_is(sgopt.vm.branchperm.niter, 1, 12, [t 'vm.branchperm.niter'])
t_is(sgopt.vm.branchperm.verbose, 0, 12, [t 'vm.branchperm.verbose'])
t_is(sgopt.vm.branchperm.overload_frac_factor, 0.95, 12, [t 'vm.branchperm.overload_frac_factor'])
t_is(sgopt.vm.nodeperm.niter, 1, 12, [t 'vm.nodeperm.niter'])
t_is(sgopt.vm.nodeperm.verbose, 0, 12, [t 'vm.nodeperm.verbose'])
t_is(sgopt.vm.nodeperm.nox, 1, 12, [t 'vm.nodeperm.nox'])
t_is(sgopt.vm.nodeperm.usedv, 0, 12, [t 'vm.nodeperm.usedv'])
t_is(sgopt.vm.nodeperm.scale_s, 1, 12, [t 'vm.nodeperm.scale_s'])
t_is(sgopt.vm.nodeperm.scale_s_factor, 0.95, 12, [t 'vm.nodeperm.scale_s_factor'])
t_is(sgopt.vm.shunts.tmag, 0.1, 12, [t 'vm.shunts.tmag'])
t_is(sgopt.vm.shunts.shift_in, 0.015, 12, [t 'vm.shunts.shift_in'])
t_is(sgopt.vm.shunts.shunt_max, 500, 12, [t 'vm.shunts.shunt_max'])
t_is(sgopt.vm.shunts.verbose, 0, 12, [t 'vm.shunts.verbose'])
t_is(sgopt.vm.shunts.soft_ratea, 0, 12, [t 'vm.shunts.soft_ratea'])
t_ok(strcmp(sgopt.vm.smpl.branch, 'direct'), [t 'vm.smpl.branch'])
t_ok(strcmp(sgopt.vm.smpl.node, 'kde'), [t 'vm.smpl.node'])
t_is(sgopt.vm.smpl.lincost, 100, 12, [t 'vm.smpl.lincost'])
t_is(sgopt.vm.smpl.usegenbus, 1, 12, [t 'vm.smpl.usegenbus'])
t_is(sgopt.vm.smpl.ngbuses, -1, 12, [t 'vm.smpl.ngbuses'])
t_is(sgopt.vm.smpl.usegen2load, 1, 12, [t 'vm.smpl.usegen2load'])
t_is(sgopt.vm.smpl.baseMVA_default, 100, 12, [t 'vm.smpl.baseMVA_default'])
t_is(sgopt.vm.smpl.rate_a_default, 400, 12, [t 'vm.smpl.rate_a_default'])
if have_fcn('ipopt')
    t_ok(strcmp(sgopt.mpopt.opf.ac.solver, 'IPOPT'), [t 'AC OPF solver = ''IPOPT''']);
    t_is(sgopt.mpopt.ipopt.opts.max_iter, 500, 12, [t 'mpopt.ipopt.opts.max_iter'])
    t_is(sgopt.mpopt.ipopt.opts.tol, 1e-6, 12, [t 'mpopts.ipopt.opts.tol'])
    t_is(sgopt.mpopt.ipopt.opts.constr_viol_tol, 1e-6, 12, [t 'mpopts.ipopt.opts.constr_viol_tol'])
    t_is(sgopt.mpopt.ipopt.opts.acceptable_tol, 1e-6, 12, [t 'mpopts.ipopt.opts.acceptable_tol'])
    t_is(sgopt.mpopt.ipopt.opts.dual_inf_tol, 1e-5, 12, [t 'mpopts.ipopt.opts.dual_inf_tol'])
    % check that MIPS is default if IPOPT not available
    have_fcn('ipopt', 0);
    sgopt = sg_options();
    t_ok(strcmp(sgopt.mpopt.opf.ac.solver, 'DEFAULT'), [t 'AC OPF solver = ''DEFAULT''']);
    have_fcn('ipopt', 1);
else
    t_skip(6, 'IPOPT not installed')
    t_ok(strcmp(sgopt.mpopt.opf.ac.solver, 'DEFAULT'), [t 'AC OPF solver = ''DEFAULT''']);
end

t = 'sg_options(ov1) : ';
ov1 = struct(...
    'verbose',      2, ...          %% no progress output
    'bm', struct( ...
        'loading',      'L', ...    %% low
        'bta_method',   1 ) ...     %% "W0" method - simpler, faster
);
sgopt = sg_options(ov1);
t_is(sgopt.verbose, 2, 12, [t 'verbose']);
t_is(sgopt.bm.refsys, 2, 12, [t 'bm.refsys']);
t_ok(isequal(sgopt.bm.loading, 'L'), [t 'bm.loading']);
t_is(sgopt.bm.br2b_ratio, 1.5, 12, [t 'bm.br2b_ratio']);
t_is(sgopt.bm.bta_method, 1, 12, [t 'bm.bta_method']);

t = 'sg_options(ov2) : ';
ov2 = struct(...
    'bm', struct( ...
        'refsys',       3, ...
        'loading',      'H', ...    %% high
        'br2b_ratio',   2.5 ) ...
);
sgopt = sg_options(ov2);
t_is(sgopt.verbose, 0, 12, [t 'verbose']);
t_is(sgopt.bm.refsys, 3, 12, [t 'bm.refsys']);
t_ok(isequal(sgopt.bm.loading, 'H'), [t 'bm.loading']);
t_is(sgopt.bm.br2b_ratio, 2.5, 12, [t 'bm.br2b_ratio']);
t_is(sgopt.bm.bta_method, 0, 12, [t 'bm.bta_method']);

if have_fcn('ipopt')
    t = 'sg_options(ov3) + IPOPT : ';
    ov3 = struct('mpopt', mpoption('ipopt.opts.max_iter', 300, 'ipopt.opts.tol', 1e-4));
    sgopt = sg_options(ov3);
    t_is(sgopt.mpopt.ipopt.opts.max_iter, 300, 12, [t 'mpopt.ipopt.opts.max_iter'])
    t_is(sgopt.mpopt.ipopt.opts.tol, 1e-4, 12, [t 'mpopts.ipopt.opts.tol'])
else
    t_skip(2, 'IPOPT not installed')
end

% check mpoptprint functionality
t = 'sg_options(ov4) (mpoptprint = 0) : ';
ov4 = struct('mpopt', mpoption('verbose', 1, 'out.all', 1));
sgopt = sg_options(ov4);
t_is(sgopt.mpopt.out.all, 0, 12, [t 'mpopt.out.all'])
t_is(sgopt.mpopt.verbose, 0, 12, [t 'mpopt.verose'])
t = 'sg_options(ov4) (mpoptprint = 1) : ';
ov4 = struct('mpoptprint', 1, 'mpopt', mpoption('verbose', 1, 'out.all', 1));
sgopt = sg_options(ov4);
t_is(sgopt.mpopt.out.all, 1, 12, [t 'mpopt.out.all'])
t_is(sgopt.mpopt.verbose, 1, 12, [t 'mpopt.verose'])

% name value test
t = 'sg_options(name, val ...) : ';
sgopt0 = sg_options('verbose', 2, 'vm.ea.generations', 10, 'bm.br2b_ratio', 2.5);
t_ok(sgopt0.verbose == 2, [t 'verbose']);
t_ok(sgopt0.vm.ea.generations == 10, [t 'vm.ea.generations']);
t_is(sgopt0.bm.br2b_ratio, 2.5, 12, [t 'bm.br2b_ratio']);

% update options structure
t = 'sg_options(sgopt0, name, val ...) : ';
sgopt = sg_options(sgopt0, 'vm.smpl.lincost', 150, 'vm.shunts.tmag', 0.5);
t_ok(sgopt.verbose == 2, [t 'verbose']);
t_ok(sgopt.vm.ea.generations == 10, [t 'vm.ea.generations']);
t_is(sgopt.bm.br2b_ratio, 2.5, 12, [t 'bm.br2b_ratio']);
t_ok(sgopt.vm.smpl.lincost == 150, [t 'vm.smpl.lincost']);
t_is(sgopt.vm.shunts.tmag, 0.5, 12, [t 'vm.shunts.tmag']);

if have_fcn('ipopt')
    t = 'sg_options(sgopt0, name, val ...) + IPOPT : ';
    sgopt = sg_options(sgopt0, 'mpopt.ipopt.opts.max_iter', 300, 'mpopt.ipopt.opts.tol', 1e-4);
    t_ok(sgopt.verbose == 2, [t 'verbose']);
    t_ok(sgopt.vm.ea.generations == 10, [t 'vm.ea.generations']);
    t_is(sgopt.bm.br2b_ratio, 2.5, 12, [t 'bm.br2b_ratio']);
    t_is(sgopt.mpopt.ipopt.opts.max_iter, 300, 12, [t 'mpopt.ipopt.opts.max_iter'])
    t_is(sgopt.mpopt.ipopt.opts.tol, 1e-4, 12, [t 'mpopts.ipopt.opts.tol'])
else
    t_skip(5, 'IPOPT not installed')
end

t = 'sg_options(sgopt0, ov) : ';
ov = struct('vm', struct('smpl', struct('lincost', 150), 'shunts', struct('tmag', 0.5)));
sgopt = sg_options(sgopt0, ov);
t_ok(sgopt.verbose == 2, [t 'verbose']);
t_ok(sgopt.vm.ea.generations == 10, [t 'vm.ea.generations']);
t_is(sgopt.bm.br2b_ratio, 2.5, 12, [t 'bm.br2b_ratio']);
t_ok(sgopt.vm.smpl.lincost == 150, [t 'vm.smpl.lincost']);
t_is(sgopt.vm.shunts.tmag, 0.5, 12, [t 'vm.shunts.tmag']);

if have_fcn('ipopt')
    t = 'sg_options(sgopt0, ov) + IPOPT : ';
    ov3 = struct('mpopt', mpoption('ipopt.opts.max_iter', 300, 'ipopt.opts.tol', 1e-4));
    sgopt = sg_options(sgopt0, ov3);
    t_ok(sgopt.verbose == 2, [t 'verbose']);
    t_ok(sgopt.vm.ea.generations == 10, [t 'vm.ea.generations']);
    t_is(sgopt.bm.br2b_ratio, 2.5, 12, [t 'bm.br2b_ratio']);
    t_is(sgopt.mpopt.ipopt.opts.max_iter, 300, 12, [t 'mpopt.ipopt.opts.max_iter'])
    t_is(sgopt.mpopt.ipopt.opts.tol, 1e-4, 12, [t 'mpopts.ipopt.opts.tol'])
else
    t_skip(5, 'IPOPT not installed')
end
%% errors
t = 'bm.refsys < 1 : ';
ov = struct('bm', struct('refsys', 0));
try
    sgopt = sg_options(ov);
    t_ok(0, [t 'no error thrown']);
catch
    t_ok(1, [t 'error thrown as expected']);
end

t = 'bm.refsys > 3 : ';
ov = struct('bm', struct('refsys', 4));
try
    sgopt = sg_options(ov);
    t_ok(0, [t 'no error thrown']);
catch
    t_ok(1, [t 'error thrown as expected']);
end

t = 'bm.loading not ''D'', ''L'', ''M'', or ''H'' : ';
ov = struct('bm', struct('loading', 'Z'));
try
    sgopt = sg_options(ov);
    t_ok(0, [t 'no error thrown']);
catch
    t_ok(1, [t 'error thrown as expected']);
end

t = 'bm.loading not ''D'', ''L'', ''M'', or ''H'' : ';
ov = struct('bm', struct('loading', 'My Goodness'));
try
    sgopt = sg_options(ov);
    t_ok(0, [t 'no error thrown']);
catch
    t_ok(1, [t 'error thrown as expected']);
end

t = 'bm.br2b_ratio < 1.25 : ';
ov = struct('bm', struct('br2b_ratio', 1.24));
try
    sgopt = sg_options(ov);
    t_ok(0, [t 'no error thrown']);
catch
    t_ok(1, [t 'error thrown as expected']);
end

t = 'bm.br2b_ratio > 2.5 : ';
ov = struct('bm', struct('br2b_ratio', 2.51));
try
    sgopt = sg_options(ov);
    t_ok(0, [t 'no error thrown']);
catch
    t_ok(1, [t 'error thrown as expected']);
end

t = 'bm.br_overload not 0 or 1 : ';
ov = struct('bm', struct('br_overload', 0.5));
try
    sgopt = sg_options(ov);
    t_ok(0, [t 'no error thrown']);
catch
    t_ok(1, [t 'error thrown as expected']);
end

t = 'bm.bta_method not 0 or 1 : ';
ov = struct('bm', struct('bta_method', 0.5));
try
    sgopt = sg_options(ov);
    t_ok(0, [t 'no error thrown']);
catch
    t_ok(1, [t 'error thrown as expected']);
end

t = 'bm.cost_model not 1 or 2 : ';
ov = struct('bm', struct('cost_model', 0));
try
    sgopt = sg_options(ov);
    t_ok(0, [t 'no error thrown']);
catch
    t_ok(1, [t 'error thrown as expected']);
end

t_end
