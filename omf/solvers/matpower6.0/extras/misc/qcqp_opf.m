function [nVAR, nEQ, nINEQ, C, c, A, a, B, b, S] = qcqp_opf(casedata,model)
%QCQP_OPF   Builds a quadratically-constrained quadratic program.
%   [nVAR, nEQ, nINEQ, C, c, A, a, B, b] = QCQP_OPF(CASEDATA,MODEL)
%
%   Inputs (all are optional):
%       CASEDATA : either a MATPOWER case struct or a string containing
%           the name of the file with the case data (default is 'case9')
%           (see also CASEFORMAT and LOADCASE)
%       MODEL : number equal to 0, 1, or 2 to indicate whether the output
%       matrices are desired to be complex (default value 0), Hermitian
%       (value 1), or real symmetric (value 2).
%
%   Outputs (all are optional):
%       nVAR : number of variables
%       nEQ : number of equality constraints
%       nINEQ : number of inequality constraints
%       C : square matrix of size nVAR defining the coefficients in the
%       cost function
%       c : real number defining the constant term in the cost function
%       A : cell array of square matrices, each of size nVAR, defining the
%       coefficients in the equality constraints
%       a : column vector of size nEQ defining the constant terms in the
%       equality constraints
%       B : cell array of square matrices, each of size nVAR, defining the
%       coefficients in the inequality constraints
%       b : column vector of size nINEQ defining the constant terms in the
%       inequality constraints
%       S : two row matrix which contains the sparsity pattern of the
%       quadratically-constrained quadratic program, that is to say the set
%       of indexes i and j between 1 and nVAR such that either x_i x_j,
%       x_i x_j', or x_i' x_j has a nonzero coefficient in the objective or
%       constraint functions. (The apostrophe stands for complex
%       conjugate).
%
%   Examples:
%       [nVAR, nEQ, nINEQ, C, c, A, a, B, b, S] = qcqp_opf(case9,0);
%       [nVAR, nEQ, nINEQ, C, c, A, a, B, b, S] = qcqp_opf(case9,1);
%       [nVAR, nEQ, nINEQ, C, c, A, a, B, b, S] = qcqp_opf(case9,2);
%       [nVAR, nEQ, nINEQ, C, c, A, a, B, b, S] = qcqp_opf(case89pegase);
%       [nVAR, nEQ, nINEQ, C, c, A, a, B, b, S] = qcqp_opf(case9241pegase);
%
%   The optimal power flow problem can be viewed as an instance of
%   quadratically-constrained quadratic programming. In order for this to
%   be true, we consider the objective function of the optimal power flow
%   problem to be a linear function of active power. Higher degree terms
%   are discarded from the objective function. Moreover, current line flow
%   constraints are enforced instead of apparent line flow constraints in
%   order to have quadratic constraints only. The optimal power flow
%   problem remains non-convex despite the slightly simplified framework
%   we consider.
%
%   The output of this code defines the problem that consists in solving
%   for a column vector variable x of size nVAR with the aim to
%
%   minimize
%
%   x' * C * x   +   c
%
%   subject to nEQ equality constraints:
%
%   x' * A{k} * x = a(k) ,   k = 1,...,nEQ,
%
%   and subject to nINEQ inequality constraints
%
%   x' * B{k} * x <= b(k) ,   k = 1,...,nINEQ,
%
%   where the apostrophe stands for conjugate transpose.
%   
%   If MODEL == 0 (default value), then
%   1) x, a, and b are complex vectors;
%   2) C is a Hermitian matrix;
%   3) A{1}, ..., A{nEQ}, B{1}, ..., and B{nINEQ} are complex matrices;
%   4) for k = 1,...,nINEQ, the inequality x' * B{k} * x <= b(k) is defined
%   by real(x' * B{k} * x) <= real(b(k)) and imag(x' * B{k} * x) <=
%   imag(b(k));
%   5) x corresponds to the complex voltages at each bus.
%
%   If MODEL == 1, then
%   1) x is complex vector;
%   2) a and b are real vectors;
%   3) C, A{1}, ..., A{nEQ}, B{1}, ..., and B{nINEQ} are Hermitian
%   matrices;
%   4) x corresponds to the complex voltages at each bus.
%
%   If MODEL == 2, then
%   1) x, a, and b are real vectors;
%   2) C, A{1}, ..., A{nEQ}, B{1}, ..., and B{nINEQ} are real symmetric
%   matrices;
%   3) x corresponds to the real parts of the complex voltages at each bus
%   followed by the imaginary parts of the complex voltages at each bus.
%
%   When publishing results based on this code, please cite:
%
%     C. Josz, S. Fliscounakis, J. Maeght, and P. Panciatici, "AC Power Flow
%     Data in MATPOWER and QCQP Format: iTesla, RTE Snapshots, and PEGASE"
%     http://arxiv.org/abs/1603.01533
%
%   Contacts:
%     Cédric Josz, Stéphane Fliscounakis, Jean Maeght, Patrick Panciatici
%     firstname.lastname@rte-france.com
%     Réseau de Transport d'Electricité (French Transmission System Operator)
%     Département Expertise Système, Immeuble "Le Colbert"
%     9 rue de la Porte de Buc, 78000 Versailles Cedex, France
%
%   March 4th, 2016

