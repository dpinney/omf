function [NFROM,NTO,BraNum,LineB,ShuntB,BCIRC,BusNum,NUMB,SelfB,mpc,ExBus,newbusnum,oldbusnum] = Initiation(mpc,ExBus)
% Subroutine Initiation read in the input full model data and convert the
% data format to be good to generate the full model admittance matrix.
% 
% [NFROM,NTO,BraNum,LineB,ShuntB,BCIRC,BusNum,NUMB,SelfB,mpc,ExBus,newbusnum,oldbusnum] = Initiation(mpc,ExBus)
%
% INPUT DATA:
%   mpc, struct, full model data in MATPOWER case format
%   ExBus, n*1 vector, includes indices of external buses
%
% OUTPUT DATA
%   NFROM, 1*n array, includes indices of all from end buses
%   NTO, 1*n array, includes indices of all to end buses
%   BraNum, 1*n array, includes indices of all branches
%   LineB, 1*n array, includes line admittance of branches
%   ShuntB, 1*n array, includes line shunt admittance of branches
%   mpc, struct, full model in MATPOWER case format
%   ExBus, n*1 vector, includes external bus indices
%   newbusnum, 1*n array, indices of buses in internal bus numbering
%   oldbusnum, 1*n array, indices of buses in original bus numbering
% NOTE:
%   All output bus indices are in internal bus numbering.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

mpc.bus = sortrows(mpc.bus,1); % sort the buses
oldbusnum = mpc.bus(:,1);
newbusnum = [1:size(mpc.bus,1)]';
mpc.bus(:,1) = newbusnum;
mpc.branch(:,1) = interp1(oldbusnum,newbusnum,mpc.branch(:,1)); % change the branch terminal bus number
mpc.branch(:,2) = interp1(oldbusnum,newbusnum,mpc.branch(:,2)); % change the branch terminal bus number
mpc.gen(:,1)=interp1(oldbusnum,newbusnum,mpc.gen(:,1)); % change the generator bus number
ExBus = interp1(oldbusnum,newbusnum,ExBus')';
% bus data
NUMB = newbusnum;
BusNum = size(mpc.bus,1);
SelfB = mpc.bus(:,6)./mpc.baseMVA;
% branch data
% status = mpc.branch(:,11);
% delete all out of service branches
% mpc.branch(status==0,:)=[];
% status(status==0)=[];
BraNum = size(mpc.branch,1);
NFROM = mpc.branch(:,1);
NTO = mpc.branch(:,2);
LineB = 1./mpc.branch(:,4); % calculate the branch susceptance (b)
ShuntB = mpc.branch(:,5)/2; % branch shunts;
BCIRC = GenerateBCIRC(mpc.branch);
% update SelfB
for i = 1:BraNum
    SelfB(NFROM(i))=SelfB(NFROM(i))+LineB(i)+ShuntB(i);
    SelfB(NTO(i))=SelfB(NTO(i))+LineB(i)+ShuntB(i);
end


end