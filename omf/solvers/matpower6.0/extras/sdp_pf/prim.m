function [E] = prim(Aadj)
%PRIM Prim's algorithm for calculating a minimal spanning tree.
%   [E] = PRIM(AADJ)
%   
%   Implementation of Prim's algorithm for calculating a minimal spanning
%   tree from a graph adjacency matrix. This implementation can incorporate
%   negative edge weights. Create a maximal spanning tree by specifying
%   the negative of the graph adjacency matrix.
%
%   Inputs:
%       AADJ : A graph adjacency matrix, including the possibility of
%           negative edge weights.
%
%   Outputs:
%       E : Matrix with two columns describing the resulting minimal weight
%           spanning tree. Each row gives the maximal cliques for a branch
%           of the tree.

%   MATPOWER
%   Copyright (c) 2013-2016, Power Systems Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.


Vnew = 1;
E = [];
nnode = size(Aadj,1);
cols(1).c = sparse(Aadj(Vnew(1),:)~=0);
cols(1).c(Vnew) = 0;
while length(Vnew) < nnode
    % Choose an edge (u,v) with minimal weight so that u is in Vnew and
    % v is not

    % Find the best available edge
    bestedge.value = inf;
    bestedge.row = [];
    bestedge.col = [];
    for i=1:length(Vnew)
        
        [tempMaxVal,tempMaxCol] = min(Aadj(Vnew(i),cols(i).c));
        if tempMaxVal < bestedge.value
            bestedge.value = tempMaxVal;
            bestedge.row = Vnew(i);
            
            tempc = find(cols(i).c,tempMaxCol);
            bestedge.col = tempc(tempMaxCol);
        end
    end
    
    Vnew = [Vnew; bestedge.col];
    cols(length(Vnew)).c = sparse(Aadj(Vnew(end),:) ~= 0);
    cols(length(Vnew)).c(Vnew) = 0;
    
    for i=1:length(Vnew)-1
        cols(i).c(Vnew(end)) = 0;
    end
    
    E = [E; bestedge.row bestedge.col];
    
    if isempty(bestedge.row) || isempty(bestedge.col)
        error('prim: Error in Prim''s Algorithm. System is probably separated into multiple island. Ensure connected system and try again.');
    end
    
end
V = Vnew;
