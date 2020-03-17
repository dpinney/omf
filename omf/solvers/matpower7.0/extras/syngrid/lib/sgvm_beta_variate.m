function rvs = sgvm_beta_variate(n, a, b)
%SGVM_BETA_VARIATE create beta distributed values
%   RVS = SGVM_BETA_VARIATE(N, A, B)
%
%   Draw samples from the beta distribution parametrized by A and B.
%   The beta distribution is:
%           f(x| a, b) = 1/Beta(a,b) * x^(a-1)*(1-x)^(b-1)
%
%   Sampling makes use of the fact that if X~gamma(a,1) and Y~gamma(b,1)
%   then X/(X+Y)~beta(a,b)
%
%   Inputs
%      N   - Number of sampes to geneerate
%      A,B - Parameters of beta distribution
%
%   Outputs
%      RVS - the beta variates

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if ~(a > 0)
    error('sgvm_gamma_variate: shape parameter ''a'' must be greater than 0.')
elseif~(b > 0)
    error('sgvm_gamma_variate: shape parameter ''b'' must be greater than 0.')
end
X = sgvm_gamma_variate(n, a, 1);
Y = sgvm_gamma_variate(n, b, 1);

rvs = X./(X + Y);
