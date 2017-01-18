function [NewGenBus,Link]=MoveExGen(mpcreduced_gen,ExBus,ExBusGen,BCIRC,acflag)
% Subroutine MoveExGen moves generators on external buses to internal buses
% based on shortest electrical distance strategy.
% 
%   [NewGenBus,Link]=MoveExGen(mpcreduced_gen,ExBus,ExBusGen,BCIRC,acflag)
%
% INPUT DATA:
%   mpcreduced_gen: struct, reduced model with all non-generator external
%       buses eliminated.
%   ExBus: 1*n array, includes all external bus indices
%   ExBusGen: 1*n array, includes external generator bus indices
%   BCIRC: 1*n array, includes branch circuit numbers in full model
%   acflag: scalar, if = 0, ignore all resistance, if = 1, calculate
%       electrical distance involving resistance.
% 
% OUTPUT DATA:
%   NewGenBus: n*1 vector, includes new generator bus numbers after moving
%       generators
%   Link: n*2 matrix, includes generator mapping data of all generators.
%       The first column is the original generator bus number and the second
%       column is the new generator bus number after moving external generators
%
% NOTE:
%   The electrical distance between two buses are calcualted as sum of
%   impedance in series connecting the two buses. If acflag = 0, the
%   impedance is same as reactance.
%   The shortest distance is found based on Dijkstra's algorithm.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

BranchRec = [mpcreduced_gen.branch(:,[1,2]),BCIRC,mpcreduced_gen.branch(:,[3,4])]; % fnum,tnum,circuit,r,x
if acflag==0
    BranchRec(:,4)=0; % for dc, ignore all resistance
end
%% Read the bus data
BusNo = mpcreduced_gen.bus(:,1);
%% Convert original bus number to new bus number
NewBusNo = (1:length(BusNo))';
BusRec(:,1) = NewBusNo;
BusRec = sortrows(BusRec,1);

tf = ismember(ExBus,ExBusGen);
ExBus = ExBus(tf==0);
ExBus=interp1(BusNo,NewBusNo,ExBus');
tf = ismember(BusRec(:,1),ExBus);
IntBus = BusRec(tf==0,1);
BranchRec(:,1) = interp1(BusNo,NewBusNo,BranchRec(:,1));
BranchRec(:,2) = interp1(BusNo,NewBusNo,BranchRec(:,2));
BranchRec = sortrows(BranchRec,[1,2,3]);

Gen = mpcreduced_gen.gen;
Gen(:,1)=interp1(BusNo,NewBusNo,Gen(:,1));
Gen = sortrows(Gen,1);

% clear num txt
%% converter all parallel lines into single lines
[ignore,I]=unique(BranchRec(:,[1 2]),'rows','first'); % return the first unique rows in BranchRec
idx = find(diff(I)~=1);
idx_del = [];
for k = idx',
    z = complex(BranchRec(I(k),4),BranchRec(I(k),5)); % complex value of impedances
    for kk = I(k)+1:I(k+1)-1 
        z1 = complex(BranchRec(kk,4),BranchRec(kk,5)); 
        z = 1/(1/z+1/z1);
    end
    BranchRec(I(k),4) = real(z); 
    BranchRec(I(k),5) = imag(z); 
    idx_del = [idx_del I(k)+1:I(k+1)-1];
end
 BranchRec(idx_del,:) = [];

%% Convert the external gen network into a radial network by Zmin
GenNum = Gen(:,1);
tf = ismember(GenNum,IntBus);
GenNum(tf==1)=[];  
LinkedBus = zeros(size(BusNo));
LinkedBra = zeros(size(BusNo)); 
%set up the levels
Level = -ones(size(BusNo));
Level(IntBus) = 0;
%set up the distance
Dist = inf*ones(size(BusNo));
Dist(IntBus) = 0;
BranchZ = sqrt(BranchRec(:,4).^2+BranchRec(:,5).^2);

BusPrevLayer = IntBus;
BusTBD = GenNum;

for lev=1:1000, 
    tf1 = ismember(BranchRec(:,1), BusPrevLayer);
    tf2 = ismember(BranchRec(:,2), BusTBD); 
    ind = find(tf1&tf2);
    for k=ind',
        pi = BranchRec(k,1);
        gi = BranchRec(k,2);
        if Dist(gi)> BranchZ(k)+Dist(pi),
            Dist(gi) = BranchZ(k)+Dist(pi);
            LinkedBus(gi) = pi;
            LinkedBra(gi) = k;
            Level(gi) = Level(pi)+1; 
        end
    end    
    tf1 = ismember(BranchRec(:,2), BusPrevLayer);
    tf2 = ismember(BranchRec(:,1), BusTBD);
    ind = find(tf1&tf2);
    for k=ind',
        pi = BranchRec(k,2); 
        gi = BranchRec(k,1);
        if Dist(gi)> BranchZ(k)+Dist(pi), 
            Dist(gi) = BranchZ(k)+Dist(pi);
            LinkedBus(gi) = pi;
            LinkedBra(gi) = k;
            Level(gi) = Level(pi)+1;
        end
    end
       
%% make some modifications here  

 % link to the internal bus with shortest path
    tf1 = ismember(BranchRec(:,1), BusTBD);
    tf2 = ismember(BranchRec(:,2), BusTBD);
    ind = find(tf1&tf2);
    
   
    
    for k=ind',
        pi = BranchRec(k,1);
        gi = BranchRec(k,2);

        if Dist(gi)> BranchZ(k)+Dist(pi),
            Level(gi) = -1;
        elseif Dist(pi)> BranchZ(k)+Dist(gi),
            Level(pi) = -1;
        end
    end
     %%   
    BusPrevLayer = find(Level==lev); 
    if isempty(BusPrevLayer), % if all buses are islanded
        maxLevel = lev-1;
        break
    end
    BusTBD = find(Level==-1); 
    if isempty(BusTBD), % all gen buses are determined
        maxLevel = lev;
        break
    end
end

%%  LinkedBus=0 ->islanded buses       LinkedBus=-1 
LinkedBus(IntBus)=-1;
islanded_Bus=BusNo(find(LinkedBus==0)); 
LinkedBus(find(LinkedBus==0))=9999999;

%%
for i=1:length(LinkedBus) 
    if LinkedBus(i)==-1
        LinkedBus(i)=i;
    end
end
%%
for lev=max(Level):-1:1    
    ind=find(Level==lev);
    Level(ind)=Level(ind)-1;
    
    for i=ind',
        p=LinkedBus(i);
        LinkedBus(i)=LinkedBus(p);
    end
end
%%
BusNo=[BusNo;9999999];
NewBusNo=[NewBusNo;9999999];
islandflag = 1;
if isempty(LinkedBus(LinkedBus==9999999))
    islandflag = 0;
    LinkedBus = [LinkedBus;9999999];
end
    LinkedBus = interp1(NewBusNo,BusNo,LinkedBus);%% all the buses in the system and its correponding bus in the reduced system

NewGenBus=interp1(BusNo,LinkedBus,mpcreduced_gen.gen(:,1));
if ~islandflag
    LinkedBus(LinkedBus==9999999)=[];
end
Link = [mpcreduced_gen.bus(:,1),LinkedBus];
%%
end