function perm = sgvm_deltainjection2perm(Pbus, Qbus, opt)
%SGVM_DELTAINJECTION2PERM convert change in injection to a permutation.
%   PERM = SGVM_DELTAINJECTION2PERM(PBUS, QBUS, OPT)
%
%   Determine a permutation of the injection vector to best achieve the
%   new desired vector. Pbus and Qbus are structures with fields 'old'
%   and 'new'. The goal is to permute 'old' so it looks as close to 'new'
%   as possible.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

nb = length(Pbus.old);
% loopsolve = opt.vm.nodeperm.loopsolve;
% some thresholding
for fld = {'new', 'old'}
    Pbus.(fld{:})(abs(Pbus.(fld{:})) < 1e-6) = 0;
    Qbus.(fld{:})(abs(Qbus.(fld{:})) < 1e-6) = 0;
end
perm = zeros(nb,1); %initialize permutation vector
%% non optimization approach
err = sqrt( (Pbus.new - Pbus.old).^2 + (Qbus.new - Qbus.old).^2 );
[~, idx] = sort(err, 'descend');
available = (1:nb).';
for k = idx.'
    [~, tmp] = min(abs(Pbus.new(k) - Pbus.old(available)) + abs(Qbus.new(k) - Qbus.old(available)));
    perm(k) = available(tmp);
    available(tmp) = [];
