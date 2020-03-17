function out = sgvm_minqflow(mpc, opt)
%SGVM_MINQFLOW minimize magintude of reactive flows by adding shunts
%   OUT = SGVM_MINQFLOW(MPC, OPT)
%
%   WARNING: NOT CURRENTLY USED

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

%% parse inputs
if nargin < 2
    mpopt = mpoption('opf.dc.solver', 'MIPS', 'opf.ac.solver', 'IPOPT', 'mips.step_control', 1);
    mpopt.out.all = 0;
    mpopt.verbose = 0;
    opt.limqflow = [];
%     dqmax         = 200/mpc.baseMVA;
%     percent_pick  = 0.1;
%     tmag          = 0.1; %default minimum shunt is  0.1 MW.
elseif ~isfield(opt, 'limqflow')
    mpopt        = opt.mpopt;
    opt.limqflow = [];
end
opt.limqflow = opt_default(opt.limqflow);
dqmax        = opt.limqflow.shunt_max/mpc.baseMVA;
percent_lines= opt.limqflow.percent_lines;
percent_pick = opt.limqflow.percent_pick;
tmag         = opt.limqflow.tmag;
%%
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, ...
    TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST, ...
    ANGMIN, ANGMAX, MU_ANGMIN, MU_ANGMAX] = idx_brch;
nb = size(mpc.bus,1);
nl = size(mpc.branch,1);
out = mpc;

%%
if QF > size(mpc.branch,2)
    % no solution in mpc try solving with softlimits
    if isfield(mpc, 'softlims')
        mpc = rmfield(mpc, 'softlims');
    end
    mpopt.opf.softlims.default = 0;
    mpc.softlims.RATE_A.hl_mod = 'remove';
    mpc.softlims.VMAX.hl_mod = 'remove';
    mpc.softlims.VMIN = struct('hl_mod', 'replace', 'hl_val', 0);
    if ~toggle_softlims(mpc, 'status')
        mpc = toggle_softlims(mpc,'on');
    end
    r = runopf(mpc,mpopt);
    if ~r.success
        error('sgvm_minqflow: could not solve OPF even after enabling soft limits.')
    end
    qold = r.branch(:,QF)/r.baseMVA;
    H    = sgvm_acptdf(r);
else
    qold = mpc.branch(:,QF)/mpc.baseMVA;
    H    = sgvm_acptdf(mpc);
end
%%
tmp = quantile(abs(qold), 1 - percent_lines);
nluse = find(abs(qold) > tmp);
% Hq   = H(nl+1:end,nb+1:end);
Hq   = H(nl+nluse,nb+1:end);
clear H;
nl    = length(nluse);
%% setup problem
vars = struct('qnew', (1:nl)', 'dqinj', (nl+1:nl+nb)', 'dqabs', (nl+nb+1:nl+2*nb)');
total_vars = nl + 2*nb;
%% constraints
% qnew - Hq*dqinj >= +qold
% qnew + Hq*dqinj >= -qold
% dqabs >= +dqinj ----> dqabs - dqinj >= 0
% dqabs >= -dqinj ----> dqabs + dqinj >= 0

%           dqnew         dqinj       dqabs
prob.A  = [speye(nl)    , -Hq       , sparse(nl,nb);
           speye(nl)    , +Hq       , sparse(nl,nb);
           sparse(nb,nl), -speye(nb), speye(nb)   ;
           sparse(nb,nl), +speye(nb), speye(nb)];
prob.l = [qold; -qold; zeros(2*nb,1)];
prob.u = Inf(2*nl + 2*nb,1);

%% cost
% objective: sum(qnew) + sum(dqabs)
prob.c = sparse([vars.qnew; vars.dqabs], 1, 1, total_vars,1);

%% variable limits
% qnew >= 0
% -dqmax <= dqinj <= dqmax
% dqabs >= 0
prob.xmin = [zeros(nl,1); -dqmax*ones(nb,1); zeros(nb,1)];
prob.xmax = [Inf(nl,1); dqmax*ones(nb,1); Inf(nb,1)];

%% solve
[x, f, eflag, output, lambda] = qps_matpower(prob);

if eflag
    dqinj = x(vars.dqinj)*mpc.baseMVA;
    dqabs = x(vars.dqabs)*mpc.baseMVA;
    
    % threshold number of shunts
    threshold = quantile(dqabs,1-percent_pick);
    dqinj(dqabs <= threshold) = 0;
    
    % apply minimum magnitude threshold of tmag
    % Note: there shouldn't be must since we already selected the largest
    % 10% shunts
    mask = (abs(dqinj) > 0) & (abs(dqinj) < tmag);
    dqinj(mask) = sign(dqinj(mask))*tmag;
    out.bus(:,BS) = out.bus(:,BS) + dqinj;
else
    error('sgvm_minqflow: optimization failed to converge.')
end

%% utility functions
function opt = opt_default(opt)
% setup default options
optdef = struct();
optdef.shunt_max     = 200;
optdef.percent_lines = 0.5; %consider the upper 50% of loaded lines
optdef.percent_pick  = 0.1;
optdef.tmag          = 0.1; %default minimum shunt is  0.1 MW.

if ~isempty(opt)
    opt = struct_compare(optdef, opt);
else
    opt = optdef;
end

function b = struct_compare(a, b)
% compares structure b to structure a.
% if b lacks a field in a it is added
% this is performed recursively, so if if a.x is a structure
% and b has field x, the the function is called on (a.x, b.x)
for f = fieldnames(a).'
    if ~isfield(b, f{:})
        b.(f{:}) = a.(f{:});
    elseif isstruct(a.(f{:}))
        b.(f{:}) = struct_compare(a.(f{:}), b.(f{:}));
    end
end
