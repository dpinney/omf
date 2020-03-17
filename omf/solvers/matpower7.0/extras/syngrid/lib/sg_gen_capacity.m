function [PgMax] = sg_gen_capacity(link_ids, Btypes, Tab_2D_Pgmax)
%SG_GEN_CAPACITY  main function to run Pg_max assignment
%   [PGMAX, CORR_PGMAX] = SG_GEN_CAPACITY(LINK_IDS, BTYPES, TAB_2D_PGMAX)
%
%   Input:
%       link_ids - matrix (m x 2) indicating the branch terminal buses
%       Btypes - bus type assignment vector (N by 1) of G/L/C (1/2/3)
%       Tab_2D_Pgmax - PMF map table to assign Pgmax based on node degree
%
%   Output:
%       PgMax - matrix (Ng x 2) indicating the generation bus numbers and
%           generation capacity at each generation bus

%   SynGrid
%   Copyright (c) 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Hamidreza Sadeghian and Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

Generation_buses = find(Btypes==1);
N=length(Btypes(:,1));
Ng=length(Generation_buses);
% indicating the node degree at each generation bus
Generation_nodedegree=nodedegree(Generation_buses,link_ids);
% calculate maximum node degree
maxnode = max(Generation_nodedegree(:,2));
% Matrix (Ng by 2) indicating bus number of generation buses and related
% normalized node degree
Normalized_Generation_nodedegree=[Generation_nodedegree(:,1),Generation_nodedegree(:,2)/maxnode];
% Total generation capacity with respect to the network size
Total_Generation= 10 ^(-0.21*(log10(N))^2+2.06*log10(N)+0.66);
% Generation capacities based on the empirical distribution of realistic power grids
[Normalized_r_Pgmax,MAX_r_Pgmax]=initialgeneration(Ng,Total_Generation);
% Assignment of generation capacities based on the related node degree
% Norm_Generation_setting is a matrix ( Ng by 3 ) indicating bus number,
% related normalized node degree and normilized assigned generation
% capacity,  respectively.
[Corr_Pgmax,Norm_Generation_setting]=Assignment(Normalized_Generation_nodedegree,Normalized_r_Pgmax,Tab_2D_Pgmax); %replace the older version of assginement_order()
% Output: calculate actual values for generation capacities
Generation_setting = Norm_Generation_setting;
Generation_setting(:,2)= Generation_setting(:,2).*maxnode;
Generation_setting(:,3)= Generation_setting(:,3).*MAX_r_Pgmax; %Now Generation_setting contains actural values of bus number, node degree, and Pgmax.
% PgMax matrix (Ng by 2)indicating the generation bus numbers and  generation capacity at each generation bus
PgMax=[Generation_setting(:,1),Generation_setting(:,3)];

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

 end

%%
function [Normalized_r_Pgmax,MAX_r_Pgmax]=initialgeneration(Ng,Total_Generation)
% This is a function to generate generation capacities based on the distribution of realistic grids
% 99% follow the exponential distribution
% 1% of generators take supper large capacity

% output:
%        Normalized_r_Pg - matrix (Ng by 1) indicating the normalized generation capacity at each generation bus
mu = Total_Generation./Ng;
P=sg_exprnd(mu,Ng,1);
% Calculate number of super large capacities
SG=round(0.01*Ng);
% Generate uniform random super large capacities from [1-3] times of
% maximum generation
P_super=max(P)+(2.*rand(SG,1)*max(P));
% Randomly sample from generations without replacement
[samp,ind]=sg_datasample(P,SG,'replace',false);
P(ind)=[];
% Replace sampled data with super large capacities
r_Pg=[P;P_super];
%% check scaling property for total generation
if (sum(r_Pg)>1.05*Total_Generation ||  sum(r_Pg)<.90*Total_Generation)
   r_Pg = r_Pg.*(Total_Generation./sum(r_Pg));
end

MAX_r_Pgmax=max(r_Pg);

Normalized_r_Pgmax=r_Pg/MAX_r_Pgmax;
 end
%%
function [Corr_co,Norm_Generation_setting]=Assignment(Normalized_Generation_nodedegree,Normalized_r_Pg,Tab_2D)
% This is a function to assign the normalized generation capacities to the generation buses based
% on node degrees
%
% input:
%       Normalized_Generation_nodedegree- matrix (2 by Ng) indicating the normalized value of node degrees
%       Normalized_r_Pg- matrix (1 by Ng) indicating the normalized value of generation capacities
%       Tab_2D - matrix (14 by 14) indicating the assignment pattern
% output:
%       Generation_setting- matrix (Ng by 3) indicating the generation capacity setting at each generation bus
%             gen bus number, norm_node degree,  norm_Pg_max

Ng=length(Normalized_r_Pg);
% calculate actual nnumber of each cell in 2D table nased on the total
% number of generation capacities
Tab_2D_Ng=round(Tab_2D.*Ng);
% check the mismatch comes from "round". Add or subtract from maximum
% number in the matrix
if sum(sum(Tab_2D_Ng))<Ng
    [Max_tab,ind_max_tab]=max(Tab_2D_Ng(:));
    [I_row, I_col] = ind2sub(size(Tab_2D_Ng),ind_max_tab);
    Tab_2D_Ng(I_row,I_col)=Tab_2D_Ng(I_row,I_col)+(Ng-sum(sum(Tab_2D_Ng)));