%   MATPOWER
%   Copyright (c) 2016, Power Systems Engineering Research Center (PSERC)
%   by Cedric Josz, Jean Maeght, Stephane Fliscounakis, and Patrick Panciatici
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% default arguments
if nargin < 2
    model = 0; % default output are complex matrices
    if nargin < 1
        casedata = 'case9'; % default data file is 'case9.m'
    end
end

%% compute admittance matrix
casedata = loadcase(casedata);
mpc = ext2int(casedata);
[Ybus, Yf, Yt] = makeYbus(mpc);
if isfield(mpc,'gencost') == 0
    error('Reference to non-existent field ''gencost''.');
end
if size(mpc.gen,1) ~= size(mpc.gencost)
    error('mpc.gen/mpc.gencost: gen and gencost must have the same number of rows');
end
Ybus = mpc.baseMVA*Ybus; % conversion from per unit to physical unit scaling
% All constraints are in physical units apart from current flow constraints
% which are in per units for better conditioning.

%% define named indices
define_constants;
PQbus = mpc.bus(mpc.bus(:,BUS_TYPE) == 1,BUS_I); % PQ bus numbers
nPQbus = length(PQbus); % number of PQ buses
PVbus = mpc.bus(mpc.bus(:,BUS_TYPE) ~= 1,BUS_I); % PV bus numbers
nPVbus = length(PVbus); % number of PV buses
LFbound = find(mpc.branch(:,RATE_A)>0); % numbers of branches with flow bounds
nLFbound = length(LFbound); % number of lines with flow bounds

%% build cost matrix
% linear function of active power
if sum( mpc.gencost(:,MODEL) ~= 2*ones(size(mpc.gen,1),1) )
    error('mpc.gencost: the objective must be a polynomial and cannot contain piecewise linear terms');
