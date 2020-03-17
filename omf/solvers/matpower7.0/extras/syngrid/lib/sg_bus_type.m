function [Btypes] = sg_bus_type(link_ids, W)
%SG_BUS_TYPE  generates a random bus type assignment
%   BTYPES = SG_BUS_TYPE(LINK_IDS, W)
%
%   Input
%       link_ids - matrix (m by 2) indicating the branch terminal buses
%       W - Bus type entropy model (see SG_OPTIONS)
%
%   Output
%       Btypes - Bus type assignment vector (N by 1) of G/L/C (1/2/3)

%   SynGrid
%   Copyright (c) 2016-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Zhifang Wang and Seyyed Hamid Elyas, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).


% global Entopy_W W_star Standard_value
% link_ids=xlsread('RT_nestedSW_129.xlsx');
if W==0
    Entopy_W=0;
    %     assignin('base','Entopy_W',Entopy_W);
elseif W==1
    Entopy_W=1;
    %     assignin('base','Entopy_W',Entopy_W);
end



M=length(link_ids(:,1));
N=max(max(link_ids));

%%%%%%%% bus type ratio setting %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if N<2000
    G=0.23; L=0.55; C=0.22;    % for IEEE-300
elseif N<10000
    G=0.33; L=0.44; C=0.23;   % for NYISO
else
    G=0.2; L=0.4; C=0.4;      % for WECC
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Iter_PDF=2000;
W_Matrix=[];
History_Bus_Matrix=[];
K=1;
pop=[];
Best=[];
V1=[];
V2=[];
n=20;
B=0.4;
s=100;
Ratio_Bus_Type=[G,L,C];
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
W_Matrix=PDF_Final(link_ids,Ratio_Bus_Type,History_Bus_Matrix,N,M,Iter_PDF,Entopy_W);    % this function generates bus type entropy for each sample of bus type assignment
W_Mat=W_Matrix;
W_Matrix=sort(W_Matrix);
mean_value=mean(W_Matrix);
Standard_value=std(W_Matrix);
%%%%%%%%%%%%%%%%%%%%% generate PDF curve %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% [yy,xx]=hist(W_Matrix,100);
% yy=yy/Iter_PDF/(xx(2)-xx(1));
% axes(handles.axes1)
% bar(xx,yy)
% xlabel('Bus type entropy');
% ylabel('PDF');
% hold on
% pd = fitdist(W_Matrix,'Normal')
% y = pdf(pd,W_Matrix);
% plot(W_Matrix,y,'LineWidth',2)
% hold off
%%%%%%%%%%%%%%%%%%%%%%%%Normalized distanse (d)%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% if Entopy_W==0                   % Entopy_W=0 for the first definition
%     if log(N)<= 8
%         d_parameter=(-3.98*(log(N)))+15.85;
%     else
%         d_parameter=(-8.67*(10^(-9))*((log(N))^10.19));
%     end
% else                              % Entopy_W=1 for the second definition
%     if log(N)<= 8
%         d_parameter=(-4.19*(log(N)))+16.48;
%     else
%         d_parameter=-6.77*10^(-9)*(log(N))^10.52;
%     end
% end
if Entopy_W==0                   % Entopy_W=0 for the first definition
    if log(N)<= 8
        d_parameter=(-1.39*(log(N)))+6.79;
    else
        d_parameter=(-6.003*(10^(-14))*((log(N))^15.48));
    end
else                              % Entopy_W=1 for the second definition
    if log(N)<= 8
        d_parameter=(-1.748*(log(N)))+8.576;
    else
        d_parameter=-6.053*10^(-22)*(log(N))^24.1;
    end
end
W_star=(d_parameter*Standard_value)+mean_value;


M=length(link_ids(:,1));
N=max(max(link_ids));
if N<2000
    G=0.23; L=0.55; C=0.22;
else
    if N<10000
        G=0.33; L=0.44; C=0.23;
    else
        G=0.2; L=0.4; C=0.4;
    end
