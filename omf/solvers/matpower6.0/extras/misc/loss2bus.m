function bus_loss = loss2bus(mpc)
%LOSS2BUS   Accumulates branch real power losses at downstream buses.
%
%   BUS_LOSS = LOSS2BUS(MPC)
%
%   Takes a solved AC power flow case as input and returns an
%   NB x 1 vector containing all branch active power losses
%   accumulated to the bus at the downstream end of the branch.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

define_constants;
    
%% create external to internal bus map
nb  = size(mpc.bus, 1);     %% number of buses
nl  = size(mpc.branch, 1);  %% number of branches
mb  = max(abs([mpc.bus(:, BUS_I); mpc.gen(:, GEN_BUS); ...
            mpc.branch(:, F_BUS); mpc.branch(:, T_BUS)]));
e2i = sparse(mpc.bus(:, BUS_I), ones(nb, 1), 1:nb, mb, 1);

%% assign losses to downstream buses
loss = mpc.branch(:, PF) + mpc.branch(:, PT);
bus_loss = zeros(nb, 1);
for j = 1:nl    %% need to use loop to accumulate for multiple lines per bus
    if mpc.branch(j, PF) >= mpc.branch(j, PT)
        b = T_BUS;
    else
        b = F_BUS;
    end
    ib = e2i(mpc.branch(j, b));
    bus_loss(ib) = bus_loss(ib) + loss(j);
end
