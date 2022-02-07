function y_rand = sg_exprnd(mu,n,m)
%SG_EXPRND Replacement for EXPRND from the Statistics Toolbox

%   SynGrid
%   Copyright (c) 2017, 2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Hamidreza Sadeghian, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

x = rand(n, m);
y_rand = -(mu) .* log(1-x);
