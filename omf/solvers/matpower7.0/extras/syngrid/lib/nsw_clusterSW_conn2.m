function [connected,lambda2,L] = nsw_clusterSW_conn2(Ma)
% Given the connectivity matrix Ma, examine if the topology is connected
% and compute its Laplacian and lambda2(L).
% Input:
%   Ma - connectivity matrix (N X N), Ma is upper-triangular matrix
% Output:
%   connected - 1/0;
%   lambda2 - algebraic connectivity;
%   L - the Laplacian of the network
% by wzf, 2008

%   SynGrid
%   Copyright (c) 2008, 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

IMa = or(Ma,Ma');%(Ma+Ma');
dd = sum(IMa,2);

% first form a Laplace matrix:
% L = [Lij](N by N)-> Lii = node degree, Lij = -1, if i-j connected,
%                                        Lij =  0, otherwise
L = -IMa + diag(dd);
eigL = eig(L);
x = sort(eigL);
lambda2 = x(2);
connected = (lambda2 > 1e-6);

% NOTE: Laplace matrix is in fact L = A'*A, where A is line index matrix.
% and Ma = -triu(L,1);
% it is sure L always has an eigenvalue to be zero; if the second smallest eigenv
% great than zero, then it is connected. otherwise, it's not.
