function [baseMVA, bus, gen, branch, success, et, z, z_est, error_sqrsum] = run_se(casename, measure, idx, sigma, type_initialguess, V0)
%RUN_SE  Run state estimation.
%   [INPUT PARAMETERS]
%   measure: measurements
%   idx: measurement indices
%   sigma: measurement variances
%   [OUTPUT PARAMETERS]
%   z: Measurement Vector. In the order of PF, PT, PG, Va, QF, QT, QG, Vm (if
%   applicable), so it has ordered differently from original measurements
%   z_est: Estimated Vector. In the order of PF, PT, PG, Va, QF, QT, QG, Vm
%   (if applicable)
%   error_sqrsum: Weighted sum of error squares
%   created by Rui Bo on 2007/11/12

%   MATPOWER
%   Copyright (c) 1996-2016 by Power System Engineering Research Center (PSERC)
%   by Rui Bo
%   and Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% read data & convert to internal bus numbering
[baseMVA, bus, gen, branch] = loadcase(casename);
[i2e, bus, gen, branch] = ext2int(bus, gen, branch);

%% get bus index lists of each type of bus
[ref, pv, pq] = bustypes(bus, gen);

%% build admittance matrices
[Ybus, Yf, Yt] = makeYbus(baseMVA, bus, branch);
Ybus = full(Ybus);
Yf = full(Yf);
Yt = full(Yt);

%% prepare initial guess
if nargin < 6
    V0 = getV0(bus, gen, type_initialguess);
else
    V0 = getV0(bus, gen, type_initialguess, V0);
end

%% run state estimation
t0 = clock;
[V, success, iterNum, z, z_est, error_sqrsum] = doSE(baseMVA, bus, gen, branch, Ybus, Yf, Yt, V0, ref, pv, pq, measure, idx, sigma);
%% update data matrices with solution, ie, V
% [bus, gen, branch] = updatepfsoln(baseMVA, bus, gen, branch, Ybus, V, ref, pv, pq);
[bus, gen, branch] = pfsoln(baseMVA, bus, gen, branch, Ybus, Yf, Yt, V, ref, pv, pq);
et = etime(clock, t0);

%%-----  output results  -----
%% convert back to original bus numbering & print results
[bus, gen, branch] = int2ext(i2e, bus, gen, branch);
%% output power flow solution
outputpfsoln(baseMVA, bus, gen, branch, success, et, 1, iterNum);
%% output state estimation solution
outputsesoln(idx, sigma, z, z_est, error_sqrsum);

