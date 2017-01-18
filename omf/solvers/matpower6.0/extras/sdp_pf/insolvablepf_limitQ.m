function [insolvable,eta,mineigratio] = insolvablepf_limitQ(mpc,mpopt)
%INSOLVABLEPF_LIMITQ A sufficient condition for power flow insolvability
%considering generator reactive power limits
%
%   [INSOLVABLE,VSLACK_MIN,SIGMA,ETA,MINEIGRATIO] =
%       INSOLVABLEPF_LIMITQ(MPC,MPOPT)
%
%   Evaluates a sufficient condition for insolvability of the power flow
%   equations considering generator reactive power limits. This function
%   uses a mixed-integer semidefinite programming formulation of the power
%   flow equations with generator reactive power limits that maximizes the
%   power injections in a uniform, constant power factor profile. eta
%   indicates the factor by which the power injections can be increased in
%   this profile. If eta < 1, no power flow solution exists that satisfies
%   the generator reactive power limits. The converse does not
%   necessarily hold; a power flow solution may not exist even for cases
%   that this function does not indicate are insolvable. See [1] for
%   further details.
%
%   Note that this function is only suitable for small systems due to the
%   computational requirements of the mixed-integer semidefinite
%   programming solver in YALMIP.
%
%   Inputs:
%       MPC : A MATPOWER case specifying the desired power flow equations.
%       MPOPT : A MATPOWER options struct. If not specified, it is
%           assumed to be the default mpoption.
%
%   Outputs:
%       INSOLVABLE : Binary variable. A value of 1 indicates that the
%           specified power flow equations are insolvable, while a value of
%           0 means that the insolvability condition is indeterminant (a
%           solution may or may not exist).
%       ETA : Power injection margin to the power flow solvability
%           boundary in the profile of a uniform, constant power factor
%           change in power injections.
%       MINEIGRATIO : A measure of satisfaction of the rank relaxation.
%           Large values indicate satisfaction. (Note that satisfaction of
%           the rank relaxation is not required for correctness of the
%           insolvability condition).
%
%   [1] D.K. Molzahn, V. Dawar, B.C. Lesieutre, and C.L. DeMarco, "Sufficient
%       Conditions for Power Flow Insolvability Considering Reactive Power
%       Limited Generators with Applications to Voltage Stability Margins,"
%       in Bulk Power System Dynamics and Control - IX. Optimization,
%       Security and Control of the Emerging Power Grid, 2013 IREP Symposium,
%       25-30 August 2013.

%   MATPOWER
%   Copyright (c) 2013-2016, Power Systems Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

if nargin < 2
    mpopt = mpoption;
end

mpc = loadcase(mpc);

% Unpack options
ignore_angle_lim    = mpopt.opf.ignore_angle_lim;
verbose             = mpopt.verbose;
ndisplay            = mpopt.sdp_pf.ndisplay;    %% Determine display frequency of diagonastic information

maxSystemSize = 57;
fixPVbusInjection = 0; % If equal to 1, don't allow changes in active power injections at PV buses.

if ~have_fcn('yalmip')
    error('insolvablepf_limitQ: The software package YALMIP is required to run insolvablepf_limitQ. See http://users.isy.liu.se/johanl/yalmip/');
end

% set YALMIP options struct in SDP_PF (for details, see help sdpsettings) 
sdpopts = yalmip_options([], mpopt);

% Change solver to YALMIP's branch-and-bound algorithm
sdpopts = sdpsettings(sdpopts,'solver','bnb','bnb.solver',sdpopts.solver);

if strcmp(sdpopts.solver, 'sedumi') || strcmp(sdpopts.solver,'sdpt3')
    sdpopts = sdpsettings(sdpopts,'solver','bnb');
end

%% define named indices into data matrices
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, ...
    TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST, ...
    ANGMIN, ANGMAX, MU_ANGMIN, MU_ANGMAX] = idx_brch;
