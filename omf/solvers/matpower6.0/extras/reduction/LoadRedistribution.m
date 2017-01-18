function [mpcreduced,BCIRCr]=LoadRedistribution(mpcfull,mpcreduced,BCIRCr,Pf_flag)
% Subroutine LoadRedistribution moves loads in reduced model in order to
% make the dcpf solution on reduced model identical to the full model with
% external generator placed in subroutine MoveExGen.
%
%   [mpcreduced,BCIRCr]=LoadRedistribution(mpcfull,mpcreduced,BCIRCr,Pf_flag)
%
% INPUT DATA:
%   mpcfull: struct, full model data in MATPOWER case format
%   mpcreduced: struct, reduced model data with all external buses
%       eliminated in MATPOWER case format
%   BCIRCr: 1*n array, includes circuit number of branches in reduced model
%   Pf_flag: scalar, indicate if dc power flow need to be solved before
%   load redistribution.
%
% OUTPUT DATA:
%   mpcreduced: struct, reduced model data with load redistributed
%   BCIRCr: 1*n array, includes reordered branch circuit number in reduced
%       model
%
% NOTE:
%   The subroutine will first run a dc power flow on the full model. If the
%   dc power flow can not be solved on the full model, the subroutine will
%   be terminated and an error will be returned.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

if Pf_flag==1
% OPT=mpoption('out.all',0);
[resultfull,successfull]=rundcpf(mpcfull);
if ~successfull
    error('unable to solve dc powerflow with original full model, load cannot be redistributed')
end
else resultfull=mpcfull;
    successfull=1;
end
    
%% Read the full model bus data
%  [BusID, V_mag, V_angle
OrigBusRec=resultfull.bus(:,[1,8,9]);
OrigBusRec=sortrows(OrigBusRec,1); %reorder bus records
%% Read Bus Data
BusRec = mpcreduced.bus;
BusRec = sortrows(BusRec,1);
BusNo = BusRec(:,1);

%% Use original bus voltage
[ignore, ind]=ismember(BusNo,OrigBusRec(:,1));
BusRec(:,8)=OrigBusRec(ind,2); % Vm
BusRec(:,9)=OrigBusRec(ind,3); % Vang
%% Read Branch DATA
branchdata = mpcreduced.branch;
branchdata = branchdata(branchdata(:,11)==1,:);
[branchdata,braindex] = sortrows(branchdata,[1,2]);
BranchRec=branchdata;
%% Renumber the branch terminal buses
Sbase=100; %MVA
NewBusNo = (1:length(BusNo))';
BusRec(:,1) = NewBusNo;
BranchRec(:,1) = interp1(BusNo,NewBusNo,BranchRec(:,1));
BranchRec(:,2) = interp1(BusNo,NewBusNo,BranchRec(:,2));
%% read phase shifter information
ind=find( abs(BranchRec(:,10)) );
flag=0;
if isempty(ind)==0
    flag=1;
    phase_shifter=BranchRec(ind,:);
end
%% Form complex voltage vector
Bus_V_Mag_PU=BusRec(:,8);
Bus_V_Pha=BusRec(:,9)/180*pi;

%% Form Y Matrix
BB=zeros(length(BusNo),length(BusNo));
bb=BranchRec(:,4);
BranchRec(BranchRec(:,9)==0,9)=1;
bb=bb.*(BranchRec(:,9)); % x/tap
bb=1./bb;
for i=1:length( BranchRec(:,4) )
%     i
    m=BranchRec(i,1);
    n=BranchRec(i,2);
    
    BB(m,m)=BB(m,m)+bb(i);
    BB(n,n)=BB(n,n)+bb(i);
    
    BB(m,n)=BB(m,n)-bb(i);
    BB(n,m)=BB(n,m)-bb(i);  
end

P_injected2=BB*Bus_V_Pha*Sbase;

if flag==1
    %% phase_shifter
    B_fix=zeros(length(BB(:,1)),1);
    for i=1:length( phase_shifter(:,1) )
        B_fix( phase_shifter(i,1) )= B_fix( phase_shifter(i,1) ) - phase_shifter(i,10)*pi/180/phase_shifter(i,4);
        B_fix( phase_shifter(i,2) )= B_fix( phase_shifter(i,2) ) + phase_shifter(i,10)*pi/180/phase_shifter(i,4);
    end
    B_fix=B_fix*Sbase;
end

gen = mpcreduced.gen;
gen(:,2)=resultfull.gen(:,2); % use the full model solution
gen(:,1) = interp1(BusNo,NewBusNo,gen(:,1));
Generation = zeros(size(mpcreduced.bus,1),2);
Generation(:,1) = NewBusNo;
for i = 1:size(gen,1)
    Generation(gen(i,1),2) = Generation(gen(i,1),2)+gen(i,2);
end
gen(:,1) = interp1(NewBusNo,BusNo,gen(:,1));
%% fix the phase shifter
if flag==1
    P_injected2=P_injected2+B_fix;
end
P_L_should=Generation(:,2)-P_injected2;
%% dealing with HVDC lines
if isfield(mpcreduced,'dcline')
    dcline = mpcfull.dcline;
    HVDC_Line=[dcline(:,1),dcline(:,2),dcline(:,4),dcline(:,5)];  
    HVDC_Line=sortrows(HVDC_Line,[1 2]);    
    HVDC_Line(:,1)=interp1(BusNo,NewBusNo,HVDC_Line(:,1));
    HVDC_Line(:,2)=interp1(BusNo,NewBusNo,HVDC_Line(:,2));
    % for HVDC lines if one bus of a line is isolated then the buses on the other end
    % of the line will be ignored in the inverse power flow program
    for i=1:length(HVDC_Line(:,1))
        if (BusRec(HVDC_Line(i,1),2)~=4)&&(BusRec(HVDC_Line(i,2),2)~=4)
            P_L_should(HVDC_Line(i,1))=P_L_should(HVDC_Line(i,1))-HVDC_Line(i,3);
            P_L_should(HVDC_Line(i,2))=P_L_should(HVDC_Line(i,2))+HVDC_Line(i,4); % YZ compensate HVDC line by adding/reducing the loads from the HVDC flows
        end
    end
end
%% Plug in the results
mpcreduced.bus(:,3)=P_L_should;
mpcreduced.gen = gen;
end
