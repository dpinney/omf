function insolvable = insolvablepfsos_limitQ(mpc,mpopt)
%INSOLVABLEPFSOS_LIMITQ A sufficient condition for power flow insolvability
%considering generator reactive power limits using sum of squares programming
%
%   [INSOLVABLE] = INSOLVABLEPFSOS_LIMITQ(MPC,MPOPT)
%
%   Uses sum of squares programming to generate an infeasibility 
%   certificate for the power flow equations considering reactive power
%   limited generators. An infeasibility certificate proves insolvability
%   of the power flow equations.
%
%   Note that absence of an infeasibility certificate does not necessarily
%   mean that a solution does exist (that is, insolvable = 0 does not imply
%   solution existence). See [1] for more details.
%
%   Note that only upper limits on reactive power generation are currently
%   considered.
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
%
%   [1] D.K. Molzahn, V. Dawar, B.C. Lesieutre, and C.L. DeMarco, "Sufficient
%       Conditions for Power Flow Insolvability Considering Reactive Power
%       Limited Generators with Applications to Voltage Stability Margins,"
%       in Bulk Power System Dynamics and Control - IX. Optimization,
%       Security and Control of the Emerging Power Grid, 2013 IREP Symposium,
%       25-30 August 2013.

%   MATPOWER
%   Copyright (c) 2013-2016 by Power System Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%   and Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

define_constants;

if nargin < 2
    mpopt = mpoption;
end

% Unpack options
ignore_angle_lim    = mpopt.opf.ignore_angle_lim;
verbose             = mpopt.verbose;

if ~have_fcn('yalmip')
    error('insolvablepfsos_limitQ: The software package YALMIP is required to run insolvablepfsos_limitQ. See http://users.isy.liu.se/johanl/yalmip/');
end

% set YALMIP options struct in SDP_PF (for details, see help sdpsettings) 
sdpopts = yalmip_options([], mpopt);

%% Load data

mpc = loadcase(mpc);
mpc = ext2int(mpc);

if toggle_dcline(mpc, 'status')
    error('insolvablepfsos_limitQ: DC lines are not implemented in insolvablepf');
end

if ~ignore_angle_lim && (any(mpc.branch(:,ANGMIN) ~= -360) || any(mpc.branch(:,ANGMAX) ~= 360))
    warning('insolvablepfsos_limitQ: Angle difference constraints are not implemented. Ignoring angle difference constraints.');
end

nbus = size(mpc.bus,1);
ngen = size(mpc.gen,1);

% Some of the larger system (e.g., case2746wp) have generators 
% corresponding to buses that have bustype == PQ. Change these
% to PV buses.
for i=1:ngen
    busidx = find(mpc.bus(:,BUS_I) == mpc.gen(i,GEN_BUS));
    if isempty(busidx) || ~(mpc.bus(busidx,BUS_TYPE) == PV || mpc.bus(busidx,BUS_TYPE) == REF)
        mpc.bus(busidx,BUS_TYPE) = PV;
        if verbose >= 1
            warning('insolvablepfsos_limitQ: Bus %s has generator(s) but is listed as a PQ bus. Changing to a PV bus.',int2str(busidx));
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
                warning('insolvablepfsos_limitQ: PV bus %i has no associated generator! Changing these buses to PQ.',i);
            end
        end
    end
end

pq = find(mpc.bus(:,2) == PQ);
pv = find(mpc.bus(:,2) == PV);
ref = find(mpc.bus(:,2) == REF);

refpv = sort([ref; pv]);
pvpq = sort([pv; pq]);

Y = makeYbus(mpc);
G = real(Y);
B = imag(Y);

% Make vectors of power injections and voltage magnitudes
S = makeSbus(mpc.baseMVA, mpc.bus, mpc.gen);
P = real(S);
Q = imag(S);

Vmag = zeros(nbus,1);
Vmag(mpc.gen(:,GEN_BUS)) = mpc.gen(:,VG);

% Determine the limits on the injected power at each bus
Qmax = 1e3*ones(length(refpv),1);
for i=1:length(refpv)
    genidx = find(mpc.gen(:,1) == refpv(i));
    Qmax(i) = (sum(mpc.gen(genidx,QMAX)) - mpc.bus(mpc.gen(genidx(1),1),QD)) / mpc.baseMVA;
%     Qmin(i) = (sum(mpc.gen(genidx,QMIN)) - mpc.bus(mpc.gen(genidx(1),1),QD)) / mpc.baseMVA;
end

% bigM = 1e2;

%% Create voltage variables
% We need a Vd and Vq for each bus

