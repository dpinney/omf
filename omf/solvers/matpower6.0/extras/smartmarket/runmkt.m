function [MVAbase, cq, cp, bus, gen, gencost, branch, f, dispatch, success, et] = ...
                runmkt(casedata, q, p, mkt, max_p, u0, t, mpopt, fname, solvedcase)
%RUNMKT  Runs smart market for PowerWeb.
%
%   Deprecated, see RUNMARKET.
%
%   [BASEMVA, CQ, CP, BUS, GEN, GENCOST, BRANCH, F, DISPATCH, SUCCESS, ET] = ...
%           RUNMKT(CASEDATA, Q, P, MKT, MAX_P, U0, T, MPOPT, FNAME, SOLVEDCASE)
%
%   Computes a new generation schedule from a set of offers and bids,
%   where offers and bids are specified by Q and P, MKT tells it what
%   type of market to use, MAX_P is the price cap, U0 is a vector
%   containing the commitment status of each generator from the previous
%   period (for computing startup/shutdown costs), T is the time duration
%   of the dispatch period in hours, and MPOPT is a MATPOWER options struct
%   (see 'help mpoption' for details). Uses default options if MPOPT is not
%   given. The rows in Q and P correspond to the rows in gen and gencost,
%   and each column corresponds to another block in the marginal offer or
%   bid. The market codes are defined as the sum of the
%   following numbers:
%        1000                - all markets
%         100 * adjust4loc   - adjust4loc = 0 to ignore network,
%                              1 to compute locational adjustments via AC OPF,
%                              2 to compute them via DC OPF
%          10 * auction_type - where the values for auction_type are as follows:
%
%      0 - discriminative pricing (price equal to offer or bid)
%      1 - last accepted offer auction
%      2 - first rejected offer auction
%      3 - last accepted bid auction
%      4 - first rejected bid auction
%      5 - first price auction (marginal unit, offer or bid, sets the price)
%      6 - second price auction (if offer is marginal, then price is set
%                                   by min(FRO,LAB), if bid, then max(FRB,LAO)
%      7 - split the difference pricing (price set by last accepted offer & bid)
%      8 - LAO sets seller price, LAB sets buyer price
%
%   If P or Q are empty or not given, they are created from the generator
%   cost function. The default market code is 1150, where the marginal
%   block (offer or bid) sets the price. The default MAX_P is 500, the
%   default U0 is all ones (assume everything was running) and the default
%   duration T is 1 hour. The results may optionally be printed to a file
%   (appended if the file exists) whose name is given in FNAME (in addition
%   to printing to STDOUT). Optionally returns the final values of BASEMVA,
%   CQ, CP, BUS, GEN, GENCOST, BRANCH, F, DISPATCH, SUCCESS, and ET. If a
%   name is given in SOLVEDCASE, the solved case will be written to a case file
%   in MATPOWER format with the specified name with a '.m' extension added.

%   MATPOWER
%   Copyright (c) 1996-2016, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%%-----  initialize  -----
%% default arguments
if nargin < 10
    solvedcase = '';                        %% don't save solved case
    if nargin < 9
        fname = '';                         %% don't print results to a file
        if nargin < 8
            mpopt = mpoption;               %% use default options
            if nargin < 7
                t = [];                     %% use default dispatch period duration (hours)
                if nargin < 6
                    u0 = [];                %% use default for previous gen commitment
                    if nargin < 5
                        max_p = 500;        %% use default price cap
                        if nargin < 4
                            mkt = [];       %% use default market
                            if nargin < 3
                                q = []; p = []; %% p & q not defined (use gencost)
                                if nargin < 1
                                    casedata = 'case9'; %% default data file is 'case9.m'
                                end
                            end
                        end
                    end
                end
            end
        end
    end
end

%% read data & convert to internal bus numbering
mpc = loadcase(casedata);

%% find indices for gens and variable loads
G = find( ~isload(mpc.gen) );   %% real generators
L = find(  isload(mpc.gen) );   %% variable loads

%% create offers, bids
if isempty(q) || isempty(p)
    offers.P.qty = [];
    offers.P.prc = [];
    bids.P.qty = [];
    bids.P.prc = [];
else
    offers.P.qty = q(G, :);
    offers.P.prc = p(G, :);
    bids.P.qty = q(L, :);
    bids.P.prc = p(L, :);
end

%% parse market code
code        = mkt - 1000;
adjust4loc  = fix(code/100);    code = rem(code, 100);
auction_type= fix(code/10);
if adjust4loc == 2
    OPF = 'DC';
elseif adjust4loc == 1
    OPF = 'AC';
else
    error('invalid market code');
end

%% eliminates offers (but not bids) above max_p
lim = struct( 'P', struct( 'max_offer',         max_p, ...
                           'max_cleared_offer', max_p ) );
mkt = struct(   'auction_type', auction_type, 'OPF', OPF, ...
                'lim', lim, 't', t', 'u0', u0   );
[mpc_out, co, cb, f, dispatch, success, et] = ...
                runmarket(mpc, offers, bids, mkt, mpopt, fname, solvedcase);

cq(G, :) = co.P.qty;
cp(G, :) = co.P.prc;
cq(L, :) = cb.P.qty;
cp(L, :) = cb.P.prc;
bus = mpc_out.bus;
gen = mpc_out.gen;
gencost = mpc_out.gencost;
branch = mpc_out.branch;

%% this is just to prevent it from printing baseMVA
%% when called with no output arguments
if nargout, MVAbase = mpc_out.baseMVA; end
