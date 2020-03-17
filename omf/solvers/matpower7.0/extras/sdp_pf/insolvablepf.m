function [insolvable,Vslack_min,sigma,eta,mineigratio] = insolvablepf(mpc,mpopt)
%INSOLVABLEPF A sufficient condition for power flow insolvability
%
%   [INSOLVABLE,VSLACK_MIN,SIGMA,ETA,MINEIGRATIO] = INSOLVABLEPF(MPC,MPOPT)
%
%   Evaluates a sufficient condition for insolvability of the power flow
%   equations. The voltage at the slack bus is minimized (with 
%   proportional changes in voltage magnitudes at PV buses) using a 
%   semidefinite programming relaxation of the power flow equations. If the
%   minimum achievable slack bus voltage is greater than the specified slack
%   bus voltage, no power flow solutions exist. The converse does not
%   necessarily hold; a power flow solution may not exist for cases
%   where the output insolvable is equal to 0. See [1] and [2] for further
%   details.
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
%       VSLACK_MIN : Minimum possible slack voltage obtained from the
%           semidefinite programming relaxation. The power flow equations
%           are insolvable if Vslack_min > V0, where V0 is the specified
%           voltage at the slack bus.
%       SIGMA : Controlled voltage margin to the power flow solvability
%           boundary.
%       ETA : Power injection margin to the power flow solvability
%           boundary in the profile of a uniform, constant power factor
%           change in power injections.
%       MINEIGRATIO : A measure of satisfaction of the rank relaxation.
%           Large values indicate satisfaction. (Note that satisfaction of
%           the rank relaxation is not required for correctness of the
%           insolvability condition).
%
%   Note that this function uses a matrix completion decomposition and is
%   therefore suitable for large systems. 
%
% [1] D.K. Molzahn, B.C. Lesieutre, and C.L. DeMarco, "A Sufficient Condition
%     for Power Flow Insolvability with Applications to Voltage Stability
%     Margins," IEEE Transactions on Power Systems, vol. 28, no. 3,
%     pp. 2592-2601, August 2013.
%
% [2] D.K. Molzahn, B.C. Lesieutre, and C.L. DeMarco, "A Sufficient Condition 
%     for Power Flow Insolvability with Applications to Voltage Stability 
%     Margins," University of Wisconsin-Madison Department of Electrical
%     and Computer Engineering, Tech. Rep. ECE-12-01, 2012, [Online]. 
%     Available: https://arxiv.org/abs/1204.6285.

%   MATPOWER
%   Copyright (c) 2013-2019, Power Systems Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%   and Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER/mx-sdp_pf.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-sdp_pf/ for more info.

if nargin < 2
    mpopt = mpoption;
end

%% define undocumented MATLAB function ismembc() if not available (e.g. Octave)
if exist('ismembc')
    ismembc_ = @ismembc;
else
    ismembc_ = @ismembc_octave;
end

mpc = loadcase(mpc);
mpc = ext2int(mpc);

% Unpack options
ignore_angle_lim    = mpopt.opf.ignore_angle_lim;
verbose             = mpopt.verbose;
enforce_Qlimits     = mpopt.pf.enforce_q_lims;
maxNumberOfCliques  = mpopt.sdp_pf.max_number_of_cliques;   %% Maximum number of maximal cliques
ndisplay            = mpopt.sdp_pf.ndisplay;        %% Determine display frequency of diagonastic information
cholopts.dense      = mpopt.sdp_pf.choldense;       %% Cholesky factorization options
cholopts.aggressive = mpopt.sdp_pf.cholaggressive;  %% Cholesky factorization options

if enforce_Qlimits > 0
    enforce_Qlimits = 1;
end

if ~have_fcn('yalmip')
    error('insolvablepf: The software package YALMIP is required to run insolvablepf. See https://yalmip.github.io');
end

% set YALMIP options struct in SDP_PF (for details, see help sdpsettings) 
sdpopts = yalmip_options([], mpopt);

%% Handle generator reactive power limits
% If no generator reactive power limits are specified, use this code
% directly. If generator reactive power limits are to be enforced, use the
% mixed integer semidefinite programming code. This code is only applicable
% for small systems (the 57-bus system is really pushing the limits)

if enforce_Qlimits
    if verbose > 0
        fprintf('Generator reactive power limits are enforced. Using function insolvablepf_limitQ.\n');
    end
    [insolvable,eta,mineigratio] = insolvablepf_limitQ(mpc,mpopt);
    Vslack_min = nan;
    sigma = nan;
    return;
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
if isfield(mpc, 'userfcn') && length(mpc.userfcn) > 0 && ...
        isfield(mpc.userfcn, 'formulation')
    c = cellfun(@func2str, {mpc.userfcn.formulation.fcn}, 'UniformOutput', 0);
    if strfind(strcat(c{:}), 'userfcn_dcline_formulation')
        error('insolvablepf: DC lines are not implemented in insolvablepf');
    end
