function rvs = sgvm_gamma_variate(n, a, b)
%SGVM_GAMMA_VARIATE generate gamma distributed samples
%   RVS = SGVM_GAMMA_VARIATE(N, A) (default scale is 1)
%   RVS = SGVM_GAMMA_VARIATE(N, A, B)
%
%   Generate N samples from the gamma distribution with shape A and scale
%   B. The gamma distribution is:
%           f(x| a, b) = 1/(gamma(k)*b^k) * x^(k-1) * exp(-x/b)
%   This sampling follows the algorithm described here:
%   https://en.wikipedia.org/wiki/Gamma_distribution#Generating_gamma-distributed_random_variables

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if nargin < 3
    b = 1;
end

if ~(a > 0)
    error('sgvm_gamma_variate: shape parameter ''a'' must be greater than 0.')
elseif~(b > 0)
    error('sgvm_gamma_variate: scale parameter ''b'' must be greater than 0.')
end

x = floor(a);
delta = a - x;

gamma_n1 = -sum(log(rand(n, x)), 2);

if delta ~= 0
    flag = false(n,1);
    
    zeta = zeros(n,1);
    eta  = zeros(n,1);
    
    while ~all(flag)
        idx = find(~flag);
        n = length(idx);
        U = rand(n,1);
        V = rand(n,1);
        W = rand(n,1);
        
        test = U <= exp(1)/(exp(1) + delta);
        
        zeta(idx(test)) = V(test).^(1/delta);
        eta(idx(test))  = W(test).*zeta(idx(test)).^(delta - 1);
        
        zeta(idx(~test)) = 1 - log(V(~test));
        eta(idx(~test))  = W(~test).*exp(-zeta(idx(~test)));
        
        flag = eta <= zeta.^(delta - 1) .* exp(-zeta);
    end
else
    zeta = 0;
end

rvs = b*(zeta + gamma_n1);
