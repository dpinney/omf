function Nb = sg_poissrnd(Lambda,m,n)
%SG_POISSRND  Replacement for POISSRND from the Statistics Toolbox

%   SynGrid
%   Copyright (c) 2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Hamidreza Sadeghian, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

Nb = zeros(1,n);
for i = 1:n
    count = 0;
    evnt = rand(1);
    while evnt >= exp(-Lambda)
        evnt = evnt*rand(1);
        count = count+1;
    end
    Nb(1,i) = count;
end
