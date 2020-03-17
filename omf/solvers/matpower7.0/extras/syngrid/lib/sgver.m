function rv = sgver(varargin)
%SGVER  Prints or returns SynGrid version info for current installation.
%   V = SGVER returns the current SynGrid version number.
%   V = SGVER('all') returns a struct with the fields Name, Version,
%   Release and Date (all strings). Calling SGVER without assigning the
%   return value prints the version and release date of the current
%   installation of SynGrid.
%
%   See also MPVER.

%   SynGrid
%   Copyright (c) 2018-2019, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

v = struct( 'Name',     'SynGrid', ... 
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
