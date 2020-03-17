function t_syngrid(quiet)
%T_SYNGRID  Tests for syngrid().

%   SynGrid
%   Copyright (c) 2017-2018, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

%% define named indices into bus, gen, branch matrices
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, ...
    TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST, ...
    ANGMIN, ANGMAX, MU_ANGMIN, MU_ANGMAX] = idx_brch;

if nargin < 1
    quiet = 0;
end

if have_fcn('octave')   %% currently SLOW, only do the smallest
    NN = [30];
else
    NN = [30 150 300];
end

num_tests = 9*length(NN) + 6;
if quiet
    verbose = 0;
else
    verbose = 0;
end
mpopt = mpoption('out.all', 0, 'opf.dc.solver', 'MIPS', 'verbose', verbose);

%% turn off warnings
if have_fcn('octave')
    warn_id1 = 'Octave:nearly-singular-matrix';
    warn_id2 = 'Octave:singular-matrix';
    if have_fcn('octave', 'vnum') >= 4
        file_in_path_warn_id = 'Octave:data-file-in-path';
    else
        file_in_path_warn_id = 'Octave:load-file-in-path';
    end
    s3 = warning('query', file_in_path_warn_id);
    warning('off', file_in_path_warn_id);
else
    warn_id1 = 'MATLAB:nearlySingularMatrix';
    warn_id2 = 'MATLAB:singularMatrix';
end
s1 = warning('query', warn_id1);
s2 = warning('query', warn_id2);
warning('off', warn_id1);
warning('off', warn_id2);

t_begin(num_tests, quiet);

%% test syngrid(N)
for k = 1:length(NN)
    N = NN(k);
    t = sprintf('syngrid(%d) : ', N);
    mpc = syngrid(N);
    nb = size(mpc.bus, 1);      %% number of buses
    t_is(nb, N, 12, [t 'number of buses']);
    
    br2b = size(mpc.branch, 1)./size(mpc.bus, 1);
    t_ok(br2b >= 1.25 && br2b <= 2.5, [t 'branch to bus ratio']);
    
    avg_ndg = 2 * br2b;
    t_ok(avg_ndg >= 2.5 && avg_ndg <= 5, [t 'average node degree']);
        
    ig = find(mpc.gen(:, GEN_STATUS) > 0);  %% online gens
    t_ok(sum(mpc.bus(:, PD)) < sum(mpc.gen(ig, PMAX)), [t 'gen adequacy']);
    
    r = rundcpf(mpc, mpopt);
    t_ok(r.success, [t 'DC PF success']);
    
    t_ok(all(r.gen(ig, PG) >= r.gen(ig, PMIN)), [t 'gen feasibility (Pmin)']);
    t_ok(all(r.gen(:,  PG) <= r.gen(:,  PMAX)), [t 'gen feasibility (Pmax)']);
    t_ok(all(abs(r.branch(:,  PT)) <= r.branch(:,  RATE_A)), [t 'no line overloads']);
%     r = runpf(mpc, mpopt);
%     t_ok(r.success, [t 'AC PF success']);
    
    r = rundcopf(mpc, mpopt);
    t_ok(r.success, [t 'DC OPF success']);
end

%% test saving to a file
N = 25;
fn = sprintf('case%dsg_%d', N, fix(1e9*rand));
t = sprintf('syngrid(%d, [], ''%s'') : ', N, fn);
syngrid(N, [], fn);
t_ok(exist([fn '.m'], 'file') == 2, [t 'file created successfully']);
mpc = loadcase(fn);
delete([fn '.m']);
nb = size(mpc.bus, 1);      %% number of buses
t_is(nb, N, 12, [t 'number of buses']);

%% test DC power flow solution for case created by SynGrid
t = 't_sg_case100 : ';
mpc = loadcase('t_sg_case100');
expected = load('t_sg_case100_V');
r = rundcpf(mpc, mpopt);
t_ok(r.success, [t 'DC PF success']);
V = r.bus(:, VM) .* exp(1j*r.bus(:, VA)*pi/180);
t_is(V, expected.Vpf, 8, [t 'DC PF correct V']);

%% test DC OPF solution for case created by SynGrid
r = rundcopf(mpc, mpopt);
t_ok(r.success, [t 'DC OPF success']);
V = r.bus(:, VM) .* exp(1j*r.bus(:, VA)*pi/180);
t_is(V, expected.Vopf, 8, [t 'DC OPF correct V']);

t_end;

%% turn warnings back on
warning(s1.state, warn_id1);
warning(s2.state, warn_id2);
if have_fcn('octave')
    warning(s3.state, file_in_path_warn_id);
end
