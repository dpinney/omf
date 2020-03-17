function [Pg_setting] = sg_gen_dispatch(PgMax, PL_setting, refsys_stat)
%SG_GEN_DISPATCH  main function to run Pg setting
%   [PG_SETTING, CORR_PG] = SG_GEN_DISPATCH(PGMAX, PL_SETTING, REFSYS_STAT)
%
%   Input:
%       PgMax - matrix (Ng by 2) indicating the generation bus numbers
%           and generation capacity at each generation bus
%       PL_setting - matrix (NL by 2) indicating the load bus numbers
%           and load size at each load bus
%       refsys_stat - statistics of reference system
%
%   Output:
%       Pg_setting - matrix (Ng by 2) indicating the generation bus numbers and
%           generation dispatch

%   SynGrid
%   Copyright (c) 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Hamidreza Sadeghian and Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
Alpha_mod = refsys_stat.Alpha_mod;
mu_committed = refsys_stat.mu_committed ;
Tab_2D_Pg = refsys_stat.Tab_2D_Pg ;
Ng=length(PgMax);
Max=max(PgMax(:,2));
Norm_PgMax=[PgMax(:,1),PgMax(:,2)./Max];
Norm_Total_load=sum(PL_setting(:,2))./Max;

%% Uncommitted  units (10~20)% of total number of generation units
Ng_Uncommitted=round(Ng*(10+rand*(10))/100);
Norm_Uncommitted_Units=[];

for i=1:Ng_Uncommitted
    % uniform selection of uncommitted unites between [0-0.6]
    T_Uncomm=0.6.*rand(1,1);
    Test=abs(Norm_PgMax(:,2)-T_Uncomm);
    [Test,ind]=sort(Test);
    Norm_PgMax=Norm_PgMax(ind,:);
    Norm_Uncommitted_Units=[Norm_Uncommitted_Units;Norm_PgMax(1,:),0];
    Norm_PgMax(1,:)=[];
end
Norm_PgMax1=Norm_PgMax;

%% Committed units (40~50)% of total number of generation units
Ng_Comm=round(Ng*(40+rand*(10))/100);
[Norm_PgMax,Norm_Committed_Units]=Pg_sellection(Norm_PgMax,Ng_Comm,mu_committed);
% Dispatch factor generation
[Alpha]=Alpha_gen(Norm_Committed_Units,Alpha_mod);
% Assignment of Alpha to committed generations
[Norm_Committed_Units,Corr_pg]=Assignment_Pg(Alpha,Norm_Committed_Units,Tab_2D_Pg);

%% Full load units
Norm_FullLoad_Units=Norm_PgMax;
Norm_FullLoad_Units(:,3)=1;
%% Load balance
[Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units,AllDispatch_f]=dispatch_finalizing(Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units);
Norm_tot_generation=sum(AllDispatch_f(:,4));
Norm_Gen_diff=Norm_tot_generation-Norm_Total_load;

if Norm_Gen_diff > 0 %Generation should be decreased
    df_comm=sum(Norm_Committed_Units(:,4))-Norm_Gen_diff;
    if df_comm > 0
        dk=1;
        while dk==1
            Norm_Committed_Units(:,3)=Norm_Committed_Units(:,3).*0.99;
            [Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units,AllDispatch_f]=dispatch_finalizing(Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units);
            Norm_tot_generation=sum(AllDispatch_f(:,4));
            Norm_Gen_diff=Norm_tot_generation-Norm_Total_load;
            if Norm_Gen_diff <= 0
                dk=0;
            else dk=1;
            end
        end
    else
        dkk=1;
        while dkk==1
            [max_1, max_1_ind]=max(Norm_FullLoad_Units(:,3));
            Norm_FullLoad_Units(max_1_ind(1),3)=0;
            [Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units,AllDispatch_f]=dispatch_finalizing(Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units);
            Norm_tot_generation=sum(AllDispatch_f(:,4));
            Norm_Gen_diff=Norm_tot_generation-Norm_Total_load;
            if Norm_Gen_diff <= 0
                dkk=0;
            else dkk=1;
            end
        end
    end
end
            [Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units,AllDispatch_f]=dispatch_finalizing(Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units);
            Norm_tot_generation=sum(AllDispatch_f(:,4));
            Norm_Gen_diff=Norm_tot_generation-Norm_Total_load;
