function [Pbus,Qbus] = sgvm_calc_injection_delta(mpc, opt)
%SGVM_CALC_INJECTION_DELTA calculate desired bus injection change
%   [PBUS,QBUS] = SGVM_CALC_INJECTION_DELTA(MPC, OPT)
%
%   Determine changes in real and reactive bus injections to satisfy
%   flow and voltage constraints given a linearized model at the
%   operating point.
%   Each output is a structure with fields, 'old' and 'new' where
%   'old' is the original injection and 'new is the desired injection.
%   the difference, dP or dQ, calculated here is 'new' - 'old'.
%   Note: outputs are in per unit.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

%% problem setup
define_constants;
prob = struct();

if isfield(opt.vm.nodeperm, 'nox')
    nox = opt.vm.nodeperm.nox;
else
    nox = true;
end

if isfield(opt.vm.nodeperm, 'usedv')
    usedv = opt.vm.nodeperm.usedv;
else
    usedv = false;
end

if isfield(opt.vm.nodeperm, 'branch_slack')
    branch_slack = opt.vm.nodeperm.branch_slack;
else
    branch_slack = false;
end

if isfield(opt.vm.nodeperm, 'scale_s')
    scale_s = opt.vm.nodeperm.scale_s;
else
    scale_s = 1;
end

nb = size(mpc.bus,1);
nl = size(mpc.branch,1);

%% get some constants
if usedv
    % calculate derivatives at operating point
    Ybus = makeYbus(mpc);
    V = mpc.bus(:,VM).*exp(1i*mpc.bus(:,VA)*pi/180);
    [~, dsbus_dvm] = dSbus_dV(Ybus,V);
    Jpv = real(dsbus_dvm);
    Jqv = imag(dsbus_dvm);
    clear dsbus_dvm;

    % threshold a bit
    Jpv(abs(Jpv) < 1e-6) = 0;
    Jqv(abs(Jqv) < 1e-6) = 0;

    [rjpv, cjpv, vjpv] = find(Jpv);
    [rjqv, cjqv, vjqv] = find(Jqv);
    clear Jpv Jqv;

    V0 = abs(V);
    Vmin = mpc.bus(:,VMIN);
    Vmax = mpc.bus(:,VMAX);
end
Sbus  = makeSbus(mpc.baseMVA, mpc.bus, mpc.gen);
dPmax = max(real(Sbus)) - min(real(Sbus));
dQmax = max(imag(Sbus)) - min(imag(Sbus));
wsv   = max(abs(Sbus)); % weight for violating voltage constraints

% line flows
Pl0 = mpc.branch(:,PF) / mpc.baseMVA;
Ql0 = mpc.branch(:,QF) / mpc.baseMVA;
Smax = scale_s * mpc.branch(:,RATE_A) / mpc.baseMVA;
wspq = nb*max(Smax);

% set Smax for lines with Smax = 0 to a relatively large number
Smax(Smax == 0) = 5*max(Smax);

% angle flows
alpha = atan(Ql0./Pl0);
alpha(Pl0 < 0) = pi - alpha(Pl0 < 0 );
%%
% only consider lines that are loaded at more than half of their rating
lfrac = sort(sqrt(Pl0.^2 + Ql0.^2)./Smax, 'descend');
if (nl < 1000) || (lfrac(1000) < 0.5)
    nluse = find(sqrt(Pl0.^2 + Ql0.^2)./Smax > 0.5);
else
    nluse = find(sqrt(Pl0.^2 + Ql0.^2)./Smax > 0.75);
end
nl    = length(nluse);

% calculate sensitivities at currrent operating point
tptdf = tic;
H = sgvm_acptdf(mpc, nluse);
[rxpp, cxpp, vxpp] = find(H(1:nl, 1:nb));
[rxqp, cxqp, vxqp] = find(H(1:nl, nb + 1: 2*nb));
[rxpq, cxpq, vxpq] = find(H(nl+1:end, 1:nb));
[rxqq, cxqq, vxqq] = find(H(nl+1:end, nb + 1: 2*nb));
% [rxpp, cxpp, vxpp] = find(H(nluse, 1:nb));
% [rxqp, cxqp, vxqp] = find(H(nluse, nb + 1: 2*nb));
% [rxpq, cxpq, vxpq] = find(H(nl+nluse, 1:nb));
% [rxqq, cxqq, vxqq] = find(H(nl+nluse, nb + 1: 2*nb));
clear H;
if opt.vm.nodeperm.verbose > 1
    fprintf('\t   AC-PTDF time %0.3f sec\n', toc(tptdf));