if verbose >= 2
    fprintf('Creating variables.\n');
end

Vd = sdpvar(nbus,1);
Vq = sdpvar(nbus,1);

% Variables for Q limits
% Vplus2 = sdpvar(ngen,1);
Vminus2 = sdpvar(ngen,1);
x = sdpvar(ngen,1);

% V = [1; Vd; Vq; Vplus2; Vminus2; x];
V = [1; Vd; Vq; Vminus2; x];

%% Create polynomials

if verbose >= 2
    fprintf('Creating polynomials.\n');
end

deg = 0;
sosdeg = 0;

% Polynomials for active power
for i=1:nbus-1
    [l,lc] = polynomial(V,deg,0);
    lambda(i) = l;
    clambda{i} = lc;
end

% Polynomials for reactive power
for i=1:length(pq)
    [g,gc] = polynomial(V,deg,0);
    gamma(i) = g;
    cgamma{i} = gc;
end

% Polynomial for reference angle
[delta, cdelta] = polynomial(V,deg,0);

% Polynomials for Qlimits
for i=1:length(refpv)
    [z,cz] = polynomial(V,deg,0);
    zeta{i}(1) = z;
    czeta{i}{1} = cz;

    [z,cz] = polynomial(V,deg,0);
    zeta{i}(2) = z;
    czeta{i}{2} = cz;
    
    [z,cz] = polynomial(V,deg,0);
    zeta{i}(3) = z;
    czeta{i}{3} = cz;
    
%     [z,cz] = polynomial(V,deg,0);
%     zeta{i}(4) = z;
%     czeta{i}{4} = cz;
    
    [s1,c1] = polynomial(V,sosdeg,0);
    [s2,c2] = polynomial(V,sosdeg,0);
%     [s3,c3] = polynomial(V,sosdeg,0);
%     [s4,c4] = polynomial(V,sosdeg,0);
%     [s5,c5] = polynomial(V,sosdeg,0);
    sigma{i}(1) = s1;
    csigma{i}{1} = c1;
    sigma{i}(2) = s2;
    csigma{i}{2} = c2;
%     sigma{i}(3) = s3;
%     csigma{i}{3} = c3;
%     sigma{i}(4) = s4;
%     csigma{i}{4} = c4;
%     sigma{i}(5) = s5;
%     csigma{i}{5} = c5;
end

%% Create power flow equation polynomials

if verbose >= 2
    fprintf('Creating power flow equations.\n');
end

% Make P equations
for k=1:nbus-1
    i = pvpq(k);
    
    % Take advantage of sparsity in forming polynomials
%     fp(k) = Vd(i) * sum(G(:,i).*Vd - B(:,i).*Vq) + Vq(i) * sum(B(:,i).*Vd + G(:,i).*Vq);
    
    y = find(G(:,i) | B(:,i));
    for m=1:length(y)
        if exist('fp','var') && length(fp) == k
            fp(k) = fp(k) + Vd(i) * (G(y(m),i)*Vd(y(m)) - B(y(m),i)*Vq(y(m))) + Vq(i) * (B(y(m),i)*Vd(y(m)) + G(y(m),i)*Vq(y(m)));
        else
            fp(k) = Vd(i) * (G(y(m),i)*Vd(y(m)) - B(y(m),i)*Vq(y(m))) + Vq(i) * (B(y(m),i)*Vd(y(m)) + G(y(m),i)*Vq(y(m)));
        end
    end

end

% Make Q equations
for k=1:length(pq)
    i = pq(k);
    
    % Take advantage of sparsity in forming polynomials
%     fq(k) = Vd(i) * sum(-B(:,i).*Vd - G(:,i).*Vq) + Vq(i) * sum(G(:,i).*Vd - B(:,i).*Vq);
    
    y = find(G(:,i) | B(:,i));
    for m=1:length(y)
        if exist('fq','var') && length(fq) == k
            fq(k) = fq(k) + Vd(i) * (-B(y(m),i)*Vd(y(m)) - G(y(m),i)*Vq(y(m))) + Vq(i) * (G(y(m),i)*Vd(y(m)) - B(y(m),i)*Vq(y(m)));
        else
            fq(k) = Vd(i) * (-B(y(m),i)*Vd(y(m)) - G(y(m),i)*Vq(y(m))) + Vq(i) * (G(y(m),i)*Vd(y(m)) - B(y(m),i)*Vq(y(m)));
        end
    end
end

% Make V equations
for k=1:length(refpv)
    i = refpv(k);
    fv(k) = Vd(i)^2 + Vq(i)^2;
