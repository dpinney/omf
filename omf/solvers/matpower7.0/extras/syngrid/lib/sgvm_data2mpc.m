function mpc = sgvm_data2mpc(data, topo, opt)
%SGVM_DATA2MPC create seed MATPOWER case by sampling DATA
%   MPC = SGVM_DATA2MPC(DATA, TOPO, OPT)

%   SGVM_DATA2MPC takes parameter data structure DATA and topology, TOPO,
%   and returns a basic matpower case, mpc.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

%% check inputs and get constants
if nargin < 3
    smpl_opt = opt_default(struct());
else
    smpl_opt = opt_default(opt);
end

nb = max(topo(:));
if ~all(sort(unique(topo(:))) == (1:nb).')
    error('sgvm_data2mpc: topology must use consecutive buses 1:nb')
end
nl = size(topo,1);
define_constants;

%% power base
if isfield(data, 'baseMVA')
    baseMVA = data.baseMVA;
else
    baseMVA = smpl_opt.baseMVA_default;
end

%% branch matrix
branch = branch_initialize(nl, topo);
if isstruct(data.branch)
    tmp = 0;
    for f = {'BR_R', 'BR_X', 'BR_B', 'RATE_A', 'TAP', 'SHIFT'}
        if ~isfield(data.branch, f{:})
            error('sgvm_data2mpc: when provided as a structure, data.branch must have field %s', f{:})
        end
        if tmp == 0
            tmp = length(data.branch.(f{:}));
        else
            if tmp ~= length(data.branch.(f{:}))
                error('sgvm_data2mpc: when provided as a structure, each field of data.branch must be the same length')
            end
        end
    end
    tmpbranch = [data.branch.BR_R, data.branch.BR_X, data.branch.BR_B,...
                            data.branch.RATE_A, data.branch.TAP, data.branch.SHIFT];
else
    tmpbranch = data.branch;
end

switch smpl_opt.branch
case {0, 'none'}
    % use samples as is
    if (size(data.branch,1) == nl) && (size(data.branch,2) == 6) % r, x, b, rate, tap, shift
        branch(:,[BR_R, BR_X, BR_B, RATE_A, TAP, SHIFT]) = tmpbranch;
    else
        error(['sgvm_data2mpc: when using sample method 0:''none'' the provided data matrix must be of length nl.',...
        'nl = %d, # of samples = %d'], nl, size(data.branch,1))
    end
case {1 , 'direct'}
    % sample nl times uniformly at random from data
    idx = randi(size(tmpbranch,1), nl, 1);
    branch(:,[BR_R, BR_X, BR_B, RATE_A, TAP, SHIFT]) = tmpbranch(idx,:);
case {2 , 'kde'}
    % fit a gaussian kde to the data and sample
    xfrm_mask = tmpbranch(:,5) ~= 0;
    nxfrm = round(nl*sum(xfrm_mask)/size(tmpbranch,1));
    nline = nl - nxfrm;
    % first sample lines
    tmp = tmpbranch(~xfrm_mask,[1:4]);
    cnstmask = all(tmp == tmp(1,:), 1);
    kde = sgvm_gaussian_kde(tmp(:,~cnstmask));
    maxval = max(tmp(:,~cnstmask), [], 1);
    minval = min(tmp(:,~cnstmask), [], 1);
    rvs = sgvm_sample_dist(nline, kde, minval, maxval);
    idx = [BR_R, BR_X, BR_B, RATE_A];
    branch(1:nline, idx(~cnstmask)) = rvs;
    branch(1:nline, idx(cnstmask))  = repmat(tmp(1,cnstmask), nline, 1);
    % next sample xfrms
    tmp = tmpbranch(xfrm_mask,:);
    cnstmask = all(tmp == tmp(1,:), 1);
    kde = sgvm_gaussian_kde(tmp(:,~cnstmask));
    maxval = max(tmp(:,~cnstmask), [], 1);
    minval = min(tmp(:,~cnstmask), [], 1);
    rvs = sgvm_sample_dist(nxfrm, kde, minval, maxval);
    idx = [BR_R, BR_X, BR_B, RATE_A, TAP, SHIFT];
    branch(nline+1:end, idx(~cnstmask)) = rvs;
    branch(nline+1:end, idx(cnstmask))  = repmat(tmp(1,cnstmask), nxfrm, 1);
end
branch(:,RATE_A) = round(branch(:,RATE_A));

if all(branch(:,RATE_A) == 0) || all(isinf(branch(:,RATE_A)))
  warning('sgvm_data2mpc: There are no line ratings in the data. Using default value of %d MVA for all lines', smpl_opt.rate_a_default)
  branch(:,RATE_A) = smpl_opt.rate_a_default;
end
%% node properties
bus = bus_initialize(nb);

%% setup load data in a matrix [PD, QD]
if isstruct(data.load)
    tmp = 0;
    for f = {'PD','QD'}
        if ~isfield(data.load, f{:})
            error('sgvm_data2mpc: when provided as a structure, data.load must have field %s', f{:})
        end
        if tmp == 0
            tmp = length(data.load.(f{:}));
        else
            if tmp ~= length(data.load.(f{:}))
                error('sgvm_data2mpc: when provided as a structure, each field of data.load must be the same length.')
            end
        end
    end
    tmpload = [data.load.PD, data.load.QD];
else
    tmpload = data.load;
end

%% setup gen data in a matrix [QMAX, QMIN, PMAX, PMIN]
% if GEN_BUS is provided it is saved in genbus, otherwise, a vector of length 1:length(gen data) is created
% genbusflag indicates whether GEN_BUS was provided or not
if isstruct(data.gen)
    tmp = 0;
    for f = {'QMAX', 'QMIN', 'PMAX', 'PMIN'}
        if ~isfield(data.gen, f{:})
            error('sgvm_data2mpc: when provided as a structure, data.gen must have field %s', f{:})
        end
        if tmp == 0
            tmp = length(data.gen.(f{:}));
        else
            if tmp ~= length(data.gen.(f{:}))
                error('sgvm_data2mpc: when provided as a structure, each field of data.gen must be the same length.')
            end
        end
    end
    if isfield(data.gen, 'GEN_BUS')
        genbus = data.gen.GEN_BUS;
        if length(genbus) ~= tmp
                error('sgvm_data2mpc: when provided as a structure, each field of data.gen must be the same length.')
        end
        genbusflag = 1;
    else
        genbusflag = 0;
        genbus= (1:tmp).';
    end
    tmpgen = [data.gen.QMAX, data.gen.QMIN, data.gen.PMAX, data.gen.PMIN];
else
    switch size(data.gen,2)
    case 4
        tmpgen = data.gen;
        genbusflag = 0;
        genbus = (1:size(tempgen,1)).';
    case 5
        tmpgen = data.gen(:,2:end);
        genbus = data.gen(:,1);
        genbusflag = 1;
    otherwise
        error('sgvm_data2mpc: when providing data.gen as a matrix it must either have 4 or 5 columns.')
    end
end

%% setup gencost data
if isfield(data, 'gencost')
    % generator cost provided
    if size(data.gencost, 1) ~= size(tmpgen, 1)
        error('sgvm_data2mpc: when providing data.gencost it must have the same number of entries as data.gen.')
    end
    tmpgencost = data.gencost;
else
    % no gencost provided create uniform cost
    tmp = size(tmpgen, 1);
    %             MODEL = 2     STARTUP/SHUTDOWN=0, NCOST = 2,   LINCOST = smpl_opt.lincost,   fixed cost = 0
    tmpgencost = [2*ones(tmp,1), zeros(tmp,2),    2*ones(tmp,1), smpl_opt.lincost*ones(tmp,1), zeros(tmp,1)];
end

%% sample node properties
switch smpl_opt.node
case {0 , 'none'}
    % use samples as is
    ng = size(tmpgen,1);
    gen = gen_initialize(ng);
    gencost = tmpgencost;
    if size(tmpload,1) ~= nb
        error(['sgvm_data2mpc: when using sample method 0: ''none'' the provided data must have size of nb, ',...
        'the number of buses. nb = %d, # of load samples = %d'], nb, size(tmpload,1))
    end
    bus(:, [PD, QD]) = tmpload;
    gen(:, [QMAX, QMIN, PMAX, PMIN]) = tmpgen;
    if genbusflag
        gen(:,GEN_BUS) = genbus;
    else
        error('sgvm_data2mpc: when using sample method 0: ''none'' generation data must include bus number')
    end
case {1 , 'direct'}
    idx = randi(size(tmpload,1), nb, 1);
    bus(:, [PD, QD]) = tmpload(idx,:);
    % directly sampe the load data (gen data is always directly sampled)
    if genbusflag && smpl_opt.usegenbus
        % if generation bus is specified simply sample buses nb times
        %nbus x 1 vector with number of generators at each bus of input data
        genperbus = full(sparse(genbus, 1, 1, size(tmpload,1), 1));
        ng = sum(genperbus(idx)); % total number of generators
        gen = gen_initialize(ng);
        gencost = gencost_initialize(ng, size(tmpgencost,2));
        ptr = 0;
        for bidx = 1:nb
            k = idx(bidx); %bus bidx in output is bus k of input data
            gidx = find(genbus == k); %rows of gen data connected to bus k
            if isempty(gidx)
                continue
            end
            gen(ptr+1:ptr+genperbus(k), [GEN_BUS, QMAX, QMIN, PMAX, PMIN]) = [ones(genperbus(k),1) * bidx, tmpgen(gidx,:)];
            gencost(ptr+1:ptr+genperbus(k),:) = tmpgencost(gidx,:);
            ptr = ptr + genperbus(k);
        end
        if ptr ~= ng
            error('sgvm_data2mpc: error while generating the gen matrix %d generators were expected but %d were created', ng, ptr)
        end
    else
        [gen, gencost] = gen_sample(bus, tmpload, tmpgen, tmpgencost, genbus, smpl_opt);
    end
case {2 , 'kde'}
    % sample load with kde (gen data is always directly sampled)
    % first determine number of no-load buses
    noloadmask  = (tmpload(:,1) == 0) & (tmpload(:,2) == 0);
    noloadbuses = round(nb*sum(noloadmask)/size(tmpload,1));
    
    % Negative PD
    negpdmask   = (tmpload(:,1) < 0);
    if sum(negpdmask) < 3
        negpdbuses = 0;
    else
        negpdbuses  = round(nb*sum(negpdmask)/size(tmpload,1));
    end
    % fit kde to positive load buses
    kde = sgvm_gaussian_kde(tmpload(~noloadmask & ~negpdmask,:));
    maxval = max(tmpload(~noloadmask & ~negpdmask, :), [], 1);
    minval = min(tmpload(~noloadmask & ~negpdmask, :), [], 1);
    pospdbuses = nb-noloadbuses-negpdbuses;
    rvs = sgvm_sample_dist(pospdbuses, kde, minval, maxval);
    bus(1:pospdbuses, [PD, QD]) = rvs;
    % fit kde to negative load buses (if any)
    if negpdbuses > 0
        kde = sgvm_gaussian_kde(tmpload(negpdmask,:));
        maxval = max(tmpload(negpdmask, :), [], 1);
        minval = min(tmpload(negpdmask, :), [], 1);
        rvs = sgvm_sample_dist(negpdbuses, kde, minval, maxval);
        bus(pospdbuses+1:pospdbuses + negpdbuses, [PD, QD]) = rvs;
    end
    % threshold small values to 0 or to minimum value (plus some noise)
    thresholdpd = min( abs(tmpload(tmpload(:,1) ~= 0, 1)) );
    thresholdqd = min( abs(tmpload(tmpload(:,2) ~= 0, 2)) );
    pdbuses  = find((abs(bus(:, PD)) < thresholdpd) & (bus(:,PD) ~= 0));
    pd2zero = (thresholdpd - abs(bus(pdbuses, PD)) ) <= 0.5*thresholdpd;
    bus(pdbuses(pd2zero), PD)  = 0;
    bus(pdbuses(~pd2zero), PD) = sign(bus(pdbuses(~pd2zero), PD)).*thresholdpd.*(1 + rand(sum(~pd2zero),1));
    
    qdbuses  = find((abs(bus(:, QD)) < thresholdqd) & (bus(:,QD) ~= 0));
    qd2zero = (thresholdqd - abs(bus(qdbuses, QD)) ) <= 0.5*thresholdqd;
    bus(qdbuses(qd2zero), QD)  = 0;
    bus(qdbuses(~qd2zero), QD) = sign(bus(qdbuses(~qd2zero), QD)).*thresholdqd.*(1 + rand(sum(~qd2zero),1));
    % sample generators
    [gen, gencost] = gen_sample(bus, tmpload, tmpgen, tmpgencost, genbus, smpl_opt);
end

%% assemble mpc
mpc = struct('version', 2, 'baseMVA', baseMVA, 'bus', bus, 'branch', branch, 'gen', gen, 'gencost', gencost);

%% adjust gen to load ratio
if ~any(strcmp(smpl_opt.node, {0, 'none'}))
    mpc = gen2load_adjust(mpc, tmpload, tmpgen, tmpgencost, genbus, genbusflag, smpl_opt);
end
%% utility functions

function [gen, gencost] = gen_sample(bus, tmpload, tmpgen, tmpgencost, genbus, opt)
% given a bus matrix alread populated with values this function
% samples from the tmpgen matrix and creates the gen matrix

define_constants;
nb = size(bus,1);
% buses with no load
noloadbuses  = find( (bus(:,PD) == 0) & (bus(:,QD) == 0));
% buses with load
loadbuses    = find( (bus(:,PD) ~= 0) | (bus(:,QD) ~= 0));

in_gbusnums = unique(genbus);       %unique *input data* generator bus numbers
multgens = sparse(genbus, 1, 1); % multgens(i) = number of generators at input bus i

% number buses with generation
if opt.ngbuses > 0
    % if specified explicitely by user input
    ngbuses = opt.ngbuses;
else
    % scale # of input generator buses to total input number of buses to the number of buses nb
    ngbuses = round(nb*length(in_gbusnums)/size(tmpload,1));
end

% sample fraction of no load and no gen buses from [0.6,0.95]
noload_nogen = round(length(noloadbuses)*(0.6 + 0.35*rand()));
noload_gen   = length(noloadbuses) - noload_nogen; % # of noload buses *with* generation
% get # of buses with both load and generation
gen_load     = max(ngbuses - noload_gen, 0); %max(x, 0) is in case noload_gen > ngbuses

usedbuses = [];
% gen indices to generation to be attached to no load and load buses
noload_gidx = in_gbusnums(randi(length(in_gbusnums),noload_gen,1));
load_gidx   = in_gbusnums(randi(length(in_gbusnums),gen_load, 1));

ng = full(sum(multgens(noload_gidx)) + sum(multgens(load_gidx))); % number of generators
gen = gen_initialize(ng);
gencost = gencost_initialize(ng, size(tmpgencost,2));
ptr = 0;
% go through the no load buses and create entries in gen matrix
for gidx = sgvm_ensure_col_vect(noload_gidx).'
    mask = genbus == gidx; % mask of all generators in input data connected to bus gidx
    gbus = noloadbuses(randi(length(noloadbuses))); %bus to attach generators
    while ismember(gbus, usedbuses)
        gbus = noloadbuses(randi(length(noloadbuses)));
    end
    gen(ptr+1:ptr+sum(mask), [GEN_BUS, QMAX, QMIN, PMAX, PMIN]) = [ones(sum(mask),1)*gbus, tmpgen(mask,:)];
    gencost(ptr+1:ptr+sum(mask),:) = tmpgencost(mask,:);
    usedbuses = [usedbuses, gbus];
    ptr = ptr + sum(mask);
end
% go through the load buses and create entries in gen matrix
for gidx = sgvm_ensure_col_vect(load_gidx).'
    mask = genbus == gidx;
    gbus = loadbuses(randi(length(loadbuses))); %bus to attach generators
    while ismember(gbus, usedbuses)
        gbus = loadbuses(randi(length(loadbuses)));
    end
    gen(ptr+1:ptr+sum(mask), [GEN_BUS, QMAX, QMIN, PMAX, PMIN]) = [ones(sum(mask),1)*gbus, tmpgen(mask,:)];
    gencost(ptr+1:ptr+sum(mask),:) = tmpgencost(mask,:);
    usedbuses = [usedbuses, gbus];
    ptr = ptr + sum(mask);
end
if ptr ~= ng
    error('sgvm_data2mpc: error while generating the gen matrix %d generators were expected but %d were created', ng, ptr)
end

function mpc = gen2load_adjust(mpc, tmpload, tmpgen, tmpgencost, genbus, genbusflag, smpl_opt)
% resample generators (and possibly load) to move target the desired
% ratio of generation capacity to load.
% If the actual ratio is SMALLER than desired samples are replaced
% until the ratio crosses the threshold. Samples are only kept if the
% move the ratio in the "correct" direction.

define_constants;
if smpl_opt.usegen2load
    % use ratio in data
    gen2load = sum(tmpgen(:,3))/sum(tmpload(:,1));
else
    % otherwise randomly select a ratio between 1.3 and 1.6 (based on
    % Birchfield Metric paper)
    gen2load = 1.3 + 0.3*rand();
end

ratiotest = gen2load - sum(mpc.gen(:,PMAX))/sum(mpc.bus(:,PD));
changedir = sign(ratiotest);
while ratiotest*changedir > 0.05
    % pick a random generator bus
    gbus0 = mpc.gen(randi(size(mpc.gen,1)), GEN_BUS);
    gidx0 = mpc.gen(:,GEN_BUS) == gbus0;
    % pick a new entry in the generation data
    gbus1 = genbus(randi(size(tmpgen,1)));
    gidx1 = genbus == gbus1;
    
    loadnew = sum(mpc.bus(:,PD));
    if any(strcmp(smpl_opt.node,{1, 'direct'})) && genbusflag && smpl_opt.usegenbus
        % load and generation are sampled together
        loadnew = loadnew - mpc.bus(gbus0,PD) + tmpload(gbus1,1);
    end
    gennew  = sum(mpc.gen(:,PMAX)) - sum(mpc.gen(gidx0,PMAX)) + sum(tmpgen(gidx1, 3));
    if ( (changedir > 0) && ((gennew/loadnew) > sum(mpc.gen(:,PMAX))/sum(mpc.bus(:,PD)))) || ...
       ( (changedir < 0) && ((gennew/loadnew) < sum(mpc.gen(:,PMAX))/sum(mpc.bus(:,PD))))
        % if more generation needed and new ratio shows MORE generation OR
        % if less generation needed and new ratio shows LESS generation
        % make change
        if any(strcmp(smpl_opt.node,{1, 'direct'})) && genbusflag && smpl_opt.usegenbus
            mpc.bus(gbus0,[PD,QD]) = tmpload(gbus1, :);
        end
        mpc.gen(gidx0, :) = [];
        mpc.gencost(gidx0, :) = [];
        gen     = gen_initialize(sum(gidx1));
        gen(:, [GEN_BUS, QMAX, QMIN, PMAX, PMIN]) = [ones(sum(gidx1),1)*gbus0, tmpgen(gidx1,:)];
        gencost = tmpgencost(gidx1,:);
        mpc.gen = [mpc.gen; gen];
        mpc.gencost = [mpc.gencost; gencost];
        
        ratiotest = gen2load - sum(mpc.gen(:,PMAX))/sum(mpc.bus(:,PD));
    end
end


function branch = branch_initialize(nl, topo)
% initialize branch matrix with topology and all branches active

branch = zeros(nl,13);   %inialize branch matrix
branch(:,[1, 2]) = topo; % 1,2 = F_BUS, T_BUS
branch(:, 11)    = 1;    % 11 = BR_STATUS

function bus = bus_initialize(nb)
% initialize bus matrix with consecutive bus numbers
% all buses in one area and loss zone and set as PQ buses

define_constants;
bus = zeros(nb, 13);
bus(:,BUS_I) = (1:nb).';
bus(:,BUS_TYPE) = 1;
bus(:,BUS_AREA) = 1;
bus(:,VM)       = 1;
bus(:,ZONE)     = 1;
bus(:,VMAX)     = 1.05;
bus(:,VMIN)     = 0.95;

function gen = gen_initialize(ng)
% initial gen matrix

gen = zeros(ng, 21);
gen(:, 8) = 1; %8 is GEN_STATUS

function gencost = gencost_initialize(ng, gencostcols)
% initialize the gencost matrix

gencost = zeros(ng, gencostcols);

function smpl_opt = opt_default(smpl_opt)
% Create opt data structure with defaults.
% Go through the data structure and update user inputs where necessary
opt = sgvm_smplopts();
smpl_opt = nested_struct_copy(opt, smpl_opt);
