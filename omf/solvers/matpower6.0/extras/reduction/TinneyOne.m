function [PivOrd,PivInd] = TinneyOne(ERP,PivInd,PivOrd,ExBus)
% Subroutine TinneyOne applied Tinney 1 optimal ordering to the input data
% in order to reduce the fills generated in the partial LU factorization
% process. 
%
%   [PivOrd,PivInd] = TinneyOne(ERP,PivInd,PivOrd,ExBus)
%
% INPUT DATA:
%   ERP: 1*n array, includes end of row pointer of input addmittance matrix
%   PivInd: 1*n array, includes bus ordering after pivotting
%   PivOrd: 1*n array, includes bus indices after pivotting
%   ExBus: 1*n array, includes bus indices of external buses
%
% OUTPUT DATA:
%   PivInd: 1*n array, includes bus ordering after pivotting by Tinney 1
%   ordering
%   PivOrd: 1*n array, includes bus indices after pivotting by Tinney 1
%   ordering
%
% NOTE:
%   This subroutine does not pivot any data but output an array includes
%   ordering of buses. Pivoting will be done in the subroutine PivotData.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% Extract the external bus part
ExLen = length(ExBus);
ERP_E = ERP(1:ExLen+1);
%%
RowLen = ERP_E;
for i = 1:ExLen
    RowLen(i)=ERP_E(i+1)-ERP_E(i); % calculate the number of non-zero entry in each row
end
RowLen(end)=[];
[RowLen,RowOrd] = sort(RowLen);
for i =1:ExLen
    RowOrdO(RowOrd(i))=i;
end
PivInd(1:ExLen)=PivInd(RowOrdO);
for i = 1:ExLen
    PivOrd(PivInd(i))=i;
end

end