function [BCIRC] = GenerateBCIRC(branch)
% Subroutine GenerateBCIRC is used to detect parallel lines and generate the circuit number of every
% branch. 
%
%   [BCIRC] = GenerateBCIRC(branch)
%
% INPUT DATA:
%   branch: matrix, includes branch data in MATPOWER case format
%
% OUTPUT DATA:
%   BCIRC: n*1 vector, includes branch circuit number
%
% NOTE: For one branch, if its circuit number is greater than 1 then it is
% parallel to one of the branch whose circuit number is 1.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

[FTnum,m,n]=unique(branch(:,[1,2]),'rows','first');
n2 = unique(n);
BCIRC = zeros(size(branch,1),1);
for i = 1:length(n2)
    Ind = find(n==n2(i));
    BCIRC(Ind)=[1:length(Ind)]';
end
end