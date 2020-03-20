function [mpc_out, status_out] = syngrid(varargin)
%SYNGRID  Create a synthetic power grid model in MATPOWER format.
%   MPC = SYNGRID(N)
%   MPC = SYNGRID(N, SGOPT)
%   MPC = SYNGRID(N, SGOPT, FNAME)
%   MPC = SYNGRID(N, DATA)
%   MPC = SYNGRID(N, DATA, SGOPT)
%   MPC = SYNGRID(N, DATA, SGOPT, FNAME)
%   MPC = SYNGRID(TOPO, DATA)
%   MPC = SYNGRID(TOPO, DATA, SGOPT)
%   MPC = SYNGRID(TOPO, DATA, SGOPT, FNAME)
%
%   Creates a synthetic power grid model with the desired number of buses,
%   optionally based on statistics from a specified reference system, and
%   returns a MATPOWER case struct for the resulting system.
%
%   Inputs
%       N - desired number of buses, or
%       TOPO - network topology, specified by a MATPOWER case name or case
%           struct, or by an nb x 2 matrix of bus numbers, with "from"
%           and "to" bus numbers in columns 1 and 2, corresponding to
%           the F_BUS and T_BUS columns of a MATPOWER branch matrix.
%           The desired number of buses corresponds to the number of
%           unique bus numbers found in TOPO (which need not be
%           consecutive starting at 1).
%       DATA - (optional) a data structure providing the data from which
%           to sample parameters. This can be a full MATPOWER case struct
%           or a struct of the form described in the SynGrid User's Manual.
%       SGOPT - (optional) SynGrid options struct or a subset thereof to be
%           used as the OVERRIDES argument to SG_OPTIONS.
%           See SG_OPTIONS for details.
%       FNAME - (optional) name of file to which synthetic case will be
%           saved case is not saved to a file by default
%
%   Output
%       MPC - MATPOWER case struct
%           currently includes:
%               bus real power demand, generator active power dispatch,
%               generator active power capacity, branch resistance,
%               branch reactance, branch MVA rating

