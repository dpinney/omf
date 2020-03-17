function mpc_vl = prepare_maxloadlim(mpc,dir_mll,varargin)
% PREPARE_MAXSLL prepares the mpc case for computing the maximum
% loadability limit by adding the relevant constraints and variables.
%   MPC_VL = PREPARE_MAXLL(MPC,DIR_MLL) returns the matpower case MPC_VL
%   prepared from MPC by transforming all loads to dispatchable loads,
%   adding a field for the direction DIR_MLL of load increase and adapting 
%   limits for the OPF formulation.
%   MPC_VL = PREPARE_MAXLL(MPC,DIR_MLL,Name,Value) does the same with additional
%   options specified in pairs Name,Value. The two supported options are as 
%   follows:
%     * 'use_qlim': 1 (Default) or 0. Enforces or not the reactive power
%     limits of the generators.
%     * 'Vlims_bus_nb': [] (Default) or array of integers. By default, the
%     bus voltage limits are not enforced. This option allows for defining
%     a set of buses at which the voltage limits are enforced.

%   MATPOWER
%   Copyright (c) 2015-2016, Power Systems Engineering Research Center (PSERC)
%   by Camille Hamon
%
%   This file is part of MATPOWER/mx-maxloadlim.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-maxloadlim/ for more info.

define_constants;
n_gen = size(mpc.gen,1);
mpc0 = mpc;
%% Checking the options, if any
input_checker = inputParser;

% Q-lims
default_qlim = 1;
check_qlim = @(x)(isnumeric(x) && isscalar(x));
addParameter(input_checker,'use_qlim',default_qlim,check_qlim);

% Enfore V-lims
default_vlim = [];
check_vlim = @(x)(isnumeric(x) && all(floor(x) == ceil(x))); % expects array of integer values (bus numbers)
addParameter(input_checker,'Vlims_bus_nb',default_vlim,check_vlim);

% Direction of change for generators
default_dir_var_gen = [];
check_dir_var_gen = @(x)(isempty(x) || (isnumeric(x) && iscolumn(x)));
addParameter(input_checker,'dir_var_gen',default_dir_var_gen,check_dir_var_gen);

% Generator numbers of the variable generators;
default_idx_var_gen = [];
check_idx_var_gen = @(x)(isempty(x) || (isnumeric(x) && iscolumn(x)));
addParameter(input_checker,'idx_var_gen',default_idx_var_gen,check_idx_var_gen);

% Parse
input_checker.KeepUnmatched = true;
parse(input_checker,varargin{:});
options = input_checker.Results;

%% CHECKS
% Check whether the number of directions of load increases is equal to the
% number of buses
if size(mpc.bus,1) ~= length(dir_mll)
    error_msg = ['The number of directions of load increases ' ...
        'is not equal to the number of buses'];
    error(error_msg);
end

% Check whether load increases have been defined for zero loads
idx_zero_loads = mpc.bus(:,PD) == 0;
if sum(dir_mll(idx_zero_loads))>0
    error('Directions of load increases cannot be defined for zero loads.');
end

% Check whether the number of variable generators is equal to the number of
% elements in the direction of change of generators
if size(options.idx_var_gen,1) ~= size(options.dir_var_gen,1)
    error('The number of variable generators does not match the direction vector.');
end

% Make sure that the slack bus is not included among the variable
% generators
[ref_init, ~] = bustypes(mpc.bus, mpc.gen);
idx_gen_slack = find(mpc.gen(1:n_gen,GEN_BUS) == ref_init);
if sum(ismember(options.idx_var_gen,idx_gen_slack)) ~= 0
    error('The direction vector cannot include changes at the slack bus');
end

%% Preparation of the case mpc_vl
% Initialise with a power flow with q-lims considered
mpopt = mpoption('pf.enforce_q_lims', options.use_qlim,'verbose',0,'out.all',0);
mpc = runpf(mpc,mpopt);
% Reset the bus types after the power flow
mpc.bus(:,BUS_TYPE) = mpc0.bus(:,BUS_TYPE);
% Convert all loads to dispatchable
mpc_vl = load2disp(mpc);

% Extract the part of dir_mll corresponding to nonzero loads
dir_mll = dir_mll(mpc.bus(:, PD) > 0);

% Add a field to mpc_vl for the load increase
mpc_vl.dir_mll = dir_mll;

% Create a vector with the direction for the variable generators with as
% many elements as the number of gens + number of sheddable loads
% (necessary for conversion to internal indexing).
dir_var_gen_all = sparse(options.idx_var_gen,1,options.dir_var_gen,...
    size(mpc_vl.gen,1),1);
% Add a field for the generators
mpc_vl.dir_var_gen = options.dir_var_gen;
mpc_vl.idx_var_gen = options.idx_var_gen;
mpc_vl.dir_var_gen_all = dir_var_gen_all;

