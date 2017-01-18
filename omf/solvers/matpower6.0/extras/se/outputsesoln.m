function outputsesoln(idx, sigma, z, z_est, error_sqrsum)
%OUTPUTSESOLN  Output state estimation solution.
%   created by Rui Bo on 2008/01/14

%   MATPOWER
%   Copyright (c) 2009-2016, Power Systems Engineering Research Center (PSERC)
%   by Rui Bo
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

fd = 1; % output to screen

fprintf(fd, '\n================================================================================');
fprintf(fd, '\n|     Comparison of measurements and their estimations                         |');
fprintf(fd, '\n|     NOTE: In the order of PF, PT, PG, Va, QF, QT, QG, Vm (if applicable)     |');
fprintf(fd, '\n================================================================================');
fprintf(fd, '\n    Type        Index      Measurement   Estimation');
fprintf(fd, '\n                 (#)         (pu)          (pu)    ');
fprintf(fd, '\n -----------  -----------  -----------   ----------');
cnt = 0;
len = length(idx.idx_zPF);
for i = 1: len
    fprintf(fd, '\n      PF        %3d      %10.4f     %10.4f', idx.idx_zPF(i), z(i+cnt), z_est(i+cnt));
end
cnt = cnt + len;
len = length(idx.idx_zPT);
for i = 1: len
    fprintf(fd, '\n      PT        %3d      %10.4f     %10.4f', idx.idx_zPT(i), z(i+cnt), z_est(i+cnt));
end
cnt = cnt + len;
len = length(idx.idx_zPG);
for i = 1: len
    fprintf(fd, '\n      PG        %3d      %10.4f     %10.4f', idx.idx_zPG(i), z(i+cnt), z_est(i+cnt));
end
cnt = cnt + len;
len = length(idx.idx_zVa);
for i = 1: len
    fprintf(fd, '\n      Va        %3d      %10.4f     %10.4f', idx.idx_zVa(i), z(i+cnt), z_est(i+cnt));
end
cnt = cnt + len;
len = length(idx.idx_zQF);
for i = 1: len
    fprintf(fd, '\n      QF        %3d      %10.4f     %10.4f', idx.idx_zQF(i), z(i+cnt), z_est(i+cnt));
end
cnt = cnt + len;
len = length(idx.idx_zQT);
for i = 1: len
    fprintf(fd, '\n      QT        %3d      %10.4f     %10.4f', idx.idx_zQT(i), z(i+cnt), z_est(i+cnt));
end
cnt = cnt + len;
len = length(idx.idx_zQG);
for i = 1: len
    fprintf(fd, '\n      QG        %3d      %10.4f     %10.4f', idx.idx_zQG(i), z(i+cnt), z_est(i+cnt));
end
cnt = cnt + len;
len = length(idx.idx_zVm);
for i = 1: len
    fprintf(fd, '\n      Vm        %3d      %10.4f     %10.4f', idx.idx_zVm(i), z(i+cnt), z_est(i+cnt));
end

fprintf(fd, '\n\n[Weighted sum of squared errors]:\t%f\n', error_sqrsum);
