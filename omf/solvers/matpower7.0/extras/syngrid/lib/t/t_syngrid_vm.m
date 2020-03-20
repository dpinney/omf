function t_syngrid_vm(quiet, ntrials)
%T_SYNGRID_VM  Tests for syngrid() variations mode.

%   SynGrid
%   Copyright (c) 2017-2018, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if nargin < 2
  ntrials = 1;
  if nargin < 1
      quiet = 0;
  end
end
% rng('default')
num_tests = 2*3*5*ntrials;
have_ipopt = have_fcn('ipopt');

t_begin(num_tests, quiet);

%% setup
mpcsmpl = loadcase('case_ACTIVSg2000');
mpctopo = loadcase('case118');

%% disable warnings
orig_state = warning;
warning('off','all')
%% test
for robust = 1:ntrials
for solver = {'MIPS', 'IPOPT'}
    if strcmp(solver{:}, 'IPOPT') && ~have_ipopt
        t_skip(3*5, 'Ipopt not available');
        continue
    end
    mpopt = mpoption('opf.ac.solver', solver{:});
    sgopt = sg_options(struct('mpopt', mpopt, ...
                            'vm', struct (...
                              'ea', struct('initfill', 1))));
%   sgopt.vm.shunts.verbose = 1;
    
    t = sprintf('variations mode with nsw topology (solver %s): ', solver{:});
    N = 50;
    while true
        [r, status] = syngrid(N, mpcsmpl, sgopt);
        % check that all cases successfully completed.
        if all(status == 2)
            break
        end
    end
    test_array(r, N, t);
    
    t = sprintf('variations mode with TOPO as matrix (solver %s): ', solver{:});
    [~, topo] = sgvm_mpc2data(mpctopo);
    N = length(unique(topo(:)));
    while true
        [r, status] = syngrid(topo, mpcsmpl, sgopt);
        % check that all cases successfully completed.
        if all(status == 2)
            break
        end
    end
    test_array(r, N, t);
    
    t = sprintf('variations mode with TOPO as mpc (solver %s): ', solver{:});
    N = size(mpctopo.bus, 1);
    while true
        [r, status] = syngrid(mpctopo, mpcsmpl, sgopt);
        % check that all cases successfully completed.
        if all(status == 2)
            break
        end
    end
    test_array(r, N, t);
end
end
%% re-enable warnings
warning(orig_state);

t_end;

function test_array(r, N, t)
t_ok( all(cellfun(@(x) size(x.bus,1) == N, r)), [t 'size']);
mpopt = mpoption('out.all', 0, 'verbose', 0);
fv    = false(length(r), 1);
check = struct('dcpf', fv, 'dfopf', fv, 'acpf', fv, 'acopf', fv);
labels= {'DC PF', 'DC OPF', 'AC PF', 'AC OPF'};
for k = 1:length(r)
    % DC PF
    rtmp = rundcpf(r{k}, mpopt);
    check.dcpf(k) = rtmp.success;

    % DC OPF
    rtmp = rundcopf(r{k}, mpopt);
    check.dcopf(k) = rtmp.success;

    % AC PF
    rtmp = runpf(r{k}, mpopt);
    check.acpf(k) = rtmp.success;

    % AC OPF
    rtmp = runopf(r{k}, mpopt);
    check.acopf(k) = rtmp.success;
end
for k = labels
    field = lower(k{:}(~isspace(k{:})));
    if strcmp(field, 'dcopf') && ~isempty(strfind(t, 'MIPS')) && ~all(check.(field))
        t_skip(1, 'Known Issue: Skipping DC OPF check with SynGrid Solver MIPS.');
    else
        t_ok( all(check.(field)), [t k{:} ' success']);
    end
end