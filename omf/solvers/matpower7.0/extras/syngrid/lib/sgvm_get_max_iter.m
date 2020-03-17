function maxit = sgvm_get_max_iter(mpopt, default)
%SGVM_GET_MAX_ITER get the maximum iteration based on the AC solver.
%   MAXIT = SGVM_GET_MAX_ITER(MPOPT, DEFAULT)
%
%   If a number is not returned, i.e. maxiter is not set the DEFAULT is
%   used.
%   If DEFAULT is not given 150 is return. Note that this may NOT be the
%   actual default that will be used by the algorithm!!!!

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if nargin < 2
    default = 150;
end

try
  switch mpopt.opf.ac.solver
    case {'DEFAULT', 'MIPS'}
      maxit = mpopt.mips.max_it;
    case 'IPOPT'
      maxit = mpopt.ipopt.opts.max_iter;
    case 'KNITRO'
      maxit = mpopt.knitro.maxit;
    case 'FMINCON'
      maxit = mpopt.fmincon.max_it;
  end
catch
    maxit = default;
end
