function rvs = sgvm_sample_dist(N, dist, vmin, vmax)
%SGVM_SAMPLE_DIST samples distribution object DIST N times.
%   RVS = SGVM_SAMPLE_DIST(N, DIST, VMIN, VMAX)
%
%   Returns N samples of a distribution object, DIST, that fall within the interval
%   [VMIN, VMAX]. VMIN and VMAX are row vectors of size 1 x D, where D is the dimension
%   of samples in distribution DIST.
%
%   Inputs
%      N -  number of samples desired
%      DIST -  object with method "resample" to sample the distribution
%      VMIN -  minimum value allowable in retured samples
%      VMAX -  maximum value allowable in retured samples
%   Outputs
%      RVS - Nx1 vector of samples

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if nargin == 2
    vmin = -inf;
    vmax = inf;
end

rvs  = dist.resample(N);
mask = any((rvs < vmin) | (rvs > vmax), 2);
while sum(mask) > 0
    tmp = dist.resample(sum(mask));
    rvs(mask,:) = tmp;
    mask = any((rvs < vmin) | (rvs > vmax), 2);
end
