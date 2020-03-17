function sgopt = sg_options(varargin)
%SG_OPTIONS  Create a SynGrid options struct with default options + overrides.
%   SGOPT = SG_OPTIONS()
%   SGOPT = SG_OPTIONS(OVERRIDES)
%   SGOPT = SG_OPTIONS(SGOPT0, OVERRIDES)
%   SGOPT = SG_OPTIONS(NAME1, VAL1, ...)
%   SGOPT = SG_OPTIONS(SGOPT0, NAME1, VAL1, ...)
%
%   Create a SynGrid options struct with default values for all options,
%   then optionally apply values specified in the OVERRIDES struct.
%   Alternatively, the options struct can be initialized with an existing
%   SynGrid options struct SGOPT0 and/or the overrides can be specified
%   as a set of name value pairs (e.g. NAME1, VAL1, ...). Note that the
%   name in the name value pairs can be a string containing '.', such as
%   'ea.parallel.numcores'.
%
%   The SynGrid options are as follows, with the default values in parenthesis:
%
%       general options:
%           verbose (0) - controls level of progress output displayed
%               0 : print no progress info
%               1 : print a little progress info
%               2 : print a lot of progress info
%               3 : print all progress info
%           debug (0) - debug mode switch
%               0 : run in normal mode
%               1 : run in debug mode (not currently used)
%           mpopt (see MPOPTION) - MATPOWER options struct, default is
%               given by MPOPTION() with the following two exceptions:
%               (1) 'out.all' and 'verbose' are set to 0, unless
%                   'mpoptprint' is set to 1
%               (2) if IPOPT is available, 'opf.ac.solver' is set to 'IPOPT'
%                   and several 'ipopt.opts.*' are set explicitly, as follows:
%                       'file_print_level', 5
%                       'print_user_options', 'yes'
%                       'tol', 1e-6
%                       'dual_inf_tol', 1e-5
%                       'max_iter', 500
%                       'print_timing_statistics', 'yes'
%                       'constr_viol_tol', 1e-6
%                       'acceptable_tol', 1e-6
%           mpoptprint (0) - determine whether mpopt controls MATPOWER output
%               0 : turn off all MATPOWER screen output
%               1 : use values in 'mpopt' to control MATPOWER screen output
%
%       base mode options:
%           bm.loading ('D') - loading level
%               'D' : default - depends on system size
%                               (based on stats from realistic grids)
%               'L' : low     - total load = 30%-40% of generation capacity
%               'M' : medium  - total load = 50%-60% of generation capacity
%               'H' : high    - total load = 70%-80% of generation capacity
%           bm.br2b_ratio (1.5) - ratio of number of branches to number of buses
%                              valid range (1.25 - 2.5)
%           bm.br_overload (0) - overloaded branches
%               0 : without overloaded branches
%               1 : with same percentage of overloaded branches as
%                   realistic grids
%           bm.bta_method (0) - bus type assignment method
%               0 : "W0" method - simpler & faster
%               1 : "W1" method - more accurate & slower
%           bm.cost_model (2) - generation cost model
%               1 : linear cost function
%               2 : quadratic cost function
%
%       variations mode options:
%           vm.opflogpath ('') - path to log files if IPOPT used
%           vm.ea.generations (5) - number of iterations in variations mode
%           vm.ea.inds (4) - # of unique cases active in each iteration
%           vm.ea.select (5) - # of cases returned upon termination
%           vm.ea.randnew (0) - # of new cases via the initialization method
%           vm.ea.initfill (0) - handling when fewer individuals than vm.ea.inds
%               0 : do not initialize new individuals
%               1 : initialize new individuals
%           vm.parallel.use (0) - controls whether PARFOR loops are used
%               0 : do not use parallelization
%               1 : use parallelization
%           vm.parallel.numcores (0) - # of cores for parallelization
%           vm.branchperm.niter (1) - # of branch permutation iterations
%               per generation
%           vm.branchperm.verbose (0) - print progress for branch permutation
%               0 : no progress info
%               1 : some progress info
%           vm.branchperm.overload_frac_factor (0.95) - scaling factor in
%               [0, 1] used to update what is considered overload.
%               E.g., if x0=1 initially is the overload factor, in the next
%               branch permutation x1=0.95
%           vm.nodeperm.niter (1) - # of node permutation iterations per
%               generation
%           vm.nodeperm.verbose (0) - print progress for node permutation
%               0 : no progress info
%               1 : some progress info
%               2 : even more progress info
%               3 : all progress info including from LP solver
%           vm.nodeperm.nox (1) - handling of impact of V on P and theta
%               on Q in sgvm_calc_injection_delta()
%               0 : include impact
%               1 : exclude impact
%           vm.nodeperm.usedv (0) - INITIAL handling of voltage change
%               constraints in sgvm_calc_injection_delta()
%               0 : ignore constraints initially
%               1 : include constraints initially
%           vm.nodeperm.scale_s (1) - initial scaling factor for determining
%               overloaded lines in node permutation
%           vm.nodeperm.scale_s_factor (0.95) - factor for decreasing 
%               'vm.nodeperm.scale_s'
%           vm.shunts (see SGVM_SHUNTSOPTS) - options for adding reactive
%               shunts
%           vm.smpl (see SGVM_SMPLOPTS) - sampling options for creating a
%               seed MATPOWER case

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