end
% overwrite nl to be the number of considered branches
% nl    = length(nluse);
Smax  = Smax(nluse);
Pl0   = Pl0(nluse);
Ql0   = Ql0(nluse);
alpha = alpha(nluse);

% if ~usedv
%     x = sgvm_calc_injection_delta_greedy(...
%         struct('p', sparse(rxpp, cxpp, vxpp, nl, nb), 'q', sparse(rxqq, cxqq, vxqq, nl, nb)),...
%         struct('p', Pl0, 'q', Ql0), struct('p', dPmax, 'q', dQmax),...
%         struct('p', abs(Smax.*cos(alpha)), 'q', abs(Smax.*sin(alpha))));
%     Pbus = struct('old', real(Sbus), 'new', real(Sbus) + x.p);
%   Qbus = struct('old', imag(Sbus), 'new', imag(Sbus) + x.q);
%     return
% end
%% setup problem
tsetup = tic;
vars = struct('xp', struct('first', 1, 'last', nb),...
                  'xq', struct('first',nb+1, 'last',2*nb),...
                'absx', struct('first',2*nb+1, 'last',4*nb));
ptr = 4*nb;
if branch_slack
    vars.sp = struct('first', ptr+1, 'last', ptr+nl);
    ptr = ptr + nl;
    vars.sq = struct('first', ptr+1, 'last', ptr+nl);
    ptr = ptr + nl;
end
if usedv
    vars.dv = struct('first',ptr+1, 'last',ptr + nb);
    ptr = ptr + nb;
    vars.sv = struct('first', ptr+1, 'last', ptr+1);
    ptr = ptr + 1;
%     vars.sv = struct('first', ptr+1, 'last', ptr+nb);
%     ptr = ptr + nb;
%     vars = struct('xp', struct('first', 1, 'last', nb),...
%                   'xq', struct('first',nb+1, 'last',2*nb),...
%                 'dv', struct('first',2*nb+1, 'last',3*nb),...
%                 'absx', struct('first', 3*nb+1, 'last', 5*nb),...
%                 'sp', struct('first', 5*nb+1, 'last', 5*nb+nl),...
%                 'sq', struct('first', 5*nb+nl+1, 'last', 5*nb + 2*nl),...
%                 'sv', struct('first', 5*nb+ 2*nl + 1, 'last', 5*nb+ 2*nl + 1));
%     total_vars = 5*nb + 2*nl + 1;
% else
%     vars = struct('xp', struct('first', 1, 'last', nb),...
%                   'xq', struct('first',nb+1, 'last',2*nb),...
%                 'absx', struct('first', 2*nb+1, 'last', 4*nb),...
%                 'sp', struct('first', 4*nb+1, 'last', 4*nb+nl),...
%                 'sq', struct('first', 4*nb+nl+1, 'last', 4*nb + 2*nl));
%     total_vars = 4*nb + 2*nl;
end
total_vars = ptr;
prob.A  = [];
prob.l  = [];
prob.u  = [];
%% Form constraints
%% delta V to delta inj
% xp - Jpv*deltaV = 0
% xq - Jqv*deltaV = 0
% Ap  = sparse(1:nb, vars.xp.first:vars.xp.last, 1, nb, 2*nb);
% Aq  = sparse(1:nb, vars.xq.first:vars.xq.last, 1, nb, 2*nb);
% A   = [Ap, -Jpv, sparse(nb,total_vars - 3*nb);
%        Aq, -Jqv, sparse(nb,total_vars - 3*nb)];
% lb = zeros(2*nb,1);
% ub = zeros(2*nb,1);
% prob = update_Albub(prob, A, lb, ub);

