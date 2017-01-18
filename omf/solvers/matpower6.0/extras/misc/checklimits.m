function [Fv, Pv, Qv, Vv] = checklimits(mpc, ac, quiet)
%CHECKLIMITS   Checks a solved power flow case for limit violations.
%
%   [FV, PV] = CHECKLIMITS(MPC)
%   [FV, PV, QV, VV] = CHECKLIMITS(MPC, AC)
%   [FV, PV, QV, VV] = CHECKLIMITS(MPC, AC, QUIET)
%
%   Inputs:
%       MPC : MATPOWER case struct
%       AC :  0 = check DC limits, real power flows, Pg limits
%             1 = check AC limits (includes |V|, Qg lims, MVA flows)
%       QUIET : 1 doesn't print anything, 0 prints results
%
%   Work-in-progress:   Currently only flow and real power generation limit
%                       checks are implemented.
%                       At this point, the code *is* the documentation.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

define_constants;
tol = 0.001;

%% input args
if nargin < 2
    ac = [];
    if nargin < 3
        quiet = 0;
    end
end

%% set default
if isempty(ac)
    if any(mpc.bus(:, VM) ~= 1)
        ac = 1;
    else
        ac = 0;
    end
end

%%-----  branch flows  -----
%% get flows
if ac
    Ff = sqrt(mpc.branch(:, PF).^2 + mpc.branch(:, QF).^2);
    Ft = sqrt(mpc.branch(:, PT).^2 + mpc.branch(:, QT).^2);
    F = max(Ff, Ft);
else
    F = abs(mpc.branch(:, PF));
end
%% find branch flow violations
Fv.i  = find(F > mpc.branch(:, RATE_A) + tol & mpc.branch(:, RATE_A) > 0);
Fv.ib = find(F > mpc.branch(:, RATE_B) + tol & mpc.branch(:, RATE_B) > 0);
Fv.ic = find(F > mpc.branch(:, RATE_C) + tol & mpc.branch(:, RATE_C) > 0);
%% absolute flow violations
Fv.v  = F(Fv.i)  - mpc.branch(Fv.i, RATE_A);
Fv.vb = F(Fv.ib) - mpc.branch(Fv.ib, RATE_B);
Fv.vc = F(Fv.ic) - mpc.branch(Fv.ic, RATE_C);
%% percentage flow violations
Fv.p  = 100 * Fv.v  ./ mpc.branch(Fv.i, RATE_A);
Fv.pb = 100 * Fv.vb ./ mpc.branch(Fv.ib, RATE_B);
Fv.pc = 100 * Fv.vc ./ mpc.branch(Fv.ic, RATE_C);
%% sort by percentage violation
[Fv.p,  k]  = sort(Fv.p,  'descend');
[Fv.pb, kb] = sort(Fv.pb, 'descend');
[Fv.pc, kc] = sort(Fv.pc, 'descend');
%% reorder indices, absolute violations
Fv.i  = Fv.i(k);
Fv.ib = Fv.ib(kb);
Fv.ic = Fv.ic(kc);
Fv.v  = Fv.v(k);
Fv.vb = Fv.vb(kb);
Fv.vc = Fv.vc(kc);

%%-----  generator real power  -----
Pg = mpc.gen(:, PG);
%% find Pmin and Pmax violations
Pv.i = find(Pg < mpc.gen(:, PMIN) - tol & mpc.gen(:, GEN_STATUS) > 0);
Pv.I = find(Pg > mpc.gen(:, PMAX) + tol & mpc.gen(:, GEN_STATUS) > 0);
%% absolute gen limit violations
Pv.v = mpc.gen(Pv.i, PMIN) - Pg(Pv.i);
Pv.V = Pg(Pv.I) - mpc.gen(Pv.I, PMAX);
%% percentage gen limit violations
Pv.p = 100 * Pv.v ./ max(abs(mpc.gen(Pv.i, PMIN)), abs(mpc.gen(Pv.i, PMAX)));
Pv.P = 100 * Pv.V ./ max(abs(mpc.gen(Pv.I, PMIN)), abs(mpc.gen(Pv.I, PMAX)));
%% sort by percentage violation
[Pv.p, k] = sort(Pv.p, 'descend');
[Pv.P, K] = sort(Pv.P, 'descend');
%% reorder indices, absolute violations
Pv.i  = Pv.i(k);
Pv.I  = Pv.I(K);
Pv.v  = Pv.v(k);
Pv.V  = Pv.V(K);

