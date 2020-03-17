function x = sgvm_ensure_col_vect(x)
%SGVM_ENSURE_COL_VECT make sure x is a column vector
%   X = SGVM_ENSURE_COL_VECT(X)

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

m = size(x,1); n = size(x,2);
if (m ~= 1) && (n ~= 1)
    error('input x must be a vector! size = (%d,%d)\n', m, n)
elseif n ~= 1
    x = x.';
end
