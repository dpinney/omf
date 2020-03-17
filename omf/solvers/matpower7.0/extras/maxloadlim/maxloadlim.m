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
%   This file is part of MATPOWER/mx-maxloadlim.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-maxloadlim/ for more info.

define_constants;

%% Checking the options, if any
input_checker = inputParser;

default_verbose = 0;
verbose_levels = [0;1];
check_verbose = @(x)(isnumeric(x) && isscalar(x) && any(x == verbose_levels));
addParameter(input_checker,'verbose',default_verbose,check_verbose);

% Direction of change for generators
default_dir_var_gen = [];
check_dir_var_gen = @(x)(isempty(x) || (isnumeric(x) && iscolumn(x)));
addParameter(input_checker,'dir_var_gen',default_dir_var_gen,check_dir_var_gen);

% Generator numbers of the variable generators;
default_idx_var_gen = [];
check_idx_var_gen = @(x)(isempty(x) || (isnumeric(x) && iscolumn(x)));
addParameter(input_checker,'idx_var_gen',default_idx_var_gen,check_idx_var_gen);

input_checker.KeepUnmatched = true;
parse(input_checker,varargin{:});

options = input_checker.Results;

%% Iterate the process when considering variable generators
cur_stab_marg = 0;
idx_var_gen = options.idx_var_gen;
dir_var_gen = options.dir_var_gen;
nb_var_gen = length(idx_var_gen);
repeat = 1;
iter = 0;
iter_max = nb_var_gen;
settings = varargin;

while iter <= iter_max && repeat
    if options.verbose
        fprintf(1,'Beginning of iteration %d\n',iter);
    end
    iter = iter + 1;
    
    %% Prepare the matpower case for the maximum loadability limit problem
    % We remove reactive power limits of the slack bus since, by
    % assumption, the slack bus is a strong grid.
    [ref,~] = bustypes(mpc.bus,mpc.gen);
    gen_ref = ismember(mpc.gen(:,GEN_BUS),ref);
    mpc.gen(gen_ref,QMAX) = 9999;
    mpc.gen(gen_ref,QMIN) = -9999;
    mpc_vl = prepare_maxloadlim(mpc,dir_mll,settings{:});
    
    %% Run opf
    % Turning off the printing and initializing from the base case
    mpopt = mpoption('verbose',options.verbose,'opf.init_from_mpc',1);
    mpopt = mpoption(mpopt,'out.all',0);
    % Decreasing the threshold for the relative complementarity constraints
    mpopt = mpoption(mpopt,'mips.comptol',1e-8);
    % Change solver
    mpopt = mpoption(mpopt,'opf.ac.solver','MIPS');
    % Execute opf
    results = runopf(mpc_vl,mpopt);
    
    %% Post-processing
    results = postproc_maxloadlim(results,dir_mll);
    % update the stability margin with that of the current iteration
    results.stab_marg = results.stab_marg+cur_stab_marg;
    cur_stab_marg = results.stab_marg;
    
    %% Check if it stopped because of a variable generator reached its PMAX
    % We check the Lagrangian multiplier of Pg<=PMAX
    if isempty(idx_var_gen)
        gen_hit_pmax = 0;
    else
        gen_hit_pmax = (abs(results.gen(idx_var_gen,PMAX)-results.gen(idx_var_gen,PG)) < 5e-4) | ...
            (results.var.mu.u.Pg(idx_var_gen) > 1e-4); %1e-4 for numerical error
    end
    if sum(gen_hit_pmax) == 0
        % The OPF did not stop because PG = PMAX so we are done.
        repeat = 0;
    else
        % We remove it from the direction of change and the set of variable
        % generators
        idx_var_gen(gen_hit_pmax) = [];
        dir_var_gen(gen_hit_pmax) = [];
        % We update the settings that are passed down to the function
        % preparing the constraints
        var_gen_set = find(strcmp(settings,'idx_var_gen'));
        settings{var_gen_set+1} = idx_var_gen;
        dir_gen_set = find(strcmp(settings,'dir_var_gen'));
        settings{dir_gen_set+1} = dir_var_gen;
        % We update mpc with the results from the current iteration
        mpc.bus(:,[PD QD]) = results.bus(:,[PD QD]);
        mpc.gen(:,PG) = results.gen(:,PG);
        mpc.bus(:,[VM VA]) = results.bus(:,[VM VA]);
%         % Remove OPF infor
%         mpc.gen(:,MU_PMAX:MU_QMIN) = [];
    end
end

%% Printing
if options.verbose
    print_maxloadlim(mpc,results);
end
