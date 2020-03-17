function r = sg_lognrnd(mu,d,m,n)
%SG_LOGNRND Replacement for LOGNRND from the Statistics Toolbox

%   SynGrid
%   Copyright (c) 2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Hamidreza Sadeghian Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

r = exp(mu + d.*randn(m,n));
