function test_se
%TEST_SE  Test state estimation.
%   created by Rui Bo on 2007/11/12

%   MATPOWER
%   Copyright (c) 2009-2016, Power Systems Engineering Research Center (PSERC)
%   by Rui Bo
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%%------------------------------------------------------
% using data in Problem 6.7 in book 'Computational
% Methods for Electric Power Systems' by Mariesa Crow
%%------------------------------------------------------
%% which measurements are available
idx.idx_zPF = [1;2];
idx.idx_zPT = [3];
idx.idx_zPG = [1;2;3];
idx.idx_zVa = [];
idx.idx_zQF = [];
idx.idx_zQT = [];
idx.idx_zQG = [];
idx.idx_zVm = [2;3];

%% specify measurements
measure.PF = [0.12;0.10];
measure.PT = [-0.04];
measure.PG = [0.58;0.30;0.14];
measure.Va = [];
measure.QF = [];
measure.QT = [];
measure.QG = [];
measure.Vm = [1.04;0.98];

%% specify measurement variances
sigma.sigma_PF = 0.02;
sigma.sigma_PT = 0.02;
sigma.sigma_PG = 0.015;
sigma.sigma_Va = [];
sigma.sigma_QF = [];
sigma.sigma_QT = [];
sigma.sigma_QG = [];
sigma.sigma_Vm = 0.01;

%% check input data integrity
nbus = 3;
[success, measure, idx, sigma] = checkDataIntegrity(measure, idx, sigma, nbus);
if ~success
    error('State Estimation input data are not complete or sufficient!');
end

%% run state estimation
casename = 'case3bus_P6_6.m';
type_initialguess = 2; % flat start
[baseMVA, bus, gen, branch, success, et, z, z_est, error_sqrsum] = run_se(casename, measure, idx, sigma, type_initialguess);