end

% Generator reactive power limits
for k=1:length(refpv)
    i = refpv(k);
    
    % Take advantage of sparsity in forming polynomials
%     fq_gen(k) = Vd(i) * sum(-B(:,i).*Vd - G(:,i).*Vq) + Vq(i) * sum(G(:,i).*Vd - B(:,i).*Vq);
    
    y = find(G(:,i) | B(:,i));
    for m=1:length(y)
        if exist('fq_gen','var') && length(fq_gen) == k
            fq_gen(k) = fq_gen(k) + Vd(i) * (-B(y(m),i)*Vd(y(m)) - G(y(m),i)*Vq(y(m))) + Vq(i) * (G(y(m),i)*Vd(y(m)) - B(y(m),i)*Vq(y(m)));
        else
            fq_gen(k) = Vd(i) * (-B(y(m),i)*Vd(y(m)) - G(y(m),i)*Vq(y(m))) + Vq(i) * (G(y(m),i)*Vd(y(m)) - B(y(m),i)*Vq(y(m)));
        end
    end
end


%% Form the test polynomial

if verbose >= 2
    fprintf('Forming the test polynomial.\n');
end

sospoly = 1;

% Add active power terms
for i=1:nbus-1
    sospoly = sospoly + lambda(i) * (fp(i) - P(pvpq(i)));
end

% Add reactive power terms
for i=1:length(pq)
    sospoly = sospoly + gamma(i) * (fq(i) - Q(pq(i)));
end

% Add angle reference term
sospoly = sospoly + delta * Vq(ref);

% Generator reactive power limits
for k=1:length(refpv)
    i = refpv(k);
    
    % Both limits
%     sospoly = sospoly + zeta{k}(1) * (Vmag(i)^2 + Vplus2(k) - Vminus2(k) - fv(k));
%     sospoly = sospoly + zeta{k}(2) * (Vminus2(k) * x(k));
%     sospoly = sospoly + zeta{k}(3) * (Vplus2(k) * (Qmax(k)-Qmin(k)-x(k)));
%     sospoly = sospoly + zeta{k}(4) * (Qmax(k) - x(k) - fq_gen(k));
% 
%     sospoly = sospoly + sigma{k}(1) * Vplus2(k);
%     sospoly = sospoly + sigma{k}(2) * Vminus2(k);
%     sospoly = sospoly + sigma{k}(3) * x(k);
%     sospoly = sospoly + sigma{k}(4) * (Qmax(k) - Qmin(k) - x(k));
%     sospoly = sospoly + sigma{k}(5) * (bigM - Vplus2(k));
    
    % Only upper reactive power limits
    sospoly = sospoly + zeta{k}(1) * (Vmag(i)^2 - Vminus2(k) - fv(k));
    sospoly = sospoly + zeta{k}(2) * (Vminus2(k) * x(k));
    sospoly = sospoly + zeta{k}(3) * (Qmax(k) - x(k) - fq_gen(k));

    sospoly = sospoly + sigma{k}(1) * Vminus2(k);
    sospoly = sospoly + sigma{k}(2) * x(k);
end

sospoly = -sospoly;

%% Solve the SOS problem

if verbose >= 2
    fprintf('Solving the sum of squares problem.\n');
end

sosopts = sdpsettings(sdpopts,'sos.newton',1,'sos.congruence',1);

constraints = sos(sospoly);

pvec = cdelta(:).';

for i=1:length(lambda)
    pvec = [pvec clambda{i}(:).'];
end

for i=1:length(gamma)
    pvec = [pvec cgamma{i}(:).'];
end

for i=1:length(refpv)
    for k=1:length(czeta{i})
        pvec = [pvec czeta{i}{k}(:).'];
    end
    
    for k=1:length(csigma{i})
        pvec = [pvec csigma{i}{k}(:).'];
    end
    
    for k=1:length(csigma{i})
        constraints = [constraints; sos(sigma{i}(k))];
    end
end

% Preserve warning settings
S = warning;
if have_fcn('matlab', 'vnum') >= 8.006 && have_fcn('cplex', 'vnum') <= 12.006003
    warning('OFF', 'MATLAB:lang:badlyScopedReturnValue');
end

sol = solvesos(constraints,[],sosopts,pvec);

warning(S);

if verbose >= 2
    fprintf('Solver exit message: %s\n',sol.info);
end

if sol.problem
    % Power flow equations may have a solution
    insolvable = 0;
elseif sol.problem == 0
    % Power flow equations do not have a solution.
    insolvable = 1;
end
