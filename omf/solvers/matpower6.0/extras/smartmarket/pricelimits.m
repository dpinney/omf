function lim = pricelimits(lim, haveQ)
%PRICELIMITS  Fills in a struct with default values for offer/bid limits.
%   LIM = PRICELIMITS(LIM, HAVEQ)
%   The final structure looks like:
%       LIM.P.min_bid           - bids below this are withheld
%            .max_offer         - offers above this are withheld
%            .min_cleared_bid   - cleared bid prices below this are clipped
%            .max_cleared_offer - cleared offer prices above this are clipped
%          .Q       (optional, same structure as P)

%   MATPOWER
%   Copyright (c) 2005-2016, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

if isempty(lim)
    if haveQ
        lim = struct( 'P', fill_lim([]), 'Q', fill_lim([]) );
    else
        lim = struct( 'P', fill_lim([]) );
    end
else
    if ~isfield(lim, 'P')
        lim.P = [];
    end
    lim.P = fill_lim(lim.P);
    if haveQ
        if ~isfield(lim, 'Q')
            lim.Q = [];
        end
        lim.Q = fill_lim(lim.Q);
    end
end



function lim = fill_lim(lim)
if isempty(lim)
    lim = struct( 'max_offer', [], 'min_bid', [], ...
                  'max_cleared_offer', [], 'min_cleared_bid', [] );
else
    if ~isfield(lim, 'max_offer'),         lim.max_offer = [];         end
    if ~isfield(lim, 'min_bid'),           lim.min_bid = [];           end
    if ~isfield(lim, 'max_cleared_offer'), lim.max_cleared_offer = []; end
    if ~isfield(lim, 'min_cleared_bid'),   lim.min_cleared_bid = [];   end
end
