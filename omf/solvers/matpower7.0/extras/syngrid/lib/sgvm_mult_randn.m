function z = sgvm_mult_randn(n, sigma, mu)
%SGVM_MULT_RANDN sample N times from a multivariate normal distribution
%   Z = SGVM_MULT_RANDN(N, SIGMA, MU)
%
%   Sample N times from a multivariate normal distribution
%   with covariance matrix SIGMA and mean vector MU
%   basically copied from the RAND help documentation example

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

d = size(sigma,1);
if nargin == 2
    mu = zeros(1,d);
end
mu = sgvm_ensure_col_vect(mu).';

R = chol(sigma);

z = repmat(mu,n,1) + randn(n, d)*R;
