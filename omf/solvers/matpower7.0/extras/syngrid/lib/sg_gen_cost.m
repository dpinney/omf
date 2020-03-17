function [gencost, genfuel, gentype] = sg_gen_cost(PgMax, cost_model, Tab_2D_gcost)
%SG_GEN_COST main function to run generation cost assignment
%   [GENCOST, GENFUEL, GENTYPE] = SG_GEN_COST(PGMAX, COST_MODEL, TAB_2D_GCOST)
%
%   Input:
%       PgMax - matrix (Ng by 2) indicating the generation bus number and
%           its maximum capacity
%       cost_model - Indicating the approach for generation cost (1/2)
%                   coefficients (1 = linear, based on heat rate and
%                   2 = quadratic, based on dispatch coefficients)
%       Tab_2D_gcost - PMF map table to assign generation types based on
%           generation capacities
%
%   Output:
%       gencost - MATPOWER generator cost matrix (see CASEFORMAT, IDX_COST)
%       genfuel - MATPOWER generator fuel type cell array (see GENFUELS)
%       gentype - MATPOWER generator type cell array (see GENTYPES)

%   SynGrid
%   Copyright (c) 2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Hamidreza Sadeghian and Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

Ng=length(PgMax);
% normalized PgMax
PgMax_norm = PgMax;
MAX_PgMax = max(PgMax(:,2));
PgMax_norm (:,2) = PgMax_norm (:,2)./MAX_PgMax;
% Assignment of generation types based on their generation capacity and 2D table
[Corr_type,Type_setting]=Assignment(PgMax_norm,Tab_2D_gcost);
% Output: calculate actual values for generation capacities
Type_setting(:,2)= Type_setting(:,2).*MAX_PgMax;
gentype = cell(Ng,1);
genfuel = cell(Ng,1);
gencost = zeros(Ng,4);
if cost_model == 2  %% Approach 2 (quadratic, based on dispatch cost coeffcients)
    gencost(:,1) = 2;
    gencost(:,4) = 3;
    for it = 1:Ng
        if Type_setting(it,3) == 1
            gentype{it}  = 'HY';
            genfuel{it}  = 'hydro';
            gencost (it,5:7) = 0;
        elseif Type_setting(it,3) == 2
            gentype{it}  = 'W2';
            genfuel{it}  = 'wind';
            gencost (it,5:7) = 0;
        elseif Type_setting(it,3) == 3
            gentype{it}  = 'GT';
            genfuel{it}  = 'ng';
            if Type_setting(it,2) <=400
                gencost (it,7) = 0 + 600*rand; %  reference "Aplication of Large-Scale Synthetic Power System Models ....." a0 -> (0 - 600)
            else
                gencost (it,7) = 600 + 3259*rand; % a0 -> (600 - 3859) [$/hr]
            end
            gencost (it,6) = 23.13 + 33.9*rand; %   a1 -> (23.13-57.03)  [$/MWh]
            gencost (it,5) = 0.002 + 0.006*rand; % a2 -> (0.002 - 0.008)  [$/MWh^2]
        elseif Type_setting(it,3) == 4
            gentype{it}  = 'ST';
            genfuel{it}  = 'coal';
            if Type_setting(it,2) <=75
                gencost (it,7) = 0 + 238*rand; % a0  -> (0-238)
            elseif Type_setting(it,2) > 75 && Type_setting(it,2) <=150
                gencost (it,7) = 238 + 507*rand; % a0 -> (238 - 745)
            elseif Type_setting(it,2) > 150 && Type_setting(it,2) <=350
                gencost (it,7) = 745 + 468*rand; % a0 -> (745 - 1213)
            else
                gencost (it,7) = 1213 + 1830*rand; % a0 -> (1213 - 3043)
            end
            gencost (it,6) = 19; %   a1 -> (19)
            gencost (it,5) = 0.001; % a2 -> (0.001)
        elseif Type_setting(it,3) == 5
            gentype{it}  = 'NB';
            genfuel{it}  = 'nuclear';
            gencost (it,7) = 1000 + 500*rand; % a0 -> (1000 - 1500)
            gencost (it,6) = 5 + 6*rand; % a1 -> (5 - 11)
            gencost (it,5) = 0.00015 + 0.00008*rand; % a2 -> (0.00015 - 0.00023)
%             gencost (it,5) = 0.000015 + 0.000008*rand; % a2 -> (0.00015 - 0.00023)
        end
    end
elseif cost_model == 1  %% Approach 1 (linear, based on heat rate)
    gencost(:,1) = 2;
    gencost(:,4) = 2;
    for it = 1:Ng
        if Type_setting(it,3) == 1
            gentype{it}  = 'HY';
            genfuel{it}  = 'hydro';
            gencost (it,5:6) = 0;
        elseif Type_setting(it,3) == 2
            gentype{it}  = 'W2';
            genfuel{it}  = 'wind';
            gencost (it,5:6) = 0;
        elseif Type_setting(it,3) == 3
            gentype{it}  = 'GT';
            genfuel{it}  = 'ng';
            if Type_setting(it,2) <=400
                gencost (it,6) = 0 + 600*rand; %  reference "Aplication of Large-Scale Synthetic Power System Models ....." a0 -> (0 - 600)
            else
                gencost (it,6) = 600 + 3259*rand; % a0 -> (600 - 3859)
            end
            gencost (it,5) = 2.59.*(6.5 + rand*11); % a1 = cf*b1 -> cf = 2.59   & b1 = (6.5 - 17.5)
        elseif Type_setting(it,3) == 4
            gentype{it}  = 'ST';
            genfuel{it}  = 'coal';
            if Type_setting(it,2) <=75
                gencost (it,6) = 0 + 238*rand; % a0  -> (0-238)
            elseif Type_setting(it,2) > 75 && Type_setting(it,2) <=150
                gencost (it,6) = 238 + 507*rand; % a0 -> (238 - 745)
            elseif Type_setting(it,2) > 150 && Type_setting(it,2) <=350
                gencost (it,6) = 745 + 468*rand; % a0 -> (745 - 1213)
            else
                gencost (it,6) = 1213 + 1830*rand; % a0 -> (1213 - 3043)
            end
            gencost (it,5) = 2.16.*(9.43 + rand*9.1); % a1 = cf*b1 -> cf = 2.16   & b1 = (9.43 - 18.53)
        elseif Type_setting(it,3) == 5
            gentype{it}  = 'NB';
            genfuel{it}  = 'nuclear';
            gencost (it,6) = 1000 + 500*rand; % a0 -> (1000 - 1500)
            gencost (it,5) = 0.85.*10.46; % a1 = cf*b1 -> cf = 0.85   & b1 = 10.46
        end
    end
