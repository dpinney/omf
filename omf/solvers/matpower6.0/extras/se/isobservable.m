function TorF = isobservable(H, pv, pq)
%ISOBSERVABLE  Test for observability.
%   returns 1 if the system is observable, 0 otherwise.
%   created by Rui Bo on Jan 9, 2010

%   MATPOWER
%   Copyright (c) 2009-2016, Power Systems Engineering Research Center (PSERC)
%   by Rui Bo
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% options
tol     = 1e-5; % mpopt.pf.tol;
check_reason = 1;	% check reason for system being not observable
                    % 0: no check
                    % 1: check (NOTE: may be time consuming due to svd calculation)

%% test if H is full rank
[m, n]  = size(H);
r       = rank(H);
if r < min(m, n)
    TorF = 0;
else
    TorF = 1;
end

%% look for reasons for system being not observable
if check_reason && ~TorF
    %% look for variables not being observed
    idx_trivialColumns = [];
    varNames = {};
    for j = 1:n
        normJ = norm(H(:, j), inf);
        if normJ < tol % found a zero column
            idx_trivialColumns = [idx_trivialColumns j];
            varName = getVarName(j, pv, pq);
            varNames{length(idx_trivialColumns)} = varName;
        end
    end

    if ~isempty(idx_trivialColumns) % found zero-valued column vector
        fprintf('Warning: The following variables are not observable since they are not related with any measurement!');
        varNames
        idx_trivialColumns
    else % no zero-valued column vector
        %% look for dependent column vectors
        for j = 1:n
            rr = rank(H(:, 1:j));
            if rr ~= j % found dependent column vector
                %% look for linearly depedent vector
                colJ = H(:, j); % j(th) column of H
                varJName = getVarName(j, pv, pq);
                for k = 1:j-1
                    colK = H(:, k);
                    if rank([colK colJ]) < 2 % k(th) column vector is linearly dependent of j(th) column vector
                        varKName = getVarName(k, pv, pq);
                        fprintf('Warning: %d(th) column vector (w.r.t. %s) of H is linearly dependent of %d(th) column vector (w.r.t. %s)!\n', j, varJName, k, varKName);
                        return;
                    end
                end
            end
        end
    fprintf('Warning: No specific reason was found for system being not observable.\n');
    end
end
