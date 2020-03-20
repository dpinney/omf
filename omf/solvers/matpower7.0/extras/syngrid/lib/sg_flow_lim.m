function [Line_capacity, Zpr, xx, rr, ref, br_link] = ...
    sg_flow_lim(link_ids, A, Zpr, PL_setting, Pg_setting, br_overload, refsys_stat)
%SG_FLOW_LIM  main function to run transmission line capacity assignment
%   [LINE_CAPACITY, ZPR, XX, RR, REF, BR_LINK] = ...
%       SG_FLOW_LIM(LINK_IDS, A, ZPR, PL_SETTING, PG_SETTING, ...
%                   BR_OVERLOAD, REFSYS_STAT)
%
%   Input:
%       link_ids - matrix (m x 2) indicating the branch terminal buses
%       A - line admittance matrix
%       Zpr - generated line impedances
%       PL_setting - matrix (Nl x 2) indicating the load bus numbers and
%           load setting at each load bus
%       Pg_setting - matrix (Ng x 2) indicating the generation bus numbers
%           and  generation dispatch at each generation bus
%       br_overload - branch overload option (see SG_OPTIONS)
%       refsys_stat - statistics of reference system
%
%   Output:
%       Line_capacity - matrix (M x 2) indicating the line capacities
%           of each branch

%   SynGrid
%   Copyright (c) 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Hamidreza Sadeghian and Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

a_stab = refsys_stat.stab(1) ; b_stab = refsys_stat.stab(2) ; g_stab = refsys_stat.stab(3) ; d_stab = refsys_stat.stab(4);
Overload_b = refsys_stat.Overload_b ; 
mu_beta = refsys_stat.mu_beta ;
Tab_2D_FlBeta = refsys_stat.Tab_2D_FlBeta ;
M = length(link_ids);
N = length (A(1,:));
%% generate phi for calculation of X
% phi=random('stable',a_stab,b_stab,g_stab,d_stab,M,1);
phi = sg_random_stable(a_stab,b_stab,g_stab,d_stab,M,1);
phi_pos1 = find(phi >90);
phi_pos2 = find(phi <0);
phi_pos = [phi_pos1;phi_pos2];
if ~isempty(phi_pos)
    LL=1;
    while LL==1
        S_phi = sg_random_stable(a_stab,b_stab,g_stab,d_stab,length(phi_pos),1);
        phi(phi_pos) = S_phi;
        phi_pos1 = find(phi >90);
        phi_pos2 = find(phi <0);
        phi_pos = [phi_pos1;phi_pos2];
        if isempty(phi_pos)
            LL=0;
        else LL=1;
        end
    end
end
X_first = Zpr.*sind(phi);
R = Zpr.*cosd(phi);
%% DC power flow
if N<300
    nl = 1;
else
    nl = 2;
end
X_uni = ones(length(Zpr),1);
[I M_ref] = max(Pg_setting(:,2));
ref = Pg_setting(M_ref,1);
%% Impedance
bus = zeros(N, 17);
bus(:, 1) = (1:N)';
bus(:, 2) = 1;
bus(ref, 2) = 3;
bus(PL_setting(:,1), 3) = PL_setting(:,2);
bus(:, 8) = 1;
bus(:, 9) = 0;
gen = zeros(length(Pg_setting), 25);
gen(:, [1 2]) = Pg_setting;
gen(:, 8) = Pg_setting(:,2)>0;
gen(:, 6) = 1;
branch = zeros(length(link_ids), 21);
branch(:,[1 2]) = link_ids;
branch(:, [3 4]) = [R,X_uni];
branch(:, 11) = 1;
branch(:, 14) = 0;
branch(:, 16) = 0;
%% form MATPOWER case struct
mpt.version = '2';
mpt.baseMVA = 100;
mpt.bus = bus;
mpt.gen = gen;
mpt.branch = branch;
mpopt = mpoption('out.all', 0, 'verbose',0);
mpt = rundcpf(mpt,mpopt);

