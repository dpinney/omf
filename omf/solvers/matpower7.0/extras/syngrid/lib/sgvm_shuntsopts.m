function opt = sgvm_shuntsopts()
%SGVM_SHUNTSOPTS default options for sgvm_add_shunts procedure
%   OPT = SGVM_SHUNTSOPTS()
%
%   tmag (0.1) - minimum shunt size (MVAr)
%   shunt_max (500) - largest shunt size (MVAr)
%   shift_in (0.015) - amount to shift in voltage limits before solving
%                      with softlims enabled. This attempts to avoid
%                      overly tight voltage constraints when softlims are
%                      later removed
%   soft_ratea (0) - controls softlimit on line rating
%       0 : soft limit not enabled
%       1 : soft limit enabled
%   verbose (0) - print progress for shunt procedure
%       0 : no printing
%       1 : some printing
%       2 : more printing

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

opt = struct(   'tmag', 0.1,...
                'shunt_max',500,...
                'shift_in', 0.015,...
                'soft_ratea', 0,...
                'verbose', 0);