end

%%
    function [Corr_co,Type_setting]=Assignment(PgMax_norm,Tab_2D)
        % This is a function to assign the generation types to the generation buses based
        % on PgMAX
        %
        % input:
        %       Normalized_Generation_capacity- matrix (2 by Ng) indicating
        %       the normalized value of generation capacity
        %       Tab_2D - matrix (5 by 14) indicating the assignment pattern
        % output:
        %       Type_setting- matrix (Ng by 3) indicating the type setting at each generation bus
        
        Ng=length(PgMax_norm);
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
        N_PgM= zeros(1,14); % matrix for total number of buses in each node degree category
        N_PgM = sum(Tab_2D_Ng,1);
        
        %% sort node degrees
        Sort_PgMax=sortrows(PgMax_norm,2);
        %% assign buses to the node degree categories
        PgM1=Sort_PgMax(1:N_PgM(1,1),:);
        Sort_PgMax(1:N_PgM(1,1),:)=[];
        
        PgM2=Sort_PgMax(1:N_PgM(1,2),:);
        Sort_PgMax(1:N_PgM(1,2),:)=[];
        
        PgM3=Sort_PgMax(1:N_PgM(1,3),:);
        Sort_PgMax(1:N_PgM(1,3),:)=[];
        
        PgM4=Sort_PgMax(1:N_PgM(1,4),:);
        Sort_PgMax(1:N_PgM(1,4),:)=[];
        
        PgM5=Sort_PgMax(1:N_PgM(1,5),:);
        Sort_PgMax(1:N_PgM(1,5),:)=[];
        
        PgM6=Sort_PgMax(1:N_PgM(1,6),:);
        Sort_PgMax(1:N_PgM(1,6),:)=[];
        
        PgM7=Sort_PgMax(1:N_PgM(1,7),:);
        Sort_PgMax(1:N_PgM(1,7),:)=[];
        
        PgM8=Sort_PgMax(1:N_PgM(1,8),:);
        Sort_PgMax(1:N_PgM(1,8),:)=[];
        
        PgM9=Sort_PgMax(1:N_PgM(1,9),:);
        Sort_PgMax(1:N_PgM(1,9),:)=[];
        
        PgM10=Sort_PgMax(1:N_PgM(1,10),:);
        Sort_PgMax(1:N_PgM(1,10),:)=[];
        
        PgM11=Sort_PgMax(1:N_PgM(1,11),:);
        Sort_PgMax(1:N_PgM(1,11),:)=[];
        
        PgM12=Sort_PgMax(1:N_PgM(1,12),:);
        Sort_PgMax(1:N_PgM(1,12),:)=[];
        
        PgM13=Sort_PgMax(1:N_PgM(1,13),:);
        Sort_PgMax(1:N_PgM(1,13),:)=[];
        
        PgM14=Sort_PgMax(1:N_PgM(1,14),:);
        Sort_PgMax(1:N_PgM(1,14),:)=[];
        
        %% calculate target number of generations in normalized generation capacity categories
        N_T=zeros(1,5); % matrix for total number of buses in each node degree category
        N_T = sum(Tab_2D_Ng,2)';
        %% assign grouped generation capacities to the 2D table cells
        % 1) Save generation buses and their related node degrees in cell arreys of
        % K_cell
        % 2) Save generation capacities in cell arreys of G_cell
        % 3) Assigne generation capacities to the node degrees based  : For each
        % cell arrey of K_cell (category of node degrees) starting from first array of G_cell based on the number of
        % each cell in Tab_2D_Ng assigne generation capacities and then remove
        % asigned generation capacities from G_cell.
        K_cell=cell(1,14);
        K_cell{1}=PgM1; K_cell{2}=PgM2; K_cell{3}=PgM3; K_cell{4}=PgM4; K_cell{5}=PgM5; K_cell{6}=PgM6; K_cell{7}=PgM7;
        K_cell{8}=PgM8; K_cell{9}=PgM9; K_cell{10}=PgM10; K_cell{11}=PgM11; K_cell{12}=PgM12; K_cell{13}=PgM13; K_cell{14}=PgM14;
        
        Type_gen =[];
        for pgm=1:14
            for tt=1:1:5
                if Tab_2D_Ng(tt,pgm)>0
                    [samp_G,ind_G]=sg_datasample(K_cell{pgm},Tab_2D_Ng(tt,pgm),'replace',false);
                    K_cell{pgm}(ind_G,3)=tt;
                    Type_gen = [Type_gen;K_cell{pgm}(ind_G,:)];
                    K_cell{pgm}(ind_G,:)=[];
                end
            end
        end
        Type_setting=sortrows(Type_gen,1);
        Corr_co=corr(Type_setting(:,2),Type_setting(:,3));
    end
end