end
% Iter_PDF=str2double(get(handles.edit7,'String'));
Iter_PDF=2000;
% Max_iter=str2double(get(handles.edit8,'String'));
W_Matrix=[];

K=1;
pop=[];
Best=[];
V1=[];
V2=[];
n=20;
B=0.4;
s=100;
Ratio_Bus_Type=[G,L,C];
History_Bus_Matrix=[];
for i=1:n
    Bus_Matrix=bus_type_assignment(link_ids,Ratio_Bus_Type,History_Bus_Matrix,N);
    History_Bus_Matrix=[History_Bus_Matrix;Bus_Matrix];
    pop=[pop;Bus_Matrix];
end
Ratio_L_Matrix=rate_link(link_ids,Bus_Matrix,M,pop);

[W,pop1]=Affinity(M,N,pop,Ratio_Bus_Type,Ratio_L_Matrix,W_star,Entopy_W);

%--------------------------------------------------------------------------
%--------------------------------------------------------------------------
%%%%%%%%%%%%%%%%%%%%%%%%%%%% Body algorithm   %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Iter_Optimization=1;opt_iter=1;
while opt_iter==1
    %Iter_Optimization
    pop_final=[];
    %--------------------- Copy from the initial population -------------------
    pop2_clone=Clonal_Operator(pop1);
    %----------------------------- Mutation -----------------------------------
    pop3=Mutation_Operator(N,pop2_clone);
    popnew=vertcat(pop3,pop2_clone);
    m=size(popnew,1);
    %------------------------- add new solution -------------------------------
    ccc =0;
    for i=1:m/10
        Bus_Matrix=bus_type_assignment(link_ids,Ratio_Bus_Type,History_Bus_Matrix,N);
        ccc = ccc+1;
        History_Bus_Matrix=[History_Bus_Matrix;Bus_Matrix];
        pop4(i,:)=Bus_Matrix;
    end
    %------------------------- Select the best solutions ----------------------
    Pnew=vertcat(pop4,pop3,pop2_clone);
    pop=[];
    pop=Pnew;
    Ratio_L_Matrix=rate_link(link_ids,Bus_Matrix,M,pop);
    
    [W,pop1,Wbb]=Affinity(M,N,pop,Ratio_Bus_Type,Ratio_L_Matrix,W_star,Entopy_W);
    pop_final=pop1((1:n),:);
    Wbb;
    if N < 50
        if Entopy_W == 0
            Criteria = Standard_value/10;
        elseif Entopy_W == 1
            Criteria = Standard_value/2;
        end
    else
        Criteria = Standard_value/1000 ;
    end
    if W(1)< Criteria
        Best=[Best;pop_final(1,:)];
        opt_iter=0;
    end
    V1=[V1,W(1)];
    V2=[V2,Iter_Optimization];
    pop1=[];
    pop1=pop_final;
    Iter_Optimization=Iter_Optimization+1;
