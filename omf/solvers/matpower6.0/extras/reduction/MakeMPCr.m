function [mpcreduced,BCIRC,ExBus] = MakeMPCr(ERPEQ,DataEQ,CIndxEQ,ShuntData,ERP,DataB,ExBus,PivInd,PivOrd,BCIRC,newbusnum,oldbusnum,mpcfull,BoundBus)
% Subroutine MakeMPCr generates the reduced model in MATPOWER case
% format. The reduced model generated in this subroutine will not involve
% generator placement and load redistribution.
%
%   [mpcreduced,BCIRC,ExBus] = MakeMPCr(ERPEQ,DataEQ,CIndxEQ,ShuntData,ERP,
%                           DataB,ExBus,PivInd,PivOrd,BCIRC,newbusnum,oldbusnum,mpcfull,BoundBus)
%
% INPUT DATA:
%   ERPEQ: 1*n array, includes end of row pointers of the equivalent lines
%   DataEQ: 1*n array, includes value of equivalent line reactance
%   CIndxEQ: 1*n array, includes column indices of equivalent lines
%   ShuntData, 1*n array, includes bus shunts data of all buses in the
%       reduced model
%   ERP, 1*n array, includes end of row pointer of the original full model
%       bus admittance matrix
%   DataB, 1*n array, includes value of all non-zeros in the original full
%       model bus adminttance matrix
%   ExBus, 1*n array, includes indices of external buses
%   PivOrd: 1*n array, includes bus indices after pivotting
%   PivInd: 1*n array, includes bus ordering after pivotting
%   BCIRC, 1*n array, includes branch circit number of the full model
%   newbusnum, 1*n array, includes internal bus indices
%   oldbusnum, 1*n array, includes original bus indices
%   mpcfull, struct, the original full model
%   BoundBus, 1*n array, includes indices of boundary buses
%
% OUTPUT DATA:
%   mpcreduced: struct, the reduced model
%   BCIRC: 1*n array, the branch circuit number of the reduced model
%   ExBus: 1*n array, the external bus indices
%
% NOTE:
%   The output data of this subroutine will be converted to original
%   indices.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

ExLen=length(ExBus);
%% Create the reduced model case file
mpcreduced = mpcfull;
branch = mpcreduced.branch;
bus = mpcreduced.bus;
int_flag = ones(size(branch,1),1);
%% delete all branches connect external buses
% 1. eliminate all branches connecting external bus
% check from bus
for i = 1:length(ExBus)
    tf=ismember(branch(:,1),ExBus(i));
    int_flag = int_flag.*~tf;
end
% check to bus
for i = 1:length(ExBus)
    tf=ismember(branch(:,2),ExBus(i));
    int_flag = int_flag.*~tf;
end
branch(int_flag==0,:)=[]; % delete all marked branches
BCIRC(int_flag==0,:)=[];
%% delete all external buses
for i = 1:length(ExBus)
    bus(bus(:,1)==ExBus(i),:)=[];
end
%% Generate data for equivalent branches
if any(DataEQ)
FromInd=zeros(size(CIndxEQ));
AddEqBranch = zeros(length(DataEQ),size(branch,2));

for i = ExLen+1:length(ERPEQ)-1
    FromInd(ERPEQ(i)+1:ERPEQ(i+1))=i;
end
for i = 1:length(CIndxEQ)
    AddEqBranch(i,[1,2,4])=[PivInd(FromInd(i)),PivInd(CIndxEQ(i)),-DataEQ(i)];
end
AddEqBranch(:,6)=99999; % RATEA
AddEqBranch(:,7)=99999; % RATEB
AddEqBranch(:,8)=99999; % RATEC

AddEqBranch(:,9)=1; % tap
AddEqBranch(:,10)=0; % phase shift
AddEqBranch(:,11)=1; % status
AddEqBranch(:,12)=-360; % min angle
AddEqBranch(:,13)=360;
% generate circuit number
EqBCIRC = max(99,10^(ceil(log10(max(BCIRC)-1)))-1);
AddEqBCIRC = ones(size(AddEqBranch,1),1)*EqBCIRC;
branch = [branch;AddEqBranch];
BCIRC = [BCIRC;AddEqBCIRC];

mpcreduced.branch = branch;
else 
    fprintf('\nNo equivalent branch is generated');
    mpcreduced.branch=branch;
end
%% Calculate Bus Shunt
BusShunt=zeros(size(mpcfull.bus,1)-ExLen,2);
BusShunt(:,1)=ExLen+1:size(mpcfull.bus,1);
BusShunt(:,2)=DataB(ERP(BusShunt(:,1))+1); % add original diagonal element in Y matrix of the bus in;
BusShunt(1:length(BoundBus),2)=BusShunt(1:length(BoundBus),2)+ShuntData';
for i = 1:size(branch,1)
    m=PivOrd(branch(i,1))-ExLen;
    n=PivOrd(branch(i,2))-ExLen;
    BusShunt(m,2)=BusShunt(m,2)-1/branch(i,4);
    BusShunt(n,2)=BusShunt(n,2)-1/branch(i,4);
end
BusShunt(:,1)=PivInd(BusShunt(:,1));
BusShunt(:,2)=BusShunt(:,2)*mpcfull.baseMVA;
% Plug the shunts value into the case file
bus=sortrows(bus,1);
BusShunt=sortrows(BusShunt,1);
bus(:,6)=BusShunt(:,2);
mpcreduced.bus=bus;
%% covert all bus numbers back to original numbering
mpcreduced.branch(:,5)=0; % all branch shunts are converted to bus shunts
mpcreduced.branch(:,1)=interp1(newbusnum,oldbusnum,mpcreduced.branch(:,1));
mpcreduced.branch(:,2)=interp1(newbusnum,oldbusnum,mpcreduced.branch(:,2));
mpcreduced.bus(:,1)=interp1(newbusnum,oldbusnum,mpcreduced.bus(:,1));
ExBus = interp1(newbusnum,oldbusnum,ExBus')';
mpcreduced.gen(:,1)=interp1(newbusnum,oldbusnum,mpcreduced.gen(:,1));

end