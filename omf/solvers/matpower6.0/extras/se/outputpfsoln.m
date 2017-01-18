function outputpfsoln(baseMVA, bus, gen, branch, converged, et, type_solver, iterNum)
%OUTPUTPFSOLN  Output power flow solution.

%   MATPOWER
%   Copyright (c) 1996-2016, Power Systems Engineering Research Center (PSERC)
%   by Rui Bo
%   and Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% define named indices into bus, gen, branch matrices
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, ...
    GEN_STATUS, PMAX, PMIN, MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN] = idx_gen;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, ...
    RATE_C, TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST] = idx_brch;

fd = 1; % output to screen

%% sizes of things
nb = size(bus, 1);      %% number of buses
nl = size(branch, 1);   %% number of branches
ng = size(gen, 1);      %% number of generators

%% parameters
ong  = find( gen(:, GEN_STATUS) > 0);
nzld = find(bus(:, PD) | bus(:, QD));

%% calculate losses
loss = branch(:, PF) + j*branch(:, QF) + branch(:, PT) + j*branch(:, QT);

%% ---output case and solver information
fprintf(fd, '\n\n');
if type_solver == 1 % newton's method
    fprintf(fd, 'Newton''s method is chosen to solve Power Flow.\n');
elseif  type_solver == 2 % decoupled method
    fprintf(fd, 'Decoupled method is chosen to solve Power Flow.\n');
else
    fprintf('Error: unknow ''type_solver''.\n');
    pause
end

if converged
    fprintf(fd, '\nConverged in %.2f seconds\n', et);
else
    fprintf(fd, '\nDid not converge (%.2f seconds)\n', et);
end
fprintf(fd, '\n[iteration number]: %d\n', iterNum);

%% ---output generation information
fprintf(fd, '\n================================================================================');
fprintf(fd, '\n|     Generator Data                                                           |');
fprintf(fd, '\n================================================================================');
fprintf(fd, '\n Gen   Bus   Status     Pg        Qg   ');
fprintf(fd, '\n  #     #              (MW)     (MVAr) ');
fprintf(fd, '\n----  -----  ------  --------  --------');
for k = 1:length(ong)
    i = ong(k);
    fprintf(fd, '\n%3d %6d     %2d ', i, gen(i, GEN_BUS), gen(i, GEN_STATUS));
    if gen(i, GEN_STATUS) > 0 & (gen(i, PG) | gen(i, QG))
        fprintf(fd, '%10.2f%10.2f', gen(i, PG), gen(i, QG));
    else
        fprintf(fd, '       -         -  ');
    end
end
fprintf(fd, '\n                     --------  --------');
fprintf(fd, '\n            Total: %9.2f%10.2f', sum(gen(ong, PG)), sum(gen(ong, QG)));
fprintf(fd, '\n');

%% ---output bus information
fprintf(fd, '\n================================================================================');
fprintf(fd, '\n|     Bus Data                                                                 |');
fprintf(fd, '\n================================================================================');
fprintf(fd, '\n Bus      Voltage          Generation             Load        ');
fprintf(fd, '\n  #   Mag(pu) Ang(deg)   P (MW)   Q (MVAr)   P (MW)   Q (MVAr)');
fprintf(fd, '\n----- ------- --------  --------  --------  --------  --------');
for i = 1:nb
    fprintf(fd, '\n%5d%7.3f%9.3f', bus(i, [BUS_I, VM, VA]));
    g  = find(gen(:, GEN_STATUS) > 0 & gen(:, GEN_BUS) == bus(i, BUS_I));
    if ~isempty(g)
        fprintf(fd, '%10.2f%10.2f', sum(gen(g, PG)), sum(gen(g, QG)));
    else
        fprintf(fd, '       -         -  ');
    end
    if bus(i, PD) | bus(i, QD)
        fprintf(fd, '%10.2f%10.2f ', bus(i, [PD, QD]));
    else
        fprintf(fd, '       -         -   ');
    end
end
fprintf(fd, '\n                        --------  --------  --------  --------');
fprintf(fd, '\n               Total: %9.2f %9.2f %9.2f %9.2f', ...
    sum(gen(ong, PG)), sum(gen(ong, QG)), ...
    sum(bus(nzld, PD)), ...
    sum(bus(nzld, QD)));
fprintf(fd, '\n');

%% ---output bus information
fprintf(fd, '\n================================================================================');
fprintf(fd, '\n|     Branch Data                                                              |');
fprintf(fd, '\n================================================================================');
fprintf(fd, '\nBrnch   From   To    From Bus Injection   To Bus Injection     Loss (I^2 * Z)  ');
fprintf(fd, '\n  #     Bus    Bus    P (MW)   Q (MVAr)   P (MW)   Q (MVAr)   P (MW)   Q (MVAr)');
fprintf(fd, '\n-----  -----  -----  --------  --------  --------  --------  --------  --------');
fprintf(fd, '\n%4d%7d%7d%10.2f%10.2f%10.2f%10.2f%10.3f%10.2f', ...
        [   [1:nl]', branch(:, [F_BUS, T_BUS]), ...
            branch(:, [PF, QF]), branch(:, [PT, QT]), ...
            real(loss), imag(loss) ...
        ]');
fprintf(fd, '\n                                                             --------  --------');
fprintf(fd, '\n                                                    Total:%10.3f%10.2f', ...
        sum(real(loss)), sum(imag(loss)));
fprintf(fd, '\n');
