function mpopt = sgvm_set_max_iter(mpopt, maxit)
%SGVM_SET_MAX_ITER set maximum iteration number in MPOPT
%   MPOPT = SGVM_SET_MAX_ITER(MPOPT, MAXIT)
%
%   Set the maximum iteration in MPOPT to MAXIT depending on the AC solver
%   If the solver type is unkonwn, returns a warning.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

switch mpopt.opf.ac.solver
    case {'DEFAULT', 'MIPS'}
        mpopt.mips.max_it = maxit;
    case {'IPOPT'}
        mpopt.ipopt.opts.max_iter = maxit;
    case {'KNITRO'}
        mpopt.knitro.maxit = maxit;
    case 'FMINCON'
        mpopt.fmincon.max_it = maxit;
  otherwise
      warning('sgvm_IndClass/sgvm_set_max_iter: setting maximum iteration for solver %s unknown.', mpopt.opf.ac.solver)
end
