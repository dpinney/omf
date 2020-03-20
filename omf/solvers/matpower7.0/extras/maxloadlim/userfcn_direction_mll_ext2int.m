function mpc = userfcn_direction_mll_ext2int(mpc, mpopt, args)

%   MATPOWER
%   Copyright (c) 2015-2016, Power Systems Engineering Research Center (PSERC)
%   by Camille Hamon
%
%   This file is part of MATPOWER/mx-maxloadlim.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-maxloadlim/ for more info.

mpc = e2i_field(mpc,'dir_var_gen_all','gen');
