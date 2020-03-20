function [Ma] = nsw_clusterSW_sel_link2(Mda,degModel,mdeg)

%   SynGrid
%   Copyright (c) 2008, 2017, Electric Power and Energy Systems (EPES) Research Lab
%   by Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

% output "Ma"  is upper triangle matrix.
N = length(Mda(:,1));
Ma  = zeros(N); % --> adjacency matrix according to Nb geometric distribution of branch numbers
if(degModel ==0)
    Nb = (geornd(1/(mdeg-1),[1 N])+1);%--> expected number of links per node, geometric distribution,
elseif(degModel == 1)
    Nb = shifted_geornd(mdeg,N);
elseif(degModel ==2)
%     Nb = (poissrnd(mdeg-1,[1 N])+1);%--> expected number of links per node, Poisson distribution
    Nb = (sg_poissrnd(mdeg-1,1,N)+1);%--> expected number of links per node, Poisson distribution
elseif(degModel ==3)
else
    disp('wrong setting of p_brh, must be 1,2 or 3')
    return;
end

if(degModel==3)
    Ma = triu(Mda,1); % level-1 upper triangle sub-matrix,contains all connections in Mda
else
    for ni = 1:N-1
        Ny = Nb(ni); % --> number of needed branches for node-ni
        if(ni>1) Ny = Ny - sum(Ma(1:ni-1,ni )); end %--> mimus previous branches with nodes (1,...,ni-1)
        if(Ny<=0)
            Ma(ni,ni+1:N)=zeros(1,N-ni);
            continue;
        end

        pos = ni+ find(Mda(ni,ni+1:N)>0); % available branches with nodes (ni+1,...,N)
        Na = length(pos);
        if(Na == 0 || Na <= Ny)
            %disp(['Na Ny',num2str(Na), '   ', num2str(Ny)]);
            Ma(ni,ni+1:N) = Mda(ni,ni+1:N);
            continue;
        end
        if(Na > Ny)
            %pos_Ny = randsrc(1,Ny,[pos, 1/Na*ones(1,Na)]);
            pos_Ny = randi([1 Na],1,Ny);
            Ma(ni,pos(pos_Ny)) = 1;
        end
    end % --> for ni = 1:N-1
end % --> if(degModel==3)


%--------------------------------------------------------------------------
function yout = shifted_geornd(mdeg, N)
% shifted Geometric distribution
% p1 = 0.1, for degree = 1 nodes;  <-- group1
% p2 = 1-p1 = 0.9, for degree = 2 or larger, nodes <-- group2
% please note: p1*mdeg1 + p2*mdeg2 = mdeg
% so mdeg2 = (mdeg-p1*mdeg1)/p2.

% calculate the shift factors
p1 = 0.1; mdeg1 = 1.0;
mdeg2 = (mdeg-p1*mdeg1)/(1-p1); % the average degree for group2

ks = ones(1,N)*mdeg1;
N1 = round(p1*N); N2 = N-N1;  % nodes count
% please note: for matlab Geometric distribution
% prob(x=k) = (1-p)^k*p; k = 0,1,2,....
% E(X) = 1/p -1;
% here, we use this to generate X of {0,1,2,...} then shift it to
% Y = X+2, so that Y of {2,3,4,...}
% E(Y) = 1/p -1 +2 = 1/p+1; on the other side, E(y) = mdeg2;
% therefore p has to be set as: 1/p = mdeg2-1.
ks(N1+1:N) = geornd( 1/(mdeg2 - 1), [1 N2] )+2; % previously set mdeg2-2, it is wrong.
yout = ks(randperm(N));