end
%% verify permutation
if ~all(sort(perm) == (1:nb).')
    error('deltainjection2per: failed to return a valid permutation.')
end
%% end of function
return
%% create partitions for large cases
vars = struct();
max_block_size = 1000;
nblock = ceil(nb/max_block_size);
avgnum = nb/nblock;
available_ids = true(nb,1);
ptr = 0;
for k = 1:nblock
    if k == nblock
        ids = find(available_ids); % automatically sorted
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

if ~loopsolve
    vars.tp = struct('first', ptr+1, 'last', ptr+nb);
    ptr = ptr + nb;
    vars.tq = struct('first', ptr+1, 'last', ptr+nb);
    ptr = ptr + nb;
    total_vars = ptr;
    prob = prob_init();
    % initial point
    prob.x0 = zeros(total_vars,1);
    prob.x0(vars.tp.first:vars.tp.last) = abs(Pbus.new - Pbus.old);
    prob.x0(vars.tq.first:vars.tq.last) = abs(Qbus.new - Qbus.old);
end
% vars = struct('Pi',struct('first',1, 'last', nb*nb),...
%               'tp', struct('first', nb*nb+1, 'last', nb*(nb+1)),...
%             'tq', struct('first',nb*(nb+1) + 1,'last', nb*(nb +2)));

% the indices in Pi are ROW-wise. For exmample if nb=3:
% 1 2 3
% 4 5 6
% 7 8 9

% total_vars = 2*nb + nb*nb;

%% Constraints

for k = 1:nblock
    v = ['Pi', num2str(k)];
    nelem = length(vars.(v).ids);
    if loopsolve
        prob = prob_init();
        varsloc = struct('Pi', struct('first', 1, 'last', nelem*nelem),...
                  'tp', struct('first',nelem*nelem+1, 'last', nelem*(nelem + 1)),...
                  'tq', struct('first',nelem*(nelem + 1)+1, 'last', nelem*(nelem + 2)));
        total_vars_loc = nelem*(nelem + 2);
    end
    % --real power P ---------------
    % -tp <= Pnew - Pi*Pold <= tp becomes
    % -Inf <= Pi*Pold - tp <= Pnew
    % Pnew <= Pi*Pold + tp <= Inf
    if ~loopsolve
        tidx = sgvm_ensure_col_vect(vars.tp.first - 1 + vars.(v).ids).';
        A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
            [tidx, vars.(v).first:vars.(v).last], ...
            [-ones(1,nelem), repmat(Pbus.old(vars.(v).ids).', 1, nelem)], ...
            nelem, total_vars);
    else
        tidx = varsloc.tp.first:varsloc.tp.last;
        A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
            [tidx, varsloc.Pi.first:varsloc.Pi.last], ...
            [-ones(1,nelem), repmat(Pbus.old(vars.(v).ids).', 1, nelem)], ...
            nelem, total_vars_loc);
    end
    lb = -Inf(nelem,1);
    ub = Pbus.new(vars.(v).ids);
    prob = update_Albub(prob, A, lb, ub);

    if ~loopsolve
        A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
            [tidx, vars.(v).first:vars.(v).last], ...
            [ones(1,nelem), repmat(Pbus.old(vars.(v).ids).', 1, nelem)], ...
            nelem, total_vars);
    else
        A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
            [tidx, varsloc.Pi.first:varsloc.Pi.last], ...
            [ones(1,nelem), repmat(Pbus.old(vars.(v).ids).', 1, nelem)], ...
            nelem, total_vars_loc);
    end
    lb = Pbus.new(vars.(v).ids);
    ub = Inf(nelem,1);
    prob = update_Albub(prob, A, lb, ub);

    % --reactive power Q ---------------
    % -tq <= Qnew - Pi*Qold <= tq becomes
    % -Inf <= Pi*Qold - tq <= Qnew
    % Qnew <= Pi*Qold + tq <= Inf
    if ~loopsolve
        tidx = sgvm_ensure_col_vect(vars.tq.first - 1 + vars.(v).ids).';
        A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
            [tidx, vars.(v).first:vars.(v).last], ...
            [-ones(1,nelem), repmat(Qbus.old(vars.(v).ids).', 1, nelem)], ...
            nelem, total_vars);
    else
        tidx = varsloc.tq.first:varsloc.tq.last;
        A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
            [tidx, varsloc.Pi.first:varsloc.Pi.last], ...
            [-ones(1,nelem), repmat(Qbus.old(vars.(v).ids).', 1, nelem)], ...
            nelem, total_vars_loc);
    end
    lb = -Inf(nelem,1);
    ub = Qbus.new(vars.(v).ids);
    prob = update_Albub(prob, A, lb, ub);
    
    if ~loopsolve
        A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
            [tidx, vars.(v).first:vars.(v).last], ...
            [ones(1,nelem), repmat(Qbus.old(vars.(v).ids).', 1, nelem)], ...
            nelem, total_vars);
    else
        A = sparse([1:nelem, reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem) ],...
            [tidx, varsloc.Pi.first:varsloc.Pi.last], ...
            [ones(1,nelem), repmat(Qbus.old(vars.(v).ids).', 1, nelem)], ...
            nelem, total_vars_loc);
    end
    lb = Qbus.new(vars.(v).ids);
    ub = Inf(nelem,1);
    prob = update_Albub(prob, A, lb, ub);
    
    % ----- stochastic rows of Pi------
    % sum(Pi_v(ridx,:)) = 1
    if ~loopsolve
        A = sparse(reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem),...
                   vars.(v).first:vars.(v).last, 1, nelem, total_vars);
    else
        A = sparse(reshape(ones(nelem,1)*(1:nelem), 1, nelem*nelem),...
                   varsloc.Pi.first:varsloc.Pi.last, 1, nelem, total_vars_loc);
    end
    lb = ones(nelem,1);
    ub = ones(nelem,1);
    prob = update_Albub(prob, A, lb, ub);
    
    % ----- stochastic columns of Pi------
    % sum(Pi_v(:,k)) = 1
    if ~loopsolve
        A  = sparse(reshape((1:nelem).'*ones(1,nelem), 1, nelem*nelem),...
                    vars.(v).first:vars.(v).last, 1, nelem, total_vars);
    else
        A  = sparse(reshape((1:nelem).'*ones(1,nelem), 1, nelem*nelem),...
                    varsloc.Pi.first:varsloc.Pi.last, 1, nelem, total_vars_loc);
    end
    lb = ones(nelem,1);
    ub = ones(nelem,1);
    prob = update_Albub(prob, A, lb, ub);
    
    % ------ sum of permutation = sum of initial vector ------
    % sum(Pi_v*Pold_v) = sum(Pold_v)
    % note all the first column of Pi_v gets Pold_v(1), second column Pold_v(2), etc.
    if ~loopsolve
        A = sparse(1, vars.(v).first:vars.(v).last, ...
            repmat(Pbus.old(vars.(v).ids).', 1, nelem), 1, total_vars);
    else
        A = sparse(1, varsloc.Pi.first:varsloc.Pi.last, ...
            repmat(Pbus.old(vars.(v).ids).', 1, nelem), 1, total_vars_loc);
    end
    lb = sum(Pbus.old(vars.(v).ids).');
    ub = sum(Pbus.old(vars.(v).ids).');
    prob = update_Albub(prob, A, lb, ub);
    
    % sum(Qi_v*Qold_v) = sum(Qold_v)
    if ~loopsolve
        A = sparse(1, vars.(v).first:vars.(v).last, ...
            repmat(Qbus.old(vars.(v).ids).', 1, nelem), 1, total_vars);
    else
        A = sparse(1, varsloc.Pi.first:varsloc.Pi.last, ...
            repmat(Qbus.old(vars.(v).ids).', 1, nelem), 1, total_vars_loc);
    end
    lb = sum(Qbus.old(vars.(v).ids).');
    ub = sum(Qbus.old(vars.(v).ids).');
    prob = update_Albub(prob, A, lb, ub);
    
    clear A;
    
    if ~loopsolve
        prob.x0(vars.(v).first + (0:nelem-1) + nelem*(0:nelem-1)) = 1;
    else
        %% variable limits
        prob.xmin = zeros(total_vars_loc,1);
        prob.xmax = Inf(total_vars_loc,1);
        prob.xmax(varsloc.Pi.first:varsloc.Pi.last) = 1;
        %% linear cost
        % sum(tp) + sum(tq)
        prob.c = sparse([varsloc.tp.first:varsloc.tp.last, varsloc.tq.first:varsloc.tq.last], ...
            1, 1, total_vars_loc, 1);
        %% initial point
        prob.x0 = zeros(total_vars_loc,1);
        prob.x0(varsloc.Pi.first + (0:nelem-1) + nelem*(0:nelem-1)) = 1;
        prob.x0(varsloc.tp.first:varsloc.tp.last) = abs(Pbus.new(vars.(v).ids) - Pbus.old(vars.(v).ids));
        prob.x0(varsloc.tq.first:varsloc.tq.last) = abs(Qbus.new(vars.(v).ids) - Qbus.old(vars.(v).ids));
        %% solve
        prob.opt.verbose = opt.vm.nodeperm.verbose;
        [x, f, eflag, output, lambda] = qps_matpower(prob);
        if eflag
            ptmp  = sgvm_extract_perm(reshape(x(varsloc.Pi.first:varsloc.Pi.last), nelem, nelem).', opt.vm.nodeperm);
            perm(vars.(v).ids) = vars.(v).ids(ptmp);
        else
            error('sgvm_deltainjection2perm: optimization failed to converge.')
        end
    end
end

if loopsolve
    %% verify permutation
    if length(unique(perm)) ~= nb
        error(['deltainjection2per: binarzation of Pi by selecting maximum entry in each row ',...
        'failed to return a valid permutation.'])
    end

else
    %% variable limits
    prob.xmin = zeros(total_vars,1);
    prob.xmax = Inf(total_vars,1);
    prob.xmax(vars.Pi1.first:vars.(['Pi', num2str(nblock)]).last) = 1;
    %% linear cost
    % sum(tp) + sum(tq)
    prob.c = sparse([vars.tp.first:vars.tp.last, vars.tq.first:vars.tq.last], ...
        1, 1, total_vars, 1);
    %% solve
    prob.opt.verbose = opt.vm.nodeperm.verbose;
    [x, f, eflag, output, lambda] = qps_matpower(prob);

    if eflag
        for k = 1:nblock
            v = ['Pi', num2str(k)];
            nelem = length(vars.(v).ids);
            ptmp  = sgvm_extract_perm(reshape(x(vars.(v).first:vars.(v).last), nelem, nelem).', opt.vm.nodeperm);
            perm(vars.(v).ids) = vars.(v).ids(ptmp);
        end
        %% verify permutation
        if length(unique(perm)) ~= nb
            error(['deltainjection2per: binarzation of Pi by selecting maximum entry in each row ',...
            'failed to return a valid permutation.'])
        end
    else
        error('sgvm_deltainjection2perm: optimization failed to converge.')
    end

end

%% helper functions
function prob = update_Albub(prob, A, lb, ub)
% simple utility function for updating the constraint and bounds arrays.

prob.A  = [prob.A; A];
prob.l  = [prob.l; lb];
prob.u  = [prob.u; ub];

function prob = prob_init()
prob = struct();
prob.A  = [];
prob.l  = [];
prob.u  = [];