elseif sum(sum(Tab_2D_Ng))>Ng
    [Max_tab,ind_max_tab]=max(Tab_2D_Ng(:));
    [I_row, I_col] = ind2sub(size(Tab_2D_Ng),ind_max_tab);
    Tab_2D_Ng(I_row,I_col)=Tab_2D_Ng(I_row,I_col)-(sum(sum(Tab_2D_Ng))-Ng);
end
%% calculate target number of buses based on node degree and 2D table
N_K=zeros(1,14); % matrix for total number of buses in each node degree category
N_K = sum(Tab_2D_Ng,1);

%% sort node degrees
Sort_nodedegree=sortrows(Normalized_Generation_nodedegree,2);
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
N_G=zeros(1,14); % matrix for total number of buses in each node degree category
N_G = sum(Tab_2D_Ng,2)';

%% sort generation capacities and assign them to normalized generation capacities groups of 2D table
%Sort_r_Pg=sort(Normalized_r_Pg,'descend');
Sort_r_Pg=sort(Normalized_r_Pg); %changed by zfwang, because Tab_2D is now both in ascending order from 1->Ng

G1=Sort_r_Pg(1:N_G(1,1),:);
Sort_r_Pg(1:N_G(1,1),:)=[];

G2=Sort_r_Pg(1:N_G(1,2),:);
Sort_r_Pg(1:N_G(1,2),:)=[];

G3=Sort_r_Pg(1:N_G(1,3),:);
Sort_r_Pg(1:N_G(1,3),:)=[];

G4=Sort_r_Pg(1:N_G(1,4),:);
Sort_r_Pg(1:N_G(1,4),:)=[];

G5=Sort_r_Pg(1:N_G(1,5),:);
Sort_r_Pg(1:N_G(1,5),:)=[];

G6=Sort_r_Pg(1:N_G(1,6),:);
Sort_r_Pg(1:N_G(1,6),:)=[];

G7=Sort_r_Pg(1:N_G(1,7),:);
Sort_r_Pg(1:N_G(1,7),:)=[];

G8=Sort_r_Pg(1:N_G(1,8),:);
Sort_r_Pg(1:N_G(1,8),:)=[];

G9=Sort_r_Pg(1:N_G(1,9),:);
Sort_r_Pg(1:N_G(1,9),:)=[];

G10=Sort_r_Pg(1:N_G(1,10),:);
Sort_r_Pg(1:N_G(1,10),:)=[];

G11=Sort_r_Pg(1:N_G(1,11),:);
Sort_r_Pg(1:N_G(1,11),:)=[];

G12=Sort_r_Pg(1:N_G(1,12),:);
Sort_r_Pg(1:N_G(1,12),:)=[];

G13=Sort_r_Pg(1:N_G(1,13),:);
Sort_r_Pg(1:N_G(1,13),:)=[];

G14=Sort_r_Pg(1:N_G(1,14),:);
Sort_r_Pg(1:N_G(1,14),:)=[];
%% assign grouped generation capacities to the 2D table cells
% 1) Save generation buses and their related node degrees in cell arreys of
% K_cell
% 2) Save generation capacities in cell arreys of G_cell
% 3) Assigne generation capacities to the node degrees based  : For each
% cell arrey of K_cell (category of node degrees) starting from first array of G_cell based on the number of
% each cell in Tab_2D_Ng assigne generation capacities and then remove
% asigned generation capacities from G_cell.
K_cell=cell(1,14);
K_cell{1}=K1; K_cell{2}=K2; K_cell{3}=K3; K_cell{4}=K4; K_cell{5}=K5; K_cell{6}=K6; K_cell{7}=K7;
K_cell{8}=K8; K_cell{9}=K9; K_cell{10}=K10; K_cell{11}=K11; K_cell{12}=K12; K_cell{13}=K13; K_cell{14}=K14;

G_cell=cell(1,14);
G_cell{1}=G1; G_cell{2}=G2; G_cell{3}=G3; G_cell{4}=G4; G_cell{5}=G5; G_cell{6}=G6; G_cell{7}=G7;
G_cell{8}=G8; G_cell{9}=G9; G_cell{10}=G10; G_cell{11}=G11; G_cell{12}=G12; G_cell{13}=G13; G_cell{14}=G14;

for kk=1:14
    K_num=1;
    for gg=14:-1:1
        if Tab_2D_Ng(gg,kk)>0
            [samp_G,ind_G]=sg_datasample(G_cell{gg},Tab_2D_Ng(gg,kk),'replace',false);
            K_cell{kk}(K_num:(K_num + Tab_2D_Ng(gg,kk)-1),3)=samp_G;
            K_num=K_num+Tab_2D_Ng(gg,kk);
            G_cell{gg}(ind_G)=[];
        else
        K_cell{kk}(K_num:(K_num + Tab_2D_Ng(gg,kk)-1),3)=G_cell{gg}(1:Tab_2D_Ng(gg,kk));
        end
    end
end
% Gen_st is a martrix (Ng by 3) inclouds bus numbers, normalized node degrees and normalized generation capacities
Gen_st=[K_cell{1};K_cell{2};K_cell{3};K_cell{4};K_cell{5};K_cell{6};K_cell{7};K_cell{8};K_cell{9};K_cell{10};K_cell{11};K_cell{12};K_cell{13};K_cell{14}];
Norm_Generation_setting=sortrows(Gen_st,1);
Corr_co=corr(Norm_Generation_setting(:,2),Norm_Generation_setting(:,3));
end
end
