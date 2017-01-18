function [MVAbase, bus, gen, branch, success, et] = runse(casedata, mpopt, fname, solvedcase)
%RUNSE  Runs a state estimator.
%   [BASEMVA, BUS, GEN, BRANCH, SUCCESS, ET] = ...
%           RUNSE(CASEDATA, MPOPT, FNAME, SOLVEDCASE)
%
%   Runs a state estimator (after a Newton power flow). Under construction with
%   parts based on code from James S. Thorp.

%   MATPOWER
%   Copyright (c) 1996-2016, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%   parts based on code by James S. Thorp, June 2004
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%%-----  initialize  -----
%% define named indices into bus, gen, branch matrices
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, ...
    TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST, ...
    ANGMIN, ANGMAX, MU_ANGMIN, MU_ANGMAX] = idx_brch;
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;

%% default arguments
if nargin < 4
    solvedcase = '';                %% don't save solved case
    if nargin < 3
        fname = '';                 %% don't print results to a file
        if nargin < 2
            mpopt = mpoption;       %% use default options
            if nargin < 1
                casedata = 'case9'; %% default data file is 'case9.m'
            end
        end
    end
end

%% options
dc = strcmp(upper(mpopt.model), 'DC');  %% use DC formulation?

%% read data & convert to internal bus numbering
[baseMVA, bus, gen, branch] = loadcase(casedata);
[i2e, bus, gen, branch] = ext2int(bus, gen, branch);

%% get bus index lists of each type of bus
[ref, pv, pq] = bustypes(bus, gen);

%% generator info
on = find(gen(:, GEN_STATUS) > 0);      %% which generators are on?
gbus = gen(on, GEN_BUS);                %% what buses are they at?

%%-----  run the power flow  -----
t0 = clock;
if dc                               %% DC formulation
    %% initial state
    Va0 = bus(:, VA) * (pi/180);
    
    %% build B matrices and phase shift injections
    [B, Bf, Pbusinj, Pfinj] = makeBdc(baseMVA, bus, branch);
    
    %% compute complex bus power injections (generation - load)
    %% adjusted for phase shifters and real shunts
    Pbus = real(makeSbus(baseMVA, bus, gen)) - Pbusinj - bus(:, GS) / baseMVA;
    
    %% "run" the power flow
    Va = dcpf(B, Pbus, Va0, ref, pv, pq);
    
    %% update data matrices with solution
    branch(:, [QF, QT]) = zeros(size(branch, 1), 2);
    branch(:, PF) = (Bf * Va + Pfinj) * baseMVA;
    branch(:, PT) = -branch(:, PF);
    bus(:, VM) = ones(size(bus, 1), 1);
    bus(:, VA) = Va * (180/pi);
    %% update Pg for swing generator (note: other gens at ref bus are accounted for in Pbus)
    %%      Pg = Pinj + Pload + Gs
    %%      newPg = oldPg + newPinj - oldPinj
    refgen = find(gbus == ref);             %% which is(are) the reference gen(s)?
    gen(on(refgen(1)), PG) = gen(on(refgen(1)), PG) + (B(ref, :) * Va - Pbus(ref)) * baseMVA;
    
    success = 1;
else                                %% AC formulation
    %% initial state
    % V0    = ones(size(bus, 1), 1);            %% flat start
    V0  = bus(:, VM) .* exp(sqrt(-1) * pi/180 * bus(:, VA));
    V0(gbus) = gen(on, VG) ./ abs(V0(gbus)).* V0(gbus);
    
    %% build admittance matrices
    [Ybus, Yf, Yt] = makeYbus(baseMVA, bus, branch);
    
    %% compute complex bus power injections (generation - load)
    Sbus = makeSbus(baseMVA, bus, gen);
    
    %% run the power flow
    alg = upper(mpopt.pf.alg);
    switch alg
        case 'NR'
            [V, success, iterations] = newtonpf(Ybus, Sbus, V0, ref, pv, pq, mpopt);
        case {'FDXB', 'FDBX'}
            [Bp, Bpp] = makeB(baseMVA, bus, branch, alg);
            [V, success, iterations] = fdpf(Ybus, Sbus, V0, Bp, Bpp, ref, pv, pq, mpopt);
        case 'GS'
            [V, success, iterations] = gausspf(Ybus, Sbus, V0, ref, pv, pq, mpopt);
        otherwise
            error('Only Newton''s method, fast-decoupled, and Gauss-Seidel power flow algorithms currently implemented.');
    end
    
    %% update data matrices with solution
    [bus, gen, branch] = pfsoln(baseMVA, bus, gen, branch, Ybus, Yf, Yt, V, ref, pv, pq, mpopt);
