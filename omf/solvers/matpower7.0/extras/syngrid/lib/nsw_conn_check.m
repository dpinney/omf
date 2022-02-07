function [lambda2,L,Lad,connected,eigs]=nsw_conn_check(link_ids,n)
% suppose a topology, n nodes, m links, given:
% network's link index matrix: % link_ids (m by 2),
% calculate:
% its Laplace matrix: L (n by n),
% link admission matrix: Lad (m by n),
% the algebraic connectivity index: lamba2,
% which is the second smallest eig of L.
% by wzf, 07/2008

%   SynGrid
%   Copyright (c) 2008, 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

m = length(link_ids);
Lad = zeros(m,n);
for k = 1:m
    nodei=link_ids(k,1); nodej=link_ids(k,2);
    Lad(k,nodei)=1;
    Lad(k,nodej)=-1;
end
L = Lad'*Lad;
eigs = sort(eig(L));
lambda2 = eigs(2);

if(lambda2 < 1e-6)
    connected = 0; % not connected
else
    connected = 1;
end
