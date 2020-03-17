function [r, status] = sgvm_mpc_perm(mpc, opt)
%SGVM_MPC_PERM main VARIATIONS MODE script
%   [R, STATUS] = SGVM_MPC_PERM(MPC, OPT)
%
%   Permutes the branch and node properties in MPC in an
%   attempt to generate a better powerflow solution.
%
%   Inputs
%       MPC - MATPOWER case to be permuted. Should have been "sanitized"
%           by some input process. For example, all buses should be
%             consecutive and (at present) no shunt elements
%             should exists.
%       OPT - SYNGRID options structure
%
%   Outputs
%     R      -  array of matpower casese
%     STATUS -  0,1,2. 2 means success, no line violations and no voltage
%            violations. 1 means success, no line violations but
%            voltage violations. 0 either means mpc did not solve OR
%            the mpc solves but only with softlims since there are line
%            violations.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

%% handle inputs
define_constants;
msg = 'sgvm_mpc_perm: error with input mpc:\n';
tests = false(2,1);
tests(1) = ~all(mpc.bus(:,BUS_I) == (1:size(mpc.bus,1)).');
if tests(1)
    msg = [msg, '\tbuses need to be consecutive starting at 1.', ...
    'Consider using sgvm_data2mpc(sgvm_mpc2data(mpc)).\n'];
end
tests(2) = any(mpc.bus(:, GS) | mpc.bus(:, BS));
if tests(2)
    msg = [msg,'\tInput mpc should not have any shunt elements ',...
    'GS or BS.\n'];
end
if any(tests)
    error(msg)
end
if ~isfield(opt, 'vm')
    error('sgvm_mpc_perm: options structure must have a field ''vm'' with the necessary subfields, see sg_options and the SynGrid Manual')
end

if ~strcmp(opt.mpopt.opf.ac.solver, 'IPOPT')
  errorstr = sprintf(['sgvm_mpc_perm: currently sgvm_mpc_perm should be used with IPOPT as the ac-opf solver.\n',...
         'Unfortunately results are too unstable with other interior-points solvers.\n',...
         'The IPOPT binaries via the PARDISO project for MATPOWER can be found at:\n',...
         '\thttps://pardiso-project.org/.']);
  warning(errorstr);
end

%% add softlimits
% the softlimit settings are (at least for now) not changeable by
% the user.
% Softlims are only enabled for line rating and voltage magnitude
max_gen_cost = max(margcost(mpc.gencost, mpc.gen(:, PMAX)));
default_cost = 1000;

% The following cost calculation effectively equates 1 MVA flow violation
% with 0.1 pu voltage violation.
% This is intentionally fairly generous w.r.t voltage violation since
% We are more ok with voltage violation than rating.
rateacost = max(default_cost, 2*max_gen_cost);
vcost     = max(default_cost*10, 2*10*max_gen_cost);
gencost   = max(default_cost*10, 2*10*max_gen_cost);
opt.vm.softlims = struct('RATE_A', struct('hl_mod', 'remove', 'cost', rateacost),...
                      'VMAX', struct('hl_mod', 'replace', 'hl_val', 1.25, 'cost', vcost),...
                      'VMIN', struct('hl_mod', 'replace', 'hl_val', 0.8, 'cost', vcost),...
                      'QMAX', struct('hl_mod', 'remove', 'cost', gencost), ...
                      'QMIN', struct('hl_mod', 'remove', 'cost', gencost),...
                      'PMAX', struct('hl_mod', 'remove', 'cost', 2*gencost), ...
                      'PMIN', struct('hl_mod', 'remove', 'cost', 2*gencost));

%% (optional) parallel pool
if opt.vm.parallel.numcores == 0
  opt.vm.parallel.use = 0;
elseif opt.vm.parallel.use && ~exist('parfor','builtin')
  warning('sgvm_mpc_perm: parallelization requested but it appears the Parallel Computing Toolbox is not installed. Setting parallel.use=0')
  opt.vm.parallel.use = 0;
end
if opt.vm.parallel.use
  if ~isempty(gcp('nocreate'))
    p = gcp;
  else
    if opt.vm.parallel.numcores > 0
      p = parpool(opt.vm.parallel.numcores);
    else
      p = parpool('local');
    end
  end
else
    p = [];
end
%% start time
tstart = tic;
%% initialize first generation
if opt.verbose > 0
  fprintf('Initializing first generation of %d cases...\n', opt.vm.ea.inds)
end
psi = sgvm_GenerationClass(mpc, opt.vm.ea.inds, opt);
if opt.verbose > 0
  fprintf('\tinitialization complete (%0.3f sec).\n', toc(tstart))
  if opt.verbose > 1
    fprintf('Current stats:\n')
    psi.stats()
  end
end
%% generations loop
for g = 1:opt.vm.ea.generations
  tgen = tic;
  if opt.verbose > 0
    fprintf('-------------------------------------------------------\n')
    fprintf('---- Generation Loop %d\n', g)
    fprintf('-------------------------------------------------------\n')
  end
  %% update gen count
  psi.update_gen();
  %% branch permutation
  tbperm = tic;
  if opt.verbose > 0
    fprintf('Performing branch permutation loop (%d cases)...\n', length(psi.inds))
  end
    psi.perm_loop('branch', opt);
  if opt.verbose > 0
    fprintf('\tbranch permutation loop completed (%0.3f sec).\n', toc(tbperm))
    if opt.verbose > 1 && ~psi.exitflag
      fprintf('Current stats:\n')
      psi.stats()
      fprintf('Stash stats:\n')
      psi.stash.stats()
    end
  end
  %% check solutions
  if length(psi.soln) >= opt.vm.ea.select
    psi.picksoln(opt.vm.ea.select);
    if psi.exitflag
      if opt.verbose > 0
        fprintf('---- Solution exit flag satisfied (%0.3f sec) \n', g, toc(tgen))
        fprintf('\tObjective Range: %0.5g -- %0.5g\n', psi.soln{1}.mpc.f, psi.soln{end}.mpc.f)
        fprintf('-------------------------------------------------------\n')
      end
      psi.inds = {};
      break
    end
  end
  %% midway cleanup
  % keep initial number of inds or half of current number, whichever is greater
  psi.select(max(opt.vm.ea.inds, floor(length(psi.inds)/2)), 0, opt)
  %% node permutation
  tnperm = tic;
  if opt.verbose > 0
    fprintf('Performing node permutation loop (%d cases)...\n', length(psi.inds))
  end
    psi.perm_loop('node', opt);
  if opt.verbose > 0
    fprintf('\tnode permutation loop completed (%0.3f sec).\n', toc(tnperm))
    if opt.verbose > 1
      fprintf('Current stats:\n')
      psi.stats()
      fprintf('Stash stats:\n')
      psi.stash.stats()
    end
  end
  %% check solutions
  if length(psi.soln) >= opt.vm.ea.select
    psi.picksoln(opt.vm.ea.select);
    if psi.exitflag
      if opt.verbose > 0
        fprintf('---- Solution exit flag satisfied (%0.3f sec) \n', g, toc(tgen))
        fprintf('\tObjective Range: %0.5g -- %0.5g\n', psi.soln{1}.mpc.f, psi.soln{end}.mpc.f)
      end
      psi.inds = {};
      break
    end
  end
  %% selection
  if g < opt.vm.ea.generations
    psi.select(opt.vm.ea.inds - opt.vm.ea.randnew, opt.vm.ea.randnew, opt);
    if opt.verbose > 0
      fprintf('---- Generation Loop %d Complete (%0.3f sec) \n', g, toc(tgen))
      fprintf('\tObjective Range: %0.5g -- %0.5g\n', psi.inds{1}.mpc.f, psi.inds{end}.mpc.f)
      fprintf('\t Total possible solutions found: %d\n', length(psi.solnlist))
    end
  else
    if length(psi.soln) < opt.vm.ea.select
      % select best non-solution individuals
      psi.select(opt.vm.ea.select - length(psi.soln), 0);
      % merge in solved individuals from stash
      psi.merge_stash();
      psi.inds_remove_soln();
      % combine for solution
      psi.soln = horzcat(psi.soln, psi.inds);
    end
      psi.picksoln(opt.vm.ea.select);
      psi.inds = {};
      if opt.verbose > 0
        fprintf('---- Final Generation Loop %d Complete (%0.3f sec) \n', g, toc(tgen))
        fprintf('\tObjective Range: %0.5g -- %0.5g\n', psi.soln{1}.mpc.f, psi.soln{end}.mpc.f)
        fprintf('\t Total possible solutions found: %d\n', length(psi.solnlist))
      end
  end
end
%% Reactive planning
if opt.verbose > 0
  tshunts = tic;
  fprintf('-------------------------------------------------------\n')
  fprintf('---- Reactive Planning Stage \n')
  fprintf('\tAdding shunts to %d cases...\n', length(psi.soln))
end
psi.reactive_planning(opt);
if opt.verbose > 0
  fprintf('\tReactive planning completed (%0.3f sec).\n', toc(tshunts))
end
%%
if opt.verbose > 0
  fprintf('-------------------------------------------------------\n')
  fprintf('---- Completed (%0.3f sec).\n', toc(tstart))
  fprintf('\tObjective Range: %0.5g -- %0.5g\n', psi.soln{1}.mpc.f, psi.soln{end}.mpc.f)
  psi.stats('soln')
end

%% delete parallel pool
if ~isempty(p)
  delete(p)
end

%% collect result
[r, status] = psi.mpc_export() ;
