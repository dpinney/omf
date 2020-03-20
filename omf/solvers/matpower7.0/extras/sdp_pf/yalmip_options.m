function opt = yalmip_options(overrides, mpopt)
%YALMIP_OPTIONS  Sets options for YALMIP.
%
%   OPT = YALMIP_OPTIONS
%   OPT = YALMIP_OPTIONS(OVERRIDES)
%   OPT = YALMIP_OPTIONS(OVERRIDES, FNAME)
%   OPT = YALMIP_OPTIONS(OVERRIDES, MPOPT)
%
%   Sets the values for the YALMIP options struct (sdpsettings) normally 
%   passed to SOLVESDP.
%
%   Inputs are all optional, second argument must be either a string
%   (FNAME) or a struct (MPOPT):
%
%       OVERRIDES - struct containing values to override the defaults
%       FNAME - name of user-supplied function called after default
%           options are set to modify them. Calling syntax is:
%                   MODIFIED_OPT = FNAME(DEFAULT_OPT);
%       MPOPT - MATPOWER options struct, uses the following fields:
%           verbose        	  - used to set opt.verbose
%           yalmip.opts       - struct containing values to use as OVERRIDES
%           yalmip.opt_fname  - name of user-supplied function used as FNAME,
%               except with calling syntax:
%                   MODIFIED_OPT = FNAME(DEFAULT_OPT, MPOPT);
%
%   Output is an sdpsettings struct to pass to SOLVESDP.
%
%   There are multiple ways of providing values to override the default
%   options. Their precedence and order of application are as follows:
%
%   With inputs OVERRIDES and FNAME
%       1. FNAME is called
%       2. OVERRIDES are applied
%   With inputs OVERRIDES and MPOPT
%       1. FNAME (from yalmip.opt_fname) is called
%       2. yalmip.opts (if not empty) are applied
%       3. OVERRIDES are applied
%
%   Example:
%
%   If yalmip.opt_fname = 'yalmip_user_options_3', then after setting the
%	default YALMIP options, YALMIP_OPTIONS will execute the following
%	user-defined function to allow option overrides:
%
%       opt = yalmip_user_options_3(opt, mpopt);
%
%   The contents of yalmip_user_options_3.m, could be something like:
%
%       function opt = yalmip_user_options_3(opt, mpopt)
%       opt.solver          = 'sedumi';
%       opt.sedumi.eps      = 0;
%       opt.sedumi.alg      = 2;
%       opt.sedumi.free     = 1;
%       opt.sedumi.stepdiff = 2;
%
%   See the YALMIP documentation (help sdpsettings) and the solver (e.g.,
%   SeDuMi, SDPT3, etc.) documentation for details.
%
%   See also SDPSETTINGS, MPOPTION.

%   MATPOWER
%   Copyright (c) 2013-2019, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%   and Daniel Molzahn, PSERC U of Wisc, Madison
%
%   This file is part of MATPOWER/mx-sdp_pf.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-sdp_pf/ for more info.

%%-----  initialization and arg handling  -----
%% defaults
verbose = 1;
fname   = '';

%% second argument
if nargin > 1 && ~isempty(mpopt)
    if ischar(mpopt)        %% 2nd arg is FNAME (string)
        fname = mpopt;
        have_mpopt = 0;
    else                    %% 2nd arg is MPOPT (MATPOWER options struct)
        have_mpopt = 1;
        verbose = mpopt.verbose;
        if isfield(mpopt.yalmip, 'opt_fname') && ~isempty(mpopt.yalmip.opt_fname)
            fname = mpopt.yalmip.opt_fname;
        end
    end
else
    have_mpopt = 0;
end

%% -----  set default options for YALMIP  -----
if have_fcn('matlab', 'vnum') >= 8.006 && have_fcn('cplex') && ...
        have_fcn('cplex', 'vnum') <= 12.006003
    s = warning('QUERY', 'MATLAB:lang:badlyScopedReturnValue');
    warning('OFF', 'MATLAB:lang:badlyScopedReturnValue');
    opt = sdpsettings;
    warning(s.state, 'MATLAB:lang:badlyScopedReturnValue');
else
    opt = sdpsettings;
end

opt.verbose = verbose >= 1;

% Store defaults for SeDuMi and SDPT3. Use a default sdpsettings object for
% any other solver.
if have_fcn('sedumi')
    opt = sdpsettings(opt, ...
        'solver','sedumi', ...
        'sedumi.eps',1e-8, ...
        'sedumi.alg',2, ...
        'sedumi.sdp',1, ...
        'sedumi.free',1, ...
        'sedumi.stepdif',2);
elseif have_fcn('sdpt3')
    opt = sdpsettings(opt, ...
        'solver','sdpt3', ...
        'sdpt3.gaptol',0, ...
        'sdpt3.maxit',100);
end

%%-----  call user function to modify defaults  -----
if ~isempty(fname)
    if have_mpopt
        opt = feval(fname, opt, mpopt);
    else
        opt = feval(fname, opt);
    end
end

%%-----  apply overrides  -----
if have_mpopt && isfield(mpopt.yalmip, 'opts') && ~isempty(mpopt.yalmip.opts)
    opt = nested_struct_copy(opt, mpopt.yalmip.opts);
end
if nargin > 0 && ~isempty(overrides)
    opt = nested_struct_copy(opt, overrides);
end