if Norm_Gen_diff < 0 %Generation should be increase
    ik=1;
    while ik==1
        if length(find(Norm_Committed_Units(:,3)<1)) > .5*length(Norm_Committed_Units(:,1))
            Norm_Committed_Units(:,3)=Norm_Committed_Units(:,3).*1.05;
            Norm_Committed_Units(Norm_Committed_Units(:,3)>1,3)=1;
            [Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units,AllDispatch_f]=dispatch_finalizing(Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units);
            Norm_tot_generation=sum(AllDispatch_f(:,4));
            Norm_Gen_diff=Norm_tot_generation-Norm_Total_load;
            if Norm_Gen_diff > 0
                ik = 0;
            else ik = 1;
            end
        else
            ikk=1;
            while ikk==1
                [min_0, min_0_ind]=min(Norm_Uncommitted_Units(:,3));
                if min_0==1
                    [min_0, min_0_ind_ful]=min(Norm_FullLoad_Units(:,3));
                    Norm_FullLoad_Units(min_0_ind_ful(1),3)=1;
                    if min_0==1
                    Norm_Committed_Units(ceil(rand*length(Norm_Committed_Units(:,1))),3)=1;
                    end
                end
                Norm_Uncommitted_Units(min_0_ind(1),3)=1;
                [Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units,AllDispatch_f]=dispatch_finalizing(Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units);
                Norm_tot_generation=sum(AllDispatch_f(:,4));
                Norm_Gen_diff=Norm_tot_generation-Norm_Total_load;
                if Norm_Gen_diff > 0
                    ikk=0;
                    ik=0;
                else ikk=1;
                end
            end
        end
%         ik=0;
    end
end
Uncommitted_Units=Norm_Uncommitted_Units;
Uncommitted_Units(:,4)=Norm_Uncommitted_Units(:,4).*Max;
Committed_Units=Norm_Committed_Units;
Committed_Units(:,4)=Norm_Committed_Units(:,4).*Max;
FullLoad_Units=Norm_FullLoad_Units;
FullLoad_Units(:,4)=Norm_FullLoad_Units(:,4).*Max;
GenerationDispatch = [Uncommitted_Units(:,[1,4]);Committed_Units(:,[1,4]);FullLoad_Units(:,[1,4])];
Pg_setting = sortrows(GenerationDispatch,1);

%%
function [Norm_PgMax,Norm_Units]=Pg_sellection(Norm_PgMax,Nunit,mu_unit)

Ng_unit_90=round(Nunit.*0.99);
Ng_unit_01=Nunit-Ng_unit_90;
Norm_Units=[];
for ic=1:Ng_unit_90
    T_unit=sg_exprnd(mu_unit,1,1);
    Test=abs(Norm_PgMax(:,2)-T_unit);
    [Test,ind]=sort(Test);
    Norm_PgMax=Norm_PgMax(ind,:);
    Norm_Units=[Norm_Units;Norm_PgMax(1,:)];
    Norm_PgMax(1,:)=[];
end
if Ng_unit_01>0
    for icc=1:Ng_unit_01
        T_comm_01=0.5 + 0.5.*rand(1,1);
        Test=abs(Norm_PgMax(:,2)-T_comm_01);
        [Test,ind]=sort(Test);
        Norm_PgMax=Norm_PgMax(ind,:);
        Norm_Units=[Norm_Units;Norm_PgMax(1,:)];
        Norm_PgMax(1,:)=[];
    end
end

%%
function [Alpha]=Alpha_gen(Norm_Committed_Units,Alpha_mod)
%This is a fuction for random dispatch factor (alpha) generation

Nc=length(Norm_Committed_Units(:,1));

%% Uniform random generation
if ~Alpha_mod
    % for NYISO and ERCOT 0<a<1
    Alpha=rand(Nc,1);
else
    % for WECC negative alpha
    Nc995=round(Nc.*0.995);
    Nc005=Nc-Nc995;
    Alpha995=rand(Nc995,1);
    Alpha005=-rand(Nc005,1);
    Alpha=[Alpha995;Alpha005];
end

%%
function [Assigned_Committed_units,Corr_pg]=Assignment_Pg(Alpha,Norm_Committed_Units,Tab_2D_Pg)
% This is a function to assign the normalized generation capacities to the generation buses based
% on node degrees
%
% input:
%       Alpha - matrix (Nc by 1) indicating the value of dispatch factors
%       Norm_committed_units - matrix (Nc by 2) indicating thecommitted units and their normalized
%       value
%       Tab_2D - matrix (14 by 10) indicating the assignment pattern
% output:
%       Generation_dispatch- matrix (Nc by 3) indicating the generation capacity setting at each generation bus
%             gen bus number, norm_node degree,  norm_Pg_max

