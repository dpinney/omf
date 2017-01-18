function [co, cb, r, dispatch, success] = ...
            smartmkt(mpc, offers, bids, mkt, mpopt)
%SMARTMKT  Runs the PowerWeb smart market.
%   [CO, CB, RESULTS, DISPATCH, SUCCESS] = SMARTMKT(MPC, ...
%       OFFERS, BIDS, MKT, MPOPT) runs the ISO smart market.

%   MATPOWER
%   Copyright (c) 1996-2016, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%%-----  initialization  -----
%% default arguments
if nargin < 5
    mpopt = mpoption;       %% use default options
end

%% initialize some stuff
G = find( ~isload(mpc.gen) );       %% real generators
L = find(  isload(mpc.gen) );       %% dispatchable loads
nL = length(L);
if isfield(offers, 'Q') || isfield(bids, 'Q')
    haveQ = 1;
else
    haveQ = 0;
end

if haveQ && mkt.auction_type ~= 0 && mkt.auction_type ~= 5
    error(['smartmkt: Combined active/reactive power markets ', ...
            'are only implemented for auction types 0 and 5']);
end

%% set power flow formulation based on market
mpopt = mpoption(mpopt, 'model', upper(mkt.OPF));

%% define named indices into data matrices
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;
[PW_LINEAR, POLYNOMIAL, MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;
[QUANTITY, PRICE, FCOST, VCOST, SCOST, PENALTY] = idx_disp;

%% set up cost info & generator limits
mkt.lim = pricelimits(mkt.lim, isfield(offers, 'Q') || isfield(bids, 'Q'));
[gen, genoffer] = off2case(mpc.gen, mpc.gencost, offers, bids, mkt.lim);

%% move Pmin and Pmax limits out slightly to avoid problems
%% with lambdas caused by rounding errors when corner point
%% of cost function lies at exactly Pmin or Pmax
if any(find(genoffer(:, MODEL) == PW_LINEAR))
    gg = find( ~isload(gen) );      %% skip dispatchable loads
    gen(gg, PMIN) = gen(gg, PMIN) - 100 * mpopt.opf.violation * ones(size(gg));
    gen(gg, PMAX) = gen(gg, PMAX) + 100 * mpopt.opf.violation * ones(size(gg));
end

%%-----  solve the optimization problem  -----
%% attempt OPF
mpc2 = mpc;
mpc2.gen = gen;
mpc2.gencost = genoffer;
[r, success] = uopf(mpc2, mpopt);
r.genoffer = r.gencost;     %% save the gencost used to run the OPF
r.gencost  = mpc.gencost;   %% and restore the original gencost
[bus, gen] = deal(r.bus, r.gen);
if mpopt.verbose && ~success
    fprintf('\nSMARTMARKET: non-convergent UOPF');
end

%%-----  compute quantities, prices & costs  -----
%% compute quantities & prices
ng = size(gen, 1);
if success      %% OPF solved case fine
    %% create map of external bus numbers to bus indices
    i2e = bus(:, BUS_I);
    e2i = sparse(max(i2e), 1);
    e2i(i2e) = (1:size(bus, 1))';

    %% get nodal marginal prices from OPF
    gbus    = e2i(gen(:, GEN_BUS));                 %% indices of buses w/gens
    nPo     = size(offers.P.qty, 2);
    nPb     = size(bids.P.qty, 2);
    nP      = max([ nPo nPb ]);
    lamP    = sparse(1:ng, 1:ng, bus(gbus, LAM_P), ng, ng) * ones(ng, nP);  %% real power prices
    lamQ    = sparse(1:ng, 1:ng, bus(gbus, LAM_Q), ng, ng) * ones(ng, nP);  %% reactive power prices
    
    %% compute fudge factor for lamP to include price of bundled reactive power
    pf   = zeros(length(L), 1);                 %% for loads Q = pf * P
    Qlim =  (gen(L, QMIN) == 0) .* gen(L, QMAX) + ...
            (gen(L, QMAX) == 0) .* gen(L, QMIN);
    pf = Qlim ./ gen(L, PMIN);

    gtee_prc.offer = 1;         %% guarantee that cleared offers are >= offers
    Poffer = offers.P;
    Poffer.lam = lamP(G,1:nPo);
    Poffer.total_qty = gen(G, PG);
    
    Pbid = bids.P;
    Pbid.total_qty = -gen(L, PG);
    if haveQ
        Pbid.lam = lamP(L,1:nPb);   %% use unbundled lambdas
        gtee_prc.bid = 0;       %% allow cleared bids to be above bid price
    else
        Pbid.lam = lamP(L,1:nPb) + sparse(1:nL, 1:nL, pf, nL, nL) * lamQ(L,1:nPb);  %% bundled lambdas
        gtee_prc.bid = 1;       %% guarantee that cleared bids are <= bids
    end

    [co.P, cb.P] = auction(Poffer, Pbid, mkt.auction_type, mkt.lim.P, gtee_prc);

    if haveQ
        nQo = size(offers.Q.qty, 2);
        nQb = size(bids.Q.qty, 2);
        nQ  = max([ nQo nQb ]);
        
        %% get nodal marginal prices from OPF
        lamQ    = sparse(1:ng, 1:ng, bus(gbus, LAM_Q), ng, ng) * ones(ng, nQ);  %% reactive power prices

        Qoffer = offers.Q;
        Qoffer.lam = lamQ(:,1:nQo);     %% use unbundled lambdas
        Qoffer.total_qty = (gen(:, QG) > 0) .* gen(:, QG);
        
        Qbid = bids.Q;
        Qbid.lam = lamQ(:,1:nQb);       %% use unbundled lambdas
        Qbid.total_qty = (gen(:, QG) < 0) .* -gen(:, QG);

        %% too complicated to scale with mixed bids/offers
        %% (only auction_types 0 and 5 allowed)
        [co.Q, cb.Q] = auction(Qoffer, Qbid, mkt.auction_type, mkt.lim.Q, gtee_prc);
    end

    quantity    = gen(:, PG);
    quantityQ   = gen(:, QG);
    price       = zeros(ng, 1);
    price(G)    = co.P.prc(:, 1);   %% need these for prices for
    price(L)    = cb.P.prc(:, 1);   %% gens that are shut down
    if nP == 1
        k = find( co.P.qty );
        price(G(k)) = co.P.prc(k, :);
        k = find( cb.P.qty );
        price(L(k)) = cb.P.prc(k, :);
    else
        k = find( sum( co.P.qty' )' );
        price(G(k)) = sum( co.P.qty(k, :)' .* co.P.prc(k, :)' )' ./ sum( co.P.qty(k, :)' )';
        k = find( sum( cb.P.qty' )' );
        price(L(k)) = sum( cb.P.qty(k, :)' .* cb.P.prc(k, :)' )' ./ sum( cb.P.qty(k, :)' )';
    end
else        %% did not converge even with imports
    quantity    = zeros(ng, 1);
    quantityQ   = zeros(ng, 1);
    if isempty(mkt.lim.P.max_offer)
        price   = NaN(ng, 1);
    else
        price   = mkt.lim.P.max_offer * ones(ng, 1);
    end
    co.P.qty = zeros(size(offers.P.qty));
    co.P.prc = zeros(size(offers.P.prc));
    cb.P.qty = zeros(size(bids.P.qty));
    cb.P.prc = zeros(size(bids.P.prc));
    if haveQ
        co.Q.qty = zeros(size(offers.Q.qty));
        co.Q.prc = zeros(size(offers.Q.prc));
        cb.Q.qty = zeros(size(bids.Q.qty));
        cb.Q.prc = zeros(size(bids.Q.prc));
    end
end


%% compute costs in $ (note, NOT $/hr)
if size(mpc.gencost, 1) == ng                   %% no reactive costs
    pgcost = mpc.gencost;
    fcost = mkt.t * totcost(pgcost, zeros(ng, 1));          %% fixed costs
    vcost = mkt.t * totcost(pgcost, quantity    ) - fcost;  %% variable costs
    scost =   (~mkt.u0 & gen(:, GEN_STATUS) >  0) .* ...
                    pgcost(:, STARTUP) + ...                %% startup costs
                ( mkt.u0 & gen(:, GEN_STATUS) <= 0) .* ...
                    pgcost(:, SHUTDOWN);                    %% shutdown costs
else    %% size(mpc.gencost, 1) == 2 * ng       %% reactive costs included
    pgcost = mpc.gencost(1:ng, :);
    qgcost = mpc.gencost(ng+(1:ng), :);
    fcost = mkt.t * ( totcost(pgcost, zeros(ng, 1)) + ...
                      totcost(qgcost, zeros(ng, 1)) );      %% fixed costs
    vcost = mkt.t * ( totcost(pgcost, quantity) + ...
                      totcost(qgcost, quantityQ) ) - fcost; %% variable costs
    scost = (~mkt.u0 & gen(:, GEN_STATUS) >  0) .* ...
                (pgcost(:, STARTUP) + qgcost(:, STARTUP)) + ... %% startup costs
            ( mkt.u0 & gen(:, GEN_STATUS) <= 0) .* ...
                (pgcost(:, SHUTDOWN) + qgcost(:, SHUTDOWN));    %% shutdown costs
end

%% store in dispatch
dispatch = zeros(ng, PENALTY);
dispatch(:, [QUANTITY PRICE FCOST VCOST SCOST]) = [quantity price fcost vcost scost];