end

if toggle_dcline(mpc, 'status')
    error('insolvablepf: DC lines are not implemented in insolvablepf');
end

nbus = size(mpc.bus,1);
ngen = size(mpc.gen,1);
nbranch = size(mpc.branch,1);

if ~ignore_angle_lim && (any(mpc.branch(:,ANGMIN) ~= -360) || any(mpc.branch(:,ANGMAX) ~= 360))
    warning('insolvablepf: Angle difference constraints are not implemented in SDP_PF. Ignoring angle difference constraints.');
end

% Some of the larger system (e.g., case2746wp) have generators 
% corresponding to buses that have bustype == PQ. Change these
% to PV buses.
for i=1:ngen
    busidx = find(mpc.bus(:,BUS_I) == mpc.gen(i,GEN_BUS));
    if isempty(busidx) || ~(mpc.bus(busidx,BUS_TYPE) == PV || mpc.bus(busidx,BUS_TYPE) == REF)
        mpc.bus(busidx,BUS_TYPE) = PV;
        if verbose >= 1
            warning('insolvablepf: Bus %s has generator(s) but is listed as a PQ bus. Changing to a PV bus.',int2str(busidx));
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
                warning('insolvablepf: PV bus %i has no associated generator! Changing these buses to PQ.',i);
            end
        end
    end
end



%% Determine Maximal Cliques
%% Step 1: Cholesky factorization to obtain chordal extension
% Use a minimum degree permutation to obtain a sparse chordal extension.

