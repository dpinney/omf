function results = postproc_maxloadlim(results,dir_mll)
% POSTPROC_MAXLOADLIM Performs some post processing on the results returned
% by the ACOPF run in MATPOWER.
%   RESULTS = POSTPROC_MAXLOADLIM(RESULTS,DIR_MLL) transforms the dispatchable
%   loads back to normal loads and parse the results in the struct RESULTS
%   to provide contextual information on the maximum loadability point
%   found in the direction of load increase defined by DIR_MLL. It returns
%   the updated struct RESULTS.

%   MATPOWER
%   Copyright (c) 2015-2016, Power Systems Engineering Research Center (PSERC)
%   by Camille Hamon
%
%   This file is part of MATPOWER/mx-maxloadlim.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-maxloadlim/ for more info.

define_constants;

% Transforming the dispatchable gen back to loads
idx_gen_load_disp = isload(results.gen);
idx_bus_load_disp = results.gen(idx_gen_load_disp,GEN_BUS);
results.bus(idx_bus_load_disp ,[PD QD]) = -results.gen(idx_gen_load_disp,[PG QG]);
results.gen(idx_gen_load_disp,:) = [];
results.gencost(idx_gen_load_disp,:) = [];
% Removing the shadow prices corresponding to dispatchable loads
results.var.mu.u.Pg(idx_gen_load_disp) = [];
results.var.mu.l.Pg(idx_gen_load_disp) = [];
results.var.mu.u.Qg(idx_gen_load_disp) = [];
results.var.mu.l.Qg(idx_gen_load_disp) = [];
% If all gens at bus have non zero reactive power shadow prices, this bus
% is PQ
for bb = 1:size(results.bus,1)
    gen_list_at_bb = results.gen(:,GEN_BUS) == bb;
    if all(results.var.mu.u.Qg(gen_list_at_bb)>0)
        results.bus(bb,BUS_TYPE) = PQ;
    end
end

% Create a new field for the stability margin in load increase
results.stab_marg = results.var.val.alpha;
% Create a new field for the stability margin in gen change
if isfield(results.var.val,'beta')
    results.gen_stab_marg = results.var.val.beta;
end

% Remove the cost for the printpf function to consider the results as load
% flow results.
results.f = [];
% Direction defined over all buses (not only over nonzero loads)
results.dir_mll = dir_mll;

% Determining the type of bifurcation (SNB or SLL)
% SLL is characterized by having both reactive power limit and voltage
% limit binding at one generator
shadow_price_Qg = results.var.mu.u.Qg;
shadow_price_Vm = results.var.mu.u.Vm;
% Map the shadow price of bus voltage magnitude to generators
shadow_price_Vg = shadow_price_Vm(results.gen(:,GEN_BUS));
idx_bus_sll = shadow_price_Qg & shadow_price_Vg;
if sum(idx_bus_sll) > 0
    results.bif.short_name = 'LIB';
    results.bif.full_name = 'limit-induced bifurcation';
    results.bif.gen_sll = find(idx_bus_sll);
else
    results.bif.short_name = 'SNB';
    results.bif.full_name = 'saddle-node bifurcation';
end
% Building the sets of gens that reached their Q lims and of gens that did
% not
gen_a = shadow_price_Vm(results.gen(:,GEN_BUS))~= 0;
gen_b = shadow_price_Qg ~= 0;
results.bif.gen_a = gen_a;
results.bif.gen_b = gen_b;
