function [clsts,clsts_size,n_clsts] = nsw_clusterSW_clstrs(nodes_rwd,d0,n,nodes_rwd_list)
% PURPOSE:  analyze and show the correlation between node degree and node
%           rewires.
% USAGE:
% INPUTS:
%           link_ids - the link list;
%           nodes_rwd - vector (n by 1): rewires count for each node
%           n - total number of nodes
%           d0  -  distance criteria to decide a rewired link;
% OUTPUTS:  co_degrwd - correlation coefficient between node degrees and
%                       rewires count.
%
% by wzf, 2008

%   SynGrid
%   Copyright (c) 2008, 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if(isempty(nodes_rwd) && nargin ==4)
    pos = nodes_rwd_list;
else
    pos = find(nodes_rwd>0);
end
if(isempty(pos))
    return;
end
clsts={};clsts_size =[];
k=1;cls_k=[];last = 0;
while(~isempty(pos))
    if(last ==0 || pos(1)==last+1)
        last = pos(1); %append this node to current cluster
        cls_k = [cls_k last];
    else
        clsts{k,1}=cls_k;
        clsts_size = [clsts_size; length(cls_k)];
        last = pos(1);
        k=k+1; cls_k =[last]; % start a new cluster
    end
    pos = pos(2:length(pos));
end
clsts{k,1}=cls_k;clsts_size = [clsts_size; length(cls_k)];
%k=k-1;
% cls_1 = clsts{1};
% cls_k = clsts{k};
% if( k>1 & any(cls_1==1) & any(cls_k==n))
%     clsts{1}=[cls_k cls_1 ];
%     clsts_size(1)=clsts_size(1)+clsts_size(k);
%     clsts = clsts{1:k-1,:};
%     clsts_size = clsts_size(1:k-1);
%     k = k-1;
% end
n_clsts = k;

% plot the results
plot_result = 0; % whether to show the figure or not
if(plot_result)
    disp([num2str(n_clsts),' clusters are shown below:']);
    meansize_txt = ['mean of cluster size =',num2str(mean(clsts_size))];
    disp(meansize_txt);
    for k=1:n_clsts
        str1 = sprintf('%3.0f-cluster (%3.0f node(s)):',k , clsts_size(k));
        form2 = [];
        for m = 1:clsts_size(k)
            form2 = [form2,'%7.0f '];
        end
        str2 = sprintf(form2,clsts{k}');
        %str3 = ['      (total: ',num2str(clsts_size(k)),' node(s))'];
        disp([str1, str2]);
    end
    figure; hist(clsts_size,1:max(clsts_size)+1);
    xlabel('cluster size'); ylabel('n_c_l');
    title(meansize_txt);
end
