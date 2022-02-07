function [maxclique,ischordal] = maxCardSearch(Aadj)
%MAXCARDSEARCH Determine graph chordality and maximal cliques.
%   [MAXCLIQUE,ISCHORDAL] = MAXCARDSEARCH(AADJ)
%
%   Determine the maximal cliques for a chordal graph described by the
%   adjacency matrix Aadj. Also test the graph for chordality. The
%   algorithms for determining the maximal cliques and testing for
%   chordality are described in [1].
%
%   Inputs:
%       AADJ : The adjacency matrix of a graph. If the graph is chordal,
%           the maximal cliques for this graph are calculated.
%
%   Outputs:
%       MAXCLIQUE : If the graph described by Aadj is chordal, maxclique
%           returns a matrix describing the maximal cliques of the graph.
%           Each column of maxclique represents a clique with nonzero
%           entries indicating the nodes included in the maximal clique. If
%           Aadj is not chordal, maxclique is set to NaN.
%       ISCHORDAL : Returns 1 if the graph described by Aadj is chordal,
%           otherwise returns 0.
%
% [1] Tarjan, R. E., and M. Yannakakis. "Simple Linear-Time Algorithms to 
% Test Chordality of Graphs, Test Acyclicity of Hypergraphs, and 
% Selectively Reduce Acyclic Hypergraphs." SIAM Journal on computing 13 
% (1984): 566.

%   MATPOWER
%   Copyright (c) 2013-2019, Power Systems Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%
%   This file is part of MATPOWER/mx-sdp_pf.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-sdp_pf/ for more info.

%% Setup

nbus = size(Aadj,1);
nline = nnz(Aadj)/2;

%% Create a perfect elimination ordering

% Store in s{i} all unnumbered vertices adjacent to exactly i numbered
% vertices.
s{nline} = [];
s{1} = 1:nbus; % This corresponds to s{0} in the paper's notation

% Maintain the largest index j such that s{j} is nonempty
jidx = 1;

% Candidate perfect elimination ordering, with vertex numbering in vnum. 
% Index of vnum corresponds to the original vertex number, and the value of
% vnum indicates the new vertex number.
alpha = zeros(nbus,1);

% v2s stores which set contains a given vertex?
v2s = ones(nbus,1);

i = nbus;

while i >= 1
    
    % To carry out a step of the search, we remove a vertex v from s(jidx)
    % and number it.
    v = s{jidx}(1);
    if length(s{jidx}(:)) > 1
        s{jidx} = s{jidx}(2:end);
    else
        s{jidx} = [];
    end
    alpha(v) = i;
    v2s(v) = 0; % This vertex is no longer in a set
    
    % For each unnumbered vertex w adjacent to v, we move w from the set
    % containing it to the next set
    vadj = find(Aadj(:,v));
    for k=1:length(vadj)
        % If this node isn't already numbered, remove it from the original set
        if v2s(vadj(k)) ~= 0
            s{v2s(vadj(k))} = s{v2s(vadj(k))}(s{v2s(vadj(k))}(:) ~= vadj(k));
        
            % Add it to the new set
            s{v2s(vadj(k))+1} = [s{v2s(vadj(k))+1}(:); vadj(k)];

            % Update v2s
            v2s(vadj(k)) = v2s(vadj(k)) + 1;
        end
    end
    
    % Add one to jidx and then decrease jidx until reaching a non-empty s(jidx)
    jidx = jidx + 1; 
    if jidx > length(s)
        jidx = jidx - 1;
    end
    while jidx >= 1 && isempty(s{jidx})
        jidx = jidx - 1;
    end
    
    i = i-1;
    
end


%% Check for chordality

f = zeros(nbus,1);
index = zeros(nbus,1);
ischordal = 1;
for i=1:nbus
    w = find(alpha == i);
    f(w) = w;
    index(w) = i;
    
    valid_v = find(Aadj(:,w));
    valid_v = valid_v(alpha(valid_v) < i);
    for vidx = 1:length(valid_v)
        v = valid_v(vidx);
        index(v) = i;
        if f(v) == v
            f(v) = w;
        end
    end
    
    for vidx = 1:length(valid_v)
        v = valid_v(vidx);
        if index(f(v)) < i
            ischordal = 0;
            break;
        end
    end
    
    if ~ischordal
        break;
    end
end


%% Determine maximal cliques

% According to https://en.wikipedia.org/wiki/Chordal_graph
% "To list all maximal cliques of a chordal graph, simply find a perfect
% elimination ordering, form a clique for each vertex v together with the 
% neighbors of v that are later than v in the perfect elimination ordering,
% and test whether each of the resulting cliques is maximal."

% alpha is a candidate perfect elimination ordering. First form all
% cliques. Then determine which cliques are maximal. Put maximal cliques in
% the columns of the variable maxclique.

if ischordal
    % Form a matrix representation of the cliques
    clique = speye(nbus,nbus);
    for i=1:nbus
        % neighbors of node i that are later in the ordering
        neighbors = find(Aadj(i,:)); 
        neighbors = neighbors(alpha(neighbors) > alpha(i));

        clique(i,neighbors) = 1;
    end

    % Test whether each clique is maximal. A clique is not maximal if a node
    % neighboring any of the nodes in the clique, but not in the clique, is 
    % connected to all nodes in the clique.
    i=0;
    nclique = size(clique,1);
    while i < nclique
        i = i+1;

        neighbors = [];
        cliquei = find(clique(i,:));
        cliquei_bool = clique(i,:).';
        nnzi = sum(cliquei_bool);

        for k = 1:length(cliquei) % Check all nodes adjacent to nodes in the clique, but not included in the clique
            neighbors = [neighbors find(Aadj(cliquei(k),:))];
        end
        neighbors = unique(setdiff(neighbors,cliquei));

        not_maximal = 0;
        for m=1:length(neighbors)
            % If this neighbor is connected to all other nodes in the clique,
            % this is not a maximal clique
            if Aadj(neighbors(m),:) * cliquei_bool >= nnzi
                not_maximal = 1;
                break;
            end
        end

        if not_maximal
            clique = clique([1:i-1 i+1:nclique],:); % Delete this clique
            i = i-1; % After deletion, the next clique is really numbered i
            nclique = nclique - 1;
        end
    end
    maxclique = clique.'; % put maximal cliques in the columns
else
    maxclique = nan; % maximal clique algorithm only works for chordal graphs
end
