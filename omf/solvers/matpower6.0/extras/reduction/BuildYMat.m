function [CIndx,ERP,DataB]=BuildYMat(NFROM,NTO,BraNum,LineB,BCIRC,BusNum,NUMB,SelfB)
% Subroutine BuildYMat construct the addmittance matrix and store it in a
% compact storage format in order to apply sparse technique.
%
%   [CIndx,ERP,DataB]=BuildYMat(NFROM,NTO,BraNum,LineB,BCIRC,BusNum,NUMB,SelfB)
%
% INPUT DATA:
%   NFROM: 1*n array, includes bus indices of from end buses of every
%       branch
%   NTO: 1*n array, includes bus indices of to end buses of every branch
%   BraNum: scalar, number of branaches
%   NUMB: 1*n array, bus indices
%   SelfB: 1*n array, total B shunts on every bus (B shunt on bus and half
%   the branch B shunt) 
%
% OUTPUT DATA:
%   CIndx: 1*n array, includes column indices of every row in the
%       addmittance matrix
%   ERP: 1*n array, includes end of row pointers of the admittance matrix
%   DataB: 1*n array, includes admittance values in the admittance matrix

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% Initialization
ERP = 0:BusNum; % consider two things: 1. 0 at the begining, 2. diagonal element is non-zero for every row
%%%% Be aware of 1. Isolated buses; 2. Offline branches
%% Read the branch one by one
%first generate the ERP array
for i=1:BraNum
    if BCIRC(i)==1 % if the circuit number is not 1, then the line is parallel line and the index will not increment
        ERP((NFROM(i)+1):(BusNum+1)) = ERP((NFROM(i)+1):(BusNum+1))+1;
        ERP((NTO(i)+1):(BusNum+1)) = ERP((NTO(i)+1):(BusNum+1))+1;
    end
end
%second generate the CIndx and Data array;
DataB = zeros(1,ERP(BusNum+1));
% DataG = AssignSpace(ERP(BusNum+1));
CIndx = zeros(1,ERP(BusNum+1));
ICLP = ERP;
ICLP = ICLP+1;
ICLP(BusNum+1) = [];
ICLP=[0,ICLP];
CIndx(ICLP(2:BusNum+1))=NUMB;
ICLP(2:BusNum+1)=ICLP(2:BusNum+1)+1; % first consider all diagonal elements

%b = 1./BranchData(:,4);
for i = 1:BraNum;

%%
    DataB(ICLP([NFROM(i)+1,NTO(i)+1]))=DataB(ICLP([NFROM(i)+1,NTO(i)+1]))-LineB(i);
%%
if i<BraNum
    if BCIRC(i+1)==1
        CIndx(ICLP([NFROM(i)+1,NTO(i)+1]))=[NTO(i),NFROM(i)];
        ICLP([NFROM(i)+1,NTO(i)+1])=ICLP([NFROM(i)+1,NTO(i)+1])+1;
    end
else
    CIndx(ICLP([NFROM(i)+1,NTO(i)+1]))=[NTO(i),NFROM(i)];
end
    
end
for i = 1:BusNum
    DataB(ERP(NUMB(i))+1)=DataB(ERP(NUMB(i))+1)+SelfB(i);
end

end