end
nbus = size(mpc.bus,1); % number of buses
nVAR = nbus; % number of variables
costs = zeros(nbus,1);
costs(mpc.gen(:,GEN_BUS)) = mpc.gencost(:,end-1); % extracting linear cost coefficients that multiply active power in optimal power flow objective function
P = sparse(diag(costs)*Ybus);
C = (P'+P)/2;
c = sum(costs.*mpc.bus(:,PD)) + sum(mpc.gencost(:,end)); % extracting constant costs in optimal power flow objective function

%% build equality matrix and vector
% power balance equations
nEQ = nPQbus; % number of constraints
A = cell(nEQ,1); % initializing cell array
a = zeros(nEQ,1); % initializing vector
for k = 1:nPQbus
    num = PQbus(k); % bus number
    % The next two lines encode
    % V(num)*I(num)' = I' e_num e_num' V = ...
    % V' ( Ybus' e_num e_num' ) V = - Pdem(num) - 1i*Qdem(num)
    % where e_num is the column vector of size nVAR that contains only one
    % nonzero element in position num equal to 1. Matrix Ybus' e_num e_num'
    % is equal to Ybus' where all columns except column k are set to zero.
    A{k} = sparse(1:nVAR, num, Ybus(num,:)', nVAR, nVAR);
    a(k) = -mpc.bus(num,PD) - 1i*mpc.bus(num,QD);
end

%% build inequality matrix and vector

nINEQ = 2*nbus+2*nLFbound+2*nPVbus;
B = cell(nINEQ,1);
b = zeros(nINEQ,1);

% voltage magnitude bounds
for k = 1:nbus
    % The next three lines encode
    % Vmin(k)^2 <= |V(k)|^2 <= Vmax(k)^2
    B{2*k-1} = sparse(k,k,1,nbus,nbus);
    B{2*k}   = sparse(k,k,-1,nbus,nbus);
    b(2*k-1:2*k) = [ mpc.bus(k,VMAX).^2 ; -mpc.bus(k,VMIN).^2 ] ;
end

% current flow bounds
count = 2*nbus;
for k = 1:nLFbound
    num = LFbound(k); % branch number
    yf = Yf(num,:); % If = Yf * V so If(num) = yf * V where "num" is a branch
    yt = Yt(num,:); % It = Yt * V so It(num) = yt * V where "num" is a branch
    % The next four lines encode:
    % |If(num)|^2 = V' * ( yf'*yf ) * V <= Imax(num)^2
    % |It(num)|^2 = V' * ( yt'*yt ) * V <= Imax(num)^2
    % Per unit scaling is used for better conditioning.
    B{count+2*k-1} = sparse(yf'*yf);
    B{count+2*k}   = sparse(yt'*yt);
    b(count+(2*k-1:2*k)) = [ (mpc.branch(num,RATE_A)/mpc.baseMVA).^2 ; ...
                             (mpc.branch(num,RATE_A)/mpc.baseMVA).^2 ];
end

% power generation bounds
count = count+2*nLFbound;
for k = 1:nPVbus
    num = PVbus(k); % bus number
    % The next six lines encode
    % Smin(num) - Sdem(num) <= V(num)*I(num)' <= Smax(num) - Sdem(num)
    % where Smin and Smax are lower and upper bounds on complex power
    % generation, and where Sdem is the complex power demand.
    B{count+2*k-1} = sparse(1:nVAR, num,  Ybus(num,:)', nVAR, nVAR);
    B{count+2*k}   = sparse(1:nVAR, num, -Ybus(num,:)', nVAR, nVAR);
    mult_gen = find(mpc.gen(:,GEN_BUS) == num);
    b(count+(2*k-1:2*k)) = ...
    [    sum(mpc.gen(mult_gen,PMAX))-mpc.bus(num,PD) + 1i*( sum(mpc.gen(mult_gen,QMAX))-mpc.bus(num,QD) ) ; ... % upper bound on complex power generation
      -( sum(mpc.gen(mult_gen,PMIN))-mpc.bus(num,PD) + 1i*( sum(mpc.gen(mult_gen,QMIN))-mpc.bus(num,QD) ) ) ];  % lower bound on complex power generation
end

% Compute sparsity pattern
S = unique(sort(mpc.branch(:,1:2),2),'rows');

%% construct Hermitian output (if MODEL == 1)
if model == 1
    
    % equality constraints
    nEQ = 2*nEQ;
    HA = cell(nEQ,1);
    ha = zeros(nEQ,1);
    for k = 1:nEQ/2
        HA{2*k-1} = (A{k}+A{k}')/2;
        HA{2*k}   = (A{k}-A{k}')/(2*1i);
        ha(2*k-1) = real(a(k));
        ha(2*k)   = imag(a(k));
    end
    A = HA;
    a = ha;
    
    % inequality constraints
    nINEQ = 2*nbus+2*nLFbound+2*(2*nPVbus);
    HB = cell(nINEQ,1);
    hb = zeros(nINEQ,1);
    for k = 1:(2*nbus+2*nLFbound)
        HB{k} = B{k};
        hb(k) = b(k);
    end
    for k = (2*nbus+2*nLFbound+1):(2*nbus+2*nLFbound+2*nPVbus)
        HB{-2*nbus-2*nLFbound+2*k-1} = (B{k}+B{k}')/2;
        HB{-2*nbus-2*nLFbound+2*k}   = (B{k}-B{k}')/(2*1i);
        hb(-2*nbus-2*nLFbound+2*k-1) = real(b(k));
        hb(-2*nbus-2*nLFbound+2*k)   = imag(b(k));
    end
    B = HB;
    b = hb;
    
end

%% construct real symmetric output (if MODEL == 2)
if model == 2
    
    % objective function
    C = [real(C) -imag(C); imag(C) real(C)];
    
    % equality constraints
    nEQ = 2*nEQ;
    RA = cell(nEQ,1);
    ra = zeros(nEQ,1);
    for k = 1:nEQ/2
        RA{2*k-1} = (A{k}+A{k}')/2;
        RA{2*k-1} = [real(RA{2*k-1}) -imag(RA{2*k-1}); ...
                     imag(RA{2*k-1})  real(RA{2*k-1})];
        RA{2*k}   = (A{k}-A{k}')/(2*1i);
        RA{2*k}   = [real(RA{2*k}) -imag(RA{2*k}); ...
                     imag(RA{2*k})  real(RA{2*k})];
        ra(2*k-1) = real(a(k));
        ra(2*k)   = imag(a(k));
    end
    A = RA;
    a = ra;
    
    % inequality constraints
    nINEQ = 2*nbus+2*nLFbound+2*(2*nPVbus);
    RB = cell(nINEQ,1);
    rb = zeros(nINEQ,1);
    for k = 1:(2*nbus+2*nLFbound)
        RB{k} = [real(B{k}) -imag(B{k}); imag(B{k}) real(B{k})];
        rb(k) = b(k);
    end
    count = -2*nbus-2*nLFbound;
    for k = (2*nbus+2*nLFbound+1):(2*nbus+2*nLFbound+2*nPVbus)
        RB{count+2*k-1} = (B{k}+B{k}')/2;
        RB{count+2*k-1} = [real(RB{count+2*k-1}) -imag(RB{count+2*k-1}); ...
                           imag(RB{count+2*k-1})  real(RB{count+2*k-1})];
        RB{count+2*k}   = (B{k}-B{k}')/(2*1i);
        RB{count+2*k}   = [real(RB{count+2*k}) -imag(RB{count+2*k}); ...
                           imag(RB{count+2*k})  real(RB{count+2*k})];
        rb(count+2*k-1) = real(b(k));
        rb(count+2*k)   = imag(b(k));
    end
    B = RB;
    b = rb;
    
    % sparsity pattern
    T = zeros(size(S));
    T(:,2) = nVAR;
    U = zeros(size(S));
    U(:,1) = nVAR;
    S = [S; S+T; S+U; S+T+U];
    
    % number of variables
    nVAR = 2*nVAR;
    
end

%% run matlab interior point solver
% to do so, uncomment the following section:
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% mpc.gencost(:,COST) = 0;
% results = runopf(mpc,mpoption('opf.ac.solver','MIPS','opf.flow_lim',...
%           'I','out.suppress_detail','1'));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