%% default values
varidx = 1;     %% input variable counter
sgopt = struct( ...
    'verbose',      0, ...      %% no progress output
    'debug', 0, ...             %% debug mode
    'mpopt', mpoption(), ...    %% MATPOWER options structure
    'mpoptprint', 0, ...        %% flag to mpopt print options
    'bm', struct ( ...
        'refsys',       2, ...      %% reference system 2
        'loading',      'D', ...    %% default - depends on system size
        'br2b_ratio',   1.5, ...
        'br_overload',  0, ...      %% without overloaded branches
        'bta_method',   0, ...      %% "W0" method - simpler, faster
        'cost_model',   2 ), ...    %% quadratic
    'vm', struct(...            %% options for variations mode
        'opflogpath', '', ...   %% path to log files if IPOPT used
        'ea', struct( ...
            'generations', 5, ...
            'inds', 4, ...
            'select', 5, ...
            'randnew', 0, ...
            'initfill', 0 ), ...
        'parallel', struct( ...
            'use', 0, ...
            'numcores', 0 ), ...
        'branchperm', struct( ...
            'niter', 1, ...
            'verbose', 0, ...
            'overload_frac_factor', 0.95 ), ...
        'nodeperm', struct( ...
            'niter', 1, ...
            'verbose', 0, ...
            'nox', 1, ...
            'usedv', 0, ...
            'scale_s', 1, ...
            'scale_s_factor', 0.95 ), ...
        'shunts', sgvm_shuntsopts(), ...
        'smpl', sgvm_smplopts() ) ...
);

nsc_opt = struct('check', 1);
overrides = [];
if nargin
    if isstruct(varargin{varidx}) && ~isempty(varargin{varidx})
        %% update SGOPT using SGOPT0
        %% (could be OVERRIDES structure, but treatment is identical)
        sgopt = nested_struct_copy(sgopt, varargin{varidx}, nsc_opt);
        varidx = varidx + 1;
    end
    if varidx <= nargin
        if isstruct(varargin{varidx})
            %% OVERRIDES provided as a struct
            overrides = varargin{varidx};
        elseif ischar(varargin{varidx}) && (mod( nargin - varidx + 1, 2) == 0)
            %% OVERRIDES provided with key-value pairs
            %% convert pairs to struct
            while varidx < nargin
                name = varargin{varidx};
                val  = varargin{varidx+1};
                varidx = varidx + 2;
                c = regexp(name, '([^\.]*)', 'tokens');
                s = struct();
                for i = 1:length(c)
                    s(i).type = '.';
                    s(i).subs = c{i}{1};
                end
                overrides = subsasgn(overrides, s, val);
            end
        else
            error('sg_options: invalid calling syntax, see ''help sg_options'' to double-check the valid options');
        end
    end
