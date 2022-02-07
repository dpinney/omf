function [cost] = combineCost(maxcliques,maxcliquesidx)
%COMBINECOST Calculate the cost of combining two maximal cliques.
%   [COST] = COMBINECOST(MAXCLIQUES,MAXCLIQUEIDX)
%
%   Calculate the cost of combining two maximal cliques in terms of the 
%   number of scalar variables and linking constraints that will be 
%   required after combining the maximal cliques specified in
%   maxcliquesidx. This is the clique combination heuristic described in
%   [1]. Negative costs indicate that the heuristic predicts
%   decreased computational costs after combining the specified maximal
%   cliques.
%
%   Inputs:
%       MAXCLIQUES : Cell array containing the buses contained in each
%           maximal clique.
%       MAXCLIQUESIDX : Vector of length two with elements corresponding to
%           the candidate maximal cliques.
%
%   Outputs:
%       COST : Scalar indicating the cost, as defined by the heuristic in
%       [1] of combining the specified maximal cliques.
%
%   [1] D.K. Molzahn, J.T. Holzer, B.C. Lesieutre, and C.L. DeMarco,
%       "Implementation of a Large-Scale Optimal Power Flow Solver Based on
%       Semidefinite Programming," IEEE Transactions on Power Systems,
%       vol. 28, no. 4, pp. 3987-3998, November 2013.

%   MATPOWER
%   Copyright (c) 2013-2019, Power Systems Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%
%   This file is part of MATPOWER/mx-sdp_pf.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-sdp_pf/ for more info.

%% define undocumented MATLAB function ismembc() if not available (e.g. Octave)
if exist('ismembc')
    ismembc_ = @ismembc;
else
    ismembc_ = @ismembc_octave;
end

maxcliques1 = maxcliques{maxcliquesidx(1)};
maxcliques2 = maxcliques{maxcliquesidx(2)};
nintersect = sum(ismembc_(maxcliques1, maxcliques2));

elimmaxcliques(1) = length(maxcliques1);
elimmaxcliques(2) = length(maxcliques2);
lnewmaxcliques = sum(elimmaxcliques) - nintersect;

nvarafter = (lnewmaxcliques)*(2*lnewmaxcliques+1) - sum((elimmaxcliques).*(2*elimmaxcliques+1));

ocostbefore = (nintersect)*(2*nintersect+1);

cost = nvarafter - ocostbefore;
