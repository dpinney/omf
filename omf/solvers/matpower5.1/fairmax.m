function [val, idx] = fairmax(x)
%FAIRMAX    Same as built-in MAX, except breaks ties randomly.
%   [VAL, IDX] = FAIRMAX(X) takes a vector as an argument and returns
%   the same output as the built-in function MAX with two output
%   parameters, except that where the maximum value occurs at more
%   than one position in the  vector, the index is chosen randomly
%   from these positions as opposed to just choosing the first occurance.
%
%   See also MAX.

%   MATPOWER
%   Copyright (c) 1996-2015 by Power System Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   $Id: fairmax.m 2644 2015-03-11 19:34:22Z ray $
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

val = max(x);               %% find max value
i   = find(x == val);       %% find all positions where this occurs
n   = length(i);            %% number of occurences
idx = i( fix(n*rand)+1 );   %% select index randomly among occurances
