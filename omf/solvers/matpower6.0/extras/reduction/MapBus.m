function [mpc]=MapBus(mpc,oldbusnum,newbusnum)
% Subroutine MapBus convert bus indices from oldbusnum to newbusnum. The
% conversion will be done to fields including buses, branches and
% generators.
%
%   [mpc]=MapBus(mpc,oldbusnum,newbusnum)
%
% INPUT DATA:
%   mpc - struct, input model in MATPOWER format
%   oldbusnum - 1*n array, the old bus indices which will be converted "from"
%   newbusnum - 1*n array, the new bus indices which will be converted "to"
%
% OUTPUT DATA:
%   mpc - sctruct, output model in MATPOWER format with converted bus
%         indices.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

% convert bus number
    mpc.bus(:,1)=interp1(oldbusnum,newbusnum,mpc.bus(:,1));
    % convert branch terminal bus number
    mpc.branch(:,1)=interp1(oldbusnum,newbusnum,mpc.branch(:,1));
    mpc.branch(:,2)=interp1(oldbusnum,newbusnum,mpc.branch(:,2));
    % convert generator bus number
    mpc.gen(:,1)=interp1(oldbusnum,newbusnum,mpc.gen(:,1));
%     if isfield(mpc,'dcline')
%     % convert hvdc line bus number
%     mpc.dcline(:,1)=interp1(oldbusnum,newbusnum,mpc.dcline(:,1));
%     mpc.dcline(:,2)=interp1(oldbusnum,newbusnum,mpc.dcline(:,2));
%     end
end