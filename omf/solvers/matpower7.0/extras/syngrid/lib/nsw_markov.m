function yout = nsw_markov(alph,bta,n,start)
% PURPOSE: run Markov flips for "n" times, get a chain of "0/1" states.
% USAGE:  nsw_markov(alph,bta,n); nsw_markov(alph,bta,n,start);
% INPUT:
%       alph: 0-->1 transition prob
%       bta:  1-->0 transition prob
%         n:  total times
%       start: inital state 0/1
% OUTPUT:
%       yout: 1 by n binary vector (0/1)
% wzf, 2008

%   SynGrid
%   Copyright (c) 2008, 2017, Electric Power and Energy Systems (EPES) Research Lab
%   by Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

% steady distribution of state 0 and 1
p0 = bta/(alph+bta); p1 = 1-p0;

if(nargin == 3) % decide "start" state
    if(rand<=p0)
        start = 0;
    else
        start =1;
    end
end

yout = zeros(1,n);
yout(1) = start; % get yout
for k = 2:n
    if(yout(k-1) == 0)
        yout(k) = flip(alph,0);
    else
        yout(k) = flip(bta,1);
    end
end


%----------------------- Subfunction --------------------------------------
%--------------------------------------------------------------------------
function next = flip(prob,curr)
% by probability of "prob", flip current state "curr"

if(rand > prob)
    next = curr;
else
    next = ~curr;
end