end
et = etime(clock, t0);

%%--------------------  begin state estimator code  --------------------
%% save some values from load flow solution
Pflf=branch(:,PF);
Qflf=branch(:,QF);
Ptlf=branch(:,PT);
Qtlf=branch(:,QT);
Sbuslf = V .* conj(Ybus * V);
Vlf=V;

%% run state estimator
[V, converged, i] = state_est(branch, Ybus, Yf, Yt, Sbuslf, Vlf, ref, pv, pq, mpopt);

%% update data matrices to match estimator solution ...
%% ... bus injections at PQ buses
Sbus = V .* conj(Ybus * V);
bus(pq, PD) = -real(Sbus(pq)) * baseMVA;
bus(pq, QD) = -imag(Sbus(pq)) * baseMVA;
%% ... gen outputs at PV buses
on = find(gen(:, GEN_STATUS) > 0);      %% which generators are on?
gbus = gen(on, GEN_BUS);                %% what buses are they at?
gen(on, PG) = real(Sbus(gbus)) * baseMVA + bus(gbus, PD);   %% inj P + local Pd
%% ... line flows, reference bus injections, etc.
[bus, gen, branch] = pfsoln(baseMVA, bus, gen, branch, Ybus, Yf, Yt, V, ref, pv, pq, mpopt);

%% plot differences from load flow solution
Pfe=branch(:,PF);
Qfe=branch(:,QF);
Pte=branch(:,PT);
Qte=branch(:,QT);
nbr = length(Pfe);
subplot(3,2,1), plot(180/pi*(angle(Vlf)-angle(V)),'.'), title('Voltage Angle (deg)');
subplot(3,2,2), plot(abs(Vlf)-abs(V),'.'), title('Voltage Magnitude (p.u.)');
subplot(3,2,3), plot((1:nbr),(Pfe-Pflf),'r.',(1:nbr),(Pte-Ptlf),'b.'), title('Real Flow (MW)');
subplot(3,2,4), plot((1:nbr),(Qfe-Qflf),'r.',(1:nbr),(Qte-Qtlf),'b.'), title('Reactive Flow (MVAr)');
subplot(3,2,5), plot(baseMVA*real(Sbuslf-Sbus), '.'), title('Real Injection (MW)');
subplot(3,2,6), plot(baseMVA*imag(Sbuslf-Sbus), '.'), title('Reactive Injection (MVAr)');
%%--------------------  end state estimator code  --------------------

%%-----  output results  -----
%% convert back to original bus numbering & print results
[bus, gen, branch] = int2ext(i2e, bus, gen, branch);
if fname
    [fd, msg] = fopen(fname, 'at');
    if fd == -1
        error(msg);
    else
        if mpopt.out.all == 0
            printpf(baseMVA, bus, gen, branch, [], success, et, fd, ...
                mpoption(mpopt, 'out.all', -1));
        else
            printpf(baseMVA, bus, gen, branch, [], success, et, fd, mpopt);
        end
        fclose(fd);
    end
end
printpf(baseMVA, bus, gen, branch, [], success, et, 1, mpopt);

%% save solved case
if solvedcase
    savecase(solvedcase, baseMVA, bus, gen, branch);
end

%% this is just to prevent it from printing baseMVA
%% when called with no output arguments
if nargout, MVAbase = baseMVA; end