if maxNumberOfCliques ~= 1
    [Ainc] = makeIncidence(mpc.bus,mpc.branch);
    sparsity_pattern = abs(Ainc.'*Ainc) + eye(nbus,nbus);
    per = amd(sparsity_pattern,cholopts);
    [Rchol,p] = chol(sparsity_pattern(per,per),'lower');

    if p ~= 0
        error('insolvablepf: sparsity_pattern not positive definite!');
    end
else
    per = 1:nbus;
end

% Rearrange mpc to the same order as the permutation per
mpc.bus = mpc.bus(per,:);
mpc.bus(:,BUS_I) = 1:nbus;

for i=1:ngen
    mpc.gen(i,GEN_BUS) = find(per == mpc.gen(i,GEN_BUS));
end

[mpc.gen genidx] = sortrows(mpc.gen,1);
mpc.gencost = mpc.gencost(genidx,:);

for i=1:nbranch
    mpc.branch(i,F_BUS) = find(per == mpc.branch(i,F_BUS));
    mpc.branch(i,T_BUS) = find(per == mpc.branch(i,T_BUS));
end
% -------------------------------------------------------------------------

Sbase = mpc.baseMVA;

% Create vectors of power injections and voltage magnitudes
Qinj = -mpc.bus(:,QD) / Sbase;
Vmag = mpc.bus(:,VM);

Pd = mpc.bus(:,PD) / Sbase;
Pg = zeros(nbus,1);
for i=1:nbus
    genidx = find(mpc.gen(:,GEN_BUS) == i);
    if ~isempty(genidx)
        Pg(i) = sum(mpc.gen(genidx,PG)) / Sbase;
        Vmag(i) = mpc.gen(genidx(1),VG);
    end
end
Pinj = Pg - Pd;

slackbus_idx = find(mpc.bus(:,BUS_TYPE) == 3);
Vslack = Vmag(slackbus_idx);

%% Step 2: Compute maximal cliques of chordal extension
% Use adjacency matrix made from Rchol

if maxNumberOfCliques ~= 1 && nbus > 3
    
    % Build adjacency matrix
    [f,t] = find(Rchol - diag(diag(Rchol)));
    Aadj = sparse(f,t,ones(length(f),1),nbus,nbus);
    Aadj = max(Aadj,Aadj');

    % Determine maximal cliques
    [MC,ischordal] = maxCardSearch(Aadj);
    
    if ~ischordal
        % This should never happen since the Cholesky decomposition should
        % always yield a chordal graph.
        error('insolvablepf: Chordal extension adjacency matrix is not chordal!');
    end
    
    for i=1:size(MC,2)
       maxclique{i} = find(MC(:,i));
    end

else
    maxclique{1} = 1:nbus;
    nmaxclique = 1;
    E = [];
end


%% Step 3: Make clique tree and combine maximal cliques

if maxNumberOfCliques ~= 1 && nbus > 3
    % Create a graph of maximal cliques, where cost between each maximal clique
    % is the number of shared buses in the corresponding maximal cliques.
    nmaxclique = length(maxclique);
    cliqueCost = sparse(nmaxclique,nmaxclique);
    for i=1:nmaxclique
        maxcliquei = maxclique{i};
        for k=i+1:nmaxclique

            cliqueCost(i,k) = sum(ismembc_(maxcliquei,maxclique{k}));

            % Slower alternative that doesn't use undocumented MATLAB function
            % cliqueCost(i,k) = length(intersect(maxcliquei,maxclique{k}));

        end
    end
    cliqueCost = max(cliqueCost,cliqueCost.');

    % Calculate the maximal spanning tree
    cliqueCost = -cliqueCost;
    [E] = prim(cliqueCost);

    % Combine maximal cliques
    if verbose >= 2
        [maxclique,E] = combineMaxCliques(maxclique,E,maxNumberOfCliques,ndisplay);
    else
        [maxclique,E] = combineMaxCliques(maxclique,E,maxNumberOfCliques,inf);
    end
    nmaxclique = length(maxclique);
end

%% Create SDP relaxation

tic;

constraints = [];

% Control growth of Wref variables
dd_blk_size = 50*nbus;
dq_blk_size = 2*dd_blk_size;

Wref_dd = zeros(dd_blk_size,2); % For terms like Vd1*Vd1 and Vd1*Vd2
lWref_dd = dd_blk_size;
matidx_dd = zeros(dd_blk_size,3);
dd_ptr = 0;

Wref_dq = zeros(dq_blk_size,2); % For terms like Vd1*Vd1 and Vd1*Vd2
lWref_dq = dq_blk_size;
matidx_dq = zeros(dq_blk_size,3);
dq_ptr = 0;

for i=1:nmaxclique
    nmaxcliquei = length(maxclique{i});
    for k=1:nmaxcliquei % row
        for m=k:nmaxcliquei % column
            
            % Check if this pair loop{i}(k) and loop{i}(m) has appeared in
            % any previous maxclique. If not, it isn't in Wref_dd.
            Wref_dd_found = 0;
            if i > 1
                for r = 1:i-1
                   if any(maxclique{r}(:) == maxclique{i}(k)) && any(maxclique{r}(:) == maxclique{i}(m))
                       Wref_dd_found = 1;
                       break;
                   end
                end
            end

            if ~Wref_dd_found
                % If we didn't find this element already, add it to Wref_dd
                % and matidx_dd
                dd_ptr = dd_ptr + 1;
                
                if dd_ptr > lWref_dd
                    % Expand the variables by dd_blk_size
                    Wref_dd = [Wref_dd; zeros(dd_blk_size,2)];
                    matidx_dd = [matidx_dd; zeros(dd_ptr-1 + dd_blk_size,3)];
                    lWref_dd = length(Wref_dd(:,1));
                end
                
                Wref_dd(dd_ptr,1:2) = [maxclique{i}(k) maxclique{i}(m)];
                matidx_dd(dd_ptr,1:3) = [i k m];
            end

            Wref_dq_found = Wref_dd_found;

            if ~Wref_dq_found
                % If we didn't find this element already, add it to Wref_dq
                % and matidx_dq
                dq_ptr = dq_ptr + 1;
                
                if dq_ptr > lWref_dq
                    % Expand the variables by dq_blk_size
                    Wref_dq = [Wref_dq; zeros(dq_blk_size,2)];
                    matidx_dq = [matidx_dq; zeros(dq_ptr-1 + dq_blk_size,3)];
                    lWref_dq = length(Wref_dq(:,1));
                end
                
                Wref_dq(dq_ptr,1:2) = [maxclique{i}(k) maxclique{i}(m)];
                matidx_dq(dq_ptr,1:3) = [i k m+nmaxcliquei];
            
                if k ~= m % Already have the diagonal terms of the off-diagonal block

                    dq_ptr = dq_ptr + 1;

                    if dq_ptr > lWref_dq
                        % Expand the variables by dq_blk_size
                        Wref_dq = [Wref_dq; zeros(dq_blk_size,2)];
                        matidx_dq = [matidx_dq; zeros(dq_ptr-1 + dq_blk_size,3)];
                    end

                    Wref_dq(dq_ptr,1:2) = [maxclique{i}(m) maxclique{i}(k)];
                    matidx_dq(dq_ptr,1:3) = [i k+nmaxcliquei m];
                end
            end
        end
    end
    
    if verbose >= 2 && mod(i,ndisplay) == 0
        fprintf('Loop identification: Loop %i of %i\n',i,nmaxclique);
    end
end

% Trim off excess zeros and empty matrix structures
Wref_dd = Wref_dd(1:dd_ptr,:);
matidx_dd = matidx_dd(1:dd_ptr,:);

% Store index of Wref variables
Wref_dd = [(1:length(Wref_dd)).' Wref_dd];
Wref_dq = [(1:length(Wref_dq)).' Wref_dq];

Wref_qq = Wref_dd;
matidx_qq = zeros(size(Wref_qq,1),3);
for i=1:size(Wref_qq,1) 
    nmaxcliquei = length(maxclique{matidx_dd(i,1)});
    matidx_qq(i,1:3) = [matidx_dd(i,1) matidx_dd(i,2)+nmaxcliquei matidx_dd(i,3)+nmaxcliquei];
end


%% Enforce linking constraints in dual

for i=1:nmaxclique
    A{i} = [];
end

% Count the number of required linking constraints
nbeta = 0;
for i=1:size(E,1)
    overlap_idx = intersect(maxclique{E(i,1)},maxclique{E(i,2)});
    for k=1:length(overlap_idx)
        for m=k:length(overlap_idx)
            E11idx = find(maxclique{E(i,1)} == overlap_idx(k));
            E12idx = find(maxclique{E(i,1)} == overlap_idx(m));
            
            nbeta = nbeta + 3;
            
            if E11idx ~= E12idx
                nbeta = nbeta + 1;
            end
        end
    end
    
    if verbose >= 2 && mod(i,ndisplay) == 0
        fprintf('Counting beta: %i of %i\n',i,size(E,1));
    end
end

% Make beta sdpvar
if nbeta > 0
    beta = sdpvar(nbeta,1);
end

% Create the linking constraints defined by the maximal clique tree
beta_idx = 0;
for i=1:size(E,1)
    overlap_idx = intersect(maxclique{E(i,1)},maxclique{E(i,2)});
    nmaxclique1 = length(maxclique{E(i,1)});
    nmaxclique2 = length(maxclique{E(i,2)});
    for k=1:length(overlap_idx)
        for m=k:length(overlap_idx)
            E11idx = find(maxclique{E(i,1)} == overlap_idx(k));
            E12idx = find(maxclique{E(i,1)} == overlap_idx(m));
            E21idx = find(maxclique{E(i,2)} == overlap_idx(k));
            E22idx = find(maxclique{E(i,2)} == overlap_idx(m));
            
            beta_idx = beta_idx + 1;
            if ~isempty(A{E(i,1)})
                A{E(i,1)} = A{E(i,1)} + 0.5*beta(beta_idx)*sparse([E11idx; E12idx], [E12idx; E11idx], [1; 1], 2*nmaxclique1, 2*nmaxclique1);
            else
                A{E(i,1)} = 0.5*beta(beta_idx)*sparse([E11idx; E12idx], [E12idx; E11idx], [1; 1], 2*nmaxclique1, 2*nmaxclique1);
            end
            if ~isempty(A{E(i,2)})
                A{E(i,2)} = A{E(i,2)} - 0.5*beta(beta_idx)*sparse([E21idx; E22idx], [E22idx; E21idx], [1; 1], 2*nmaxclique2, 2*nmaxclique2);
            else
                A{E(i,2)} = -0.5*beta(beta_idx)*sparse([E21idx; E22idx], [E22idx; E21idx], [1; 1], 2*nmaxclique2, 2*nmaxclique2);
            end
            
            beta_idx = beta_idx + 1;
            A{E(i,1)} = A{E(i,1)} + 0.5*beta(beta_idx)*sparse([E11idx+nmaxclique1; E12idx+nmaxclique1],[E12idx+nmaxclique1; E11idx+nmaxclique1], [1;1], 2*nmaxclique1, 2*nmaxclique1);
            A{E(i,2)} = A{E(i,2)} - 0.5*beta(beta_idx)*sparse([E21idx+nmaxclique2; E22idx+nmaxclique2],[E22idx+nmaxclique2; E21idx+nmaxclique2], [1;1], 2*nmaxclique2, 2*nmaxclique2);
            
            beta_idx = beta_idx + 1;
            A{E(i,1)} = A{E(i,1)} + 0.5*beta(beta_idx)*sparse([E11idx; E12idx+nmaxclique1], [E12idx+nmaxclique1; E11idx], [1;1], 2*nmaxclique1, 2*nmaxclique1);
            A{E(i,2)} = A{E(i,2)} - 0.5*beta(beta_idx)*sparse([E21idx; E22idx+nmaxclique2], [E22idx+nmaxclique2; E21idx], [1;1], 2*nmaxclique2, 2*nmaxclique2);
            
            if E11idx ~= E12idx
                beta_idx = beta_idx + 1;
                A{E(i,1)} = A{E(i,1)} + 0.5*beta(beta_idx)*sparse([E11idx+nmaxclique1; E12idx], [E12idx; E11idx+nmaxclique1], [1;1], 2*nmaxclique1, 2*nmaxclique1);
                A{E(i,2)} = A{E(i,2)} - 0.5*beta(beta_idx)*sparse([E21idx+nmaxclique2; E22idx], [E22idx; E21idx+nmaxclique2], [1;1], 2*nmaxclique2, 2*nmaxclique2);
            end
        end
    end
    
    if verbose >= 2 && mod(i,ndisplay) == 0
        fprintf('SDP linking: %i of %i\n',i,size(E,1));
    end
    
end

% For systems with only one maximal clique, A doesn't get defined above.
% Explicitly define it here.
if nmaxclique == 1
    A{1} = sparse(2*nbus,2*nbus);
end

%% Build matrices

[Yk,Yk_,Mk,Ylineft,Ylinetf,Y_lineft,Y_linetf] = makesdpmat(mpc);

%% Create SDP variables for dual

% lambda: active power equality constraints
% gamma:  reactive power equality constraints
% mu:     voltage magnitude constraints

% Bus variables
lambda = sdpvar(nbus,1);
gamma = sdpvar(nbus,1);
mu = sdpvar(nbus,1);



%% Build bus constraints

cost = 0;
for k=1:nbus
        
    if mpc.bus(k,BUS_TYPE) == PQ
        % PQ bus has equality constraints on P and Q
        
        % Active power constraint
        A = addToA(Yk(k), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, -lambda(k), maxclique);
        
        % Reactive power constraint
        A = addToA(Yk_(k), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, -gamma(k), maxclique);
        
        % Cost function
        cost = cost + lambda(k)*Pinj(k) + gamma(k)*Qinj(k);
        
    elseif mpc.bus(k,BUS_TYPE) == PV
        % Scale the voltage at PV buses in constant proportion to the slack
        % bus voltage. Don't set the PV bus voltages to any specific value.

        % alpha is the square of the ratio between the voltage magnitudes 
        % of the slack and PV bus, such that Vpv = alpha*Vslack
        alpha = Vmag(k)^2 / Vslack^2; 
        
        % Active power constraint
        A = addToA(Yk(k), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, -lambda(k), maxclique);
        
        % Voltage magnitude constraint
        A = addToA(Mk(k)-alpha*Mk(slackbus_idx), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, -mu(k), maxclique);
        
        % Cost function
        cost = cost + lambda(k)*Pinj(k);
        
    elseif mpc.bus(k,BUS_TYPE) == REF
        % Reference bus is unconstrained.
    else
        error('insolvablepf: Invalid bus type');
    end
   
    if verbose >= 2 && mod(k,ndisplay) == 0
        fprintf('SDP creation: Bus %i of %i\n',k,nbus);
    end
    
end % Loop through all buses

%% Incorporate objective function (minimize Vslack^2)

A = addToA(Mk(slackbus_idx), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, 1, maxclique);

%% Formulate dual psd constraints

for i=1:nmaxclique
    % Can multiply A by any non-zero scalar. This may affect numerics
    % of the solver.
    constraints = [constraints; 1*A{i} >= 0]; 
end


%% Solve the SDP

% Preserve warning settings
S = warning;

% Run sdp solver
sdpinfo = solvesdp(constraints, -cost, sdpopts); % Negative cost to convert maximization to minimization problem
if sdpinfo.problem == 2 || sdpinfo.problem == -2 || sdpinfo.problem == -3
    error(yalmiperror(sdpinfo.problem));
end
if ~have_fcn('octave') || have_fcn('octave', 'vnum') >= 4.001
    %% (avoid bug in Octave 4.0.x, where warning state is left corrupted)
    warning(S);
end

if verbose >= 2
    fprintf('Solver exit message: %s\n',sdpinfo.info);
end

%% Calculate rank characteristics of the solution

mineigratio = inf;
for i=1:length(A)
    evl = eig(double(A{i}));

    % Calculate mineigratio
    eigA_ratio = abs(evl(3) / evl(1));

    if eigA_ratio < mineigratio
        mineigratio = eigA_ratio;
    end
end


%% Output results

Vslack_min = sqrt(abs(double(cost)));
insolvable = Vslack_min > Vmag(slackbus_idx);
sigma = Vmag(slackbus_idx) / Vslack_min;
eta = sigma^2;