flow = mpt.branch(:,14);
theta_deg = mpt.bus(:,9);

for kk = 1:nl
    Z_BrF = (1:length(link_ids))';
    Z_BrF (:,[2,3]) = link_ids;
    Z_BrF (:,[4,5]) = [Zpr , abs(flow)];
    Z_BrF_sort = sortrows(Z_BrF,-5);
    Zpr_sort = sort(Zpr); % sort in ascending order
    Zpr_asgn = zeros(length(Zpr),2);
    for j= 1:length(Zpr)
        Zpr_asgn (Z_BrF_sort(j,1),1) = Z_BrF_sort(j,1);
        Zpr_asgn (Z_BrF_sort(j,1),2) = Zpr_sort(j,1);
    end
    Zpr_new_sort = sortrows(Zpr_asgn,2);
    if N>1200
        as = 0.3;
        an = 0.8;
    else
        as = 0.2;
        an = 0.2;
    end
    
    N_swap = round(as.*M); % control variable for the number of swaps
    N_neib = round(an.*M);% control variable for the range of neigboring
    for k = 1:N_swap;
        xch_idx1 = floor(M.*rand);
        if xch_idx1 ==0
            xch_idx1 =1;
        end
        xch_disf = floor(N_neib.*rand);
        xch_dis = min( xch_disf , (M -xch_idx1));
        xch_idx2 = xch_idx1 + xch_dis;
        Zpr_new_sort ([xch_idx1 xch_idx2] , 2) = Zpr_new_sort ([xch_idx2 xch_idx1] , 2); % swap elements of matrix
    end
    Zpr_new = sortrows(Zpr_new_sort, 1);
    X = Zpr_new(:,2).*sind(phi);
    R = Zpr_new(:,2).*cosd(phi);
    mpt.branch(:,4) = X;
    mpopt = mpoption('out.all', 0, 'verbose',0);
    mpt = rundcpf(mpt,mpopt);
    flow = mpt.branch(:,14);
    theta_deg = mpt.bus(:,9);
    Zpr = Zpr_new(:,2);
end
mpopt = mpoption('out.all', 0, 'verbose',0);
mpt = rundcpf(mpt,mpopt);
flow = mpt.branch(:,14);
theta_deg = mpt.bus(:,9);