if usedv
    if ~nox
        A = sparse([1:nb, rjpv.' ], ...
                   [vars.xp.first:vars.xp.last, vars.dv.first - 1 + cjpv.'],...
                   [ones(1,nb), vjpv.'], nb, total_vars);
        lb = zeros(nb, 1);
        ub = zeros(nb, 1);
        prob = update_Albub(prob, A, lb, ub);
    end

    A = sparse([1:nb, rjqv.' ], ...
               [vars.xq.first:vars.xq.last, vars.dv.first - 1 + cjqv.'],...
               [ones(1,nb), vjqv.'], nb, total_vars);
    lb = zeros(nb, 1);
    ub = zeros(nb, 1);
    prob = update_Albub(prob, A, lb, ub);
end
%% Change of voltage limits
% Vmin - V0 - s <= Delta V <= Vmax - V0 + s
% becomes
% Vmin - V0 <= DeltaV + s <= Inf
% -Inf <= DeltaV - s <= Vmax - V0

% Adv = sparse(1:nb, vars.dv.first:vars.dv.last, nb, vars.dv.last);
% A   = [Adv, sparse(nb,2*nb), ones(nb,1)];
if usedv
    A   = sparse([1:nb, 1:nb],...
        [vars.dv.first:vars.dv.last, vars.sv.first*ones(1,nb)],...
        [ones(1,nb), ones(1,nb)], nb, total_vars);
%     A   = sparse([1:nb, 1:nb],...
%         [vars.dv.first:vars.dv.last, vars.sv.first:vars.sv.last],...
%         [ones(1,nb), ones(1,nb)], nb, total_vars);
    lb  = Vmin - V0;
    lb(abs(lb) < 1e-6) = 0;
    ub  = Inf(nb,1);
    prob = update_Albub(prob, A, lb, ub);

    A   = sparse([1:nb, 1:nb],...
        [vars.dv.first:vars.dv.last, vars.sv.first*ones(1,nb)],...
        [ones(1,nb), -ones(1,nb)], nb, total_vars);
%      A   = sparse([1:nb, 1:nb],...
%         [vars.dv.first:vars.dv.last, vars.sv.first:vars.sv.last],...
%         [ones(1,nb), -ones(1,nb)], nb, total_vars);
    % A   = [Adv, sparse(nb,2*nb), -ones(nb,1)];
    lb  = -Inf(nb,1);
    ub  = Vmax - V0;
    ub(abs(ub) < 1e-6) = 0;
    prob = update_Albub(prob, A, lb, ub);
end
%% Line limits
% -|Smax*cos(alpha)| - sp <= Pl0 + Hp*x <= |Smax*cos(alpha)| + sp
% -|Smax*sin(alpha)| - sq <= Ql0 + Hq*x <= |Smax*sin(alpha)| + sq

% Ap = [H(1:nl,:), sparse(nl,total_vars - 2*nb)];
% Aq = [H(nl+1:2*nl,:), sparse(nl,total_vars - 2*nb)];

% -|Smax*cos(alpha)| - Pl0 <= Hp*x + sp <= Inf
r = rxpp.';
c = vars.xp.first - 1 + cxpp.';
v = vxpp.';
if ~nox
    r = [r, rxqp.'];
    c = [c, vars.xq.first - 1 + cxqp.'];
    v = [v, vxqp.'];
end
if branch_slack
    r = [r, 1:nl];
    c = [c, vars.sp.first:vars.sp.last];
    v = [v, ones(1,nl)];
end
A = sparse(r, c, v, nl, total_vars);
% if nox
%     A  = sparse( [rxpp.', 1:nl], ...
%         [vars.xp.first - 1 + cxpp.', vars.sp.first:vars.sp.last], ...
%         [vxpp.', ones(1,nl)],...
%         nl, total_vars);
% else
%     A  = sparse( [rxpp.', rxqp.', 1:nl], ...
%         [vars.xp.first - 1 + cxpp.', vars.xq.first - 1 + cxqp.', vars.sp.first:vars.sp.last], ...
%         [vxpp.', vxqp.', ones(1,nl)],...
%         nl, total_vars);
% end
lb = -abs(Smax.*cos(alpha)) - Pl0;
lb(abs(lb) < 1e-6) = 0;
ub = Inf(nl,1);
prob = update_Albub(prob, A, lb, ub);

% -Inf <= Hp*x - sp <= |Smax*cos(alpha)| - Pl0
r = rxpp.';
c = vars.xp.first - 1 + cxpp.';
v = vxpp.';
if ~nox
    r = [r, rxqp.'];
    c = [c, vars.xq.first - 1 + cxqp.'];
    v = [v, vxqp.'];
end
if branch_slack
    r = [r, 1:nl];
    c = [c, vars.sp.first:vars.sp.last];
    v = [v, -ones(1,nl)];
end
A = sparse(r, c, v, nl, total_vars);
% if nox
%     A  = sparse( [rxpp.', 1:nl], ...
%         [vars.xp.first - 1 + cxpp.', vars.sp.first:vars.sp.last], ...
%         [vxpp.', -ones(1,nl)],...
%         nl, total_vars);
% else
%     A  = sparse( [rxpp.', rxqp.', 1:nl], ...
%         [vars.xp.first - 1 + cxpp.', vars.xq.first - 1 + cxqp.', vars.sp.first:vars.sp.last], ...
%         [vxpp.', vxqp.', -ones(1,nl)],...
%         nl, total_vars);
% end
lb = -Inf(nl,1);
ub = abs(Smax.*cos(alpha)) - Pl0;
ub(abs(ub) < 1e-6) = 0;
prob = update_Albub(prob, A, lb, ub);

% -|Smax*sin(alpha)| - Ql0 <= Hq*x + sq <= Inf
r = rxqq.';
c = vars.xq.first - 1 + cxqq.';
v = vxqq.';
if ~nox
    r = [r, rxpq.'];
    c = [c, vars.xp.first - 1 + cxpq.'];
    v = [v, vxpq.'];
end
if branch_slack
    r = [r, 1:nl];
    c = [c, vars.sq.first:vars.sq.last];
    v = [v, ones(1,nl)];
end
A = sparse(r, c, v, nl, total_vars);
% if nox
%     A  = sparse( [rxqq.', 1:nl], ...
%         [vars.xq.first - 1 + cxqq.', vars.sq.first:vars.sq.last], ...
%         [vxqq.', ones(1,nl)],...
%         nl, total_vars);
% else
%     A  = sparse( [rxpq.', rxqq.', 1:nl], ...
%         [vars.xp.first - 1 + cxpq.', vars.xq.first - 1 + cxqq.', vars.sq.first:vars.sq.last], ...
%         [vxpq.', vxqq.', ones(1,nl)],...
%         nl, total_vars);
% end
lb = -abs(Smax.*sin(alpha)) - Ql0;
lb(abs(lb) < 1e-6) = 0;
ub = Inf(nl,1);
prob = update_Albub(prob, A, lb, ub);

% -Inf <= Hq*x - sq <= |Smax*sin(alpha)| - Ql0
r = rxqq.';
c = vars.xq.first - 1 + cxqq.';
v = vxqq.';
if ~nox
    r = [r, rxpq.'];
    c = [c, vars.xp.first - 1 + cxpq.'];
    v = [v, vxpq.'];
end
if branch_slack
    r = [r, 1:nl];
    c = [c, vars.sq.first:vars.sq.last];
    v = [v, -ones(1,nl)];
end
A = sparse(r, c, v, nl, total_vars);
% if nox
%     A  = sparse( [rxqq.', 1:nl], ...
%         [vars.xq.first - 1 + cxqq.', vars.sq.first:vars.sq.last], ...
%         [vxqq.', -ones(1,nl)],...
%         nl, total_vars);
% else
%     A  = sparse( [rxpq.', rxqq.', 1:nl], ...
%         [vars.xp.first - 1 + cxpq.', vars.xq.first - 1 + cxqq.', vars.sq.first:vars.sq.last], ...
%         [vxpq.', vxqq.', -ones(1,nl)],...
%         nl, total_vars);
% end
lb = -Inf(nl,1);
ub = abs(Smax.*sin(alpha)) - Ql0;
ub(abs(ub) < 1e-6) = 0;
prob = update_Albub(prob, A, lb, ub);

%% zero net change
% 1' * x_p = 0
% 1' * x_q = 0

A  = sparse(1,vars.xp.first:vars.xp.last, 1, 1, total_vars);
lb = 0;
ub = 0;
prob = update_Albub(prob, A, lb, ub);

A = sparse(1,vars.xq.first:vars.xq.last, 1, 1, total_vars);
lb = 0;
ub = 0;
prob = update_Albub(prob, A, lb, ub);

%% magnitude of x
% absx + x >= 0
% absx - x >= 0
A = sparse([1:2*nb,1:2*nb],...
    [vars.absx.first:vars.absx.last, vars.xp.first:vars.xp.last, vars.xq.first:vars.xq.last],...
    1, 2*nb, total_vars);
lb = zeros(2*nb,1);
ub = Inf(2*nb,1);
prob = update_Albub(prob, A, lb, ub);

A = sparse([1:2*nb,1:2*nb],...
    [vars.absx.first:vars.absx.last, vars.xp.first:vars.xp.last, vars.xq.first:vars.xq.last], ...
    [ones(1,2*nb), -ones(1,2*nb)], 2*nb, total_vars);
lb = zeros(2*nb,1);
ub = Inf(2*nb,1);
prob = update_Albub(prob, A, lb, ub);

%% variable limits
prob.xmin = -Inf(total_vars,1);
prob.xmin(vars.xp.first:vars.xp.last) = -dPmax;
prob.xmin(vars.xq.first:vars.xq.last) = -dQmax;
prob.xmin(vars.absx.first:vars.absx.last) = 0;
if branch_slack
    prob.xmin(vars.sp.first:vars.sp.last) = 0;
    prob.xmin(vars.sq.first:vars.sq.last) = 0;
end
if usedv
    prob.xmin(vars.sv.first:vars.sv.last) = 0;
end

prob.xmax = Inf(total_vars,1);
prob.xmax(vars.xp.first:vars.xp.last) = dPmax;
prob.xmax(vars.xq.first:vars.xq.last) = dQmax;
%% Linear  cost
% norm(x,1) + + wspq*sum(sp) + wspq*sum(sq) + wsv*sv
% norm(x,1) = sum(absx)
r = vars.absx.first:vars.absx.last;
v = ones(1, 2*nb);
if branch_slack
    r = [r, vars.sp.first:vars.sp.last, vars.sq.first:vars.sq.last];
    v = [v, wspq*ones(1,2*nl)];
end
if usedv
    r = [r, vars.sv.first:vars.sv.last];
    v = [v, wsv*ones(1, vars.sv.last-vars.sv.first+1)];
end
prob.c = sparse(r, 1, v, total_vars, 1);
% if usedv
%     prob.c = sparse([vars.absx.first:vars.absx.last, ...
%         vars.sp.first:vars.sp.last, vars.sq.first:vars.sq.last, vars.sv.first], 1, ...
%         [ones(1, 2*nb), wspq*ones(1,2*nl), wsv], total_vars, 1);
% else
%     prob.c = sparse([vars.absx.first:vars.absx.last, ...
%         vars.sp.first:vars.sp.last, vars.sq.first:vars.sq.last], 1, ...
%         [ones(1, 2*nb), wspq*ones(1,2*nl)], total_vars, 1);
% end
% prob.c = zeros(total_vars,1);
% prob.c(vars.absx.first:vars.absx.last) = 1;
% prob.c(vars.sv.first:vars.sv.last)     = wsv;

%% Quadratic cost
% no quadratic cost for this problem
% prob.H = sparse(total_vars,total_vars);

%% initial point
prob.x0 = zeros(total_vars,1);
if branch_slack
    prob.x0(vars.sp.first:vars.sp.last) = max(0, abs(Pl0) - abs(Smax.*cos(alpha)));
    prob.x0(vars.sq.first:vars.sq.last) = max(0, abs(Ql0) - abs(Smax.*sin(alpha)));
end
if usedv
    prob.x0(vars.sv.first) = max(0, max(max(Vmin - V0, V0 - Vmax)));
%     prob.x0(vars.sv.first:vars.sv.last) = max(0, max(Vmin - V0, V0 - Vmax));
end
if opt.vm.nodeperm.verbose > 1
    fprintf('\t   problem setup time %0.3f sec\n', toc(tsetup));
end
%% solve
tsolve = tic;
if opt.vm.nodeperm.verbose > 2
    prob.opt.verbose = opt.vm.nodeperm.verbose;
end
prob.opt.grb_opt.BarConvTol = 1e-4;
[x, f, eflag, output, lambda] = qps_matpower(prob);
if opt.vm.nodeperm.verbose > 1
    fprintf('\t   solve time %0.3f sec\n', toc(tsolve));
end
if eflag
    dPb = x(vars.xp.first:vars.xp.last);
    dQb = x(vars.xq.first:vars.xq.last);
    Pbus = struct('old', real(Sbus), 'new', real(Sbus) + dPb);
    Qbus = struct('old', imag(Sbus), 'new', imag(Sbus) + dQb);
else
    if ~branch_slack
        if opt.verbose > 0
            warning('sgvm_calc_injection_delta: optimization did not converge. Turning on branch slacks and retrying.')
        end
        opt.vm.nodeperm.branch_slack = true;
        [Pbus, Qbus] = sgvm_calc_injection_delta(mpc, opt);
    else
        error('sgvm_calc_injection_delta: optimization failed to converge.')
    end
end

function prob = update_Albub(prob, A, lb, ub)
% simple utility function for updating the constraint and bounds arrays.

prob.A  = [prob.A; A];
prob.l  = [prob.l; lb];
prob.u  = [prob.u; ub];
