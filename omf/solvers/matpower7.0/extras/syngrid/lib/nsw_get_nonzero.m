function y = nsw_get_nonzero(x)
% get non zero elements from matrix x,
% put them into a col-vec - y
% by Kyli wzf, 04/07

%   SynGrid
%   Copyright (c) 2007, 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

[n,m]=size(x);
x_vec = reshape(x,n*m,1);
pos = find(x_vec~=0);
y = x_vec(pos);
% [I,J] = find(x~=0);
% y = zeros(length(I),1);
% for ni = 1:length(I)
%     y(ni) = x(I(ni),J(ni));
% end