end
WW = W(1);
%%%%%%%%%%%%%%%%%%%%%End of optimization process %%%%%%%%%%%%%%%%%%%%%%%%%%
% Btypes(:,1)=1:length(Best');
Btypes=Best';
% save  Btypes Btypes;
% axes(handles.axes2)
% plot(V2,V1)
% xlabel('Iteration');
% ylabel('Error');

Best_Bus_Type_Assignments = Best;
L=size(Best_Bus_Type_Assignments,1);
Ratio_L_Matrix=[];
for k=1 : L
    Bus_Matrix=Best_Bus_Type_Assignments(k,:);
    Link_CC=0;
    Link_LL=0;
    Link_GG=0;
    Link_LC=0;
    Link_GC=0;
    Link_GL=0;
    
    for i=1:M
        T1=link_ids(i,1);
        T2=link_ids(i,2);
        if Bus_Matrix(1,T1)==1 && Bus_Matrix(1,T2)==1
            Link_GG=Link_GG+1;
        end
        if Bus_Matrix(1,T1)==1 && Bus_Matrix(1,T2)==2
            Link_GL=Link_GL+1;
        end
        if Bus_Matrix(1,T1)==1 && Bus_Matrix(1,T2)==3
            Link_GC=Link_GC+1;
        end
        if Bus_Matrix(1,T1)==2 && Bus_Matrix(1,T2)==1
            Link_GL=Link_GL+1;
        end
        if Bus_Matrix(1,T1)==2 && Bus_Matrix(1,T2)==2
            Link_LL=Link_LL+1;
        end
        if Bus_Matrix(1,T1)==2 && Bus_Matrix(1,T2)==3
            Link_LC=Link_LC+1;
        end
        if Bus_Matrix(1,T1)==3 && Bus_Matrix(1,T2)==1
            Link_GC=Link_GC+1;
        end
        if Bus_Matrix(1,T1)==3 && Bus_Matrix(1,T2)==2
            Link_LC=Link_LC+1;
        end
        if Bus_Matrix(1,T1)==3 && Bus_Matrix(1,T2)==3
            Link_CC=Link_CC+1;
        end
    end
    Rate_Link_GG=Link_GG/M;
    Rate_Link_LL=Link_LL/M;
    Rate_Link_CC=Link_CC/M;
    Rate_Link_GL=Link_GL/M;
    Rate_Link_GC=Link_GC/M;
    Rate_Link_LC=Link_LC/M;
    
    Ratio_Link=[Rate_Link_GG,Rate_Link_LL,Rate_Link_CC,Rate_Link_GL,Rate_Link_GC,Rate_Link_LC];
    Ratio_L_Matrix=[Ratio_L_Matrix;Ratio_Link];
end
for i=1:L
    W(i)=0;
    if Entopy_W==0
        X1=0;
        for f=1 : 3             %%% Three different bus types : G/L/C %%%
            X1=X1+(Ratio_Bus_Type(1,f)*log(Ratio_Bus_Type(1,f)));
        end
        X2=0;
        for f=1 : 6          %%% Six different link types : GG/LL/CC/GL/GC/LC %%%
            if Ratio_Link(1,f) ~=0
                X2=X2+(Ratio_Link(1,f)*log(Ratio_Link(1,f)));
            else
                X2=X2;
            end
        end
    end
    if Entopy_W==1
        X1=0;
        for f=1 : 3             %%% Three different bus types : G/L/C %%%
            X1=X1+(log(Ratio_Bus_Type(1,f))*(Ratio_Bus_Type(1,f)*N));
        end
        X2=0;
        for f=1 : 6          %%% Six different link types : GG/LL/CC/GL/GC/LC %%%
            if Ratio_Link(1,f) ~=0
                X2=X2+(log(Ratio_Link(1,f))*(Ratio_Link(1,f)*M));
            else
                X2=X2;
            end
        end
    end
    W(i)=-(X1+X2);
end
Best_W=W(1,1:L)';
% assignin('base','Best_Bus_Type_Assignments',Best_Bus_Type_Assignments);
% assignin('base','Best_W',Best_W);
% save Best_W Best_W

%%

function W_Matrix=PDF_Final(link_ids,Ratio_Bus_Type,History_Bus_Matrix,N,M,Iter_PDF,Entopy_W)

BBus =  (1:N)';
BBranch = link_ids;
Bus_degs=zeros(length(BBus(:,1)),1);
for Bii=1:length(BBus(:,1))
    count=0;
    for Li=1:length(BBranch)
        if BBranch(Li,1)==BBus(Bii,1)
            count=count+1;
        elseif BBranch(Li,2)==BBus(Bii,1)
            count=count+1;
        end
    end
    Bus_degs(Bii)=count;
end


W_Matrix=[];

K=1;
for iter_PDF=1:Iter_PDF
    %iter_PDF
    k=1;
    Bus_Matrix=[];

    G= round(N*Ratio_Bus_Type(1,1));             %%%%%%% total Number of Generator Bus %%%%%%%
    while K>0
        Bus_Matrix= zeros(1,N);
        C= round(N*Ratio_Bus_Type(1,3));  %%%%%% total Number of Connection Bus %%%%%%%
        for i=1:C
            T=round(1+rand*(N-1));
%             Bus_Matrix(1,T)
%             Bus_degs(T,1)
            if Bus_Matrix(1,T)==0 && Bus_degs(T,1) ~= 1;
                Bus_Matrix(1,T)=3;
            else
                while Bus_Matrix(1,T)~=0 && Bus_degs(T) == 1
                    T=round(1+rand*(N-1));
                end
                Bus_Matrix(1,T)=3;
            end
        end
        
        for i=1:G
            T=round(1+rand*(N-1));
            if Bus_Matrix(1,T)==0
                Bus_Matrix(1,T)=1;
            else
                while Bus_Matrix(1,T)~=0
                    T=round(1+rand*(N-1));
                end
                Bus_Matrix(1,T)=1;
            end
        end
        % L= round(N*Ratio_Bus_Type(1,2));             %%%%%%% total Number of Generator Bus %%%%%%%
        % for i=1:L
        %     T=round(1+rand*(N-1));
        %     if Bus_Matrix(1,T)==0
        %         Bus_Matrix(1,T)=2;
        %     else
        %         while Bus_Matrix(1,T)~=0
        %               T=round(1+rand*(N-1));
        %         end
        %          Bus_Matrix(1,T)=2;
        %     end
        % end
        for i=1:N
            if Bus_Matrix(1,i)==0
                %         Bus_Matrix(1,i)=3;
                Bus_Matrix(1,i)=2;
            end
        end
        ind=strfind(char(reshape(History_Bus_Matrix',1,[])),char(Bus_Matrix));
        K=size(ind);
    end
    History_Bus_Matrix=[History_Bus_Matrix;Bus_Matrix];
    K=1;
    Link_CC=0;
    Link_LL=0;
    Link_GG=0;
    Link_LC=0;
    Link_GC=0;
    Link_GL=0;
    for i=1:M
        T1=link_ids(i,1);
        T2=link_ids(i,2);
        if Bus_Matrix(1,T1)==1 && Bus_Matrix(1,T2)==1
            Link_GG=Link_GG+1;
        end
        if Bus_Matrix(1,T1)==1 && Bus_Matrix(1,T2)==2
            Link_GL=Link_GL+1;
        end
        if Bus_Matrix(1,T1)==1 && Bus_Matrix(1,T2)==3
            Link_GC=Link_GC+1;
        end
        if Bus_Matrix(1,T1)==2 && Bus_Matrix(1,T2)==1
            Link_GL=Link_GL+1;
        end
        if Bus_Matrix(1,T1)==2 && Bus_Matrix(1,T2)==2
            Link_LL=Link_LL+1;
        end
        if Bus_Matrix(1,T1)==2 && Bus_Matrix(1,T2)==3
            Link_LC=Link_LC+1;
        end
        if Bus_Matrix(1,T1)==3 && Bus_Matrix(1,T2)==1
            Link_GC=Link_GC+1;
        end
        if Bus_Matrix(1,T1)==3 && Bus_Matrix(1,T2)==2
            Link_LC=Link_LC+1;
        end
        if Bus_Matrix(1,T1)==3 && Bus_Matrix(1,T2)==3
            Link_CC=Link_CC+1;
        end
    end
    Rate_Link_GG=Link_GG/M;
    Rate_Link_LL=Link_LL/M;
    Rate_Link_CC=Link_CC/M;
    Rate_Link_GL=Link_GL/M;
    Rate_Link_GC=Link_GC/M;
    Rate_Link_LC=Link_LC/M;
    Ratio_Link=[Rate_Link_GG,Rate_Link_LL,Rate_Link_CC,Rate_Link_GL,Rate_Link_GC,Rate_Link_LC];
    
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    if Entopy_W==0
        X1=0;
        for f=1 : 3             %%% Three different bus types : G/L/C %%%
            X1=X1+(log(Ratio_Bus_Type(1,f))*Ratio_Bus_Type(1,f));
        end
        X2=0;
        for f=1 : 6          %%% Six different link types : GG/LL/CC/GL/GC/LC %%%
            if Ratio_Link(1,f) ~=0
                X2=X2+(log(Ratio_Link(1,f))*Ratio_Link(1,f));
            else
                X2=X2;
            end
        end
    end
    
    if Entopy_W==1
        X1=0;
        for f=1 : 3             %%% Three different bus types : G/L/C %%%
            X1=X1+(log(Ratio_Bus_Type(1,f))*(Ratio_Bus_Type(1,f)*N));
        end
        X2=0;
        for f=1 : 6          %%% Six different link types : GG/LL/CC/GL/GC/LC %%%
            if Ratio_Link(1,f) ~=0
                X2=X2+(log(Ratio_Link(1,f))*(Ratio_Link(1,f)*M));
            else
                X2=X2;
            end
        end
    end
    
    W=-(X1+X2);
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    W_Matrix=[W_Matrix;W];
end

%%
function Bus_Matrix=bus_type_assignment(link_ids,Ratio_Bus_Type,History_Bus_Matrix,N)
%--------------------------------------------------------------------------
% bus_type_assignment function generates a random bus type assignment.
% In order to prevent re-use of previous bus type assignment this function
% considers the History_Bus_Matrix to record all previous generated ones.
%
% Output:   for example: [2 2 3 1 3 2 1  ..... 3 1 2 2 3]
% The output is going to be an array (1 by N) including just 1,2 or 3 and
% as a candidate for bus type assignment. In this array 1: presents
% generation bus    2: presents load bus     3: presnets connection bus
%--------------------------------------------------------------------------


K=1;                                   %%%% Control parameter
Bus_Matrix=[];                         %%%% storage matrix

BBus =  (1:N)';
BBranch = link_ids;
Bus_degs=zeros(length(BBus(:,1)),1);
for Bii=1:length(BBus(:,1))
    count=0;
    for Li=1:length(BBranch)
        if BBranch(Li,1)==BBus(Bii,1)
            count=count+1;
        elseif BBranch(Li,2)==BBus(Bii,1)
            count=count+1;
        end
    end
    Bus_degs(Bii)=count;
end

%--------------------------------------------------------------------------
Node_no1 = find(Bus_degs(:,1) ~= 1);

while K>0
    Bus_Matrix= zeros(1,N);
    CC= round(N*Ratio_Bus_Type(1,2));     %%%% Total Number of Load Bus
    for i=1:CC
        T = sg_datasample(Node_no1,1);
%         T=round(1+rand*(N-1));
        if Bus_Matrix(1,T)==0
            Bus_Matrix(1,T)=3;
        else
            while Bus_Matrix(1,T)~=0
                T = sg_datasample(Node_no1,1);
%                 T=round(1+rand*(N-1));
            end
            Bus_Matrix(1,T)=3;
        end
    end
    
    
    G= round(N*Ratio_Bus_Type(1,1));       %%%% Total Number of Generator Bus
    %--------------------------------------------------------------------------
    %%%%%%%%%% Random procedure to determine the generation buses %%%%%%%%%%%%%
    for i=1:G
        T=round(1+rand*(N-1));
        if Bus_Matrix(1,T)==0
            Bus_Matrix(1,T)=1;
        else
            while Bus_Matrix(1,T)~=0
                T=round(1+rand*(N-1));
            end
            Bus_Matrix(1,T)=1;
        end
    end
    %--------------------------------------------------------------------------
%     %%%%%%%%%% Random procedure to determine the load buses %%%%%%%%%%%%%%%%%%%
%     
%     L= round(N*Ratio_Bus_Type(1,2));     %%%% Total Number of Load Bus
%     
%     for i=1:L
%         T=round(1+rand*(N-1));
%         if Bus_Matrix(1,T)==0
%             Bus_Matrix(1,T)=2;
%         else
%             while Bus_Matrix(1,T)~=0
%                 T=round(1+rand*(N-1));
%             end
%             Bus_Matrix(1,T)=2;
%         end
%     end
    %--------------------------------------------------------------------------
    %%%%%%%%%% Consider remained buses as connection buses  %%%%%%%%%%%%%%%%%%%
    
    for i=1:N
        if Bus_Matrix(1,i)==0
            Bus_Matrix(1,i)=2;
        end
    end
    %--------------------------------------------------------------------------
    %%%%%%%%%%%%% Check the generated bus type assignment   %%%%%%%%%%%%%%%%%%%
    
    ind=strfind(char(reshape(History_Bus_Matrix',1,[])),char(Bus_Matrix));
    K=size(ind);
    %--------------------------------------------------------------------------
end

%%
function Ratio_L_Matrix=rate_link(link_ids,Bus_Matrix,M,pop)
%--------------------------------------------------------------------------
% rate_link provides the ratio of six different link types.
%
%    Link_CC :  total number of links between two connection buses
%    Link_LL :  total number of links between two load buses
%    Link_GG :  total number of links between two generation buses
%    Link_LC :  total number of links between two connection and load buses
%    Link_GC :  total number of links between two connection and generation buses
%    Link_GL :  total number of links between two generation and load buses
%
%
% Output: The output is a matrix which each single row presents the link
% ratios for each random generated bus type assignments.
%
%--------------------------------------------------------------------------

Ratio_L_Matrix=[];
L=size(pop,1);
for k=1 : L
    Bus_Matrix=pop(k,:);
    Link_CC=0;
    Link_LL=0;
    Link_GG=0;
    Link_LC=0;
    Link_GC=0;
    Link_GL=0;
    
    for i=1:M
        T1=link_ids(i,1);
        T2=link_ids(i,2);
        if Bus_Matrix(1,T1)==1 && Bus_Matrix(1,T2)==1
            Link_GG=Link_GG+1;
        end
        if Bus_Matrix(1,T1)==1 && Bus_Matrix(1,T2)==2
            Link_GL=Link_GL+1;
        end
        if Bus_Matrix(1,T1)==1 && Bus_Matrix(1,T2)==3
            Link_GC=Link_GC+1;
        end
        if Bus_Matrix(1,T1)==2 && Bus_Matrix(1,T2)==1
            Link_GL=Link_GL+1;
        end
        if Bus_Matrix(1,T1)==2 && Bus_Matrix(1,T2)==2
            Link_LL=Link_LL+1;
        end
        if Bus_Matrix(1,T1)==2 && Bus_Matrix(1,T2)==3
            Link_LC=Link_LC+1;
        end
        if Bus_Matrix(1,T1)==3 && Bus_Matrix(1,T2)==1
            Link_GC=Link_GC+1;
        end
        if Bus_Matrix(1,T1)==3 && Bus_Matrix(1,T2)==2
            Link_LC=Link_LC+1;
        end
        if Bus_Matrix(1,T1)==3 && Bus_Matrix(1,T2)==3
            Link_CC=Link_CC+1;
        end
    end
    Rate_Link_GG=Link_GG/M;
    Rate_Link_LL=Link_LL/M;
    Rate_Link_CC=Link_CC/M;
    Rate_Link_GL=Link_GL/M;
    Rate_Link_GC=Link_GC/M;
    Rate_Link_LC=Link_LC/M;
    
    Ratio_Link=[Rate_Link_GG,Rate_Link_LL,Rate_Link_CC,Rate_Link_GL,Rate_Link_GC,Rate_Link_LC];
    Ratio_L_Matrix=[Ratio_L_Matrix;Ratio_Link];
end

%%
function [W,pop1,Wbb]=Affinity(M,N,pop,Ratio_Bus_Type,Ratio_L_Matrix,W_star,Entopy_W)
%--------------------------------------------------------------------------
%
% Affinity is a function which sorts the population "pop" from the best one
% to the worst one.
%
% Objective function :    Min (abs(W_star-W0))
%
% X=-sigma[Ratio_bus_types*log(Ratio_bus_types)]-sigma[Ratio_links*log(Ratio_links)]
%

%In other words we try to find the minimum value for objective function, say zero, to find
%some random bus type assignment which have maximum similarity to W_star
%
%
%Output: pop1 is the sorted version of pop from the maximum to minimum similarity
%
%--------------------------------------------------------------------------

L=size(pop,1);

for i=1:L
    W(i)=0;
    
    if Entopy_W==0
        X1=0;
        for f=1 : 3          %%% Three different bus types : G/L/C
            Ratio_Bus_Type(1,f);
            X1=X1+(Ratio_Bus_Type(1,f)*log(Ratio_Bus_Type(1,f)));
        end
        X2=0;
        
        for d=1 : 6          %%% Six different link types : GG/LL/CC/GL/GC/LC
            
            Ratio_L_Matrix(i,d);
            X2=X2+(Ratio_L_Matrix(i,d)*log(Ratio_L_Matrix(i,d))) ;
        end
    end
    if Entopy_W==1
        X1=0;
        for f=1 : 3             %%% Three different bus types : G/L/C %%%
            X1=X1+(log(Ratio_Bus_Type(1,f))*(Ratio_Bus_Type(1,f)*N));
        end
        X2=0;
        
        for d=1 : 6          %%% Six different link types : GG/LL/CC/GL/GC/LC
            Ratio_L_Matrix(i,d);
            X2=X2+(log(Ratio_L_Matrix(i,d))*(Ratio_L_Matrix(i,d)*M));
        end
    end
    
    X=-(X1+X2);
    Wbb (i) = X;
    W(i)=abs(W_star-X);
end
[W,ind]=sort(W);
Wbb = Wbb(ind);
pop1=pop(ind,:);

%%
function pop2_clone=Clonal_Operator(pop1)
%--------------------------------------------------------------------------
% Clone_Operator is used to copy the each single row of pop1. the pop1 is
% sorted from the best to worst. So the number of copies will be decreased
% from the first row, as the best one, to the last row, as the worst one.
%
% "B" and "s" are two parameters in the loop to generate different number of
% copies. The optimum values for 'B" and "s" are determined experimentally.
%
% Output: the output "pop2_clone" is a matrix including C1 copies from the
% first row of pop1, C2 copies from the second row of pop1, .... , Cn copies
% from the last row of pop1.

%               C1>C2>C3> ... >Cn
%
%--------------------------------------------------------------------------

B=0.4;
s=100;
X1=[];
L=size(pop1,1);
for i=1:L
    nc=round(B*s/i);
    for j=1:nc
        X(j,:)=pop1(i,:);
    end
    % X
    X1=[X1;X];
    X=[];
end
pop2_clone=X1;

%%
function pop3=Mutation_Operator(N,pop2_clone)
%--------------------------------------------------------------------------
% Mutation operator mutates the output of Clonal_operator. this function
% plays a very important role in local search and to skip the local
% optimum solutions.
%
% pop2_clone is a sorted matrix from the best to worst. So from the first
% row (the best one) to the last row (the worst one) we should increas the
% effect of mutation operator on random population.
% The first row of pop2_clone -----> minimum change
%  .
%  .
%  .
% The last row of pop2_clone -----> maximum change
%
%
% Output: the output is pop3 which includes mutated random bus type
% assignments. The size of pop3 and pop2_clone are the same.
%
%
%--------------------------------------------------------------------------

L=size(pop2_clone,1);
pop3=[];

for b=1:10
    for j=round(((b-1)*(L/10)))+1 : round(b*(L/10))
        for c=1:b
            X=round(1+rand*(N-1));
            mr=rand;
            pop2_clone(j,X);
            if mr<0.50
%             if mr<0.33
                pop2_clone(j,X)=1;
            else
%             if mr>0.33 && mr<0.66
                pop2_clone(j,X)=2;
            end
%             if mr>0.66
%                 pop2_clone(j,X)=1;
%             end
        end
        pop3=[pop3;pop2_clone(j,:)];
    end
end
pop3;
