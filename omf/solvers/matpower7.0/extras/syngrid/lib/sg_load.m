function [PL_setting] = sg_load(link_ids, Btypes, PgMax, loading, Tab_2D_load)
%SG_LOAD  main function to run load assignment
%   [PL_SETTING, CORR_L] = SG_LOAD(LINK_IDS, BTYPES, PGMAX, LOADING, ...
%                                   TAB_2D_LOAD)
%   Input:
%       link_ids - matrix (m by 2) indicating the branch terminal buses
%       Btypes - bus type assignment vector (N by 1) of G/L/C (1/2/3)
%       PgMax - matrix (Ng x 2) indicating the generation bus numbers and
%           generation capacity at each generation bus
%       loading - loading level (see SG_OPTIONS)
%       Tab_2D_load - PMF map table to assign loads based on node degree
%
%   Output:
%       PL_setting - matrix (NL by 2) indicating the load bus numbers
%           and load size at each load bus

%   SynGrid
%   Copyright (c) 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Hamidreza Sadeghian and Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

Gen_tot = sum(PgMax(:,2));
Load_buses = find(Btypes==2);
N=length(Btypes(:,1));
NL=length(Load_buses);
% indicating the node degree at each load bus
Load_nodedegree=nodedegree(Load_buses,link_ids);
% calculate maximum node degree
maxnode=max(Load_nodedegree(:,2));
% Matrix (Nl by 2) indicating bus number of load buses and related
% normalized node degree
Normalized_Load_nodedegree=[Load_nodedegree(:,1),Load_nodedegree(:,2)/maxnode];
% Total load with respect to the network size
switch loading
    case 'D'
        Total_Load = 10 ^(-0.2*(log10(N))^2+1.98*log10(N)+0.58);
    case 'L'
        Total_Load = Gen_tot.*(0.3 + rand*0.1);
    case 'M'
        Total_Load = Gen_tot.*(0.5 + rand*0.1);
    case 'H'
        Total_Load = Gen_tot.*(0.7 + rand*0.1);
end
% generated loads based on the empirical distribution of realistic power grids
[Normalized_r_PL,MAX_r_PL]=initialLoad(NL,Total_Load);
% Assignment of loads based on the related node degree
% Norm_Load_setting is a matrix ( Nl by 3 ) indicating bus number,
% related normalized node degree and normilized assigned load setting,  respectively.
[Corr_L,Norm_Load_setting]=Assignment_Pl(Normalized_Load_nodedegree,Normalized_r_PL,Tab_2D_load);
% Output: calculate actual values for load settings
Load_setting = Norm_Load_setting;
Load_setting(:,2)= Load_setting(:,2).*maxnode;
Load_setting(:,3)= Load_setting(:,3).*MAX_r_PL;
PL_setting=[Load_setting(:,1),Load_setting(:,3)];

%%
function Load_nodedegree=nodedegree(Load_buses,link_ids)
% This function calculates the node degree at each load buses

Load_nodedegree=[];
L1=length(Load_buses(:,1));
L2=length(link_ids(:,1));

for Bii=1:length(Load_buses(:,1))
    count=0;
    for Li=1:length(link_ids(:,1))
        if link_ids(Li,1)==Load_buses(Bii,1)
            count=count+1;
        elseif link_ids(Li,2)==Load_buses(Bii,1)
            count=count+1;
        end
    end
    Load_nodedegree=[Load_nodedegree;Load_buses(Bii,1),count];
end

%%
function [Normalized_r_PL,MAX_r_PL]=initialLoad(NL,Total_Load)

% This is a function to generate loads based on the distribution of realistic grids
% 99% follow the exponential distribution
% 1% of loads take supper large values

% output:
%        Normalized_r_PL - matrix (NL by 1) indicating the normalized load size at each load bus


mu = Total_Load./NL;
P=sg_exprnd(mu,NL,1);
SG=round(0.01*NL);
P_super=max(P)+(2.*rand(SG,1)*max(P));
[samp,ind]=sg_datasample(P,SG,'replace',false);
P(ind)=[];
r_PL=[P;P_super];

% check scaling property
if (sum(r_PL)>1.05*Total_Load ||  sum(r_PL)<.90*Total_Load)
   r_PL=r_PL.*(Total_Load./sum(r_PL));
end

