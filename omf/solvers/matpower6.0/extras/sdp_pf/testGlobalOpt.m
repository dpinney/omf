function [globalopt,comp,Apsd] = testGlobalOpt(mpc,mpopt)
%TESTGLOABALOPT A sufficient condition for OPF global optimality
%
%   [GLOBALOPT,COMP,APSD] = TESTGLOBALOPT(MPC,MPOPT)
%
%   Evaluates a sufficient condition for global optimality of a solution to
%   an OPF problem based on the KKT conditions of a semidefinite relaxation
%   of the OPF problem. The guarantee of global optimality requires
%   satisfaction of the complementarity condition (trace(A*W) = 0) and the
%   positive semidefinite A matrix condition (A >= 0). Note that failure
%   to satisfy these conditions does not necessarily indicate that the
%   solution is not globally optimal, but satisfaction gurantees global
%   optimality. See [1] for further details.
%
%   Inputs:
%       MPC : A solved MATPOWER case (e.g., mpc = runopf(mpc,mpopt)).
%       MPOPT : The options struct used to solve the MATPOWER case. If not
%           specified, it is assumed to be the default mpoption.
%
%   Outputs:
%       GLOBALOPT : Flag indicating whether the complementarity condition
%           and positive semidefinite A matrix constraints are satisfied to
%           the tolerances specified in mpopt.
%       COMP : Value of the complementarity condition trace(A*W). A value
%           equal to zero within the tolerance sqrt(ZEROEVAL_TOL) satisfies
%           the complementarity condition.
%       APSD : Flag indicating if the A matrix is positive semidefinite to
%           within the tolerance of ZEROEVAL_TOL specified in mpopt.
%           Positive semidefiniteness is determined using a Cholesky
%           factorization.
%
%   Note that this function does not currently handle DC Lines or
%   angle-difference constraints. Piecewise-linear cost functions should
%   work, but were not extensively tested.
%
%   Note that tight solution tolerances are typically required for good
%   results.
%
%   Positive branch resistances are not required. However, enforcing a 
%   small branch resistance may result in better results. With a small 
%   minimum branch resistance, global optimality is confirmed for all test
%   cases up to and including the 118-bus system.
%
%
%   Example: Both the complementarity and positive semidefinite conditions
%   are satisfied for the IEEE 14-bus system.
%
%           define_constants;
%           mpc = loadcase('case14');
%           mpc.branch(:,BR_R) = max(mpc.branch(:,BR_R), 1e-4);
%           mpopt = mpoption('opf.ac.solver', 'MIPS', ...
%               'opf.violation', 1e-10, 'mips.gradtol', 1e-10, ...
%               'mips.comptol', 1e-10, 'mips.costtol', 1e-10);
%           results = runopf(mpc, mpopt);
%           [globalopt, comp, Apsd] = testGlobalOpt(results, mpopt)
%
% [1] D.K. Molzahn, B.C. Lesieutre, and C.L. DeMarco, "A Sufficient
%     Condition for Global Optimality of Solutions to the Optimal Power
%     Flow Problem," To appear in IEEE Transactions on Power Systems 
%     (Letters).

%   MATPOWER
%   Copyright (c) 2013-2016, Power Systems Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%   and Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% define named indices into data matrices
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, ...
    TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST, ...
    ANGMIN, ANGMAX, MU_ANGMIN, MU_ANGMAX] = idx_brch;