Nc=length(Norm_Committed_Units);
% calculate actual nnumber of each cell in 2D table nased on the total
% number of generations
Tab_2D_Nc=round(Tab_2D_Pg.*Nc);
% check the mismatch comes from "round". Add or subtract from maximum
% number in the matrix
if sum(sum(Tab_2D_Nc))<Nc
    [Max_tab,ind_max_tab]=max(Tab_2D_Nc(:));
    [I_row, I_col] = ind2sub(size(Tab_2D_Nc),ind_max_tab);
    Tab_2D_Nc(I_row,I_col)=Tab_2D_Nc(I_row,I_col)+(Nc-sum(sum(Tab_2D_Nc)));
elseif sum(sum(Tab_2D_Nc))>Nc
    [Max_tab,ind_max_tab]=max(Tab_2D_Nc(:));
    [I_row, I_col] = ind2sub(size(Tab_2D_Nc),ind_max_tab);
    Tab_2D_Nc(I_row,I_col)=Tab_2D_Nc(I_row,I_col)-(sum(sum(Tab_2D_Nc))-Nc);
end
%% calculate target number of buses based on node degree and 2D table
N_a=zeros(1,10); % matrix for total number of buses in each dispatch factor category
N_a = sum(Tab_2D_Nc,1);

%% sort node degrees
Sort_alpha=sort(Alpha);
%% assign buses to the node degree categories
A1=Sort_alpha(1:N_a(1,1),:);
Sort_alpha(1:N_a(1,1),:)=[];

A2=Sort_alpha(1:N_a(1,2),:);
Sort_alpha(1:N_a(1,2),:)=[];

A3=Sort_alpha(1:N_a(1,3),:);
Sort_alpha(1:N_a(1,3),:)=[];

A4=Sort_alpha(1:N_a(1,4),:);
Sort_alpha(1:N_a(1,4),:)=[];

A5=Sort_alpha(1:N_a(1,5),:);
Sort_alpha(1:N_a(1,5),:)=[];

A6=Sort_alpha(1:N_a(1,6),:);
Sort_alpha(1:N_a(1,6),:)=[];

A7=Sort_alpha(1:N_a(1,7),:);
Sort_alpha(1:N_a(1,7),:)=[];

A8=Sort_alpha(1:N_a(1,8),:);
Sort_alpha(1:N_a(1,8),:)=[];

A9=Sort_alpha(1:N_a(1,9),:);
Sort_alpha(1:N_a(1,9),:)=[];

A10=Sort_alpha(1:N_a(1,10),:);
Sort_alpha(1:N_a(1,10),:)=[];

%% calculate target number of generations in normalized generation capacity categories
N_C=zeros(1,14); % matrix for total number of buses in each node degree category
N_C = sum(Tab_2D_Nc,2)';

%% sort generation capacities and assign them to normalized generation capacities groups of 2D table
Sort_r_PgCm=sortrows(Norm_Committed_Units,2); %changed by zfwang, because Tab_2D is now both in ascending order from 1->Ng

G1=Sort_r_PgCm(1:N_C(1,1),:);
Sort_r_PgCm(1:N_C(1,1),:)=[];

G2=Sort_r_PgCm(1:N_C(1,2),:);
Sort_r_PgCm(1:N_C(1,2),:)=[];

G3=Sort_r_PgCm(1:N_C(1,3),:);
Sort_r_PgCm(1:N_C(1,3),:)=[];

G4=Sort_r_PgCm(1:N_C(1,4),:);
Sort_r_PgCm(1:N_C(1,4),:)=[];

G5=Sort_r_PgCm(1:N_C(1,5),:);
Sort_r_PgCm(1:N_C(1,5),:)=[];

G6=Sort_r_PgCm(1:N_C(1,6),:);
Sort_r_PgCm(1:N_C(1,6),:)=[];

G7=Sort_r_PgCm(1:N_C(1,7),:);
Sort_r_PgCm(1:N_C(1,7),:)=[];

G8=Sort_r_PgCm(1:N_C(1,8),:);
Sort_r_PgCm(1:N_C(1,8),:)=[];