if ~quiet
    fprintf('\n');
    if isempty(Fv.ic)
        fprintf('No Branch Flow Emergency Rating Violations\n');
    else
        fprintf('Branch Flow Emergency Rating Violations\n');
        fprintf(' branch     from       to        flow        limit     violation  %% violation\n');
        fprintf('--------  --------  --------  ----------  ----------  ----------  ----------\n');
        for k = 1:length(Fv.ic);
            fprintf('%7d  %8d  %8d  %10.1f  %10.1f  %10.2f  %10.1f\n', Fv.ic(k), ...
                mpc.branch(Fv.ic(k), F_BUS), ...
                mpc.branch(Fv.ic(k), T_BUS), ...
                F(Fv.ic(k)), ...
                mpc.branch(Fv.ic(k), RATE_C), ...
                Fv.vc(k), ...
                Fv.pc(k) ...
            );
        end
    end
    if isempty(Fv.ib)
        fprintf('No Branch Flow Short Term Rating Violations\n');
    else
        fprintf('Branch Flow Short Term Rating Violations\n');
        fprintf(' branch     from       to        flow        limit     violation  %% violation\n');
        fprintf('--------  --------  --------  ----------  ----------  ----------  ----------\n');
        for k = 1:length(Fv.ib);
            fprintf('%7d  %8d  %8d  %10.1f  %10.1f  %10.2f  %10.1f\n', Fv.ib(k), ...
                mpc.branch(Fv.ib(k), F_BUS), ...
                mpc.branch(Fv.ib(k), T_BUS), ...
                F(Fv.ib(k)), ...
                mpc.branch(Fv.ib(k), RATE_B), ...
                Fv.vb(k), ...
                Fv.pb(k) ...
            );
        end
    end
    if isempty(Fv.i)
        fprintf('No Branch Flow Normal Rating Violations\n');
    else
        fprintf('Branch Flow Normal Rating Violations\n');
        fprintf(' branch     from       to        flow        limit     violation  %% violation\n');
        fprintf('--------  --------  --------  ----------  ----------  ----------  ----------\n');
        for k = 1:length(Fv.i);
            fprintf('%7d  %8d  %8d  %10.1f  %10.1f  %10.2f  %10.1f\n', Fv.i(k), ...
                mpc.branch(Fv.i(k), F_BUS), ...
                mpc.branch(Fv.i(k), T_BUS), ...
                F(Fv.i(k)), ...
                mpc.branch(Fv.i(k), RATE_A), ...
                Fv.v(k), ...
                Fv.p(k) ...
            );
        end
    end

    fprintf('\n');
    fprintf('Generator Limit Violations\n');
    if isempty(Pv.i)
        fprintf('No Pmin Violations\n');
    else
        fprintf('Pmin Violations\n');
        fprintf('  gen       bus        Pmin         Pg         Pmax     violation  %% violation\n');
        fprintf('--------  --------  ----------  ----------  ----------  ----------  ----------\n');
        for k = 1:length(Pv.i);
            fprintf('%7d  %8d  %10.1f  %10.1f  %10.1f  %10.2f  %10.1f\n', Pv.i(k), ...
                mpc.gen(Pv.i(k), GEN_BUS), ...
                mpc.gen(Pv.i(k), PMIN), ...
                Pg(Pv.i(k)), ...
                mpc.gen(Pv.i(k), PMAX), ...
                Pv.v(k), ...
                Pv.p(k) ...
            );
        end
    end
    if isempty(Pv.I)
        fprintf('No Pmax Violations\n');
    else
        fprintf('Pmax Violations\n');
        fprintf('  gen       bus        Pmin         Pg         Pmax     violation  %% violation\n');
        fprintf('--------  --------  ----------  ----------  ----------  ----------  ----------\n');
        for k = 1:length(Pv.I);
            fprintf('%7d  %8d  %10.1f  %10.1f  %10.1f  %10.2f  %10.1f\n', Pv.I(k), ...
                mpc.gen(Pv.I(k), GEN_BUS), ...
                mpc.gen(Pv.I(k), PMIN), ...
                Pg(Pv.I(k)), ...
                mpc.gen(Pv.I(k), PMAX), ...
                Pv.V(k), ...
                Pv.P(k) ...
            );
        end
    end
end
