function [results,success,raw] = sdpopf_solver(om, mpopt)
%SDPOPF_SOLVER A semidefinite programming relaxtion of the OPF problem
%
%   [RESULTS,SUCCESS,RAW] = SDPOPF_SOLVER(OM, MPOPT)
%
%   Inputs are an OPF model object and a MATPOWER options vector.
%
%   Outputs are a RESULTS struct, SUCCESS flag and RAW output struct.
%
%   RESULTS is a MATPOWER case struct (mpc) with the usual baseMVA, bus
%   branch, gen, gencost fields, along with the following additional
%   fields:
%       .f           final objective function value
%       .mineigratio Minimum eigenvalue ratio measure of rank condition
%                    satisfaction
%       .zero_eval   Zero eigenvalue measure of optimal voltage profile
%                    consistency
%
%   SUCCESS     1 if solver converged successfully, 0 otherwise
%
%   RAW         raw output
%       .xr     final value of optimization variables
%           .A  Cell array of matrix variables for the dual problem
%           .W  Cell array of matrix variables for the primal problem
%       .pimul  constraint multipliers on 
%           .lambdaeq_sdp   Active power equalities
%           .psiU_sdp       Generator active power upper inequalities
%           .psiL_sdp       Generator active power lower inequalities
%           .gammaeq_sdp    Reactive power equalities
%           .gammaU_sdp     Reactive power upper inequalities
%           .gammaL_sdp     Reactive power lower inequalities
%           .muU_sdp        Square of voltage magnitude upper inequalities
%           .muL_sdp        Square of voltage magnitude lower inequalities
%       .info   solver specific termination code
%
%   See also OPF.

%   MATPOWER
%   Copyright (c) 2013-2016 by Power System Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%   and Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

% Unpack options
ignore_angle_lim    = mpopt.opf.ignore_angle_lim;
verbose             = mpopt.verbose;
maxNumberOfCliques  = mpopt.sdp_pf.max_number_of_cliques;   %% Maximum number of maximal cliques
eps_r               = mpopt.sdp_pf.eps_r;               %% Resistance of lines when zero line resistance specified
recover_voltage     = mpopt.sdp_pf.recover_voltage;     %% Method for recovering the optimal voltage profile
recover_injections  = mpopt.sdp_pf.recover_injections;  %% Method for recovering the power injections
minPgendiff         = mpopt.sdp_pf.min_Pgen_diff;       %% Fix Pgen to midpoint of generator range if PMAX-PMIN < MINPGENDIFF (in MW)
minQgendiff         = mpopt.sdp_pf.min_Qgen_diff;       %% Fix Qgen to midpoint of generator range if QMAX-QMIN < MINQGENDIFF (in MVAr)
maxlinelimit        = mpopt.sdp_pf.max_line_limit;      %% Maximum line limit. Anything above this will be unconstrained. Line limits of zero are also unconstrained.
maxgenlimit         = mpopt.sdp_pf.max_gen_limit;       %% Maximum reactive power generation limits. If Qmax or abs(Qmin) > maxgenlimit, reactive power injection is unlimited.
ndisplay            = mpopt.sdp_pf.ndisplay;            %% Determine display frequency of diagonastic information
cholopts.dense      = mpopt.sdp_pf.choldense;           %% Cholesky factorization options
cholopts.aggressive = mpopt.sdp_pf.cholaggressive;      %% Cholesky factorization options
binding_lagrange    = mpopt.sdp_pf.bind_lagrange;       %% Tolerance for considering a Lagrange multiplier to indicae a binding constraint
zeroeval_tol        = mpopt.sdp_pf.zeroeval_tol;        %% Tolerance for considering an eigenvalue in LLeval equal to zero
mineigratio_tol     = mpopt.sdp_pf.mineigratio_tol;     %% Tolerance for considering the rank condition satisfied

if upper(mpopt.opf.flow_lim(1)) ~= 'S' && upper(mpopt.opf.flow_lim(1)) ~= 'P'
    error('sdpopf_solver: Only ''S'' and ''P'' options are currently implemented for MPOPT.opf.flow_lim when MPOPT.opf.ac.solver == ''SDPOPF''');
end

% set YALMIP options struct in SDP_PF (for details, see help sdpsettings) 
sdpopts = yalmip_options([], mpopt);

if verbose > 0
    v = sdp_pf_ver('all');
    fprintf('SDPOPF Version %s, %s', v.Version, v.Date);
    if ~isempty(sdpopts.solver)
        fprintf('  --  Using %s.\n\n',upper(sdpopts.solver));
    else
        fprintf('\n\n');
    end
end

tic;

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

mpc = get_mpc(om);

if toggle_dcline(mpc, 'status')
    error('sdpopf_solver: DC lines are not implemented in SDP_PF');
end

nbus = size(mpc.bus,1);
ngen = size(mpc.gen,1);
nbranch = size(mpc.branch,1);
bustype = mpc.bus(:,BUS_TYPE);

if any(mpc.gencost(:,NCOST) > 3 & mpc.gencost(:,MODEL) == POLYNOMIAL)
    error('sdpopf_solver: SDPOPF is limited to quadratic cost functions.');
end

if size(mpc.gencost,1) > ngen && verbose >= 1 % reactive power costs are specified
    warning('sdpopf_solver: Reactive power costs are not implemented in SDPOPF. Ignoring reactive power costs.');
end

if ~ignore_angle_lim && (any(mpc.branch(:,ANGMIN) ~= -360) || any(mpc.branch(:,ANGMAX) ~= 360))
    warning('sdpopf_solver: Angle difference constraints are not implemented in SDPOPF. Ignoring angle difference constraints.');
end

% Enforce a minimum resistance for all branches
mpc.branch(:,BR_R) = max(mpc.branch(:,BR_R),eps_r); 

% Some of the larger system (e.g., case2746wp) have generators 
% corresponding to buses that have bustype == PQ. Change these
% to PV buses.
for i=1:ngen
    busidx = find(mpc.bus(:,BUS_I) == mpc.gen(i,GEN_BUS));
    if isempty(busidx) || ~(bustype(busidx) == PV || bustype(busidx) == REF)
        bustype(busidx) = PV;
    end
end

% Buses may be listed as PV buses without associated generators. Change
% these buses to PQ.
for i=1:nbus
    if bustype(i) == PV
        genidx = find(mpc.gen(:,GEN_BUS) == mpc.bus(i,BUS_I), 1);
        if isempty(genidx)
            bustype(i) = PQ;
        end
    end
end

% if any(mpc.gencost(:,MODEL) == PW_LINEAR)
%     error('sdpopf_solver: Piecewise linear generator costs are not implemented in SDPOPF.');
% end

% The code does not handle the case where a bus has both piecewise-linear
% generator cost functions and quadratic generator cost functions. 
for i=1:nbus
    genidx = find(mpc.gen(:,GEN_BUS) == mpc.bus(i,BUS_I));
    if ~all(mpc.gencost(genidx,MODEL) == PW_LINEAR) && ~all(mpc.gencost(genidx,MODEL) == POLYNOMIAL)
        error('sdpopf_solver: Bus %i has generators with both piecewise-linear and quadratic generators, which is not supported in this version of SDPOPF.',i);
    end
end

% Save initial bus indexing in a new column on the right side of mpc.bus
mpc.bus(:,size(mpc.bus,2)+1) = mpc.bus(:,BUS_I);

tsetup = toc;

tic;
%% Determine Maximal Cliques
%% Step 1: Cholesky factorization to obtain chordal extension
% Use a minimum degree permutation to obtain a sparse chordal extension.