MAX_r_PL=max(r_PL);

Normalized_r_PL=r_PL/MAX_r_PL;


function [Corr_coL,Norm_Load_setting]=Assignment_Pl(Normalized_Load_nodedegree,Normalized_r_PL,Tab_2D)
% This is a function to assign the normalized generation capacities to the generation buses besed
% on node degrees
%
% input:
%       Normalized_Generation_nodedegree- matrix (2 by Ng) indicating the normalized value of node degrees
%       Normalized_r_Pg- matrix (1 by Ng) indicating the normalized value of generation capacities
%       Tab_2D - matrix (14 by 14) indicating the assignment pattern
% output:
%       Generation_setting- matrix (Ng by 3) indicating the load setting at each bus

NL=length(Normalized_r_PL);
% calculate actual nnumber of each cell in 2D table nased on the total
% number of generation capacities
Tab_2D_NL=round(Tab_2D.*NL);
% check the mismatch comes from "round". Add or subtract from maximum
% number in the matrix
if sum(sum(Tab_2D_NL))<NL
    [Max_tab,ind_max_tab]=max(Tab_2D_NL(:));
    [I_row, I_col] = ind2sub(size(Tab_2D_NL),ind_max_tab);
    Tab_2D_NL(I_row,I_col)=Tab_2D_NL(I_row,I_col)+(NL-sum(sum(Tab_2D_NL)));
elseif sum(sum(Tab_2D_NL))>NL
    [Max_tab,ind_max_tab]=max(Tab_2D_NL(:));
    [I_row, I_col] = ind2sub(size(Tab_2D_NL),ind_max_tab);
    Tab_2D_NL(I_row,I_col)=Tab_2D_NL(I_row,I_col)-(sum(sum(Tab_2D_NL))-NL);
end
%% calculate target number of buses based on node degree and 2D table
N_K=zeros(1,14); % matrix for total number of buses in each node degree category
N_K = sum(Tab_2D_NL,1);

%% sort node degrees
Sort_nodedegree=sortrows(Normalized_Load_nodedegree,2);
%% assign buses to the node degree categories
K1=Sort_nodedegree(1:N_K(1,1),:);
Sort_nodedegree(1:N_K(1,1),:)=[];

K2=Sort_nodedegree(1:N_K(1,2),:);
Sort_nodedegree(1:N_K(1,2),:)=[];

K3=Sort_nodedegree(1:N_K(1,3),:);
Sort_nodedegree(1:N_K(1,3),:)=[];

K4=Sort_nodedegree(1:N_K(1,4),:);
Sort_nodedegree(1:N_K(1,4),:)=[];

K5=Sort_nodedegree(1:N_K(1,5),:);
Sort_nodedegree(1:N_K(1,5),:)=[];

K6=Sort_nodedegree(1:N_K(1,6),:);
Sort_nodedegree(1:N_K(1,6),:)=[];

K7=Sort_nodedegree(1:N_K(1,7),:);
Sort_nodedegree(1:N_K(1,7),:)=[];

K8=Sort_nodedegree(1:N_K(1,8),:);
Sort_nodedegree(1:N_K(1,8),:)=[];

K9=Sort_nodedegree(1:N_K(1,9),:);
Sort_nodedegree(1:N_K(1,9),:)=[];

K10=Sort_nodedegree(1:N_K(1,10),:);
Sort_nodedegree(1:N_K(1,10),:)=[];

K11=Sort_nodedegree(1:N_K(1,11),:);
Sort_nodedegree(1:N_K(1,11),:)=[];

K12=Sort_nodedegree(1:N_K(1,12),:);
Sort_nodedegree(1:N_K(1,12),:)=[];

K13=Sort_nodedegree(1:N_K(1,13),:);
Sort_nodedegree(1:N_K(1,13),:)=[];

K14=Sort_nodedegree(1:N_K(1,14),:);
Sort_nodedegree(1:N_K(1,14),:)=[];

%% calculate target number of generations in normalized generation capacity categories
N_L=zeros(1,14); % matrix for total number of buses in each node degree category
N_L = sum(Tab_2D_NL,2)';

%% sort generation capacities and assign them to normalized generation capacities groups of 2D table
% Sort_r_PL=sort(Normalized_r_PL,'descend');
Sort_r_PL=sort(Normalized_r_PL);
G1=Sort_r_PL(1:N_L(1,1),:);
Sort_r_PL(1:N_L(1,1),:)=[];