end

%% apply overrides, if specified
if nargin && ~isempty(overrides)
    sgopt = nested_struct_copy(sgopt, overrides, nsc_opt);
end

%% validate options
if ~isnumeric(sgopt.bm.refsys) || sgopt.bm.refsys < 1 || sgopt.bm.refsys > 3
    error('sg_options: reference system SGOPT.bm.refsys must be 1, 2 or 3');
end
if length(sgopt.bm.loading) ~= 1 || ( upper(sgopt.bm.loading) ~= 'D' && ...
                                      upper(sgopt.bm.loading) ~= 'L' && ...
                                      upper(sgopt.bm.loading) ~= 'M' && ...
                                      upper(sgopt.bm.loading) ~= 'H' )
    error('sg_options: reference system SGOPT.bm.loading must be ''D'' (default), ''L'' (low), ''M'' (medium), or ''H'' (high)');
end
if ~isnumeric(sgopt.bm.br2b_ratio) || sgopt.bm.br2b_ratio < 1.25 || sgopt.bm.br2b_ratio > 2.5
    error('sg_options: branch to bus ratio SGOPT.bm.br2b_ratio must between 1.25 and 2.5');
end
if ~isnumeric(sgopt.bm.bta_method) || (sgopt.bm.bta_method ~= 0 && sgopt.bm.bta_method ~= 1)
    error('sg_options: bus type assignment method SGOPT.bm.bta_method must 0 or 1');
end
if ~isnumeric(sgopt.bm.cost_model) || (sgopt.bm.cost_model ~= 1 && sgopt.bm.cost_model ~= 2)
    error('sg_options: generation cost model SGOPT.bm.cost_model must 1 or 2');
end
if ~isnumeric(sgopt.bm.br_overload) || (sgopt.bm.br_overload ~= 0 && sgopt.bm.br_overload ~= 1)
    error('sg_options: branch overload option SGOPT.bm.br_overload must 0 or 1');
end

%% handle MATPOWER options
sgopt.mpopt = mpoption(sgopt.mpopt, 'opf.softlims.default', 0); %% required for variations mode
if ~sgopt.mpoptprint
    %% print options overridden here unless explicitly prohibited
    %% by setting SGOPT.mpoptprint

    %% turn off all printing
    sgopt.mpopt = mpoption(sgopt.mpopt, 'out.all', 0, 'verbose', 0);
end

%% set default AC OPF solver to IPOPT, if available
if strcmp(sgopt.mpopt.opf.ac.solver, 'DEFAULT') && have_fcn('ipopt')
    sgopt.mpopt = mpoption(sgopt.mpopt, 'opf.ac.solver', 'IPOPT');
end

%% add IPOPT specific settings, if available
if strcmp(sgopt.mpopt.opf.ac.solver, 'IPOPT')
    sg_ipopt_defaults = struct( ...
        'file_print_level', 5, ...
        'print_user_options', 'yes', ...
        'tol', 1e-6, ...
        'dual_inf_tol', 1e-5, ...
        'max_iter', 500, ...
        'print_timing_statistics', 'yes', ...
        'constr_viol_tol', 1e-6, ...
        'acceptable_tol', 1e-6 );
    if isempty(sgopt.mpopt.ipopt.opts)
        ipopt_opts = sg_ipopt_defaults;
    else
        ipopt_opts = nested_struct_copy(sg_ipopt_defaults, sgopt.mpopt.ipopt.opts);
    end
    sgopt.mpopt = mpoption(sgopt.mpopt, 'ipopt.opts', ipopt_opts);
end
