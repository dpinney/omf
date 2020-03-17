function [youtN, Zpr, lambda2, L, A, indx] = sg_topology(N, N0, ks, ltc_k, topo_pars, rwd_pars, Zpr_pars)
%SG_TOPOLOGY Generate random power grid topology using RT-nestedSmallWorld
%[YOUTN, ZPR, LAMBDA2, L, A, INDX] = ...
%   SG_TOPOLOGY(N, N0, KS, LTC_K, TOPO_PARS, RWD_PARS, ZPR_PARS)
%
%   Inputs:
%       N - network size
%       N0 - island size; if this given '0', the program will compute it
%       ks - total number of islands
%       ltc_k - total number of lattice connections between neighboring islands
%       topo_pars - topology parameters
%       rwd_pars - rewiring parameters
%       Zpr_pars - line impedance parameters
%
%   Outputs:
%       youtN - actual network size;
%       Zpr - generated line impedances;
%       lambda2 - algebraic connectivity
%       L - the Laplacian
%       A - line admittance matrix;
%       indx - link index
%
%   model:  (1) form islands limited by connectivity limits
%           (2) connect the islands with lattice connections

%   SynGrid
%   Copyright (c) 2008-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

% obtain the parameters
degModel = topo_pars{1}; mdeg = topo_pars{2};
if(N0 == 0)
    N0 = round(3*exp(mdeg(1)));
    ks = ceil(N/N0);
end
 % added to make youtN == N as given
    N0s = round(N/ks).*ones(1,ks);
    N0s(ks) = N-sum(N0s(1:ks-1));
    if(N~=sum(N0s))
        disp('error, youtN does not equal N as given!');
    end
    N0=N0s(1);
if(isempty(rwd_pars)) % if rewired_pars not given
    if(N0 <= 30)
        p_lrwd = 0.24; p_nrwd = 0.43; avg_clsts = 2.6;
    elseif(N0 <= 57)
        p_lrwd = 0.22; p_nrwd = 0.37; avg_clsts = 3.0;
    elseif(N0 <= 118)
        p_lrwd = 0.21; p_nrwd = 0.46; avg_clsts = 2.0;
    elseif(N0 <= 300)
        %p_lrwd = 0.367; p_nrwd = 0.67; avg_clsts = 4.22;  % estimate from NYISO data
        %p_lrwd = 0.15; p_nrwd = 0.3; avg_clsts = 3; % for the clustreing coefficient
        p_lrwd = 0.1; p_nrwd = 0.1; avg_clsts = 3;
    else
        p_lrwd = 0.367; p_nrwd = 0.67; avg_clsts = 4.22;
    end
else
    p_lrwd = rwd_pars(1); p_nrwd = rwd_pars(2); avg_clsts = rwd_pars(3);
end
bta = 1/avg_clsts;
alph = bta*(p_nrwd/(1-p_nrwd));


if(ltc_k==0) % if lattice connection not specified
    % the number of links between neighboring islands, each side have ltc_k links.
    ltc_k = 2;
end

% Form the topology
indx =[];
youtNs =zeros(ks,1);
lls = zeros(ks*ltc_k,1); % starting nodes of lattice links between islands
llt = zeros(ks*ltc_k,1); % terminating nodes

for ni = 1:ks
    % the island with size of N0
    N0i=N0s(ni);
    [Ai,Mai,indxi,Mdi,lbd2i,youtNi,L] = nsw_cluster_smallworld(N0i,degModel,mdeg,p_lrwd,alph,bta);
    indx =[indx;
           indxi+sum(youtNs)]; % generate ks islands, update links of each island

    % generate lattice links between islands
    lls( (ni-1)*ltc_k+1 : ni*ltc_k ) = randi([1,youtNi],ltc_k,1)+sum(youtNs);
    if(ni>1)
        llt( (ni-2)*ltc_k+1 : (ni-1)*ltc_k ) = randi([1,youtNi],ltc_k,1)+sum(youtNs);
    else
        llt( (ks-1)*ltc_k+1 :  ks*ltc_k )  =  randi([1,youtNi],ltc_k,1)+sum(youtNs);
    end
    % update island size
    youtNs(ni) = youtNi;
    end
youtN = sum(youtNs); % total topology size
if(ks>1)
   indx     = [indx; [lls llt] ]; % all the links
   m3 = length(lls);
else
    m3 =0;
end
m = length(indx(:,1));
m2 = round((m-m3)*p_lrwd);
m1 = m-m2-m3;
[lambda2,L,A]=nsw_conn_check(indx,youtN);

% Generate the line impedances
Zpr = nsw_gen_Zpr(Zpr_pars, [m1 m2 m3]);
