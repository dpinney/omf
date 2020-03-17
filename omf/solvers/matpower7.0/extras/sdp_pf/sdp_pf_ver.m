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
%   Copyright (c) 2014-2019, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER/mx-sdp_pf.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-sdp_pf/ for more info.

v = struct( 'Name',     'SDP_PF', ... 
            'Version',  '1.0.1', ...
            'Release',  '', ...
            'Date',     '20-Jun-2019' );
if nargout > 0
    if nargin > 0
        rv = v;
    else
        rv = v.Version;
    end
else
    fprintf('%-22s Version %-9s  %11s\n', v.Name, v.Version, v.Date);
end