%   SynGrid
%   Copyright (c) 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   Copyright (c) 2017-2018, Power Systems Engineering Research Center (PSERC)
%   by Zhifang Wang and Hamidreza Sadeghian, Virginia Commonwealth University
%   Eran Schweitzer, Arizona State University
%   and Ray Zimmerman, PSERC Cornell
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
[PW_LINEAR, POLYNOMIAL, MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;

%% default input arguments
args = varargin;
na = length(args);

if isstruct(args{1}) || ischar(args{1})     %% first arg is MPC
    mpc = loadcase(args{1});
    [~, topo] = sgvm_mpc2data(mpc);
    N    = length(unique(topo(:)));
elseif isscalar(args{1})                    %% first arg is N
    N = args{1};
    topo = [];
elseif size(args{1}, 2) == 2                %% first arg is TOPO
    topo = args{1};
    N    = length(unique(topo(:)));
else
    error('syngrid: first argument must be either scalar N, or nl x 2 array TOPO, or MPC struct');
end

if na == 1
    sgopt = sg_options();
    fname = '';
    data  = [];
else                     %% second argument is either SGOPT or DATA
    if ischar(args{2})
        data = sgvm_mpc2data(loadcase(args{2}));
    elseif isstruct(args{2})
        if isfield(args{2}, 'branch')   %% 2nd argument is DATA
            data = args{2};
            if isfield(data, 'bus')     %% input DATA is MPC
                data = sgvm_mpc2data(data);
            end
        else                            %% 2nd argument is SGOPT
            data = [];
            sgopt = sg_options(args{2});
        end
    elseif isempty(args{2})
        data  = [];
        sgopt = sg_options();
    else
        error('syngrid: argument 2 (SGOPT or DATA) MUST be a structure or empty')
    end
    if na > 2                       %% 3rd argument is FNAME or SGOPT
        if ischar(args{3})          %% 3rd argument is FNAME
            fname = args{3};
            if ~exist('sgopt','var')
                error('syngrid: when 3rd argument is FNAME, the second argument must be either empty or SGOPT.')
            end
        elseif isstruct(args{3})    %% 3rd argument is SGOPT
            sgopt = sg_options(args{3});
        elseif isempty(args{3})     %% 3rd argument is empty SGOPT
            sgopt = sg_options();
        else
            error('syngrid: 3rd argument is either FNAME or SGOPT structure.')
        end
        if na > 3                   %% 4th argument can only be FNAME
            fname = args{4};
            if ~ischar(fname)
                error('syngrid: FNAME must be a string.')
            end
        else    %% only 3 arguments
            if ~exist('fname', 'var')
                fname = '';
            end
        end
    else        %% only 2 arguments
        fname = '';
        if ~exist('sgopt', 'var')   %% if inputs were N (or TOPO) and DATA
            sgopt = sg_options();
        end
    end
end

variations_mode = ~isempty(data);

if N < 25
    error('syngrid: minimum allowed for desired number of buses N is 25');
end

if sgopt.verbose
    fprintf('SynGrid v%s : creating %d bus synthetic MATPOWER case.\n', sgver, N);
end

if isempty(topo)    %% create a nested small-world topology from scratch
    %% get reference system statistics
    [refsys_stat] = sg_refsys_stat(sgopt.bm.refsys);

    %% input data for sg_topology function
    N0 = 0;
    ks = 10;
    if N < 150
        ks = 0;
    elseif N < 300
        N0 = 30;
    end
    topo_pars = {2 2.*sgopt.bm.br2b_ratio};
    [N, Zpr, lambda2, L, A, link_ids] = sg_topology(N, N0, ks, 4, ...
        topo_pars, {}, refsys_stat.Zpr_pars);
end
if variations_mode
    if isempty(topo)
        topo = link_ids;
    end
    seedmpc = sgvm_data2mpc(data, topo, sgopt.vm.smpl);
    [mpc, status] = sgvm_mpc_perm(seedmpc, sgopt);
else
    [Btypes] = sg_bus_type(link_ids, sgopt.bm.bta_method);
    [PgMax] = sg_gen_capacity(link_ids, Btypes, refsys_stat.Tab_2D_Pgmax);
    [gencost, genfuel, gentype] = sg_gen_cost(PgMax, sgopt.bm.cost_model, ...
        refsys_stat.Tab_2D_gcost);
    [PL_setting] = sg_load(link_ids, Btypes, PgMax, sgopt.bm.loading, ...
        refsys_stat.Tab_2D_load);
    [Pg_setting] = sg_gen_dispatch(PgMax, PL_setting, refsys_stat);
    [Line_capacity, Zpr, X, R, ref,link_ids] = sg_flow_lim(link_ids, A, ...
        Zpr, PL_setting, Pg_setting, sgopt.bm.br_overload, refsys_stat);

    %% generate MATPOWER data matrices
    ng = length(PgMax);     %% number of generators
    nl = length(link_ids);  %% number of branches
    
    bus = zeros(N, VMIN);
    bus(:, VM) = 1;
    bus(:, BUS_I) = (1:N)';
    bus(:, BUS_TYPE) = PQ;
    bus(PgMax(:,1), BUS_TYPE) = PV;
    bus(ref, BUS_TYPE) = REF;
    bus(PL_setting(:,1), PD) = PL_setting(:,2);
    
    gen = zeros(ng, APF);
    gen(:, [GEN_BUS PG]) = Pg_setting;
    gen(:, GEN_STATUS) = Pg_setting(:,2)>0;
    gen(:, VG) = 1;
    gen(:, PMAX) = PgMax(:,2);
    
    branch = zeros(nl, ANGMAX);
    branch(:,[F_BUS T_BUS]) = link_ids;
    branch(:, [BR_R BR_X]) = [R,X];
    branch(:, RATE_A) = Line_capacity(:,3);
    branch(:, BR_STATUS) = 1;
    
    %% form MATPOWER case struct
    mpc.version = '2';
    mpc.baseMVA = 100;
    mpc.bus = bus;
    mpc.gen = gen;
    mpc.branch = branch;
    mpc.gencost = gencost;
    mpc.genfuel = genfuel;
    mpc.gentyp = gentype;
end

%% optionally save to a case file
if ~isempty(fname)
    comment = sprintf('Synthetic %d bus MATPOWER case created by SynGrid\n%%   Created by SynGrid v%s, %s', ...
        N, sgver, datestr(now, 0));
    savecase(fname, comment, mpc);
end

%% don't return struct if it wasn't requested (hopefully it was saved)
if nargout
    mpc_out = mpc;
    if nargout > 1
        status_out = status;
    end
end