[PW_LINEAR, POLYNOMIAL, MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;


%% Load mpc data

mpc = ext2int(mpc);

if toggle_dcline(mpc, 'status')
    error('insolvablepf_limitQ: DC lines are not implemented in insolvablepf');
end

nbus = size(mpc.bus,1);
ngen = size(mpc.gen,1);

if nbus > maxSystemSize
    error('insolvablepf_limitQ: System is too large (more than 57 buses) to solve with insolvablepf_limitQ');
end

if ~ignore_angle_lim && (any(mpc.branch(:,ANGMIN) ~= -360) || any(mpc.branch(:,ANGMAX) ~= 360))
    warning('insolvablepf_limitQ: Angle difference constraints are not implemented in SDP_PF. Ignoring angle difference constraints.');
end

% Some of the larger system (e.g., case2746wp) have generators 
% corresponding to buses that have bustype == PQ. Change these
% to PV buses.
for i=1:ngen
    busidx = find(mpc.bus(:,BUS_I) == mpc.gen(i,GEN_BUS));
    if isempty(busidx) || ~(mpc.bus(busidx,BUS_TYPE) == PV || mpc.bus(busidx,BUS_TYPE) == REF)
        mpc.bus(busidx,BUS_TYPE) = PV;
        if verbose >= 1
            warning('insolvablepf_limitQ: Bus %s has generator(s) but is listed as a PQ bus. Changing to a PV bus.',int2str(busidx));
        end
    end
end

% Buses may be listed as PV buses without associated generators. Change
% these buses to PQ.
for i=1:nbus
    if mpc.bus(i,BUS_TYPE) == PV
        genidx = find(mpc.gen(:,GEN_BUS) == mpc.bus(i,BUS_I), 1);
        if isempty(genidx)
            mpc.bus(i,BUS_TYPE) = PQ;
            if verbose >= 1
                warning('insolvablepf_limitQ: PV bus %i has no associated generator! Changing these buses to PQ.',i);
            end
        end
    end
end


Sbase = mpc.baseMVA;

% Create vectors of power injections and voltage magnitudes
Qd = mpc.bus(:,QD) / Sbase;
Qinj = -Qd;
Vmag = mpc.bus(:,VM);

Pd = mpc.bus(:,PD) / Sbase;
Pg = zeros(nbus,1);
Qmin = zeros(nbus,1);
Qmax = zeros(nbus,1);
for i=1:nbus
    genidx = find(mpc.gen(:,GEN_BUS) == i);
    if ~isempty(genidx)
        Pg(i) = sum(mpc.gen(genidx,PG)) / Sbase;
        Vmag(i) = mpc.gen(genidx(1),VG);
        Qmin(i) = sum(mpc.gen(genidx,QMIN)) / Sbase - Qd(i);
        Qmax(i) = sum(mpc.gen(genidx,QMAX)) / Sbase - Qd(i);
    end
end
Pinj = Pg - Pd;


%% Functions to build matrices

[Yk,Yk_,Mk,Ylineft,Ylinetf,Y_lineft,Y_linetf] = makesdpmat(mpc);

%% Create primal SDP variables

[junk1,uniqueGenIdx,junk2] = unique(mpc.gen(:,GEN_BUS));
mpc.gen = mpc.gen(uniqueGenIdx,:);
ngen = size(mpc.gen,1);

W = sdpvar(2*nbus,2*nbus);
eta = sdpvar(1,1);
constraints = [];

% Binary variables
yL = binvar(ngen,1);
yU = binvar(ngen,1);

% We need a number greater than any plausible value of V^2, but too large
% of a value causes numerical problems
bigM = 10*max(Vmag)^2; 

%% Build primal problem

for k=1:nbus
    
    if ~fixPVbusInjection
        % PQ and PV buses have uniform active power injection changes
        if mpc.bus(k,BUS_TYPE) == PQ || mpc.bus(k,BUS_TYPE) == PV
            constraints = [constraints; 
                trace(Yk(k)*W) == eta*Pinj(k)];
        end
    else
        % Alternatively, we can fix PV bus active power injections for a
        % different power injection profile.
        if mpc.bus(k,BUS_TYPE) == PQ 
            constraints = [constraints; 
                trace(Yk(k)*W) == eta*Pinj(k)];
        end
        if mpc.bus(k,BUS_TYPE) == PV
            constraints = [constraints; 
                trace(Yk(k)*W) == Pinj(k)];
        end    
    end
        
    % PQ buses have uniform reactive power injection changes
    if mpc.bus(k,BUS_TYPE) == PQ
            constraints = [constraints;
                trace(Yk_(k)*W) == eta*Qinj(k)];
    end
    
    % Mixed integer formulation for generator reactive power limits
    if mpc.bus(k,BUS_TYPE) == PV || mpc.bus(k,BUS_TYPE) == REF
        
        genidx = find(mpc.gen(:,GEN_BUS) == k,1);
        
        constraints = [constraints;
            trace(Yk_(k)*W) <= Qmin(k)*yL(genidx) + Qmax(k)*(1-yL(genidx));
            trace(Yk_(k)*W) >= Qmax(k)*yU(genidx) + Qmin(k)*(1-yU(genidx))];

        constraints = [constraints;
            trace(Mk(k)*W) >= Vmag(k)^2*(1-yU(genidx));
            trace(Mk(k)*W) <= Vmag(k)^2*(1-yL(genidx)) + bigM*(yL(genidx))];
        
        constraints = [constraints;
            yU(genidx) + yL(genidx) <= 1];
        
    end
    
    if verbose >= 2 && mod(k,ndisplay) == 0
        fprintf('SDP creation: Bus %i of %i\n',k,nbus);
    end
    
end % Loop through all buses

% Force at least one bus to supply reactive power balance
% genbuses = (mpc.bus(:,BUS_TYPE) == PV | mpc.bus(:,BUS_TYPE) == REF);
% constraints = [constraints;
%     sum(yL(genbuses)+yU(genbuses)) <= ngen - 1];
constraints = [constraints;
    sum(yL + yU) <= ngen - 1];

constraints = [constraints; W >= 0];



%% Solve the SDP

% Preserve warning settings
S = warning;

% Run sdp solver
sdpinfo = solvesdp(constraints, -eta, sdpopts);
warning(S);

if verbose >= 2
    fprintf('Solver exit message: %s\n',sdpinfo.info);
end


%% Calculate rank characteristics of the solution

evl = sort(eig(double(W)));
mineigratio = abs(evl(end) / evl(end-2));


%% Output results

eta = double(eta);
insolvable = eta < 1; % Is this right? I think it should be the other way around...
