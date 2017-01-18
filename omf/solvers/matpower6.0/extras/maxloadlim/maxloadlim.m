function results = maxloadlim(mpc,dir_mll,varargin)
% MAXLOADLIM computes the maximum loadability limit in one direction. It
% uses dispatchable loads in MATPOWER
%   RESULTS = MAXLOADLIM(MPC,DIR_MLL) returns the results from the
%   optimization problem looking for the maximum loadability limit in
%   the direction of load increase DIR_MLL. DIR_MLL defines the directions
%   of load increases for all buses. For buses with zero loads, the
%   direction of load increases must be zero. RESULTS contains all fields
%   returned from the runopf MATPOWER function. It also contains the 
%   following additional fields:
%   * dir_mll: the direction of load increase used as input.
%   * stab_marg: the stability margin to the maximum loadability point from
%   the base case defined in the input MPC.
%   * bif: information about the bifurcation at the MLL point.
%   
%   RESULTS = MAXLOADLIM(MPC,DIR_MLL,NAME,VALUE) uses the options defined
%   by the pair NAME,VALUE. The currently supported options are 
%     * 'verbose': 1 or 0 (Default). If set to 1, a summary of the results
%     at the maximum loadability limit is printed. 
%     * 'use_qlim': 1 (Default) or 0. Enforces or not the reactive power
%     limits of the generators.
%     * 'Vlims_bus_nb': [] (Default) or array of integers. By default, the
%     bus voltage limits are not enforced. This option allows for defining
%     a set of buses at which the voltage limits are enforced.
%
%   See also PREPARE_MAXLOADLIM, POSTPROC_MAXLOADLIM, PRINT_MAXLOADLIM, 
%   RUNOPF.

%   MATPOWER
%   Copyright (c) 2015-2016, Power Systems Engineering Research Center (PSERC)
%   by Camille Hamon
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

define_constants;

%% Checking the options, if any
input_checker = inputParser;

default_verbose = 0;
verbose_levels = [0;1];
check_verbose = @(x)(isnumeric(x) && isscalar(x) && any(x == verbose_levels));
addParameter(input_checker,'verbose',default_verbose,check_verbose);

input_checker.KeepUnmatched = true;
parse(input_checker,varargin{:});

options = input_checker.Results;

%% Prepare the matpower case for the maximum loadability limit problem
mpc_vl = prepare_maxloadlim(mpc,dir_mll,varargin{:});

%% Run opf
% Turning off the printing and initializing from the base case
mpopt = mpoption('verbose',options.verbose,'opf.init_from_mpc',1);
mpopt = mpoption(mpopt,'out.all',0);
% Decreasing the threshold for the relative complementarity constraints
mpopt = mpoption(mpopt,'mips.comptol',1e-8);
% Change solver
mpopt = mpoption(mpopt, 'opf.ac.solver', 'MIPS');
% Execute opf
results = runopf(mpc_vl,mpopt);

%% Post-processing
results = postproc_maxloadlim(results,dir_mll);

%% Printing
if options.verbose
    print_maxloadlim(mpc,results);
end
