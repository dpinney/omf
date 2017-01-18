function [mpc,ExBus]=PreProcessData(mpc,ExBus)
% Subroutine PreProcess do following tasks to input model:
% 1. Eliminate all isolated buses
% 2. Eliminate all out-of-service branches
% 3. Eliminate all in-service but connected to isolated bus branches
% 4. Eliminate all HVDC line connected to isolated buses
% 5. Eliminate all generators on isolated buses
% 6. Update the list of external bus (ExBus) by eliminating the isolated
% buses in the list
% 
%   [mpc,ExBus]=PreProcessData(mpc,ExBus)
%
% INPUT DATA:
% mpc: struct, input original full model (MATPOWER case file)
% ExBus: 1*n array, original list of external buses
%
% OUTPUT DATA:
% mpc: struct, updated model
% ExBus: 1*n array, updated list of external buses

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

mpc.bus = sortrows(mpc.bus,1);
mpc.branch = sortrows(mpc.branch,[1,2]);
numbr=size(mpc.branch,1);
mpc.branch(mpc.branch(:,11)==0,:)=[];% eliminated all out-of-service lines
isobus=mpc.bus(mpc.bus(:,2)==4,1);
fprintf('\nEliminate %d isolated buses',length(isobus));
tf1=ismember(mpc.branch(:,1),isobus);
tf2=ismember(mpc.branch(:,2),isobus);
mpc.branch(tf1|tf2,:)=[]; % eliminate all branch connected to isolated buses
fprintf('\nEliminate %d branches',numbr-size(mpc.branch,1));

mpc.bus(mpc.bus(:,2)==4,:)=[]; % eliminate all isolated buses
tfgen=ismember(mpc.gen(:,1),isobus);
mpc.gen(tfgen,:)=[]; % eliminate all generators on isolated buses
fprintf('\nEliminate %d generators',length(tfgen(tfgen==1)));
if isfield (mpc,'gencost')
    mpc.gencost(tfgen,:)=[];
end
ind=ismember(ExBus,isobus);
ExBus(ind)=[];
if isfield(mpc,'dcline')
    tfdc1=ismember(mpc.dcline(:,1),isobus);
    tfdc2=ismember(mpc.dcline(:,2),isobus);
    mpc.dcline(tfdc1|tfdc2,:)=[]; % eliminate dcline connecting isolated terminal
    fprintf('\nEliminate %d dc lines',length(length(find(tfdc1|tfdc2))));

end
fprintf('\nPreprocessing complete');
end