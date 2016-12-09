function rv = sdp_pf_ver(varargin)
%SPD_PF_VER  Prints or returns SDP_PF version info for current installation.
%   V = SDP_PF_VER returns the current SDP_PF version number.
%   V = SDP_PF_VER('all') returns a struct with the fields Name, Version,
%   Release and Date (all strings). Calling SDP_PF_VER without assigning the
%   return value prints the version and release date of the current
%   installation of SDP_PF.
%
%   See also MPVER.

%   MATPOWER
%   Copyright (c) 2014-2016 by Power System Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

v = struct( 'Name',     'SDP_PF', ... 
            'Version',  '1.0', ...
            'Release',  '', ...
            'Date',     '17-Jan-2014' );
if nargout > 0
    if nargin > 0
        rv = v;
    else
        rv = v.Version;
    end
else
    fprintf('%-22s Version %-9s  %11s\n', v.Name, v.Version, v.Date);
end
