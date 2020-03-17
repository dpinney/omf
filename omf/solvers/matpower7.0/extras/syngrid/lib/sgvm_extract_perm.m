function perm = sgvm_extract_perm(A, opt)
%SGVM_EXTRACT_PERM Map matrix A to a permutation matrix (WARINING INCOMPLETE)
%   PERM = SGVM_EXTRACT_PERM(A, OPT)

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

n       = size(A, 1);
[r,c,v] = find(A); % find non-zero entries

% remove very small entries
mask = v > 1e-3;
r = r(mask); c = c(mask); v = v(mask);

prob = struct();
prob.A  = [];
prob.l  = [];
prob.u  = [];

total_vars = length(r);

% ---- sum of elements in a single row = 1 -----
A  = sparse(r.', 1:total_vars, 1, n , total_vars);
lb = ones(n, 1);
ub = ones(n, 1);
prob = update_Albub(prob, A, lb, ub);

% ---- sum of elements in a single column = 1 -----
A  = sparse(c.', 1:total_vars, 1, n , total_vars);
lb = ones(n, 1);
ub = ones(n, 1);
prob = update_Albub(prob, A, lb, ub);

% ---- maximize v'*u ---> minimize -v'*u
prob.c = -v;

% ---- initialize with all variables = 1
prob.x0 = ones(total_vars, 1);

% --- upper and lower bound
prob.xmin = zeros(total_vars,1);
prob.xmax = ones(total_vars,1);

% --- variable type is binary
prob.vtype = 'B';

% --- solve
prob.opt.verbose = opt.verbose;
[x, f, eflag, output, lambda] = miqps_matpower(prob);
if eflag
    perm = zeros(n, 1);
    mask = abs(x) > 0.1; % make sure solution is a logical array
    perm(r(mask)) = c(mask);
    
    if any(perm == 0)
        error('sgvm_extract_perm: some rows were not assigned in the permutation.')
    end
    if ~all(sort(perm) == (1:n).')
        error('sgvm_extract_perm: some columns were not assigned in the permutation.')
    end
else
    error('sgvm_extract_perm: the MILP failed to converge.')
end

return
%% old greedy approach
perm = zeros(size(A,1),1);
d = [];
available = true(size(A,1),1);
[~, idx] = sort(A(:), 'descend');
ptr = 1;
while any(perm == 0)
    [r, c] = ind2sub(size(A), idx(ptr));
    if (perm(r) == 0) && available(c)
        perm(r) = c;
        available(c) = false;
    else
        d = append_d(d, r, c, A(r,c));
    end
    ptr = ptr + 1;
end

function d = append_d(d, r, c, v)
if isempty(d)
    d = [r, c, v];
else
    d = [d; r, c, v];
end

function prob = update_Albub(prob, A, lb, ub)
% simple utility function for updating the constraint and bounds arrays.

prob.A  = [prob.A; A];
prob.l  = [prob.l; lb];
prob.u  = [prob.u; ub];
