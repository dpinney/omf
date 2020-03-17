function [mpc, flag] = sgvm_branch_perm(mpc, opt)
%SGVM_BRANCH_PERM permute the branch properties of the mpc case
%   [MPC, FLAG] = SGVM_BRANCH_PERM(MPC, OPT)
%
%   Permuting the branch parameters simply means perumuting
%   the rows of the mpc.branch matrix, while keeping
%   columns F_BUS and T_BUS (1,2) fixed.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

%% some constants
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, ...
    TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST, ...
    ANGMIN, ANGMAX, MU_ANGMIN, MU_ANGMAX] = idx_brch;
nl = size(mpc.branch,1);

%% random permutation
if QT > size(mpc.branch,2)
    % if no power flow results, create a random permutation
    perm = randperm(nl);
    mpc.branch(:,BR_R:ANGMAX) = mpc.branch(perm, BR_R:ANGMAX);
    return
end

%%
if ~isfield(opt.vm.branchperm, 'overload_frac')
    overload_frac = 1;
else
    overload_frac = opt.vm.branchperm.overload_frac;
end
Sf = sqrt(mpc.branch(:,PF).^2 + mpc.branch(:,QF).^2);
St = sqrt(mpc.branch(:,PT).^2 + mpc.branch(:,QT).^2);
%maximum apparent flow on branch in per-unit
S  = max(Sf,St) / mpc.baseMVA;
% line ratings in per-unit
r  = mpc.branch(:,RATE_A) / mpc.baseMVA;

R = mpc.branch(:, BR_R); % branch resistance
X = mpc.branch(:, BR_X); % branch reactance

perm = (1:nl).'; % initialize identity permutation
%% find overloaded branches
% indices of overloaded branches
overloaded = find(S./r > overload_frac);
% overloaded = find(mpc.softlims.RATE_A.overload > 1e-4);

% sort overloades from LARGEST to SMALLEST
% [~,tmp] = sort(mpc.softlims.RATE_A.overload(overloaded), 'descend');
[~,tmp] = sort(S(overloaded) - r(overloaded), 'descend');
overloaded = overloaded(tmp);

%% swap loop
% loop over overload branches and find possible elements to swap with.
% Normal case: possible branches, B, have rating GREATER than current flow,
%              their current flow is SMALLER than the overloded branche's rating, and
%              they have not been used in a swap yet. From these, the branch whose
%              impedance most closesly matches the overloaded branch in the L2 sense is chosen.
% Alternative: The requirement that rating is GREATER than overload flow is dropped.
%              In this case branches are chosen based on the closest
%              rating to the flow.
% Otherwise:   Skip this branch, no good swaps are possible.
available  = true(nl,1);
for k = 1:length(overloaded)
    if ~available(overloaded(k))
        % if branch overloaded(k) was already part of a swap
        continue
    end
    B = find( (r*overload_frac >= S(overloaded(k))) & (S <= r(overloaded(k))*overload_frac) & available );
    if isempty(B)
        if S(overloaded(k)) <= r(overloaded(k))
           % if branch is just heavily loaded by not overloaded: ignore
           continue
        end
        B = find( S <= r(overloaded(k)) & available ); % allow overload
        if isempty(B)
            % still no possiblities: ignore
            continue
        end
        % in this case, ignore impedance and just pick the best rating
        [~, tmp] = min(S(overloaded(k)) - r(B));
        idx = B(tmp);
        end
    %else
    % minimize the distance between the impedances as well as the
    % rating from the actual flow.
%     [~, tmp1] = min((R(overloaded(k)) - R(B)).^2 + (X(overloaded(k)) - X(B)).^2); % impedance
    [~, tmp1] = sort((R(overloaded(k)) - R(B)).^2 + (X(overloaded(k)) - X(B)).^2); % impedance
    [~, tmp2] = sort( S(overloaded(k)) - r(B) ); % best rating for branch k
    [~, tmp3] = sort( S(B) - r(overloaded(k)) ); % best flow to recieve branch k's rating
    
    % for each entry in B sum up its location in the three tests. Then
    % take the minimum to pick the final swap candidate
    test_stat = full(sparse([tmp1; tmp2; tmp3], 1, repmat(1:length(B), 1, 3), length(B), 1));
    [~, tmp]  = min(test_stat);
    idx = B(tmp);
    %end
    perm(overloaded(k)) = idx; % overloaded branch gets branch idx's property
    perm(idx)           = overloaded(k); %branch idx gets overloaded(k)'s property
    available([overloaded(k), idx]) = false;