% Adjust the Pmin of dispatchable loads to make them negative enough so
% that the max load lim can be found
idx_vl = isload(mpc_vl.gen);
mpc_vl.gen(idx_vl,PMIN) = 300*mpc_vl.gen(idx_vl,PMIN);
% Adjust Qmin so that Qmin/Pmin is the power factor of the load, if
% inductive, and change Qmax if the load is capacitive
idx_vl_inductive = idx_vl & mpc_vl.gen(:,QMAX) == 0;
idx_vl_capacitive = idx_vl & mpc_vl.gen(:,QMIN) == 0;
tanphi_vl_ind = mpc_vl.gen(idx_vl_inductive,QG)./mpc_vl.gen(idx_vl_inductive,PG);
tanphi_vl_cap = mpc_vl.gen(idx_vl_capacitive,QG)./mpc_vl.gen(idx_vl_capacitive,PG);
mpc_vl.gen(idx_vl_inductive,QMIN) = mpc_vl.gen(idx_vl_inductive,PMIN).*tanphi_vl_ind;
mpc_vl.gen(idx_vl_capacitive,QMAX) = mpc_vl.gen(idx_vl_capacitive,PMIN).*tanphi_vl_cap;
% Make the cost zero
mpc_vl.gencost(:,COST:end) = 0;
% Make the non variable generators not dispatchable
% Note, we look only for the real PV buses, i.e. we do not consider the
% dispatchable loads in this search. Hence the search over 1:n_gen
[ref, pv, pq] = bustypes(mpc_vl.bus, mpc_vl.gen);
idx_gen_pv = find(ismember(mpc_vl.gen(1:n_gen,GEN_BUS),pv));
% Note we filter out non variable generators with nonzero direction of
% increase from the pv buses
idx_non_var_pv = setdiff(idx_gen_pv,options.idx_var_gen(options.dir_var_gen~=0));
mpc_vl.gen(idx_non_var_pv,PMIN) = mpc_vl.gen(idx_non_var_pv,PG);
mpc_vl.gen(idx_non_var_pv,PMAX) = mpc_vl.gen(idx_non_var_pv,PG);
% Raise the flow limits so that they are not binding
mpc_vl.branch(:,RATE_A) = 9999;%1e5;
% Raise the slack bus limits so that they are not binding
idx_gen_slack = find(mpc_vl.gen(1:n_gen,GEN_BUS) == ref);
mpc_vl.gen(idx_gen_slack,[QMAX,PMAX]) = 9999;
% Decrease the slack bus limits so that they are not binding
mpc_vl.gen(idx_gen_slack,[QMIN,PMIN]) = -9999;
% Change the voltage constraints of the PQ buses so that they are not 
% binding
mpc_vl.bus(pq,VMIN) = 0.01;
mpc_vl.bus(pq,VMAX) = 10;
% Lock the voltages of the slack bus
mpc_vl.bus(ref,VMAX) = mpc_vl.gen(idx_gen_slack(1),VG);
mpc_vl.bus(ref,VMIN) = mpc_vl.gen(idx_gen_slack(1),VG);
% Put Vmax = Vset and low Vmin for all pv buses
for bb = 1:length(pv)
    idx_gen_at_bb = find(ismember(mpc_vl.gen(1:n_gen,GEN_BUS),pv(bb)));
    mpc_vl.bus(pv(bb),VMAX) = mpc_vl.gen(idx_gen_at_bb(1),VG);
    mpc_vl.bus(pv(bb),VMIN) = 0.01;
%     mpc_vl.bus(pv(bb),VMAX) = mpc_vl.gen(idx_gen_at_bb(1),VG);
%     mpc_vl.bus(pv(bb),VMIN) = mpc_vl.gen(idx_gen_at_bb(1),VG);
end
% If we do not consider Qlim, increase Qmax and decrease Qmin 
% of all generators to arbitrarily large values 
if ~options.use_qlim
    mpc_vl.gen(idx_gen_pv,QMAX) = 9999;
    mpc_vl.gen(idx_gen_pv,QMIN) = -9999;
    for bb = 1:length(pv)
        idx_gen_at_bb = find(ismember(mpc_vl.gen(1:n_gen,GEN_BUS),pv(bb)));
        mpc_vl.bus(pv(bb),VMAX) = mpc_vl.gen(idx_gen_at_bb(1),VG);
        mpc_vl.bus(pv(bb),VMIN) = mpc_vl.gen(idx_gen_at_bb(1),VG);
    end
end
if ~isempty(options.Vlims_bus_nb)
    idx_gen_vlim = find(ismember(mpc_vl.gen(:,GEN_BUS),options.Vlims_bus_nb));
    mpc_vl.bus(options.Vlims_bus_nb,VMAX) = mpc_vl.gen(idx_gen_vlim,VG);
    mpc_vl.bus(options.Vlims_bus_nb,VMIN) = mpc_vl.gen(idx_gen_vlim,VG);
end

% Convert external to internal indexing
mpc_vl = add_userfcn(mpc_vl, 'ext2int', @userfcn_direction_mll_ext2int);
% Build the constraint for enforcing the direction of load increase
mpc_vl = add_userfcn(mpc_vl, 'formulation', @userfcn_direction_mll_formulation);
