function mpc = userfcn_direction_mll_ext2int(mpc,args)

%   MATPOWER
%   Copyright (c) 2015-2016, Power Systems Engineering Research Center (PSERC)
%   by Camille Hamon
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

mpc = e2i_field(mpc,'dir_var_gen_all','gen');
