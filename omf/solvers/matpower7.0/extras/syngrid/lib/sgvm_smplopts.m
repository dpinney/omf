function opt = sgvm_smplopts()
%SGVM_SMPLOPTS default options for SGVM_DATA2MPC()
%   OPT = SGVM_SMPLOPTS()
%
%   branch ('direct') - branch sampling method
%       'none'   : use samples as is (not recommended)
%       'direct' : sample instances from available data
%       'kde'    : fit data with kde and then sample
%   node ('kde') - sampling method for load (generation is always sampled
%                  either as 'direct' or 'none')
%       'none'   : use samples as is (not recommended)
%       'direct' : sample instances from available data
%       'kde'    : fit data with kde and then sample
%   lincost (100) - generation cost used if non is given
%   usegenbus (1) - use GENBUS data if given to group generators
%       0 : ignore GENBUS data even if provided
%       1 : use GENBUS data if provided
%   ngbuses (-1) - number of buses with generators
%       ngbuses > 0 : case will have ngbuses generator buses
%       ngbuses < 0 : number of generator buses is scaled based on input data
%   usegen2load (1) - handling of targeted generation to load ration
%       0 : desired ratio is determined as: gen2load = 1.3 + 0.3*rand();
%       1 : desired ratio is calculated from input data.
%   baseMVA_default (100) - default MVA base if non given
%   rate_a_default (400) - default MVA line rating if non given

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

opt = struct( ...
    'branch', 'direct',...      %% branch sampling method
    'node', 'kde', ...          %% node sampling method
    'lincost', 100, ...         %% generation cost if non given
    'usegenbus', 1,...          %% use GENBUS data if given
    'ngbuses', -1,...           %% number of buses with generators (-1 -> scale ratio from input data)
    'usegen2load', 1,...        %% target gen to load ratio (1 -> target from sampled data)
    'baseMVA_default', 100, ... %% default MVA base if non given
    'rate_a_default', 400 ...   %% default MVA line rating if non given
);
