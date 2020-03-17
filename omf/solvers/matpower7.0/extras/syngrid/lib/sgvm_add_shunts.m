function [out, bsh] = sgvm_add_shunts(mpc, mpopt, opt)
%SGVM_ADD_SHUNTS add shunt elements to MPC to satisfy voltage constraints
%   [OUT, BSH] = SGVM_ADD_SHUNTS(MPC)
%   [OUT, BSH] = SGVM_ADD_SHUNTS(MPC, MPOPT)
%   [OUT, BSH] = SGVM_ADD_SHUNTS(MPC, MPOPT, OPT)
%   [OUT, BSH] = SGVM_ADD_SHUNTS(MPC, [], OPT)

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if nargin < 3
    opt = struct();
    if nargin < 2
        % copy mpoptions from syngrid options
        mpopt = sg_options();
        mpopt = mpopt.mpopt;
    end
elseif isempty(mpopt)
    % copy mpoptions from syngrid options
    mpopt = sg_options();
    mpopt = mpopt.mpopt;
end
opt = opt_default(opt);
tmag = opt.tmag;
shift_in = opt.shift_in;
shunt_max = opt.shunt_max;
soft_ratea= opt.soft_ratea;
mpopt.opf.softlims.default = 0; %required for algorithm to work
%%
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;
[PW_LINEAR, POLYNOMIAL, MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;

nb = size(mpc.bus,1);
ng = size(mpc.gen,1);

if any(mpc.bus(:,BUS_I) ~= (1:nb)')
    error('sgvm_add_shunts: bus matrix needs to have consecutive bus numbering.')
end
out = mpc; %save output mpc before modifications
%% tighten voltage limits slightely
% hopefully helps avoid edge cases
mpc.bus(:,VMAX) = mpc.bus(:,VMAX) - shift_in;
mpc.bus(:,VMIN) = mpc.bus(:,VMIN) + shift_in;
%% add ficticious generators at each bus for VAr support

tmpgen = (1:nb)';
ngtmp  = nb;
new_gen = zeros(ngtmp, size(mpc.gen,2));
new_gen(:,[GEN_BUS, VG, MBASE, GEN_STATUS]) = [tmpgen, ones(ngtmp,1), mpc.baseMVA*ones(ngtmp,1), ones(ngtmp,1)];
mpc.gen = [mpc.gen; new_gen];

new_gencost = zeros(ngtmp, size(mpc.gencost,2));
new_gencost(:,[MODEL, NCOST, COST]) = [2*ones(ngtmp,1), 2*ones(ngtmp,1), zeros(ngtmp,1)];

mpc.gencost = [mpc.gencost; new_gencost];
if isfield(mpc, 'genfuel')
    mpc.genfuel = vertcat(mpc.genfuel, ...
            cellfun(@(x) 'other', num2cell(1:ngtmp), 'UniformOutput', 0).');
end
if isfield(mpc, 'gentype')
    mpc.gentype = vertcat(mpc.gentype, ...
            cellfun(@(x) 'OT', num2cell(1:ngtmp), 'UniformOutput', 0).');
end

%% softlimits
if isfield(mpc, 'softlims')
    mpc = rmfield(mpc, 'softlims');
end
if soft_ratea
    mpc.softlims.RATE_A.hl_mod = 'remove';
end
current_shunt = mpc.bus(:, BS);
qmax_lim = shunt_max - current_shunt;
idx = find(qmax_lim > 0);
mpc.softlims.QMAX   = struct('hl_mod', 'replace', 'idx', ng+idx, 'hl_val', qmax_lim(idx));%, 'cost', 100);

qmin_lim = current_shunt - shunt_max;
idx = find(qmin_lim < 0);
mpc.softlims.QMIN   = struct('hl_mod', 'replace', 'idx', ng+idx, 'hl_val', qmin_lim(idx));%, 'cost', 100);
%mpc.softlims.QMAX   = struct('hl_mod', 'replace', 'idx', (ng+1:ng+ngtmp)', 'hl_val',  shunt_max, 'cost', 100);
%mpc.softlims.QMIN   = struct('hl_mod', 'replace', 'idx', (ng+1:ng+ngtmp)', 'hl_val', -shunt_max, 'cost', 100);

%% solve opf
if ~toggle_softlims(mpc, 'status')
    mpc = toggle_softlims(mpc,'on');
end
r   = runopf(mpc,mpopt);

if ~r.success
  if ~isinf(shunt_max)
    warning('sgvm_add_shunts: OPF with Qg softlimits failed to converge. Removing shunt limits.')
    opt.shunt_max = Inf;
    [out, bsh] = sgvm_add_shunts(out, mpopt, opt);
    return
  elseif ~soft_ratea
    warning('sgvm_add_shunts: OPF with Qg softlimits failed to converge. Adding soft branch limits.')
    opt.soft_ratea = 1;
    [out, bsh] = sgvm_add_shunts(out, mpopt, opt);
    return
  end
  warning('sgvm_add_shunts: No possible solution found! (Inf shunt limits and branch limits attempted).')
  out = r;
  bsh = zeros(nb,1);
  return
end

if opt.verbose > 1
  fprintf('Result in sgvm_add_shunts:\n')
  printpf(r)
end
%% Convert generators to shunt elements
bsh = (r.softlims.QMAX.overload(ng+1:end) - r.softlims.QMIN.overload(ng+1:end))./r.bus(:,VM).^2;

% apply minimum magnitude threshold of tmag
mask = (abs(bsh) > 0) & (abs(bsh) < tmag);
bsh(mask) = sign(bsh(mask))*tmag;

%% add shunts to case
%out.bus(:,BS) = out.bus(:,BS) +  bsh;
r.bus(:,BS) = r.bus(:,BS) + bsh;

%% update out with power-flow results in r
out = update_out(out, r, ng);

%% utility functions
function opt = opt_default(opt)
%% setup default options
optdef = sgvm_shuntsopts();

if ~isempty(opt)
    opt = nested_struct_copy(optdef, opt);
else
    opt = optdef;
end

function out = update_out(out, r, ng)
%% update the output mpc case with the powerflow results in r
define_constants;

r.bus(:,[VMAX, VMIN] ) = out.bus(:,[VMAX, VMIN]);
r.gen = r.gen(1:ng,:);
r.gencost = r.gencost(1:ng, :);
out = r;
%%------ bus matrix -------------------
%out.bus(:,[VM,VA]) = r.bus(:,[VM, VA]);
%out.bus = [out.bus(:,1:13), r.bus(:, 14:end)];
%
%%------ branch matrix ---------------
%out.branch = [out.branch(:,1:13), r.branch(:,14:end)];
%
%%----- gen matrix ------------------
%out.gen(:,[PG,QG,VG]) = r.gen(1:ng, [PG,QG,VG]);
%out.gen = [out.gen(:,1:21), r.gen(1:ng, 22:end)];