G2=Sort_r_PL(1:N_L(1,2),:);
Sort_r_PL(1:N_L(1,2),:)=[];

G3=Sort_r_PL(1:N_L(1,3),:);
Sort_r_PL(1:N_L(1,3),:)=[];

G4=Sort_r_PL(1:N_L(1,4),:);
Sort_r_PL(1:N_L(1,4),:)=[];

G5=Sort_r_PL(1:N_L(1,5),:);
Sort_r_PL(1:N_L(1,5),:)=[];

G6=Sort_r_PL(1:N_L(1,6),:);
Sort_r_PL(1:N_L(1,6),:)=[];

G7=Sort_r_PL(1:N_L(1,7),:);
Sort_r_PL(1:N_L(1,7),:)=[];

G8=Sort_r_PL(1:N_L(1,8),:);
Sort_r_PL(1:N_L(1,8),:)=[];

G9=Sort_r_PL(1:N_L(1,9),:);
Sort_r_PL(1:N_L(1,9),:)=[];

G10=Sort_r_PL(1:N_L(1,10),:);
Sort_r_PL(1:N_L(1,10),:)=[];

G11=Sort_r_PL(1:N_L(1,11),:);
Sort_r_PL(1:N_L(1,11),:)=[];

G12=Sort_r_PL(1:N_L(1,12),:);
Sort_r_PL(1:N_L(1,12),:)=[];

G13=Sort_r_PL(1:N_L(1,13),:);
Sort_r_PL(1:N_L(1,13),:)=[];

G14=Sort_r_PL(1:N_L(1,14),:);
Sort_r_PL(1:N_L(1,14),:)=[];
%% assign grouped generation capacities to the 2D table cells
% 1) Save generation buses and their related node degrees in cell arreys of
% K_cell
% 2) Save load settings in cell arreys of L_cell
% 3) Assigne generation capacities to the node degrees based  : For each
% cell arrey of K_cell (category of node degrees) starting from first array of L_cell based on the number of
% each cell in Tab_2D_Ng assigne load settings and then remove
% asigned generation capacities from L_cell.
K_cell=cell(1,14);
K_cell{1}=K1; K_cell{2}=K2; K_cell{3}=K3; K_cell{4}=K4; K_cell{5}=K5; K_cell{6}=K6; K_cell{7}=K7;
K_cell{8}=K8; K_cell{9}=K9; K_cell{10}=K10; K_cell{11}=K11; K_cell{12}=K12; K_cell{13}=K13; K_cell{14}=K14;

L_cell=cell(1,14);
L_cell{1}=G1; L_cell{2}=G2; L_cell{3}=G3; L_cell{4}=G4; L_cell{5}=G5; L_cell{6}=G6; L_cell{7}=G7;
L_cell{8}=G8; L_cell{9}=G9; L_cell{10}=G10; L_cell{11}=G11; L_cell{12}=G12; L_cell{13}=G13; L_cell{14}=G14;

for kk=1:14
    K_num=1;
    for gg=14:-1:1
        if Tab_2D_NL(gg,kk)>0
            [samp_L,ind_L]=sg_datasample(L_cell{gg},Tab_2D_NL(gg,kk),'replace',false);
            K_cell{kk}(K_num:(K_num + Tab_2D_NL(gg,kk)-1),3)=samp_L;
            K_num=K_num+Tab_2D_NL(gg,kk);
            L_cell{gg}(ind_L)=[];
        else
            K_cell{kk}(K_num:(K_num + Tab_2D_NL(gg,kk)-1),3)=L_cell{gg}(1:Tab_2D_NL(gg,kk));
        end
    end
end
% Load_st is a martrix (Ng by 3) inclouds bus numbers, normalized node degrees and normalized Load settings
Load_st=[K_cell{1};K_cell{2};K_cell{3};K_cell{4};K_cell{5};K_cell{6};K_cell{7};K_cell{8};K_cell{9};K_cell{10};K_cell{11};K_cell{12};K_cell{13};K_cell{14}];
Norm_Load_setting=sortrows(Load_st,1);
Corr_coL=corr(Norm_Load_setting(:,2),Norm_Load_setting(:,3));