if maxNumberOfCliques ~= 1
    [Ainc] = makeIncidence(mpc.bus,mpc.branch);
    sparsity_pattern = abs(Ainc.'*Ainc) + speye(nbus,nbus);
    per = amd(sparsity_pattern,cholopts);
    [Rchol,p] = chol(sparsity_pattern(per,per),'lower');

    if p ~= 0
        error('sdpopf_solver: sparsity_pattern not positive definite!');
    end
else
    per = 1:nbus;
end

% Rearrange mpc to the same order as the permutation per
mpc.bus = mpc.bus(per,:);
mpc.bus(:,BUS_I) = 1:nbus;
bustype = bustype(per);

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

Pd = mpc.bus(:,PD) / Sbase;
Qd = mpc.bus(:,QD) / Sbase;

for i=1:nbus  
    genidx = find(mpc.gen(:,GEN_BUS) == i);
    if ~isempty(genidx)
        Qmax(i) = sum(mpc.gen(genidx,QMAX)) / Sbase;
        Qmin(i) = sum(mpc.gen(genidx,QMIN)) / Sbase;
    else
        Qmax(i) = 0;
        Qmin(i) = 0;
    end
end

Vmax = mpc.bus(:,VMAX);
Vmin = mpc.bus(:,VMIN);

Smax = mpc.branch(:,RATE_A) / Sbase;

% For generators with quadratic cost functions (handle piecewise linear
% costs elsewhere)
c2 = zeros(ngen,1);
c1 = zeros(ngen,1);
c0 = zeros(ngen,1);
for genidx=1:ngen
    if mpc.gencost(genidx,MODEL) == POLYNOMIAL
        if mpc.gencost(genidx,NCOST) == 3 % Quadratic cost function
            c2(genidx) = mpc.gencost(genidx,COST) * Sbase^2;
            c1(genidx) = mpc.gencost(genidx,COST+1) * Sbase^1;
            c0(genidx) = mpc.gencost(genidx,COST+2) * Sbase^0;
        elseif mpc.gencost(genidx,NCOST) == 2 % Linear cost function
            c1(genidx) = mpc.gencost(genidx,COST) * Sbase^1;
            c0(genidx) = mpc.gencost(genidx,COST+1) * Sbase^0;
        else
            error('sdpopf_solver: Only piecewise-linear and quadratic cost functions are implemented in SDPOPF');
        end
    end
end

if any(c2 < 0)
    error('sdpopf_solver: Quadratic term of generator cost function is negative. Must be convex (non-negative).');
end

maxlinelimit = maxlinelimit / Sbase;
maxgenlimit = maxgenlimit / Sbase;
minPgendiff = minPgendiff / Sbase;
minQgendiff = minQgendiff / Sbase;

% Create Ybus with new bus numbers
[Y, Yf, Yt] = makeYbus(mpc);


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
        error('sdpopf_solver: Chordal extension adjacency matrix is not chordal!');
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

            cliqueCost(i,k) = sum(ismembc(maxcliquei,maxclique{k}));

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
tmaxclique = toc;

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

%% Functions to build matrices

[Yk,Yk_,Mk,Ylineft,Ylinetf,Y_lineft,Y_linetf] = makesdpmat(mpc);

%% Create SDP variables for dual

% lambda: active power equality constraints
% gamma:  reactive power equality constraints
% mu:     voltage magnitude constraints
% psi:    generator upper and lower active power limits (created later)

% Bus variables
nlambda_eq = 0;
ngamma_eq = 0;
ngamma_ineq = 0;
nmu_ineq = 0;

for i=1:nbus
    
    nlambda_eq = nlambda_eq + 1;
    lambda_eq(i) = nlambda_eq;
    
    if bustype(i) == PQ || (Qmax(i) - Qmin(i) < minQgendiff)
        ngamma_eq = ngamma_eq + 1;
        gamma_eq(i) = ngamma_eq;
    else
        gamma_eq(i) = nan;
    end
        
    if (bustype(i) == PV || bustype(i) == REF) && (Qmax(i) - Qmin(i) >= minQgendiff) && (Qmax(i) <= maxgenlimit || Qmin(i) >= -maxgenlimit)
        ngamma_ineq = ngamma_ineq + 1;
        gamma_ineq(i) = ngamma_ineq;
    else
        gamma_ineq(i) = nan;
    end
    
    nmu_ineq = nmu_ineq + 1;
    mu_ineq(i) = nmu_ineq;

    psiU_sdp{i} = [];
    psiL_sdp{i} = [];
    
    pwl_sdp{i} = [];
end

lambdaeq_sdp = sdpvar(nlambda_eq,1);

gammaeq_sdp = sdpvar(ngamma_eq,1);
gammaU_sdp = sdpvar(ngamma_ineq,1);
gammaL_sdp = sdpvar(ngamma_ineq,1);

muU_sdp = sdpvar(nmu_ineq,1);
muL_sdp = sdpvar(nmu_ineq,1);

% Branch flow limit variables
% Hlookup: [line_idx ft]
if upper(mpopt.opf.flow_lim(1)) == 'S'
    Hlookup = zeros(2*sum(Smax ~= 0 & Smax < maxlinelimit),2);
end

nlconstraint = 0;
for i=1:nbranch
    if Smax(i) ~= 0 && Smax(i) < maxlinelimit
        nlconstraint = nlconstraint + 1;
        Hlookup(nlconstraint,:) = [i 1];
        nlconstraint = nlconstraint + 1;
        Hlookup(nlconstraint,:) = [i 0];
    end
end

if upper(mpopt.opf.flow_lim(1)) == 'S'
    for i=1:nlconstraint
        Hsdp{i} = sdpvar(3,3);
    end
elseif upper(mpopt.opf.flow_lim(1)) == 'P'
    Hsdp = sdpvar(2*nlconstraint,1);
end



%% Build bus constraints

for k=1:nbus
        
    if bustype(k) == PQ
        % PQ bus has equality constraints on P and Q
        
        % Active power constraint
        % -----------------------------------------------------------------
        A = addToA(Yk(k), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, -lambdaeq_sdp(lambda_eq(k),1), maxclique);

        % No constraints on lambda_eq_sdp
        % -----------------------------------------------------------------
        
        
        % Reactive power constraint
        % -----------------------------------------------------------------
        A = addToA(Yk_(k), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, -gammaeq_sdp(gamma_eq(k),1), maxclique);
        
        % No constraints on gamma_eq_sdp
        % -----------------------------------------------------------------
        
        
        % Create cost function
        % -----------------------------------------------------------------
        if exist('cost','var')
            cost = cost ... 
                + lambdaeq_sdp(lambda_eq(k))*(-Pd(k)) ...
                + gammaeq_sdp(gamma_eq(k))*(-Qd(k));
        else
            cost = lambdaeq_sdp(lambda_eq(k))*(-Pd(k)) ...
                   + gammaeq_sdp(gamma_eq(k))*(-Qd(k));
        end
        % -----------------------------------------------------------------
        
    elseif bustype(k) == PV || bustype(k) == REF 
        % PV and slack buses have upper and lower constraints on both P and
        % Q, unless the constraints are tighter than minPgendiff and
        % minQgendiff, in which case the inequalities are set to equalities
        % at the midpoint of the upper and lower limits.
        
        genidx = find(mpc.gen(:,GEN_BUS) == k);
        
        if isempty(genidx)
            error('sdpopf_solver: Generator for bus %i not found!',k);
        end
        
        % Active power constraints
        % -----------------------------------------------------------------
        % Make Lagrange multipliers for generator limits
        psiU_sdp{k} = sdpvar(length(genidx),1);
        psiL_sdp{k} = sdpvar(length(genidx),1);
        
        clear lambdai Pmax Pmin
        for i=1:length(genidx)
            
            % Does this generator have pwl costs?
            if mpc.gencost(genidx(i),MODEL) == PW_LINEAR
                pwl = 1;
                % If so, define Lagrange multipliers for each segment
                pwl_sdp{k}{i} = sdpvar(mpc.gencost(genidx(i),NCOST)-1,1);
                
                % Get breakpoints for this curve
                x_pw = mpc.gencost(genidx(i),-1+COST+(1:2:2*length(pwl_sdp{k}{i})+1)) / Sbase; % piecewise powers
                c_pw = mpc.gencost(genidx(i),-1+COST+(2:2:2*length(pwl_sdp{k}{i})+2)); % piecewise costs
            else
                pwl = 0;
                pwl_sdp{k}{i} = [];
            end
            
            Pmax(i) = mpc.gen(genidx(i),PMAX) / Sbase;
            Pmin(i) = mpc.gen(genidx(i),PMIN) / Sbase;
            
            if (Pmax(i) - Pmin(i) >= minPgendiff)
                
                % Constrain upper and lower Lagrange multipliers to be positive
                constraints = [constraints;
                    psiL_sdp{k}(i) >= 0;
                    psiU_sdp{k}(i) >= 0];
                
                if pwl
                    
                    lambdasum = 0;
                    for pwiter = 1:length(pwl_sdp{k}{i})
                        
                        m_pw = (c_pw(pwiter+1) - c_pw(pwiter)) / (x_pw(pwiter+1) - x_pw(pwiter)); % slope for this piecewise cost segement
                        
                        if exist('cost','var')
                            cost = cost - pwl_sdp{k}{i}(pwiter) * (m_pw*x_pw(pwiter) - c_pw(pwiter));
                        else
                            cost = -pwl_sdp{k}{i}(pwiter) * (m_pw*x_pw(pwiter) - c_pw(pwiter));
                        end
                        
                        lambdasum = lambdasum + pwl_sdp{k}{i}(pwiter) * m_pw;

                    end
                    
                    constraints = [constraints; 
                                   pwl_sdp{k}{i}(:) >= 0];
                    
                    if ~exist('lambdai','var')
                        lambdai = lambdasum + psiU_sdp{k}(i) - psiL_sdp{k}(i);
                    else
                        % Equality constraint on prices (equal marginal
                        % prices requirement) for all generators at a bus
%                         constraints = [constraints;
%                             lambdasum + psiU_sdp{k}(i) - psiL_sdp{k}(i) == lambdai];
                        
                        % Instead of a strict equality, numerical
                        % performance works better with tight inequalities
                        % for equal marginal price requirement with
                        % multiple piecewise generators at the same bus.
                        constraints = [constraints;
                            lambdasum + psiU_sdp{k}(i) - psiL_sdp{k}(i) - binding_lagrange <= lambdai <= lambdasum + psiU_sdp{k}(i) - psiL_sdp{k}(i) + binding_lagrange];
                    end
                    
                    constraints = [constraints; 
                                    sum(pwl_sdp{k}{i}) == 1];
                    
                else
                    if c2(genidx(i)) > 0
                        % Cost function has nonzero quadratic term

                        % Make a new R matrix
                        R{k}{i} = sdpvar(2,1);

                        constraints = [constraints; 
                            [1 R{k}{i}(1);
                             R{k}{i}(1) R{k}{i}(2)] >= 0]; % R psd

                        if ~exist('lambdai','var')
                            lambdai = c1(genidx(i)) + 2*sqrt(c2(genidx(i)))*R{k}{i}(1) + psiU_sdp{k}(i) - psiL_sdp{k}(i);
                        else
                            % Equality constraint on prices (equal marginal
                            % prices requirement) for all generators at a bus
                            constraints = [constraints;
                                c1(genidx(i)) + 2*sqrt(c2(genidx(i)))*R{k}{i}(1) + psiU_sdp{k}(i) - psiL_sdp{k}(i) == lambdai];
                        end

                        if exist('cost','var')
                            cost = cost - R{k}{i}(2);
                        else
                            cost = -R{k}{i}(2);
                        end
                    else
                        % Cost function is linear for this generator
                        R{k}{i} = zeros(2,1);

                        if ~exist('lambdai','var')
                            lambdai = c1(genidx(i)) + psiU_sdp{k}(i) - psiL_sdp{k}(i);
                        else
                            % Equality constraint on prices (equal marginal
                            % prices requirement) for all generators at a bus
                            constraints = [constraints;
                                c1(genidx(i)) + psiU_sdp{k}(i) - psiL_sdp{k}(i) == lambdai];
                        end

                    end
                end
                
                if exist('cost','var')
                    cost = cost ...
                           + psiL_sdp{k}(i)*Pmin(i) - psiU_sdp{k}(i)*Pmax(i);
                else
                    cost = psiL_sdp{k}(i)*Pmin(i) - psiU_sdp{k}(i)*Pmax(i);
                end

            else % Active power generator is constrained to a small range
                % Set the power injection to the midpoint of the small range
                % allowed by the problem, and use a free variable to force an
                % equality constraint.

                Pavg = (Pmin(i)+Pmax(i))/2;
                Pd(k) = Pd(k) - Pavg;

                % Add on the (known) cost of this generation
                if pwl
                    % Figure out what this fixed generation costs
                    pwidx = find(Pavg <= x_pw,1);
                    if isempty(pwidx)
                        pwidx = length(x_pw);
                    end
                    pwidx = pwidx - 1;
                    
                    m_pw = (c_pw(pwidx+1) - c_pw(pwidx)) / (x_pw(pwidx+1) - x_pw(pwidx)); % slope for this piecewise cost segement
                    fix_gen_cost = m_pw * (Pavg - x_pw(pwidx)) + c_pw(pwidx);
                    
                    if exist('cost','var')
                        cost = cost + fix_gen_cost;
                    else
                        cost = fix_gen_cost;
                    end
                else
                    c0(genidx(i)) = c2(genidx(i))*Pavg^2 + c1(genidx(i))*Pavg + c0(genidx(i));
                end
                
                % No constraints on lambdaeq_sdp (free var)
            end
            
            if ~pwl
                if exist('cost','var')
                    cost = cost + c0(genidx(i));
                else
                    cost = c0(genidx(i));
                end
            end
        end
               
        % If there are only generator(s) with tight active power 
        % constraints at this bus, explicitly set an equality constraint to
        % the (modified) load demand directly.
        if exist('lambdai','var')
            lambda_aggregate = lambdai;
        else
            lambda_aggregate = lambdaeq_sdp(lambda_eq(k));
        end
        
        lambdaeq_sdp(k) = -lambda_aggregate;
        
        cost = cost + lambda_aggregate*Pd(k);
        
        A = addToA(Yk(k), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, lambda_aggregate, maxclique);
        % -----------------------------------------------------------------
        

        % Reactive power constraints
        % -----------------------------------------------------------------
        % Sum reactive power injections from all generators at each bus
        
        clear gamma_aggregate
        if (Qmax(k) - Qmin(k) >= minQgendiff)
            
            if Qmin(k) >= -maxgenlimit % This generator has a lower Q limit
                
                gamma_aggregate = -gammaL_sdp(gamma_ineq(k));
                
                if exist('cost','var')
                    cost = cost ...
                           + gammaL_sdp(gamma_ineq(k))*(Qmin(k) - Qd(k));
                else
                    cost = gammaL_sdp(gamma_ineq(k))*(Qmin(k) - Qd(k));
                end
            
                % Constrain upper and lower lagrange multipliers to be positive
                constraints = [constraints;
                    gammaL_sdp(gamma_ineq(k)) >= 0];        
            end
            
            if Qmax(k) <= maxgenlimit % We have an upper Q limit
                
                if exist('gamma_aggregate','var')
                    gamma_aggregate = gamma_aggregate + gammaU_sdp(gamma_ineq(k));
                else
                    gamma_aggregate = gammaU_sdp(gamma_ineq(k));
                end
                
                if exist('cost','var')
                    cost = cost ...
                           - gammaU_sdp(gamma_ineq(k))*(Qmax(k) - Qd(k));
                else
                    cost = -gammaU_sdp(gamma_ineq(k))*(Qmax(k) - Qd(k));
                end
            
                % Constrain upper and lower lagrange multipliers to be positive
                constraints = [constraints;
                    gammaU_sdp(gamma_ineq(k)) >= 0];    
            end
            
        else
            gamma_aggregate = -gammaeq_sdp(gamma_eq(k));
            
            if exist('cost','var')
                cost = cost ...
                       + gammaeq_sdp(gamma_eq(k))*((Qmin(k)+Qmax(k))/2 - Qd(k));
            else
                cost = gammaeq_sdp(gamma_eq(k))*((Qmin(k)+Qmax(k))/2 - Qd(k));
            end
            
            % No constraints on gammaeq_sdp (free var)
        end
        
        % Add to appropriate A matrices
        if (Qmax(k) <= maxgenlimit || Qmin(k) >= -maxgenlimit)
            A = addToA(Yk_(k), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, gamma_aggregate, maxclique);
        end
        % -----------------------------------------------------------------
        
    else
        error('sdpopf_solver: Invalid bus type');
    end

    
    % Voltage magnitude constraints
    % -----------------------------------------------------------------   
    mu_aggregate = -muL_sdp(mu_ineq(k)) + muU_sdp(mu_ineq(k));    
    A = addToA(Mk(k), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, mu_aggregate, maxclique);
    
    % Constrain upper and lower Lagrange multipliers to be positive
    constraints = [constraints;
        muL_sdp(mu_ineq(k)) >= 0;
        muU_sdp(mu_ineq(k)) >= 0];
    
    % Create sdp cost function
    cost = cost + muL_sdp(mu_ineq(k))*Vmin(k)^2 - muU_sdp(mu_ineq(k))*Vmax(k)^2;
    % -----------------------------------------------------------------
    
    if verbose >= 2 && mod(k,ndisplay) == 0
        fprintf('SDP creation: Bus %i of %i\n',k,nbus);
    end
    
end % Loop through all buses



%% Build line constraints

nlconstraint = 0;

for i=1:nbranch
    if Smax(i) ~= 0 && Smax(i) < maxlinelimit
        if upper(mpopt.opf.flow_lim(1)) == 'S'  % Constrain MVA at both line terminals
            
            nlconstraint = nlconstraint + 1;
            cost = cost ...
                   - (Smax(i)^2*Hsdp{nlconstraint}(1,1) + Hsdp{nlconstraint}(2,2) + Hsdp{nlconstraint}(3,3));
               
            constraints = [constraints; Hsdp{nlconstraint} >= 0];
            
            A = addToA(Ylineft(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, 2*Hsdp{nlconstraint}(1,2), maxclique);
            A = addToA(Y_lineft(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, 2*Hsdp{nlconstraint}(1,3), maxclique);
            
            nlconstraint = nlconstraint + 1;
            cost = cost ...
                   - (Smax(i)^2*Hsdp{nlconstraint}(1,1) + Hsdp{nlconstraint}(2,2) + Hsdp{nlconstraint}(3,3));
               
            constraints = [constraints; Hsdp{nlconstraint} >= 0];
            
            A = addToA(Ylinetf(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, 2*Hsdp{nlconstraint}(1,2), maxclique);
            A = addToA(Y_linetf(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, 2*Hsdp{nlconstraint}(1,3), maxclique);

        elseif upper(mpopt.opf.flow_lim(1)) == 'P'  % Constrain active power flow at both terminals
            
            nlconstraint = nlconstraint + 1;
            cost = cost ...
                   - Smax(i)*Hsdp(nlconstraint);

            A = addToA(Ylineft(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, Hsdp(nlconstraint), maxclique);
            
            nlconstraint = nlconstraint + 1;
            cost = cost ...
                   - Smax(i)*Hsdp(nlconstraint);
            
            A = addToA(Ylinetf(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, Hsdp(nlconstraint), maxclique);
            
        else
            error('sdpopf_solver: Invalid line constraint option');
        end
    end
    
    if verbose >= 2 && mod(i,ndisplay) == 0
        fprintf('SDP creation: Branch %i of %i\n',i,nbranch);
    end
    
end

if upper(mpopt.opf.flow_lim(1)) == 'P'
    constraints = [constraints; Hsdp >= 0];
end


%% Formulate dual psd constraints

Aconstraints = zeros(nmaxclique,1);
for i=1:nmaxclique
    % Can multiply A by any non-zero scalar. This may affect numerics
    % of the solver.
    constraints = [constraints; 1*A{i} >= 0]; 
    Aconstraints(i) = length(constraints);
end

tsdpform = toc;

%% Solve the SDP

if recover_voltage == 2 || recover_voltage == 3 || recover_voltage == 4
    sdpopts = sdpsettings(sdpopts,'saveduals',1);
end

% Preserve warning settings
S = warning;

% sdpopts = sdpsettings(sdpopts,'sedumi.eps',0);

% Run sdp solver
sdpinfo = solvesdp(constraints, -cost, sdpopts); % Negative cost to convert maximization to minimization problem

if sdpinfo.problem == 2 || sdpinfo.problem == -3
    error(yalmiperror(sdpinfo.problem));
end
warning(S);
tsolve = sdpinfo.solvertime;

if verbose >= 2
    fprintf('Solver exit message: %s\n',sdpinfo.info);
end

objval = double(cost);

%% Extract the optimal voltage profile from the SDP solution

% Find the eigenvector associated with a zero eigenvalue of each A matrix. 
% Enforce consistency between terms in different nullspace eigenvectors
% that refer to the same voltage component. Each eigenvector can be 
% multiplied by a complex scalar to enforce consistency: create a matrix 
% with elements of the eigenvectors. Two more binding constraints are 
% needed: one with a voltage magnitude at its upper or lower limit and one 
% with the voltage angle equal to zero at the reference bus.

tic;

% Calculate eigenvalues from dual problem (A matrices)
if recover_voltage == 1 || recover_voltage == 3 || recover_voltage == 4
    dual_mineigratio = inf;
    dual_eval = nan(length(A),1);
    for i=1:length(A)
        [evc, evl] = eig(double(A{i}));

        % We only need the eigenvector associated with a zero eigenvalue
        evl = diag(evl);
        dual_u{i} = evc(:,abs(evl) == min(abs(evl)));

        % Calculate mineigratio
        dual_eigA_ratio = abs(evl(3) / evl(1));
        dual_eval(i) = 1/dual_eigA_ratio;
        
        if dual_eigA_ratio < dual_mineigratio
            dual_mineigratio = dual_eigA_ratio;
        end
    end
end

% Calculate eigenvalues from primal problem (W matrices)
if recover_voltage == 2 || recover_voltage == 3  || recover_voltage == 4
    primal_mineigratio = inf;
    primal_eval = nan(length(A),1);
    for i=1:length(A)
        [evc, evl] = eig(double(dual(constraints(Aconstraints(i)))));

        % We only need the eigenvector associated with a non-zero eigenvalue
        evl = diag(evl);
        primal_u{i} = evc(:,abs(evl) == max(abs(evl)));

        % Calculate mineigratio
        primal_eigA_ratio = abs(evl(end) / evl(end-2));
        primal_eval(i) = 1/primal_eigA_ratio;
        
        if primal_eigA_ratio < primal_mineigratio
            primal_mineigratio = primal_eigA_ratio;
        end
    end
end

if recover_voltage == 3 || recover_voltage == 4
    recover_voltage_loop = [1 2];
else
    recover_voltage_loop = recover_voltage;
end
    
for r = 1:length(recover_voltage_loop)
    
    if recover_voltage_loop(r) == 1
        if verbose >= 2
            fprintf('Recovering dual solution.\n');
        end
        u = dual_u;
        eval = dual_eval;
        mineigratio = dual_mineigratio;
    elseif recover_voltage_loop(r) == 2
        if verbose >= 2
            fprintf('Recovering primal solution.\n');
        end
        u = primal_u;
        eval = primal_eval;
        mineigratio = primal_mineigratio;
    else
        error('sdpopf_solver: Invalid recover_voltage');
    end
 
    % Create a linear equation to match up terms from different matrices
    % Each matrix gets two unknown parameters: alpha and beta.
    % The unknown vector is arranged as [alpha1; alpha2; ... ; beta1; beta2 ; ...]
    % corresponding to the matrices representing maxclique{1}, maxclique{2}, etc.
    Aint = [];
    Aslack = [];
    slackbus_idx = find(mpc.bus(:,2) == 3);
    for i=1:nmaxclique
        maxcliquei = maxclique{i};
        for k=i+1:nmaxclique
            
            temp = maxcliquei(ismembc(maxcliquei, maxclique{k}));
            
            % Slower alternative that does not use undocumented MATLAB
            % functions:
            % temp = intersect(maxclique{i},maxclique{k});
            
            Aint = [Aint; i*ones(length(temp),1) k*ones(length(temp),1) temp(:)];
        end

        if any(maxcliquei == slackbus_idx)
            Aslack = i;
        end
    end
    if nmaxclique > 1
        L = sparse(2*length(Aint(:,1))+1,2*nmaxclique);
    else
        L = sparse(1,2);
    end
    Lrow = 0; % index the equality
    for i=1:size(Aint,1)
        % first the real part of the voltage
        Lrow = Lrow + 1;
        L(Lrow,Aint(i,1)) = u{Aint(i,1)}(maxclique{Aint(i,1)}(:) == Aint(i,3));
        L(Lrow,Aint(i,1)+nmaxclique) = -u{Aint(i,1)}(find(maxclique{Aint(i,1)}(:) == Aint(i,3))+length(maxclique{Aint(i,1)}(:)));
        L(Lrow,Aint(i,2)) = -u{Aint(i,2)}(maxclique{Aint(i,2)}(:) == Aint(i,3));
        L(Lrow,Aint(i,2)+nmaxclique) = u{Aint(i,2)}(find(maxclique{Aint(i,2)}(:) == Aint(i,3))+length(maxclique{Aint(i,2)}(:)));

        % then the imaginary part of the voltage
        Lrow = Lrow + 1;
        L(Lrow,Aint(i,1)) = u{Aint(i,1)}(find(maxclique{Aint(i,1)}(:) == Aint(i,3))+length(maxclique{Aint(i,1)}(:)));
        L(Lrow,Aint(i,1)+nmaxclique) = u{Aint(i,1)}(maxclique{Aint(i,1)}(:) == Aint(i,3));
        L(Lrow,Aint(i,2)) = -u{Aint(i,2)}(find(maxclique{Aint(i,2)}(:) == Aint(i,3))+length(maxclique{Aint(i,2)}(:)));
        L(Lrow,Aint(i,2)+nmaxclique) = -u{Aint(i,2)}(maxclique{Aint(i,2)}(:) == Aint(i,3));
    end

    % Add in angle reference constraint, which is linear
    Lrow = Lrow + 1;
    L(Lrow,Aslack) = u{Aslack}(find(maxclique{Aslack}(:) == slackbus_idx)+length(maxclique{Aslack}(:)));
    L(Lrow,Aslack+nmaxclique) = u{Aslack}(maxclique{Aslack}(:) == slackbus_idx);

    % Get a vector in the nullspace
    if nmaxclique == 1 % Will probably get an eigenvalue exactly at zero. Only a 2x2 matrix, just do a normal eig
        [LLevec,LLeval] = eig(full(L).'*full(L));
        LLeval = LLeval(1);
        LLevec = LLevec(:,1);
    else
        % sometimes get an error when the solution is "too good" and we have an
        % eigenvalue very close to zero. eigs can't handle this situation
        % eigs is necessary for large numbers of loops, which shouldn't 
        % have exactly a zero eigenvalue. For small numbers of loops,
        % we can just do eig. First try eigs, if it fails, then try eig.
        try
            warning off
            [LLevec,LLeval] = eigs(L.'*L,1,'SM');
            warning(S);
        catch
            [LLevec,LLeval] = eig(full(L).'*full(L));
            LLeval = LLeval(1);
            LLevec = LLevec(:,1);
            warning(S);
        end
    end

    % Form a voltage vector from LLevec. Piece together the u{i} to form
    % a big vector U. This vector has one degree of freedom in its length.
    % When we get values that are inconsistent (due to numerical errors if
    % the SDP OPF satisifes the rank condition), take an average of the
    % values, weighted by the corresponding eigenvalue.
    U = sparse(2*nbus,nmaxclique);
    Ueval = sparse(2*nbus,nmaxclique); 
    for i=1:nmaxclique
        newentries = [maxclique{i}(:); maxclique{i}(:)+nbus];
        newvals_phasor = (u{i}(1:length(maxclique{i}))+1i*u{i}(length(maxclique{i})+1:2*length(maxclique{i})))*(LLevec(i)+1i*LLevec(i+nmaxclique));
        newvals = [real(newvals_phasor(:)); imag(newvals_phasor(:))];

        Ueval(newentries,i) = 1/eval(i);
        U(newentries,i) = newvals;

    end
    Ueval_sum = sum(Ueval,2);
    for i=1:2*nbus
        Ueval(i,:) = Ueval(i,:) / Ueval_sum(i);
    end
    U = full(sum(U .* Ueval,2));

    % Find the binding voltage constraint with the largest Lagrange multiplier
    muL_val = abs(double(muL_sdp(mu_ineq)));
    muU_val = abs(double(muU_sdp(mu_ineq)));

    [maxmuU,binding_voltage_busU] = max(muU_val);
    [maxmuL,binding_voltage_busL] = max(muL_val);

    if (maxmuU < binding_lagrange) && (maxmuL < binding_lagrange)
        if verbose > 1
            fprintf('No binding voltage magnitude. Attempting solution recovery from line-flow constraints.\n');
        end

        % No voltage magnitude limits are binding. 
        % Try to recover the solution from binding line flow limits.
        % This should cover the vast majority of cases

        % First try to find a binding line flow limit.
        largest_H_norm = 0;
        largest_H_norm_idx = 0;
        for i=1:length(Hsdp)
            if norm(double(Hsdp{i})) > largest_H_norm
                largest_H_norm = norm(double(Hsdp{i}));
                largest_H_norm_idx = i;
            end
        end

        if largest_H_norm < binding_lagrange
            if verbose > 1
                error('sdpopf_solver: No binding voltage magnitude or line-flow limits, and no PQ buses. Error recovering solution.');
            end
        else
            % Try to recover solution from binding line-flow limit
            if Hlookup(largest_H_norm_idx,2) == 1
                [Yline_row, Yline_col, Yline_val] = find(Ylineft(Hlookup(largest_H_norm_idx,1)));
                [Y_line_row, Y_line_col, Y_line_val] = find(Y_lineft(Hlookup(largest_H_norm_idx,1)));
            else
                [Yline_row, Yline_col, Yline_val] = find(Ylinetf(Hlookup(largest_H_norm_idx,1)));
                [Y_line_row, Y_line_col, Y_line_val] = find(Y_linetf(Hlookup(largest_H_norm_idx,1)));
            end
            trYlineUUT = 0;
            for i=1:length(Yline_val)
                trYlineUUT = trYlineUUT + Yline_val(i) * U(Yline_row(i))*U(Yline_col(i));
            end
            
            if upper(mpopt.opf.flow_lim(1)) == 'S'
                trY_lineUUT = 0;
                for i=1:length(Y_line_val)
                    trY_lineUUT = trY_lineUUT + Y_line_val(i) * U(Y_line_row(i))*U(Y_line_col(i));
                end
                chi = (Smax(Hlookup(largest_H_norm_idx,1))^2 / ( trYlineUUT^2 + trY_lineUUT^2 ) )^(0.25);
            elseif upper(mpopt.opf.flow_lim(1)) == 'P'
                % We want to scale U so that trace(chi^2*U*U.') = Smax
                chi = sqrt(Smax(Hlookup(largest_H_norm_idx,1)) / trYlineUUT);
            end
            
            U = chi*U;
        end
        
    else % recover from binding voltage magnitude
        if maxmuU > maxmuL
            binding_voltage_bus = binding_voltage_busU;
            binding_voltage_mag = Vmax(binding_voltage_bus);
        else
            binding_voltage_bus = binding_voltage_busL;
            binding_voltage_mag = Vmin(binding_voltage_bus);
        end
        chi = binding_voltage_mag^2 / (U(binding_voltage_bus)^2 + U(binding_voltage_bus+nbus)^2);
        U = sqrt(chi)*U;
    end

    Vopt = (U(1:nbus) + 1i*U(nbus+1:2*nbus));

    if real(Vopt(slackbus_idx)) < 0
        Vopt = -Vopt;
    end
    
    if recover_voltage == 3 || recover_voltage == 4
        Sopt = Vopt .* conj(Y*Vopt);
        PQerr = norm([real(Sopt(bustype(:) == PQ))*100+mpc.bus(bustype(:) == PQ,PD); imag(Sopt(bustype(:) == PQ))*100+mpc.bus(bustype(:) == PQ,QD)], 2);
        if recover_voltage_loop(r) == 1
            Vopt_dual = Vopt;
            dual_PQerr = PQerr;
        elseif recover_voltage_loop(r) == 2
            Vopt_primal = Vopt;
            primal_PQerr = PQerr;
        end
    end
end

if recover_voltage == 3
    if dual_PQerr > primal_PQerr
        fprintf('dual_PQerr: %g MW. primal_PQerr: %g MW. Using primal solution.\n',dual_PQerr,primal_PQerr)
        Vopt = Vopt_primal;
    else
        fprintf('dual_PQerr: %g MW. primal_PQerr: %g MW. Using dual solution.\n',dual_PQerr,primal_PQerr)
        Vopt = Vopt_dual;
    end
elseif recover_voltage == 4
    if primal_mineigratio > dual_mineigratio
        if verbose >= 2
            fprintf('dual_mineigratio: %g. primal_mineigratio: %g. Using primal solution.\n',dual_mineigratio,primal_mineigratio)
        end
        Vopt = Vopt_primal;
    else
        if verbose >= 2
            fprintf('dual_mineigratio: %g. primal_mineigratio: %g. Using dual solution.\n',dual_mineigratio,primal_mineigratio)
        end
        Vopt = Vopt_dual;
    end
end

% Store voltages
for i=1:nbus
    mpc.bus(i,VM) = abs(Vopt(i));
    mpc.bus(i,VA) = angle(Vopt(i))*180/pi;
    mpc.gen(mpc.gen(:,GEN_BUS) == i,VG) = abs(Vopt(i));
end


%% Calculate power injections

if recover_injections == 2
    % Calculate directly from the SDP solution
    
    for i=1:length(A)
        W{i} = dual(constraints(Aconstraints(i)));
    end

    Pinj = zeros(nbus,1);
    Qinj = zeros(nbus,1);
    for i=1:nbus

        % Active power injection
        Pinj(i) = recoverFromW(Yk(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, W, maxclique);

        % Reactive power injection
        Qinj(i) = recoverFromW(Yk_(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, W, maxclique);

        % Voltage magnitude
%         Vmag(i)  = sqrt(recoverFromW(Mk(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, W, maxclique));       

    end
    
    Pflowft = zeros(nbranch,1);
    Pflowtf = zeros(nbranch,1);
    Qflowft = zeros(nbranch,1);
    Qflowtf = zeros(nbranch,1);
    for i=1:nbranch
        Pflowft(i) = recoverFromW(Ylineft(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, W, maxclique) * Sbase;
        Pflowtf(i) = recoverFromW(Ylinetf(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, W, maxclique) * Sbase;
        Qflowft(i) = recoverFromW(Y_lineft(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, W, maxclique) * Sbase;
        Qflowtf(i) = recoverFromW(Y_linetf(i), Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, W, maxclique) * Sbase;
    end
    
    
elseif recover_injections == 1 
    % Calculate power injections from voltage profile
    Sopt = Vopt .* conj(Y*Vopt);
    Pinj = real(Sopt);
    Qinj = imag(Sopt);
   
    Vf = Vopt(mpc.branch(:,F_BUS));
    Vt = Vopt(mpc.branch(:,T_BUS));
    
    Sft = Vf.*conj(Yf*Vopt);
    Stf = Vt.*conj(Yt*Vopt);
    
    Pflowft = real(Sft) * Sbase;
    Pflowtf = real(Stf) * Sbase;
    Qflowft = imag(Sft) * Sbase;
    Qflowtf = imag(Stf) * Sbase;
end

% Store the original bus ordering
busorder = mpc.bus(:,end);
mpc.bus = mpc.bus(:,1:end-1);
    
% Convert from injections to generation
Qtol = 5e-2;
mpc.gen(:,PG) = 0;
mpc.gen(:,QG) = 0;
for i=1:nbus
    
    if bustype(i) == PV || bustype(i) == REF
        % Find all generators at this bus
        genidx = find(mpc.gen(:,GEN_BUS) == i);

        % Find generator outputs from the known injections by solving an
        % economic dispatch problem at each bus. (Identifying generators at
        % their limits from non-zero dual variables is not numerically
        % reliable.)
        
        % Initialize all generators at this bus
        gen_not_limited_pw = [];
        gen_not_limited_q = [];
        Pmax = mpc.gen(genidx,PMAX);
        Pmin = mpc.gen(genidx,PMIN);
        remove_from_list = [];
        for k=1:length(genidx)
            % Check if this generator is fixed at its midpoint
            if (Pmax(k) - Pmin(k) < minPgendiff * Sbase)
                mpc.gen(genidx(k),PG) = (Pmin(k)+Pmax(k))/2;
                remove_from_list = [remove_from_list; k];
            else
                if mpc.gencost(genidx(k),MODEL) == PW_LINEAR
                    gen_not_limited_pw = [gen_not_limited_pw; genidx(k)];
                    mpc.gen(genidx(k),PG) = mpc.gen(genidx(k),PMIN);
                else
                    gen_not_limited_q = [gen_not_limited_q; genidx(k)];
                    mpc.gen(genidx(k),PG) = 0;
                end
            end
        end
        Pmax(remove_from_list) = [];
        Pmin(remove_from_list) = [];

        % Figure out the remaining power injections to distribute among the
        % generators at this bus.
        Pgen_remain = Pinj(i) + mpc.bus(i,PD) / Sbase - sum(mpc.gen(genidx,PG)) / Sbase;

        % Use the equal marginal cost criterion to distribute Pgen_remain
        gen_not_limited = [gen_not_limited_q; gen_not_limited_pw];
        if length(gen_not_limited) == 1
            % If only one generator not at its limit, assign the remaining 
            % generation to this generator
            mpc.gen(gen_not_limited,PG) = mpc.gen(gen_not_limited,PG) + Pgen_remain * Sbase;
        elseif length(genidx) == 1
            % If there is only one generator at this bus, assign the
            % remaining generation to this generator.
            mpc.gen(genidx,PG) = mpc.gen(genidx,PG) + Pgen_remain * Sbase;
        else % Multiple generators that aren't at their limits
            
            % We know the LMP at this bus. For that LMP, determine the
            % generation output for each generator.
            
            % For piecewise linear cost functions:
            % Stack Pgen_remain into the generators in the order of
            % cheapest cost.
            if ~isempty(gen_not_limited_pw)
                while Pgen_remain > 1e-5

                    % Find cheapest available segment
                    lc = inf;
                    for geniter = 1:length(gen_not_limited_pw)
                        nseg = mpc.gencost(gen_not_limited_pw(geniter),NCOST)-1;

                        % Get breakpoints for this curve
                        x_pw = mpc.gencost(gen_not_limited_pw(geniter),-1+COST+(1:2:2*nseg+1)) / Sbase; % piecewise powers
                        c_pw = mpc.gencost(gen_not_limited_pw(geniter),-1+COST+(2:2:2*nseg+2)); % piecewise costs

                        for pwidx = 1:nseg
                            m_pw = (c_pw(pwidx+1) - c_pw(pwidx)) / (x_pw(pwidx+1) - x_pw(pwidx)); % slope for this piecewise cost segement
                            if x_pw(pwidx) > mpc.gen(gen_not_limited_pw(geniter),PG)/Sbase
                                x_min = x_pw(pwidx-1);
                                x_max = x_pw(pwidx);
                                break;
                            end
                        end

                        if m_pw < lc
                            lc = m_pw;
                            lc_x_min = x_min;
                            lc_x_max = x_max;
                            lc_geniter = geniter;
                        end

                    end
                    if mpc.gen(gen_not_limited_pw(lc_geniter), PG) + min(Pgen_remain, lc_x_max-lc_x_min)*Sbase < Pmax(lc_geniter)
                        % If we don't hit the upper gen limit, add up to the
                        % breakpoint for this segment to the generation.
                        mpc.gen(gen_not_limited_pw(lc_geniter), PG) = mpc.gen(gen_not_limited_pw(lc_geniter), PG) + min(Pgen_remain, lc_x_max-lc_x_min)*Sbase;
                        Pgen_remain = Pgen_remain - min(Pgen_remain, lc_x_max-lc_x_min);
                    else
                        % If we hit the upper generation limit, set the
                        % generator to this limit and remove it from the list
                        % of genenerators below their limit.
                        Pgen_remain = Pgen_remain - (Pmax(lc_geniter) - mpc.gen(gen_not_limited_pw(lc_geniter), PG));
                        mpc.gen(gen_not_limited_pw(lc_geniter), PG) = Pmax(lc_geniter);
                        gen_not_limited_pw(lc_geniter) = [];
                        Pmax(lc_geniter) = [];
                        Pmin(lc_geniter) = [];
                    end
                end
            end
            
            
            % For generators with quadratic cost functions:
            % Solve the quadratic program that is the economic dispatch
            % problem at this bus.
            if ~isempty(gen_not_limited_q)
                
                Pg_q = sdpvar(length(gen_not_limited_q),1);
                cost_q = Pg_q.' * diag(c2(gen_not_limited_q)) * Pg_q + c1(gen_not_limited_q).' * Pg_q;
                
                % Specifying no generator costs leads to numeric problems
                % in the solver. If no generator costs are specified,
                % assign uniform costs for all generators to assign active
                % power generation at this bus.
                if isnumeric(cost_q)
                    cost_q = sum(Pg_q);
                end
                
                constraints_q = [Pmin/Sbase <= Pg_q <= Pmax/Sbase;
                                 sum(Pg_q) == Pgen_remain];
                sol_q = solvesdp(constraints_q,cost_q, sdpsettings(sdpopts,'Verbose',0,'saveduals',0));
                
                % This problem should have a feasible solution if we have a
                % rank 1 solution to the OPF problem. However, it is
                % possible that no set of power injections satisfies the
                % power generation constraints if we recover the closest
                % rank 1 solution from a higher rank solution to the OPF
                % problem.
                
                constraint_q_err = checkset(constraints_q);
                if sol_q.problem == 0 || max(abs(constraint_q_err)) < 1e-3 % If error in assigning active power generation is less than 0.1 MW, ignore it
                    mpc.gen(gen_not_limited_q, PG) = double(Pg_q) * Sbase;
                elseif sol_q.problem == 4 || sol_q.problem == 1
                    % Solutions with errors of "numeric problems" or "infeasible" are
                    % typically pretty close. Use the solution but give a
                    % warning.
                    mpc.gen(gen_not_limited_q, PG) = double(Pg_q) * Sbase;
                    warning('sdpopf_solver: Numeric inconsistency assigning active power injection to generators at bus %i.',busorder(i));
                else
                    % If there is any other error, just assign active power
                    % generation equally among all generators without
                    % regard for active power limits.
                    mpc.gen(gen_not_limited_q, PG) = (Pgen_remain / length(gen_not_limited_q))*Sbase;
                    warning('sdpopf_solver: Error assigning active power injection to generators at bus %i. Assiging equally among all generators at this bus.',busorder(i));
                end
                
            end
            
        end

        % Now assign reactive power generation. <-- Problem: positive
        % reactive power lower limits causes problems. Initialize all
        % generators to lower limits and increase as necessary.
        mpc.gen(genidx,QG) = mpc.gen(genidx,QMIN);
        Qremaining = (Qinj(i) + Qd(i))*Sbase - sum(mpc.gen(genidx,QG));
        genidx_idx = 1;
        while abs(Qremaining) > Qtol && genidx_idx <= length(genidx)
            if mpc.gen(genidx(genidx_idx),QG) + Qremaining <= mpc.gen(genidx(genidx_idx),QMAX) % && mpc.gen(genidx(genidx_idx),QG) + Qremaining >= mpc.gen(genidx(genidx_idx),QMIN)
                mpc.gen(genidx(genidx_idx),QG) = mpc.gen(genidx(genidx_idx),QG) + Qremaining;
                Qremaining = 0;
            else
                Qremaining = Qremaining - (mpc.gen(genidx(genidx_idx),QMAX) - mpc.gen(genidx(genidx_idx),QG));
                mpc.gen(genidx(genidx_idx),QG) = mpc.gen(genidx(genidx_idx),QMAX);
            end
            genidx_idx = genidx_idx + 1;
        end
        if abs(Qremaining) > Qtol
            % If the total reactive generation specified is greater than 
            % the reactive generation available, assign the remainder to
            % equally to all generators at the bus.
            mpc.gen(genidx,QG) = mpc.gen(genidx,QG) + Qremaining / length(genidx);
            warning('sdpopf_solver: Inconsistency in assigning reactive power to generators at bus index %i.',i);
        end
    end
end

% Line flows (PF, PT, QF, QT)
mpc.branch(:,PF) = Pflowft;
mpc.branch(:,PT) = Pflowtf;
mpc.branch(:,QF) = Qflowft;
mpc.branch(:,QT) = Qflowtf;


% Store bus Lagrange multipliers into results
mpc.bus(:,LAM_P) = -double(lambdaeq_sdp) / Sbase;
for i=1:nbus
    if ~isnan(gamma_eq(i))
        mpc.bus(i,LAM_Q) = -double(gammaeq_sdp(gamma_eq(i))) / Sbase;
    elseif Qmin(i) >= -maxgenlimit && Qmax(i) <= maxgenlimit % bus has both upper and lower Q limits
        mpc.bus(i,LAM_Q) = (double(gammaU_sdp(gamma_ineq(i))) - double(gammaL_sdp(gamma_ineq(i)))) / Sbase;
    elseif Qmax(i) <= maxgenlimit % bus has only upper Q limit
        mpc.bus(i,LAM_Q) = double(gammaU_sdp(gamma_ineq(i))) / Sbase;
    elseif Qmin(i) >= -maxgenlimit % bus has only lower Q limit
        mpc.bus(i,LAM_Q) = double(gammaL_sdp(gamma_ineq(i))) / Sbase;
    else % bus has no reactive power limits, so cost for reactive power is zero
        mpc.bus(i,LAM_Q) = 0;
    end
end

% Convert Lagrange multipliers to be in terms of voltage magntiude rather
% than voltage magnitude squared.

mpc.bus(:,MU_VMAX) = 2*abs(Vopt) .* double(muU_sdp);
mpc.bus(:,MU_VMIN) = 2*abs(Vopt) .* double(muL_sdp);

% Store gen Lagrange multipliers into results
for i=1:nbus
    genidx = find(mpc.gen(:,GEN_BUS) == i);
    for k=1:length(genidx)
        if ~isnan(double(psiU_sdp{i}(k))) && ~isnan(double(psiU_sdp{i}(k)))
            mpc.gen(genidx(k),MU_PMAX) = double(psiU_sdp{i}(k)) / Sbase;
            mpc.gen(genidx(k),MU_PMIN) = double(psiL_sdp{i}(k)) / Sbase;
        else % Handle generators with tight generation limits

            % Calculate generalized Lagrange multiplier R for this generator
            % To do so, first calculate the dual of R (primal matrix)
            Pavg = (mpc.gen(genidx(k),PMAX)+mpc.gen(genidx(k),PMIN))/(2*Sbase);
            c0k = mpc.gencost(genidx(k),COST+2);
            alphak = c2(genidx(k))*Pavg^2 + c1(genidx(k))*Pavg + c0k;
            
            %  dualR = [-c1(genidx(k))*Pavg+alphak-c0k -sqrt(c2(genidx(k)))*Pavg;
            %          -sqrt(c2(genidx(k)))*Pavg 1] >= 0;
             
            % At the optimal solution, trace(dualR*R) = 0 and det(R) = 0
            %  -c1(genidx(k))*Pavg+alphak-c0k + R22 + -2*sqrt(c2(genidx(k)))*Pavg*R12 = 0 % trace(dualR*R) = 0
            %  R22 - R12^2 = 0                                                            % det(R) = 0
            
            % Rearranging these equations gives
            % -c1(genidx(k))*Pavg+alphak-c0k + R12^2 - 2*sqrt(c2(genidx(k)))*Pavg*R12 = 0
            
            % Solve with the quadratic equation
            a = 1;
            b = -2*sqrt(c2(genidx(k)))*Pavg;
            c = -c1(genidx(k))*Pavg+alphak-c0k;
            R12 = (-b+sqrt(b^2-4*a*c)) / (2*a);
            if abs(imag(R12)) > 1e-3
                warning('sdpopf_solver: R12 has a nonzero imaginary component. Lagrange multipliers for generator active power limits may be incorrect.');
            end
            R12 = real(R12);
            
            % With R known, calculate psi
            % c1(genidx(i)) + 2*sqrt(c2(genidx(i)))*R{k}{i}(1) + psi == lambdai 
            psi_tight = -double(lambdaeq_sdp(lambda_eq(i))) / Sbase - c1(genidx(k)) / Sbase - 2*sqrt(c2(genidx(k))/Sbase^2)*R12;
            if psi_tight < 0
                mpc.gen(genidx(k),MU_PMAX) = 0;
                mpc.gen(genidx(k),MU_PMIN) = -psi_tight;
            else
                mpc.gen(genidx(k),MU_PMAX) = psi_tight;
                mpc.gen(genidx(k),MU_PMIN) = 0;
            end
        end
    end
    if ~isempty(genidx)
        if ~isnan(gamma_eq(i))
            gamma_tight = double(gammaeq_sdp(gamma_eq(i))) / Sbase;
            if gamma_tight > 0 
                mpc.gen(genidx(k),MU_QMAX) = 0;
                mpc.gen(genidx(k),MU_QMIN) = double(gammaeq_sdp(gamma_eq(i))) / Sbase;
            else
                mpc.gen(genidx(k),MU_QMAX) = -double(gammaeq_sdp(gamma_eq(i))) / Sbase;
                mpc.gen(genidx(k),MU_QMIN) = 0;
            end
        else
            if any(Qmin(i) < -maxgenlimit) % bus has no lower Q limit
                mpc.gen(genidx,MU_QMIN) = 0;
            else
                mpc.gen(genidx,MU_QMIN) = double(gammaL_sdp(gamma_ineq(i))) / Sbase;
            end

            if any(Qmax(i) > maxgenlimit) % bus has no upper Q limit
                mpc.gen(genidx,MU_QMAX) = 0;
            else
                mpc.gen(genidx,MU_QMAX) = double(gammaU_sdp(gamma_ineq(i))) / Sbase;
            end
        end
    end
end

% Line flow Lagrange multipliers are calculated in terms of squared
% active and reactive power line flows. 
%
% Calculate line-flow limit Lagrange multipliers for MVA limits as follows.
% temp = Hsdp{i} ./ Sbase;
% 2*sqrt((temp(1,2)^2 + temp(1,3)^2))
if nlconstraint > 0
    for i=1:nbranch
        Hidx = Hlookup(:,1) == i & Hlookup(:,2) == 1;
        if any(Hidx)
            if upper(mpopt.opf.flow_lim(1)) == 'S'
                Hft = double(Hsdp{Hidx}) ./ Sbase;
                mpc.branch(i,MU_SF) = 2*sqrt((Hft(1,2)^2 + Hft(1,3)^2));
                Htf = double(Hsdp{Hlookup(:,1) == i & Hlookup(:,2) == 0}) ./ Sbase;
                mpc.branch(i,MU_ST) = 2*sqrt((Htf(1,2)^2 + Htf(1,3)^2));
            elseif upper(mpopt.opf.flow_lim(1)) == 'P'
                mpc.branch(i,MU_SF) = Hsdp(Hidx) / Sbase;
                mpc.branch(i,MU_ST) = Hsdp(Hlookup(:,1) == i & Hlookup(:,2) == 0) / Sbase;
            end
        else
            mpc.branch(i,MU_SF) = 0;
            mpc.branch(i,MU_ST) = 0;
        end
    end
else
    mpc.branch(:,MU_SF) = 0;
    mpc.branch(:,MU_ST) = 0;
end

% Angle limits are not implemented
mpc.branch(:,MU_ANGMIN) = nan;
mpc.branch(:,MU_ANGMAX) = nan;

% Objective value
mpc.f = objval;

%% Convert back to original bus ordering

mpc.bus(:,BUS_I) = busorder;
mpc.bus = sortrows(mpc.bus,1);

for i=1:ngen
    mpc.gen(i,GEN_BUS) = busorder(mpc.gen(i,GEN_BUS));
end

[mpc.gen genidx] = sortrows(mpc.gen,1);
mpc.gencost = mpc.gencost(genidx,:);

for i=1:nbranch
    mpc.branch(i,F_BUS) = busorder(mpc.branch(i,F_BUS));
    mpc.branch(i,T_BUS) = busorder(mpc.branch(i,T_BUS));
end


%% Generate outputs

results = mpc;
success = mineigratio > mineigratio_tol && LLeval < zeroeval_tol;

raw.xr.A = A; 
if recover_injections == 2
    raw.xr.W = W;
else
    raw.xr.W = [];
end

raw.pimul.lambdaeq_sdp = lambdaeq_sdp;
raw.pimul.gammaeq_sdp = gammaeq_sdp;
raw.pimul.gammaU_sdp = gammaU_sdp;
raw.pimul.gammaL_sdp = gammaL_sdp;
raw.pimul.muU_sdp = muU_sdp;
raw.pimul.muL_sdp = muL_sdp;
raw.pimul.psiU_sdp = psiU_sdp;
raw.pimul.psiL_sdp = psiL_sdp;

raw.info = sdpinfo.problem;

results.zero_eval = LLeval;
results.mineigratio = mineigratio;

results.sdpinfo = sdpinfo;

toutput = toc;
results.et = tsetup + tmaxclique + tsdpform + tsolve + toutput;
