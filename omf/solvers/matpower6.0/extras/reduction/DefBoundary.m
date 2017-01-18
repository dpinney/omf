function [BoundBus]=DefBoundary(mpc,ExBus)
% Subroutine DefBoundary indentify the boundary buses in the given model
% mpc based on the list of external buses (ExBus).
%
%   [BoundBus]=DefBoundary(mpc,ExBus)
%
% INPUT DATA:
%   mpc - struct, input system model in MATPOWER format
%   ExBus - 1*n array, includes external bus indices
% 
% OUTPUT DATA:
%   BoundBus - 1*n array, Boundary bus indices
%
% Note:
%   Boundary buses are the retained buses directly connected to external
%   buses.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

BoundBus=zeros(size(mpc.bus,1),1);
ExFlag=BoundBus;
ExFlag(ExBus)=1;

for i = 1:size(mpc.branch,1)
    m=mpc.branch(i,1);
    n=mpc.branch(i,2);    
    if ExFlag(m)+ExFlag(n)<2 % exclude external branch
        if (ExFlag(m)*n+ExFlag(n)*m)~=0
            BoundBus(ExFlag(m)*n+ExFlag(n)*m)=1;
        end
    end
end
BoundBus=find(BoundBus==1);

end