%% Line connection
bus = zeros(N, 17);
bus(:, 1) = (1:N)';
bus(:, 2) = 1;
bus(ref, 2) = 3;
bus(PL_setting(:,1), 3) = PL_setting(:,2);
bus(:, 8) = 1;
bus(:, 9) = theta_deg;
gen = zeros(length(Pg_setting), 25);
gen(:, [1 2]) = Pg_setting;
gen(:, 8) = Pg_setting(:,2)>0;
gen(:, 6) = 1;
branch = zeros(length(link_ids), 21);
branch(:,[1 2]) = link_ids;
branch(:, [3 4]) = [R,X];
branch(:, 11) = 1;
branch(:, 14) = flow;
branch(:, 16) = -flow;
%% form MATPOWER case struct
mpp.version = '2';
mpp.baseMVA = 100;
mpp.bus = bus;
mpp.gen = gen;
mpp.branch = branch;
mpopt = mpoption('out.all', 0, 'verbose',0);
mpp = rundcpf(mpp,mpopt);
theta = mpp.bus(:,9);
d = repmat(theta,1,length(theta));
dd = repmat(theta',length(theta),1);
Bus_theta = dd-d;
DD = [];
DD = Bus_theta(:);
Branch = link_ids;
AA = A;
XX = X;
TT_target = 10.^(0.3196.*log10(N)+0.8324);
cc =0;
if max(abs(DD))> TT_target + 2
    while max(abs(DD)) > TT_target + 2
        cc = cc+1;
        theta = mpp.bus(:,9);
        d = repmat(theta,1,length(theta));
        dd = repmat(theta',length(theta),1);
        Bus_theta = dd-d;
        DD = [];
        DD = Bus_theta(:);
        Bus_delta = abs(triu(Bus_theta,0));
        [Rc,Cc] = ndgrid(1:size(Bus_delta,1),1:size(Bus_delta,2));
        [b,idx] = sort(Bus_delta(:),'descend');
        Bus_idx = [Rc(idx),Cc(idx)];
        Bus_phase_diff  = Bus_idx;
        Bus_phase_diff (:,3) = b;
        New_row = length(mpp.branch)+1;
        mpp.branch(New_row,1:2) = Bus_phase_diff(1,1:2);
        mpp.branch(New_row,3)  = 0.001 + rand*0.001;
        mpp.branch(New_row,4)  = 0.002 + rand*0.003;
        mpp.branch(New_row,11)  = 1;
        
        %% remove the branch
        Bus = mpp.bus;
        Branch = mpp.branch;
        Bus_degs=zeros(length(Bus(:,1)),1);
        for Bii=1:length(Bus(:,1))
            count=0;
            for Li=1:length(Branch)
                if Branch(Li,1)==Bus(Bii,1)
                    count=count+1;
                elseif Branch(Li,2)==Bus(Bii,1)
                    count=count+1;
                end
            end
            Bus_degs(Bii)=count;
        end
        Br_SL = 0.8; % parameter to select the range for branch removing
        Branch_deg_data = (1:length(mpp.branch))';
        Branch_deg_data (:,[2,3,4]) = mpp.branch(:,[1,2,4]); % collect branch 'from' 'to' and 'X'
        Branch_deg_data (:,5) = Bus_degs(Branch_deg_data(:,2)); % 'from' bus degree
        Branch_deg_data (:,6) = Bus_degs(Branch_deg_data(:,3)); % 'to' bus degree
        Branch_deg_data = sortrows(Branch_deg_data,4); % sort rows based on the X
        Branch_select = Branch_deg_data (round(Br_SL*length(mpp.branch)):end,:); % select candidate branches
        if N<40
            select_node = 2;
        else
            select_node = 3;
        end
        Branch_select(Branch_select(:,5)<select_node,:) = []; % remove branches with 'from' node degree < select_node, (2 or 3)
        Branch_select(Branch_select(:,6)<select_node,:) = []; % remove branches with 'to' node degree < select_node
        Row_num = ceil(rand*length(Branch_select(:,1)));
        if Row_num > 0 && Row_num <= length(Branch_select(:,1))
            Remove_idx = Branch_select(Row_num,1); % select the branch number to remove by generating random number in rang of 'Branch_select' length
            Rem_branch = mpp.branch;
            mpp.branch(Remove_idx,:) = [];
        end
        mpopt = mpoption('out.all', 0, 'verbose',0);
        mpp = rundcpf(mpp,mpopt);
        if mpp.success == 0
            mpp.branch = Rem_branch;
            mpp = rundcpf(mpp,mpopt);
        end
        xx = mpp.branch(:,4);
        rr = mpp.branch(:,3);
        br_link = mpp.branch(:,[1,2]);
    end
    xx = mpp.branch(:,4);
    rr = mpp.branch(:,3);
end
cc;
mpp = rundcpf(mpp,mpopt);
xx = mpp.branch(:,4);
rr = mpp.branch(:,3);
Zpr = (rr.^2+xx.^2).^(0.5);
br_link = mpp.branch(:,[1,2]);
flow = mpp.branch(:,14);
Flow=abs(mpp.branch(:,14));
meanflowww = mean(Flow);
thetadifff = max(mpp.bus(:,9)) - min(mpp.bus(:,9));
line_indx = colon(1,length(mpp.branch))';
Max_flow = max(Flow);
M = length(mpp.branch);
Norm_Flow = [line_indx,Flow./Max_flow];
%% generate line capacity factor
Overload_bet_n = round(M*Overload_b);
beta = sg_exprnd(mu_beta,M,1);
L_pos = find(beta >1);
if ~isempty(L_pos)
    LL=1;
    while LL==1
        S_beta = sg_exprnd(mu_beta,length(L_pos),1);
        beta(L_pos) = S_beta;
        L_pos = find(beta >1);
        if isempty(L_pos)
            LL=0;
        else LL=1;
        end
    end
end
if br_overload && Overload_bet_n > 0
    Overload_bet = 1 + 0.2*rand(Overload_bet_n,1);
    ind = randi([1,M],Overload_bet_n,1);
    beta(ind) = Overload_bet;
end
beta = sort(beta); % to avoid generation of line capacity factor equal to zero
beta_0 = find(beta == 0);
beta_0_rand = 0.01 + 0.099.*rand(length(beta_0),1);
beta(1:beta_0) = beta_0_rand;
[Norm_Flow_setting,Corr_FL] = Assignment_Fl(Norm_Flow,beta,Tab_2D_FlBeta);

% Line_capacity = [link_ids, Norm_Flow_setting(:,4).*Max_flow];
Line_capacity = [br_link, Norm_Flow_setting(:,4).*Max_flow];
Total_Trans_Cap = 10 ^(0.2875*(log10(N))^2-1.457*log10(N)+7.734);
Line_capacity (Line_capacity(:,3)<=2,3) = 5 +100*rand;
% Total_Trans_Cap1 = 11790*(N).^0.617;
% check the total backbone transmission capacity
% sometimes the total transmission capacity scaling cause to decrease the
% capaceties, increasing the over rating operation of lines
% Over_lines = find(abs(mpp.branch(:,14)) > Line_capacity(:,3)+0.001);
% Over_lines_beta = abs(mpp.branch(Over_lines,14))./ Line_capacity(Over_lines,3);
% k = 0;
% while k ==0
% if (sum(Line_capacity(:,3))>1.05*Total_Trans_Cap ||  sum(Line_capacity(:,3))<.95*Total_Trans_Cap)
%     Line_capacity(:,3) = Line_capacity(:,3).*(Total_Trans_Cap./sum(Line_capacity(:,3)));
%     k =0;
% else
%     k =1;
% end
% F_find = find(abs(mpp.branch(:,14)) >= Line_capacity(:,3));
% if ~isempty(F_find)
% Line_capacity(F_find,3) = abs(mpp.branch(F_find,14))+1;
% end
% end
% Line_capacity(Over_lines,3) = abs(mpp.branch(Over_lines,14))./Over_lines_beta;
mpp.branch(:,6) = Line_capacity(:,3);
mpp = rundcpf(mpp,mpopt);
Line_capacity(:,3);

%%
function [flow,theta_diff,ref,diff,theta_deg] = DFPF(N,A,X,link_ids,PL_setting,Pg_setting)

bus=zeros(N,2);
bus(PL_setting(:,1),1)=PL_setting(:,2);
bus(Pg_setting(:,1),2)=Pg_setting(:,2);
[~, ind_max]=max(bus(:,2));
ref=ind_max(1);
Pbus=(bus(:, 2) - bus(:, 1))./100;
B=A'*diag(1./X)*A;
pv=Pg_setting(:,1);
pq=(1:N)';
pq(pv) = [];
pv(pv==ref)=[];
Va0=zeros(N,1);
% Eliminating the corresponding row & col. i.e. row & col. of reference bus
[Va, ~] = dcpf(B, Pbus, Va0, ref, pv, pq);
theta_deg=Va.*(180/pi);
flow=diag(1./X)*A*Va;
flow = flow.*100; % actual value (Base MVA 100)
diff = max(theta_deg)-min(theta_deg);
for i=1:length(flow)
    theta_diff(i)=theta_deg(link_ids(i,1))-theta_deg(link_ids(i,2));
end

%%
function [Norm_Flow_setting,Corr_FL]=Assignment_Fl(Norm_Flow,beta,Tab_2D_FlBeta)

M=length(beta);
% calculate actual nnumber of each cell in 2D table nased on the total
% numbers
Tab_2D_M=round(Tab_2D_FlBeta.*M);
% check the mismatch comes from "round". Add or subtract from maximum
% number in the matrix
if sum(sum(Tab_2D_M))<M
    [~,ind_max_tab]=max(Tab_2D_M(:));
    [I_row, I_col] = ind2sub(size(Tab_2D_M),ind_max_tab);
    Tab_2D_M(I_row,I_col)=Tab_2D_M(I_row,I_col)+(M-sum(sum(Tab_2D_M)));
elseif sum(sum(Tab_2D_M))>M
    [~,ind_max_tab]=max(Tab_2D_M(:));
    [I_row, I_col] = ind2sub(size(Tab_2D_M),ind_max_tab);
    Tab_2D_M(I_row,I_col)=Tab_2D_M(I_row,I_col)-(sum(sum(Tab_2D_M))-M);
end
%% calculate target number of buses based on power flows and 2D table
N_F=zeros(1,14); % matrix for total number of buses in each node degree category
N_F = sum(Tab_2D_M,1);
sum(sum(Tab_2D_M,1));
sum(sum(Tab_2D_M,2));
%% sort power flows
Sort_norm_flow = sortrows(Norm_Flow,2);
%% assign branches to the power flow categories
Fl1=Sort_norm_flow(1:N_F(1,1),:);
Sort_norm_flow(1:N_F(1,1),:)=[];

Fl2=Sort_norm_flow(1:N_F(1,2),:);
Sort_norm_flow(1:N_F(1,2),:)=[];

Fl3=Sort_norm_flow(1:N_F(1,3),:);
Sort_norm_flow(1:N_F(1,3),:)=[];

Fl4=Sort_norm_flow(1:N_F(1,4),:);
Sort_norm_flow(1:N_F(1,4),:)=[];

Fl5=Sort_norm_flow(1:N_F(1,5),:);
Sort_norm_flow(1:N_F(1,5),:)=[];

Fl6=Sort_norm_flow(1:N_F(1,6),:);
Sort_norm_flow(1:N_F(1,6),:)=[];

Fl7=Sort_norm_flow(1:N_F(1,7),:);
Sort_norm_flow(1:N_F(1,7),:)=[];

Fl8=Sort_norm_flow(1:N_F(1,8),:);
Sort_norm_flow(1:N_F(1,8),:)=[];

Fl9=Sort_norm_flow(1:N_F(1,9),:);
Sort_norm_flow(1:N_F(1,9),:)=[];

Fl10=Sort_norm_flow(1:N_F(1,10),:);
Sort_norm_flow(1:N_F(1,10),:)=[];
N_F(1,11);
Sort_norm_flow(1:N_F(1,11),:);
Sort_norm_flow;
Fl11=Sort_norm_flow(1:N_F(1,11),:);
Sort_norm_flow(1:N_F(1,11),:)=[];

Fl12=Sort_norm_flow(1:N_F(1,12),:);
Sort_norm_flow(1:N_F(1,12),:)=[];

Fl13=Sort_norm_flow(1:N_F(1,13),:);
Sort_norm_flow(1:N_F(1,13),:)=[];

Fl14=Sort_norm_flow(1:N_F(1,14),:);
Sort_norm_flow(1:N_F(1,14),:)=[];


%% calculate target number of line capacity factors
N_B=zeros(1,14); % matrix for total number of buses in each node degree category
N_B = sum(Tab_2D_M,2)';

%% sort line capacity factors a
Sort_beta=sort(beta);

B1=Sort_beta(1:N_B(1,1),:);
Sort_beta(1:N_B(1,1),:)=[];

B2=Sort_beta(1:N_B(1,2),:);
Sort_beta(1:N_B(1,2),:)=[];

B3=Sort_beta(1:N_B(1,3),:);
Sort_beta(1:N_B(1,3),:)=[];

B4=Sort_beta(1:N_B(1,4),:);
Sort_beta(1:N_B(1,4),:)=[];

B5=Sort_beta(1:N_B(1,5),:);
Sort_beta(1:N_B(1,5),:)=[];

B6=Sort_beta(1:N_B(1,6),:);
Sort_beta(1:N_B(1,6),:)=[];

B7=Sort_beta(1:N_B(1,7),:);
Sort_beta(1:N_B(1,7),:)=[];

B8=Sort_beta(1:N_B(1,8),:);
Sort_beta(1:N_B(1,8),:)=[];

B9=Sort_beta(1:N_B(1,9),:);
Sort_beta(1:N_B(1,9),:)=[];

B10=Sort_beta(1:N_B(1,10),:);
Sort_beta(1:N_B(1,10),:)=[];

B11=Sort_beta(1:N_B(1,11),:);
Sort_beta(1:N_B(1,11),:)=[];

B12=Sort_beta(1:N_B(1,12),:);
Sort_beta(1:N_B(1,12),:)=[];

B13=Sort_beta(1:N_B(1,13),:);
Sort_beta(1:N_B(1,13),:)=[];

B14=Sort_beta(1:N_B(1,14),:);
Sort_beta(1:N_B(1,14),:)=[];

B15=Sort_beta(1:N_B(1,15),:);
Sort_beta(1:N_B(1,15),:)=[];

B16=Sort_beta(1:N_B(1,16),:);
Sort_beta(1:N_B(1,16),:)=[];
%% assign grouped power flows to the 2D table cells
Fl_cell=cell(1,14);
Fl_cell{1}=Fl1; Fl_cell{2}=Fl2; Fl_cell{3}=Fl3; Fl_cell{4}=Fl4; Fl_cell{5}=Fl5; Fl_cell{6}=Fl6; Fl_cell{7}=Fl7;
Fl_cell{8}=Fl8; Fl_cell{9}=Fl9; Fl_cell{10}=Fl10; Fl_cell{11}=Fl11; Fl_cell{12}=Fl12; Fl_cell{13}=Fl13; Fl_cell{14}=Fl14;

B_cell=cell(1,14);
B_cell{1}=B1; B_cell{2}=B2; B_cell{3}=B3; B_cell{4}=B4; B_cell{5}=B5; B_cell{6}=B6; B_cell{7}=B7;
B_cell{8}=B8; B_cell{9}=B9; B_cell{10}=B10; B_cell{11}=B11; B_cell{12}=B12; B_cell{13}=B13; B_cell{14}=B14; B_cell{15}=B15; B_cell{16}=B16;

for ff=14:-1:1
    Fl_num=1;
    for bb=16:-1:1
        if Tab_2D_M(bb,ff)>0
            [samp_B,ind_B]=sg_datasample(B_cell{bb},Tab_2D_M(bb,ff),'replace',false);
            Fl_cell{ff}(Fl_num:(Fl_num + Tab_2D_M(bb,ff)-1),3)=samp_B;
            Fl_num=Fl_num+Tab_2D_M(bb,ff);
            B_cell{bb}(ind_B)=[];
        else
            Fl_cell{ff}(Fl_num:(Fl_num + Tab_2D_M(bb,ff)-1),3)=B_cell{bb}(1:Tab_2D_M(bb,ff));
        end
    end
end
% Flow_st is a martrix (M by 4) inclouds line numbers, normalized
% power flow and line capacity factor
Flow_st=[Fl_cell{1};Fl_cell{2};Fl_cell{3};Fl_cell{4};Fl_cell{5};Fl_cell{6};Fl_cell{7};Fl_cell{8};Fl_cell{9};Fl_cell{10};Fl_cell{11};Fl_cell{12};Fl_cell{13};Fl_cell{14}];
Norm_Flow_setting = sortrows(Flow_st,1);
Norm_Flow_setting(:,4) = Norm_Flow_setting(:,2)./ Norm_Flow_setting(:,3);
Corr_FL = corr(Norm_Flow_setting(:,2), Norm_Flow_setting(:,3));
