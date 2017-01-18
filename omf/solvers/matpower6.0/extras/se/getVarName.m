function [varName] = getVarName(varIndex, pv, pq)
%GETVARNAME  Get variable name by variable index (as in H matrix).
%   [OUTPUT PARAMETERS]
%   varName: comprise both variable type ('Va', 'Vm') and the bus number of
%   the variable. For instance, Va8, Vm10, etc.
%   created by Rui Bo on Jan 9, 2010

%   MATPOWER
%   Copyright (c) 2009-2016, Power Systems Engineering Research Center (PSERC)
%   by Rui Bo
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% get non reference buses
nonref = [pv;pq];

if varIndex <= length(nonref)
    varType = 'Va';
    newIdx = varIndex;
else
    varType = 'Vm';
    newIdx = varIndex - length(nonref);
end
varName = sprintf('%s%d', varType, nonref(newIdx));
