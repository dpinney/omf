% Example_9bus
% test reduction code on 9-bus system (case9)
%
% Created by Yujia Zhu, yzhu54@asu.edu, Oct. 2014

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% load 9-bus case in MATPOWER format
% If you have installed MATPOWER, you can use function "loadcase" instead
% to read the case data
mpc = loadcase('case9'); % input full model in MATPOWER case format
%% give external bus indices
ExBus=[1,5,8]'; % input list of external buses (buses to be eliminated)
%% run reduction subroutine (MPReduction)
%Input notes:
% mpc: struct, the original full model in MATPOWER case format
% ExBus: 1*n array, list of external buses
[mpcreduced,Link,BCIRCr]=MPReduction(mpc,ExBus,0); % call reduction subroutine
% Output notes:
% 1. The output mpcreduced is the reduced 6 bus model
% 2. All branch B shunts are converted to B shunts on buses
% 3. There are 4 equivalent branches generated in the reduction process
%    branch between bus: 2-7, 2-9, 4-6, 7-9, all equivalent branches have
%    circuit number 99.
% 4. Equivalent lines have no line ratings. 
% 5. Link gives generator bus mapping showing how generators are moved.
%    E.g: Generator on bus 1 is moved to bus 4, all other generators are
%    not moved since they were on retained buses
% 6. The reduction process will generate equivalent lines with large
%   impedance. The software eliminate equivalent lines whose impedance is
%   larger than the threshold value. The threshold value in the software is
%   10 times of maximum impedance (reactance) value in the original full
%   model.