G9=Sort_r_PgCm(1:N_C(1,9),:);
Sort_r_PgCm(1:N_C(1,9),:)=[];

G10=Sort_r_PgCm(1:N_C(1,10),:);
Sort_r_PgCm(1:N_C(1,10),:)=[];

G11=Sort_r_PgCm(1:N_C(1,11),:);
Sort_r_PgCm(1:N_C(1,11),:)=[];

G12=Sort_r_PgCm(1:N_C(1,12),:);
Sort_r_PgCm(1:N_C(1,12),:)=[];

G13=Sort_r_PgCm(1:N_C(1,13),:);
Sort_r_PgCm(1:N_C(1,13),:)=[];

G14=Sort_r_PgCm(1:N_C(1,14),:);
Sort_r_PgCm(1:N_C(1,14),:)=[];
%% assign grouped generation capacities to the 2D table cells
% 1) Save generation buses and their related node degrees in cell arreys of
% K_cell
% 2) Save generation capacities in cell arreys of G_cell
% 3) Assigne generation capacities to the node degrees based  : For each
% cell arrey of K_cell (category of node degrees) starting from first array of G_cell based on the number of
% each cell in Tab_2D_Ng assigne generation capacities and then remove
% asigned generation capacities from G_cell.
Al_cell=cell(1,10);
Al_cell{1}=A1; Al_cell{2}=A2; Al_cell{3}=A3; Al_cell{4}=A4; Al_cell{5}=A5; Al_cell{6}=A6; Al_cell{7}=A7;
Al_cell{8}=A8; Al_cell{9}=A9; Al_cell{10}=A10;

Cm_cell=cell(1,14);
Cm_cell{1}=G1; Cm_cell{2}=G2; Cm_cell{3}=G3; Cm_cell{4}=G4; Cm_cell{5}=G5; Cm_cell{6}=G6; Cm_cell{7}=G7;
Cm_cell{8}=G8; Cm_cell{9}=G9; Cm_cell{10}=G10; Cm_cell{11}=G11; Cm_cell{12}=G12; Cm_cell{13}=G13; Cm_cell{14}=G14;

for aa=1:10
    K_num=1;
    for gg=14:-1:1
        if Tab_2D_Nc(gg,aa)>0
            [samp_G,ind_G]=sg_datasample(Cm_cell{gg}(:,1),Tab_2D_Nc(gg,aa),'replace',false);
            Al_cell{aa}(K_num:(K_num + Tab_2D_Nc(gg,aa)-1),2:3)=Cm_cell{gg}(ind_G,:)  ;
            K_num=K_num+Tab_2D_Nc(gg,aa);
            Cm_cell{gg}(ind_G,:)=[];
        else
        Al_cell{aa}(K_num:(K_num + Tab_2D_Nc(gg,aa)-1),2:3)=Cm_cell{gg}(1:Tab_2D_Nc(gg,aa),:);
        end
    end
end
% Gen_dispatch is a martrix (Ng by 3) inclouds Alpha, bus numbers of
% commited units and their generation capacity
Gen_dispatch=[Al_cell{1};Al_cell{2};Al_cell{3};Al_cell{4};Al_cell{5};Al_cell{6};Al_cell{7};Al_cell{8};Al_cell{9};Al_cell{10}];
Rearrange_Gen_dispatch=[Gen_dispatch(:,2:3),Gen_dispatch(:,1)];
Assigned_Committed_units=sortrows(Rearrange_Gen_dispatch,1);
Corr_pg=corr(Assigned_Committed_units(:,3),Assigned_Committed_units(:,2));

%%
function [Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units,AllDispatch_f]=dispatch_finalizing(Norm_Uncommitted_Units,Norm_Committed_Units,Norm_FullLoad_Units)
% this fuction calculate final the generation of each generation by
% multiplying dispatch factor and Pgmax     
Norm_Uncommitted_Units(:,4)=Norm_Uncommitted_Units(:,2).*Norm_Uncommitted_Units(:,3);
Norm_Committed_Units(:,4)=Norm_Committed_Units(:,2).*Norm_Committed_Units(:,3);
Norm_FullLoad_Units(:,4)=Norm_FullLoad_Units(:,2).*Norm_FullLoad_Units(:,3);
AllDispatch_f=[Norm_Uncommitted_Units;Norm_Committed_Units;Norm_FullLoad_Units];