end

%% apply permutation
if ~all(perm == (1:nl).')
    flag = 1;
    mpc.branch(:,BR_R:ANGMAX) = mpc.branch(perm, BR_R:ANGMAX);
else
    % no permutation performed
    flag = 0;
end
%% end of function
return

%% optimization formulation
% the optimization formulation currently does not work well due to the need
% to minimize a non PSD quadratic term. It is kept here for potential
% implementation with a local solver (e.g. IPOPT)
%% create partitions for large cases
vars = struct();
max_block_size = 1000;
nblock = ceil(nl/max_block_size);
avgnum = nl/nblock;
available_ids = true(nl,1);
ptr = 0;
for k = 1:nblock
    if k == nblock
        ids = find(available_ids);
        nelem = length(ids);
    elseif mod(k,2) == 0
        nelem = floor(avgnum);
        ids = find(available_ids);
        ids = ids(randperm(length(ids), nelem)); % sample WITHOUT replacement
        ids = sort(ids); %sort in ascending order
        available_ids(ids) = false;
    else
        nelem = ceil(avgnum);
        ids = find(available_ids);
        ids = ids(randperm(length(ids), nelem)); % sample WITHOUT replacement
        ids = sort(ids); %sort in ascending order
        available_ids(ids) = false;
    end
    vars.(['Pi', num2str(k)]) = struct('first', ptr+1, 'last', ptr + nelem^2, 'ids', ids);
    ptr = ptr + nelem^2;
end
%% problem setup
prob = struct();

vars.t = struct('first', ptr+1, 'last', ptr+nl);
ptr    = ptr + nl;

vars.tr = struct('first', ptr+1, 'last', ptr+nl);
ptr    = ptr + nl;
vars.tx = struct('first', ptr+1, 'last', ptr+nl);
ptr    = ptr + nl;
% vars = struct('Pi', struct('first',1, 'last', nl*nl),...
%                           't', struct('first',nl*nl + 1, 'last', nl*(nl + 1)));

% the indices in Pi are ROW-wise. For exmample if nl=3:
% 1 2 3
% 4 5 6
% 7 8 9

prob.A  = [];
prob.l = [];
prob.u = [];

total_vars = ptr; %nl + nl*nl;

Sf = sqrt(mpc.branch(:,PF).^2 + mpc.branch(:,QF).^2);
St = sqrt(mpc.branch(:,PT).^2 + mpc.branch(:,QT).^2);
%maximum apparent flow on branch in per-unit
S  = max(Sf,St) / mpc.baseMVA;
% line ratings in per-unit
r  = mpc.branch(:,RATE_A) / mpc.baseMVA;

R = mpc.branch(:, BR_R);
X = mpc.branch(:, BR_X);
%% Constraints
% go one branch at a time
% for k = 0:nl-1
% for k = 1:nl
%     for kk = 1:nblock
%         v = ['Pi', num2str(kk)];
%         ridx = find(vars.(v).ids == k);
%         if ~isempty(ridx)
%             nelem = length(vars.(v).ids);
%             break
%         end
%     end
%     % variable indices of row k in Pi_v
%     Pirowidx = vars.(v).first + (nelem*(ridx-1):nelem*ridx-1);
%     % variable indices of column k in Pi_v
%     Picolidx = vars.(v).first + (ridx-1:nelem:nelem*nelem-1);
% %     Pirowidx = (nl*k+1):(nl*(k+1)); %variable ids of row k+1 in Pi
% %     Picolidx = k+1:nl:nl*nl; % variable ids for column k+1 in Pi
% 
%   % -------- overload -----------
%   % t_i + (Pi(i,:) * r - S_i) >= 0 ---> t_i + Pi(i,:)*r >= S_i
% %     A  = sparse(1, [Pirowidx, vars.t.first+k], [r.', 1], 1, total_vars);
%     A  = sparse(1, [Pirowidx, vars.t.first+k-1], [r(vars.(v).ids).', 1], 1, total_vars);
% %     lb = S(k+1);
%     lb = S(k);
%   ub = Inf;
%   prob = update_Albub(prob, A, lb, ub);
% 
%   % ----- stochastic rows of Pi------
%   % sum(Pi(k+1,:)) = 1
%     % sum(Pi_v(ridx,:)) = 1
%   A = sparse(1, Pirowidx, 1, 1, total_vars);
%   lb = 1;
%   ub = 1;
%   prob = update_Albub(prob, A, lb, ub);
% 
%   % ----- stochastic columns of Pi------
%   % sum(Pi(:,k+1)) = 1
%     % sum(Pi_v(:,k)) = 1
%   A = sparse(1, Picolidx, 1, 1, total_vars);
%   lb = 1;
%   ub = 1;
%   prob = update_Albub(prob, A, lb, ub);
% end
rows = cell(nblock, 1);
for k = 1:nblock
    v = ['Pi', num2str(k)];
    nelem = length(vars.(v).ids);
    
    % -------- overload -----------
    % t_i + (Pi(i,:) * r - S_i) >= 0 ---> t_i + Pi(i,:)*r >= S_i
    tidx = sgvm_ensure_col_vect(vars.t.first - 1 + vars.(v).ids).';
    A  = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
         [tidx, vars.(v).first:vars.(v).last], ...
         [ones(1,nelem), repmat(r(vars.(v).ids).', 1, nelem)], nelem, total_vars);
    lb = S(vars.(v).ids);
    ub = Inf(nelem,1);
    prob = update_Albub(prob, A, lb, ub);
    
    % -------- branch resistance ----------
    % -tr_i <= Pi(i, :)*R - R <= tr_i leads to
    % Pi(i, :)*R + tr_i >= R
    % Pi(i, :)*R - tr_i <= R
    tidx = sgvm_ensure_col_vect(vars.tr.first - 1 + vars.(v).ids).';
    A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
        [tidx, vars.(v).first:vars.(v).last],...
        [ones(1,nelem), repmat(R(vars.(v).ids).', 1, nelem)], nelem, total_vars);
    lb = R(vars.(v).ids);
    ub = Inf(nelem,1);
    prob = update_Albub(prob, A, lb, ub);
    
    tidx = sgvm_ensure_col_vect(vars.tr.first - 1 + vars.(v).ids).';
    A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
        [tidx, vars.(v).first:vars.(v).last],...
        [-ones(1,nelem), repmat(R(vars.(v).ids).', 1, nelem)], nelem, total_vars);
    lb = -Inf(nelem,1);
    ub = R(vars.(v).ids);
    prob = update_Albub(prob, A, lb, ub);
    
    % -------- branch reactance ----------
    % -tx_i <= Pi(i, :)*X - X_i <= tx_i leads to
    % Pi(i, :)*X + tx_i >= X_i
    % Pi(i, :)*X - tx_i <= X_i
    tidx = sgvm_ensure_col_vect(vars.tx.first - 1 + vars.(v).ids).';
    A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
        [tidx, vars.(v).first:vars.(v).last],...
        [ones(1,nelem), repmat(X(vars.(v).ids).', 1, nelem)], nelem, total_vars);
    lb = X(vars.(v).ids);
    ub = Inf(nelem,1);
    prob = update_Albub(prob, A, lb, ub);
    
    tidx = sgvm_ensure_col_vect(vars.tx.first - 1 + vars.(v).ids).';
    A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
        [tidx, vars.(v).first:vars.(v).last],...
        [-ones(1,nelem), repmat(X(vars.(v).ids).', 1, nelem)], nelem, total_vars);
    lb = -Inf(nelem,1);
    ub = X(vars.(v).ids);
    prob = update_Albub(prob, A, lb, ub);
    
    % ----- stochastic rows of Pi------
    % sum(Pi_v(ridx,:)) = 1
    A = sparse(reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem),...
               vars.(v).first:vars.(v).last, 1, nelem, total_vars);
    lb = ones(nelem,1);
    ub = ones(nelem,1);
    prob = update_Albub(prob, A, lb, ub);
    
    % ----- stochastic columns of Pi------
    % sum(Pi_v(:,k)) = 1
    A  = sparse(reshape((1:nelem).'*ones(1,nelem), 1, nelem*nelem),...
                vars.(v).first:vars.(v).last, 1, nelem, total_vars);
    lb = ones(nelem,1);
    ub = ones(nelem,1);
    prob = update_Albub(prob, A, lb, ub);
    
    % sum(Pi_v*r_v) = sum(r_v)
    % note all the first column of Pi_v gets r_v(1), second column r_v(2), etc.
    A = sparse(1, vars.(v).first:vars.(v).last, ...
        repmat(r(vars.(v).ids).', 1, nelem), 1, total_vars);
    lb = sum(r(vars.(v).ids).');
    ub = sum(r(vars.(v).ids).');
    prob = update_Albub(prob, A, lb, ub);
    
%     % sum(Pi_v^T*r_v) = sum(r_v)
%     % note all the first column of Pi_v gets r_v(1), second column r_v(2), etc.
%     A = sparse(1, vars.(v).first:vars.(v).last, ...
%         reshape(ones(nelem,1)*r(vars.(v).ids).', 1, nelem*nelem), 1, total_vars);
%     lb = sum(r(vars.(v).ids).');
%     ub = sum(r(vars.(v).ids).');
%     prob = update_Albub(prob, A, lb, ub);
    
    if k == 1
        rows{1} = [1, size(prob.A,1)];
    else
        rows{k} = [rows{k-1}(2)+1, size(prob.A, 1)];
    end
end
A = [];
% % sum(Pi*r) = sum(r)
% A  = sparse(1, vars.Pi.first:vars.Pi.last, repmat(r.',1,nl),1,total_vars);
% lb = sum(r);
% ub = sum(r);
% prob = update_Albub(prob, A, lb, ub);

%% variable limits
prob.xmin = zeros(total_vars,1);
prob.xmax = Inf(total_vars,1);
% prob.xmax(vars.Pi.first:vars.Pi.last) = 1;
prob.xmax(vars.Pi1.first:vars.(['Pi', num2str(nblock)]).last) = 1;
%% linear cost

% sum(t) - mu*sum(Pi_ii);
% mu = 1e-4/mpc.baseMVA;
% prob.f_fcn = @(x)obj_fnc(x, lambda, nblock, vars);
% prob.x0 = zeros(total_vars, 1);
% the indices of diagonal elements of Pi are 1, nl+2, 2*nl+3 etc.
% Pidiagidx = (nl*(0:nl-1)) + 1:nl;

% the diagonal indices of each Pi_v are first+ (0, nelem-1+2, 2*nelem -
% 1+3) etc. = first + nelem*(0:nelem-1) + 0:nelem-1

% Pidiagidx = zeros(1,nl);
% ptr = 0;
% for k = 1:nblock
%     v = ['Pi', num2str(k)];
%     nelem = length(vars.(v).ids);
%     Pidiagidx(ptr+1:ptr+nelem) = vars.(v).first + nelem*(0:nelem-1) + (0:nelem-1);
%     ptr = ptr + nelem;
% end
% prob.x0(Pidiagidx) = 1;
% prob.c = sparse([vars.t.first:vars.t.last, Pidiagidx], 1, ...
% [ceil(avgnum)*ones(1,nl), -mu*ones(1,nl)], total_vars, 1);

prob.c = sparse([vars.t.first:vars.t.last,...
                 vars.tr.first:vars.t.last,...
                 vars.tx.first:vars.t.last], 1, 1, total_vars, 1);

%% quadratic cost
% sum of squares of elements in Pi_v weighted by lambda
% prob.H = sparse(vars.Pi1.first:vars.(['Pi', num2str(nblock)]).last, ...
%                 vars.Pi1.first:vars.(['Pi', num2str(nblock)]).last, ...
%                 -lambda, total_vars,total_vars);

%% solve
prob.opt.verbose = opt.vm.branchperm.verbose;
% for k = 1:nblock
%     v = ['Pi', num2str(k)];
%     nelem = length(vars.(v).ids);
%     tidx = sgvm_ensure_col_vect(vars.t.first - 1 + vars.(v).ids).';
%     idxtmp = [vars.(v).first:vars.(v).last, tidx];
%     varstmp = struct('Pi1', struct('first', 1, 'last', nelem*nelem, 'ids', vars.(v).ids),...
%         't', struct('first', nelem*nelem+1, 'last', nelem*nelem + nelem));
%     probtmp = struct('A', prob.A(rows{k}(1):rows{k}(2),idxtmp), ...
%         'l', prob.l(rows{k}(1):rows{k}(2)), 'u', prob.u(rows{k}(1):rows{k}(2)),...
%         'x0', prob.x0(idxtmp), 'f_fcn', @(x)obj_fnc(x, lambda, 1, varstmp),...
%         'opt', prob.opt);
%     [x, f, exitflag, output, lambda] = mips(probtmp);
% end
[x, f, eflag, output, lambda] = qps_matpower(prob);

if eflag
    % for each row find the largest entry
    perm = zeros(nl,1);
    for k = 1:nblock
        v = ['Pi', num2str(k)];
        nelem = length(vars.(v).ids);
        ptmp  = sgvm_extract_perm(reshape(x(vars.(v).first:vars.(v).last), nelem, nelem));
        perm(vars.(v).ids) = vars.(v).ids(ptmp);
    end
%   for k = 0:nl-1
%         for kk = 1:nblock
%             v = ['Pi', num2str(kk)];
%             ridx = find(vars.(v).ids == k+1); % row in Pi_v corresponding to branch k+1
%             if ~isempty(ridx)
%                 nelem = length(vars.(v).ids);
%                 break
%             end
%         end
% %         Pirowidx = (nl*k+1):(nl*(k+1)); %variable ids of row k+1 in Pi
% %         [~,perm(k+1)] = max(x(Pirowidx));
%         Pirowidx = vars.(v).first + (ridx-1)*nelem + (0:nelem-1); % variable indices of row ridx  in Pi_v
%         [~, tmp] = max(x(Pirowidx)); % maximum value index along this row
%         perm(k+1) = vars.(v).ids(tmp); % maps property at branch with maximum value of Pi to branch k+1.
%   end
    % double check that all integers are found. this should be
    % the case as long as no row has uniform values 1/nl
    if length(unique(perm)) ~= nl
        error(['sgvm_branch_perm: binarzation of Pi by selecting maximum entry in each row ',...
        'failed to return a valid permutation.'])
    end
else
    error('sgvm_branch_perm: optimization failed to converge.')
end

%% apply permutation
mpc.branch(:,BR_R:ANGMAX) = mpc.branch(perm, BR_R:ANGMAX);

function prob = update_Albub(prob, A, lb, ub)
% simple utility function for updating the constraint and bounds arrays.

prob.A  = [prob.A; A];
prob.l  = [prob.l; lb];
prob.u  = [prob.u; ub];

function [f, df, d2f] = obj_fnc(x, lambda, nblock, vars)

v = ['Pi', num2str(nblock)];
f = sum(x(vars.t.first:vars.t.last)) + ...
    -lambda*sum(x(vars.Pi1.first:vars.(v).last).^2);
if nargout > 1          %% gradient is required
    df = [ ones(vars.t.last-vars.t.first + 1, 1); ...
           -2*lambda*x(vars.Pi1.first:vars.(v).last)];
    if nargout > 2    %% Hessian is required
        d2f = sparse(vars.Pi1.first:vars.(v).last,...
            vars.Pi1.first:vars.(v).last, -2*lambda, length(x), length(x));
    end
end
