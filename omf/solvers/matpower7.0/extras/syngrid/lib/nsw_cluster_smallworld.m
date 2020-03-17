function [A,Ma,indx,Md,lambda2,youtN,L] = nsw_cluster_smallworld(N,degModel,mdeg,p_lrwd,alph,bta)
% Cluster-small world model to generation rand topo power grids
% start from cluster lattice, instead of physical nodal locations.
% Inputs:
%   N - network size;
%   degModel - degree distribution model;
%   mdeg - average nodal degree;
%   p_lrwd - probability of rewiring links;
%   alph, bta - transition probability in the Markov chain model
% Outputs:
%   A - link admittance matrix;
%   Ma - connectivity matrix;
%   indx - link indexs;
%   Md - distance matrix;
%   lambda2 - algebraic connecity, i.e., lambda2(L)
%   youtN - actual network size of resulting topology;
%   L - the Laplacian matrix
%
% wzf, Dec 2008

%   SynGrid
%   Copyright (c) 2008, 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

conn = 0; count =0;
while(~conn) %-> this cycle for generation of connected toplogy

    % distance matrix Md computed by Md(i,j) = abs(i-j), the bus number distance
    Md=abs(((1:N)'*ones(1,N)-ones(N,1)*(1:N)));
    ds = nsw_get_nonzero(Md);
    switch N
        case 30
            d0 = 10;
        case 57
            d0 = 10;
        case 118
            d0 = 15;
        case 300
            d0 = 15; % 20, orignal setting, change it to 10 for bigger clustering coefficient
        otherwise
            d0 = 10;
    end


    % first step link selection -- among d0-neighbors
    Mda =or((Md>0 & Md<=d0),(Md>N/2 & Md>=(N-d0)));
    [Ma ]= nsw_clusterSW_sel_link2(Mda,degModel,mdeg); % choose links from local ngbrs
    degs = sum(or(Ma,Ma'),2);
    pos = find(degs==0);
%     if(length(pos)>N*.1)
%         continue;
%     end
    % remove single isolated nodes
    [Ma, Md, Mda, Nn]= rmv_sgls_clusterSM(Ma,Md,Mda,N);

    rwd_yes = nsw_markov(alph,bta,Nn);
    rwdnodes_list = find(rwd_yes ==1);
    if(~isempty(rwdnodes_list))
        % decide rewiring clusters
        [clsts,clsts_size,n_clsts] = nsw_clusterSW_clstrs(rwd_yes,d0,Nn);
        rwd_clsts      = clsts;

        deg_all = sum(degs(rwdnodes_list));
        if(deg_all>0)
            p_sel = p_lrwd*mdeg*N*.5/deg_all;
            [Ma]= rewind(Ma,rwdnodes_list,rwd_clsts,p_sel);
        end
    end
    [conn,lambda2,L] = nsw_clusterSW_conn2(Ma);
    if(conn == 1)
       [A,indx,Ma] = Ma2net_clusterSM(or(Ma,Ma'),Md);
       youtN = Nn;
    end
end

%--------------------------------------------------------------------------
%--------------------------------------------------------------------------
function [Ma, Md, Mda,N]= rmv_sgls_clusterSM(Ma,Md,Mda,n)
% remove the single isolated nodes from system

degs = sum(or(Ma,Ma'),2);
pos0 = find(degs==0); % nodes to remove
for ii=1:length(pos0)
    ki=pos0(ii);
    ks_ngr = find(Mda(ki,:)>0);
    tmp =randi(length(ks_ngr));
    new_ngr = ks_ngr(tmp);
    Ma(ki,new_ngr)=1;
    Ma(new_ngr, ki)=1;
end
Ma = triu(Ma);
%Md, Mda keep unchanged.
N =n;
% seq = 1:n; seq(pos0)=0;
% pos = find(seq>0);   % nodes to keep
% % shrink the vectors and matrix
% tmp = Ma(:,pos); Ma = tmp(pos,:);
% tmp = Md(:,pos); Md = tmp(pos,:);
% tmp = Mda(:,pos); Mda = tmp(pos,:);
% %x = x(pos); y = y(pos);
% N = length(pos);

%--------------------------------------------------------------------------
%--------------------------------------------------------------------------
function [Ma]= rewind(Ma,rwdnodes_list,rwd_clsts,p_sel)
% rewind local links to across-network links

Ma = or(Ma,Ma');
n = length(Ma(:,1));
for k = 1:length(rwdnodes_list)
    nodek = rwdnodes_list(k);
    ngsk  = find(Ma(nodek,:)>0);
    if(isempty(ngsk))
        continue;
    end
    degk = length(ngsk);
    pos  = find(rand(degk,1) < p_sel);
    if(~isempty(pos))
        old_ngsk = ngsk(pos);
        n_rwd = length(old_ngsk);
        new_ngsk = sel_newngs(rwd_clsts,nodek,n_rwd,n);
        
        if(length(new_ngsk)<n_rwd) % in case there are not enough rwd ngbrs
            n_rwd = length(new_ngsk);
            old_ngsk = old_ngsk(1:n_rwd);
        end
        
        
        Ma = update_Ma(Ma,nodek,old_ngsk,new_ngsk);
    end
end


%--------------------------------------------------------------------------
function Ma_new = update_Ma(Ma,k,old_ngs,new_ngs)
% update Ma, replace old neighbors with new neighbors

Ma_new = Ma;

% below section is added to avoid disconnectivity case
old_ngK = sum(Ma(old_ngs,:),2); % node degree of old neighbors
pos = find(old_ngK <= 1);       % if old ngbr only has this one link, not rewind it.
if(~isempty(pos))
    old_ngs(pos)=0;
    new_pos = find(old_ngs>0);
    old_ngs = old_ngs(new_pos);   % shrink the rewiring list
    new_ngs = new_ngs(new_pos);   % shrink the rewiring list
end
Ma_new(k,old_ngs)= 0;
Ma_new(k,new_ngs)=1;
Ma_new(:,k)=Ma_new(k,:);

%--------------------------------------------------------------------------
function new_ngs = sel_newngs(rwd_clsts,nodek,n_rwd,n)
% slect new neighbors for node-k from outside clsts

sizec = size(rwd_clsts);
nodes_avl =[];
for ci = 1:sizec(1)
    nodes_ci = rwd_clsts{ci,1};
    if(isempty(find(nodes_ci == nodek)))
        nodes_avl = [nodes_avl nodes_ci];
    end
end
if(isempty(nodes_avl))
    nodes_aval = 1:n;
end
new_ngs = sel_nodes(nodes_avl,n_rwd);

%--------------------------------------------------------------------------
%--------------------------------------------------------------------------
function nodes_sel = sel_nodes(nodes_avl,k)
% select k nodes from nodes_aval
m = length(nodes_avl);
if(k<m)
    [tmp,ord] = sort(rand(1,m));
    nodes_sel = nodes_avl(ord(1:k));
else
    nodes_sel = nodes_avl;
end

%--------------------------------------------------------------------------
function yout = new2old_nodes(new_ord,nodes_new,clsts_new)
% change new nodes number to old nodes number according to new_ord.
%
if(nargin == 2)
    m = length(nodes_new); nodes_old = zeros(1,m);
    for k = 1:m
        nodes_old(k) = find(new_ord == nodes_new(k));
    end
    yout = nodes_old;
elseif(nargin == 3)
    sizenew= size(clsts_new);
    clsts_old = cell(sizenew);
    for ii = 1: sizenew(1)
        nodes_new = clsts_new{ii,1};
        nodes_old = new2old_nodes(new_ord,nodes_new);
        clsts_old{ii,1}= nodes_old;
    end
    yout = clsts_old;
end

%--------------------------------------------------------------------------
function [A,indx,Ma] = Ma2net_clusterSM(Ma_full,Md)
% Form the link admission matrix from the full connectivty matrix
Ma = triu(Ma_full,1);
N = length(Ma(:,1));
[Lx,Ly] = find(Ma==1);
num_lines = length(Lx);
indx =[Lx Ly];
% 4. form branch incidence matrix A
A = sparse(zeros(num_lines,N));
for ni = 1: num_lines
    A(ni, indx(ni,1)) = 1;
    A(ni, indx(ni,2)) = -1;
end
