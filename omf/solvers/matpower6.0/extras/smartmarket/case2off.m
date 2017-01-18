function [q, p] = case2off(gen, gencost)
%CASE2OFF  Creates quantity & price offers from gen & gencost.
%   [Q, P] = CASE2OFF(GEN, GENCOST) creates quantity and price offers
%   from case variables GEN & GENCOST.
%
%   See also OFF2CASE.

%   MATPOWER
%   Copyright (c) 1996-2016, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% define named indices into data matrices
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;
[PW_LINEAR, POLYNOMIAL, MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;

%% do conversion
oldgencost = gencost;
i_poly = find(gencost(:, MODEL) == POLYNOMIAL);
npts = 6;                   %% 6 points => 5 blocks
%% convert polynomials to piece-wise linear by evaluating at zero and then
%% at evenly spaced points between Pmin and Pmax
if any(i_poly)
    [m, n] = size(gencost(i_poly, :));                              %% size of piece being changed
    gencost(i_poly, MODEL) = PW_LINEAR * ones(m, 1);                %% change cost model
    gencost(i_poly, COST:n) = zeros(size(gencost(i_poly, COST:n))); %% zero out old data
    gencost(i_poly, NCOST) = npts * ones(m, 1);                     %% change number of data points
    
    for i = 1:m
        ig = i_poly(i);     %% index to gen
        Pmin = gen(ig, PMIN);
        Pmax = gen(ig, PMAX);
        if Pmin == 0
            step = (Pmax - Pmin) / (npts - 1);
            xx = (Pmin:step:Pmax);
        else
            step = (Pmax - Pmin) / (npts - 2);
            xx = [0 Pmin:step:Pmax];
        end
        yy = totcost(oldgencost(ig, :), xx);
        gencost(ig,     COST:2:(COST + 2*(npts-1)    )) = xx;
        gencost(ig, (COST+1):2:(COST + 2*(npts-1) + 1)) = yy;
    end
end
n = max(gencost(:, NCOST));
xx = gencost(:,     COST:2:( COST + 2*n - 1 ));
yy = gencost(:, (COST+1):2:( COST + 2*n     ));
i1 = 1:(n-1);
i2 = 2:n;
q = xx(:, i2) - xx(:, i1);
p = ( yy(:, i2) - yy(:, i1) ) ./ q;
