function [y, i] = sg_datasample(varargin)
%SG_DATASAMPLE  Select K samples from DATA (without replacement)
%   Y = SG_DATASAMPLE(DATA, K)
%   [Y, I] = SG_DATASAMPLE(DATA, K)

%   SynGrid
%   Copyright (c) 2017-2018, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
input = varargin;
n_inpput = length(input);
data = input{1};
k = input{2} ;
N = length(data);

if k > N
    error('sg_datasample: number of samples limited to size of data');
end

if n_inpput == 4
    if strcmp(input{3},'replace') && ~input{4}
        ii = (1:N);
        ord = rand(size(data(:,1)));
        [junk, j] = sort(ord);
        i = ii(j(1:k));
        y = data(i,:);
    end
else
    i = randi(N,k,1);
    y = data(i,:);
end