[PW_LINEAR, POLYNOMIAL, MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;

%% Load in options, give warnings

if nargin < 2
    mpopt = mpoption;
end

if nargin == 0
    error('testGlobalOpt: testGlobalOpt requires a solved optimal power flow problem.');
end

mpc = loadcase(mpc);
mpc = ext2int(mpc);

ignore_angle_lim    = mpopt.opf.ignore_angle_lim;
binding_lagrange    = mpopt.sdp_pf.bind_lagrange;   %% Tolerance for considering a Lagrange multiplier to indicae a binding constraint
zeroeval_tol        = mpopt.sdp_pf.zeroeval_tol;    %% Tolerance for considering an eigenvalue in LLeval equal to zero
comp_tol            = sqrt(zeroeval_tol);       %% Tolerance for considering trace(A*W) equal to zero

if size(mpc.bus,2) < LAM_P
    error('testGlobalOpt: testGlobalOpt requires a solved optimal power flow problem.');
end

if toggle_dcline(mpc, 'status')
    error('testGlobalOpt: DC lines are not implemented in testGlobalOpt');
end

nbus = size(mpc.bus,1);
Sbase = mpc.baseMVA;

if ~ignore_angle_lim && (any(mpc.branch(:,ANGMIN) ~= -360) || any(mpc.branch(:,ANGMAX) ~= 360))
    warning('testGlobalOpt: Angle difference constraints are not implemented in testGlobalOpt. Ignoring angle difference constraints.');
end


%% Create matrices

[Yk,Yk_,Mk,Ylineft,Ylinetf,Y_lineft,Y_linetf] = makesdpmat(mpc);

%% Form the A matrix

lambda = mpc.bus(:,LAM_P)*Sbase;
gamma = mpc.bus(:,LAM_Q)*Sbase;

% Convert voltage Lagrange multiplier to be in terms of voltage squared
% dLdV^2 * dV^2dV = dLdV --> dLdV^2 = dLdV / (2*V)
mu_V = mpc.bus(:,MU_VMAX) - mpc.bus(:,MU_VMIN);
mu = mu_V ./ (2*mpc.bus(:,VM));

A = sparse(2*nbus,2*nbus);

% Add bus terms
for k=1:nbus
    A = A + lambda(k)*Yk(k) + gamma(k)*Yk_(k) + mu(k)*Mk(k);
end

% Add branch terms
Pft = mpc.branch(:,PF) / Sbase;
Ptf = mpc.branch(:,PT) / Sbase;
Qft = mpc.branch(:,QF) / Sbase;
Qtf = mpc.branch(:,QT) / Sbase;
Sft = sqrt(Pft.^2 + Qft.^2);
Stf = sqrt(Ptf.^2 + Qtf.^2);

dLdSft = mpc.branch(:,MU_SF) * Sbase;
dLdStf = mpc.branch(:,MU_ST) * Sbase;

dLdSft_over_Sft = dLdSft ./ (Sft);
dLdStf_over_Stf = dLdStf ./ (Stf);
dLdPft = Pft .* dLdSft_over_Sft;
dLdQft = Qft .* dLdSft_over_Sft;
dLdPtf = Ptf .* dLdStf_over_Stf;
dLdQtf = Qtf .* dLdStf_over_Stf;

binding_branches_ft = find(abs(dLdSft) > binding_lagrange);
binding_branches_tf = find(abs(dLdStf) > binding_lagrange);

if ~isempty(binding_branches_ft)
    for ft_idx=1:length(binding_branches_ft)
        k = binding_branches_ft(ft_idx);
        if strcmp(upper(mpopt.opf.flow_lim), 'S')       % apparent power limits
            
            A = A + dLdPft(k)*Ylineft(k) ...
                  + dLdQft(k)*Y_lineft(k);
        elseif strcmp(upper(mpopt.opf.flow_lim), 'P')   % active power limits
            % Active power Lagrange multipliers are stored in mpc.branch(:,MU_SF)
            % No need for conversion
            
            A = A + dLdSft(k) * Ylineft(k);

        else
            error('testGlobalOpt: Only ''S'' and ''P'' options are currently implemented for MPOPT.opf.flow_lim\n');
        end
    end
end

if ~isempty(binding_branches_tf)
    for tf_idx=1:length(binding_branches_tf)
        k = binding_branches_tf(tf_idx);
        if strcmp(upper(mpopt.opf.flow_lim), 'S')       % apparent power limits

            A = A + dLdPtf(k)*Ylinetf(k) ...
                  + dLdQtf(k)*Y_linetf(k);

        elseif strcmp(upper(mpopt.opf.flow_lim), 'P')   % active power limits
            % Active power Lagrange multipliers are stored in mpc.branch(:,MU_SF)
            % No need for conversion

            A = A + dLdStf(k) * Ylinetf(k);

        else
            error('testGlobalOpt: Only ''S'' and ''P'' options are currently implemented for MPOPT.opf.flow_lim\n');
        end

    end
end

%% Calculate trace(A*W)

V = mpc.bus(:,VM).*(cos(mpc.bus(:,VA)*pi/180)+1i*sin(mpc.bus(:,VA)*pi/180));
x = [real(V); imag(V)];

comp = 0;

[Arow,Acol,Aval] = find(A);

for i=1:length(Aval)
    comp = comp + Aval(i)*x(Arow(i))*x(Acol(i));
end


%% Determine if A is psd using a Cholesky decomposition

Abar = A + zeroeval_tol*speye(size(A));
per = amd(Abar);
[junk, p] = chol(Abar(per,per));

Apsd = p == 0;

%% Calculate globalopt flag

if Apsd && abs(comp) < comp_tol
    globalopt = 1;
else
    globalopt = 0;
end
