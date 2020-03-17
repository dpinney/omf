classdef sgvm_IndClass < handle
%SGVM_INDCLASS individual placement in the variations method
%   IND = SGVM_INDCLASS(MPC, TYPE, GEN, OPT) evolves individuals based on
%   MPC and the TYPE of permuation (NODE, BRANCH, INIT) that is specified.
%
%   The SGVM_INDCLASS contains a MATPOWER case and methods to modify it
%   towards a more desireable solution by permuting properties as well as
%   adding shunt elements.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

    properties
        mpc
        id
        pid
        ng
        nb
        nl
        gen
        scale_s
        overload_frac
        call
        deltaf
    end
    methods
        function obj = sgvm_IndClass(mpc, type, gen, opt)
            if isa(mpc, 'sgvm_IndClass')
              parent = mpc;
              mpc    = parent.mpc;
              obj.scale_s = parent.scale_s;
              obj.overload_frac = parent.overload_frac;
              obj.pid = parent.id;
            else
              obj.scale_s = opt.vm.nodeperm.scale_s;
              obj.overload_frac = 1;
              obj.pid = '--N/A--';
            end
            obj.ng = size(mpc.gen, 1);
            obj.nb = size(mpc.bus, 1);
            obj.nl = size(mpc.branch, 1);
            obj.gen = gen;

            switch type
              case 'init'
                obj.call = 'init';
                obj.mpc = mpc;
                obj.strip_result();
                obj.mpc = sgvm_branch_perm(obj.mpc);
                obj.mpc = sgvm_nodeperm_init(obj.mpc);
                obj.assign_bustypes();
                obj.setid();
                obj.solve(opt);
            %         obj = sgvm_IndClass(obj.mpc, 'branch', obj.gen, opt);
              case 'branch'
                obj.call = 'branch';
                [~, nviolations] = obj.checkoverloads(mpc);
                if nviolations < 15
                  obj.overload_frac = max(0.80, opt.vm.branchperm.overload_frac_factor*obj.overload_frac);
                else
                  obj.overload_frac = 1;
                end
                opt.vm.branchperm.overload_frac = obj.overload_frac;
                if opt.vm.branchperm.verbose > 0
                  fprintf('\t(child of %s) overload_frac = %0.3f\n', obj.pid(1:6), obj.overload_frac);
                end
                [obj.mpc, flag] = sgvm_branch_perm(mpc, opt);
                obj.setid();
                if flag
                  obj.clear_shunts();
                  obj.solve(opt);
                elseif opt.vm.branchperm.verbose > 0
                  fprintf('\t(child of %s) Identity permutation returned (i.e no improvement).\n', obj.pid(1:6));
                end
              case 'node'
                obj.call = 'node';
                if opt.vm.nodeperm.verbose > 0 && ~opt.vm.parallel.use
                  fprintf('\t(child of %s)---Time stats:\n', obj.pid(1:6));
                end
                [~, nviolations] = obj.checkoverloads(mpc);
                if nviolations < 10
                  opt.vm.nodeperm.usedv = true;
                  obj.scale_s = max(0.75, opt.vm.nodeperm.scale_s_factor*obj.scale_s);
                else
                  obj.scale_s = min(1, obj.scale_s/opt.vm.nodeperm.scale_s_factor);
                end
                opt.vm.nodeperm.scale_s = obj.scale_s;
                tcalc = tic;
                [Pbus,Qbus] = sgvm_calc_injection_delta(mpc, opt);
                if opt.vm.nodeperm.verbose > 0
                  fprintf('\t(child of %s) injection calc: scale_s = %0.3f, time %0.3f\n', obj.pid(1:6), obj.scale_s, toc(tcalc));
                end
                tperm = tic;
                perm = sgvm_deltainjection2perm(Pbus, Qbus, opt);
                if opt.vm.nodeperm.verbose > 0
                  fprintf('\t(child of %s) sgvm_deltainjection2perm: time %0.3f\n', obj.pid(1:6), toc(tperm));
                end
                if all(perm == (1:size(mpc.bus,1)).')
                  if opt.vm.nodeperm.verbose > 0
                     fprintf('\t(child of %s) Identity permutation returned (i.e no improvement).\n', obj.pid(1:6));
                  end
                  obj.mpc = mpc;
                else
                  obj.mpc = sgvm_perform_permute(mpc, perm, 'perm');
                  obj.assign_bustypes();
                  obj.setid();
                  tsolve = tic;
                  obj.clear_shunts();
                  obj.solve(opt);
                  if opt.vm.nodeperm.verbose > 0
                    fprintf('\tInd %s (child of %s) solve time: %0.3f\n', obj.id(1:6), obj.pid(1:6), toc(tsolve));
                  end
                end
            end
            obj.setid();
            if isfield(mpc,'f') && obj.solcheck()
                obj.deltaf = obj.mpc.f - mpc.f;
            else
                obj.deltaf = NaN;
            end
        end

        function setid(obj)
            % ID is a hash of some of the key data
            % hashing is largely copied from:
            % https://www.mathworks.com/matlabcentral/answers/45323-how-to-calculate-hash-sum-of-a-string-using-java

            define_constants;
            data = [obj.mpc.bus(:,PD); obj.mpc.bus(:,QD);...
                obj.mpc.branch(:,BR_R); obj.mpc.branch(:,BR_X); obj.mpc.branch(:,BR_B);...
                obj.mpc.branch(:,TAP); obj.mpc.branch(:,SHIFT); obj.mpc.gen(GEN_BUS)];
            str = mat2str(data,8);
            if have_fcn('octave')
                obj.id = hash('SHA256', str);
            else
                md = java.security.MessageDigest.getInstance('SHA-256');
                obj.id = sprintf('%2.2x', typecast(md.digest(uint8(str)), 'uint8'));
            end
        end

        function obj = solve(obj, opt)
            % ensure softlimits are turned on and solve opf

            define_constants;
            obj.mpc.softlims = opt.vm.softlims;
            if ~toggle_softlims(obj.mpc, 'status')
              obj.mpc = toggle_softlims(obj.mpc, 'on');
            end
            obj.toggle_var_support('on'); % add fictitious generators for var support
            mpopt = opt.mpopt;
            if ~isempty(opt.vm.opflogpath) && strcmp(mpopt.opf.ac.solver, 'IPOPT')
              fname = fullfile(opt.vm.opflogpath,sprintf('Ind%s_%s.out', obj.id(1:6), obj.call));
              mpopt.ipopt.opts.output_file =fname;
            end
            if strcmp(obj.call, 'init')
              maxit = sgvm_get_max_iter(mpopt);
              if maxit < 1000
                  mpopt = sgvm_set_max_iter(mpopt, 1000);
              end
            elseif obj.gen >= opt.vm.ea.generations
              obj.mpc.softlims.PMAX.hl_mod = 'none';
              obj.mpc.softlims.PMIN.hl_mod = 'none';
            end
            if (obj.gen > 0) && obj.gen <= opt.vm.ea.generations
              % progressively make reactive support less expensive and line violations more expensive
              obj.mpc.softlims.QMAX.cost = opt.vm.softlims.RATE_A.cost + (opt.vm.ea.generations - obj.gen)/opt.vm.ea.generations * (opt.vm.softlims.QMAX.cost - opt.vm.softlims.RATE_A.cost);
              obj.mpc.softlims.QMIN.cost = obj.mpc.softlims.QMAX.cost;

              obj.mpc.softlims.RATE_A.cost = opt.vm.softlims.QMAX.cost - (opt.vm.ea.generations - obj.gen)/opt.vm.ea.generations * (opt.vm.softlims.QMAX.cost - opt.vm.softlims.RATE_A.cost);

              % progressively shrink tolerable voltage range
              obj.mpc.softlims.VMAX.hl_val = 1.1 + (opt.vm.ea.generations - obj.gen)/opt.vm.ea.generations * (opt.vm.softlims.VMAX.hl_val - 1.1);
              obj.mpc.softlims.VMIN.hl_val = 0.9 - (opt.vm.ea.generations - obj.gen)/opt.vm.ea.generations * (0.9 - opt.vm.softlims.VMIN.hl_val);
            end
            while true
              if opt.verbose > 1
                maxit = sgvm_get_max_iter(mpopt);
                fprintf('  Ind %s (child of %s): solving with %d max iterations\n', obj.id(1:6), obj.pid(1:6), maxit);
              end
              obj.mpc = rundcopf(obj.mpc, mpopt);
              mpopt.opf.start = 2;
              r = runopf(obj.mpc, mpopt);
              if opt.verbose > 1
                fprintf('  Ind %s (child of %s): runopf complete with status %d\n', obj.id(1:6), obj.pid(1:6), r.success);
              end
              if ~r.success
                % if initial solution fails try using a powerflow initialization
                tmp = struct('baseMVA', r.baseMVA, 'bus', r.bus,...
                    'branch', r.branch, 'gen', r.gen, ...
                    'gencost', r.gencost);
                rpf = runpf(tmp, opt.mpopt);
                if opt.verbose > 1
                  fprintf('  Ind %s (child of %s): runpf complete with status %d\n', obj.id(1:6), obj.pid(1:6), rpf.success);
                end
                if rpf.success
                  obj.mpc_from_pf(rpf, r.softlims);
                  break
                else
                  if strcmp(obj.mpc.softlims.PMAX.hl_mod, 'none')
                      obj.mpc.softlims.PMAX.hl_mod = 'remove';
                      obj.mpc.softlims.PMIN.hl_mod = 'remove';
                  %end
                  %switch mpopt.opf.ac.solver
                  %    case {'MIPS', 'IPOPT'}
                  %        maxit = sgvm_get_max_iter(mpopt, 1000);
                  %        if maxit < 1000
                  %            warning('sgvm_IndClass/solve: increasing Ind %s (child of %s) maximum iteration to %d.', obj.id(1:6), obj.pid(1:6), 2*maxit)
                  %            mpopt = sgvm_set_max_iter(mpopt, 2*maxit);
                  %        else
                  %            obj.mpc = r;
                  %            warning('sgvm_IndClass/solve: Unable to solve opf (Ind %s, child of %s).', obj.id(1:6), obj.pid(1:6))
                  %            break
                  %        end
                  %    otherwise
                  else
                    obj.mpc = r;
                    warning('sgvm_IndClass/solve: Unable to solve opf (Ind %s, child of %s).', obj.id(1:6), obj.pid(1:6))
                    break
                  end
                end
              else
                obj.mpc = r;
                break
              end
            end
            obj.toggle_var_support('off'); % remove fictitious generators for var support
            obj.clean_opf_fields();
        end

        function toggle_var_support(obj,on_off)
            % toggle variable shunts at every node on or off

            define_constants;
            if strcmp(on_off, 'on')
              new_gen = zeros(obj.nb, size(obj.mpc.gen,2));
              new_gen(:,[GEN_BUS, VG, MBASE, GEN_STATUS]) = ...
                  [(1:obj.nb)', ones(obj.nb,1), obj.mpc.baseMVA*ones(obj.nb,1), ones(obj.nb,1)];
              obj.mpc.gen = [obj.mpc.gen; new_gen];

              cst = 0;%obj.mpc.softlims.QMAX.cost(1);
              new_gencost = zeros(obj.nb, size(obj.mpc.gencost,2));
              new_gencost(:,[MODEL, NCOST, COST]) = [2*ones(obj.nb,1), 2*ones(obj.nb,1), cst*ones(obj.nb,1)];

              obj.mpc.gencost = [obj.mpc.gencost; new_gencost];

              obj.mpc.softlims.QMAX.idx   = (obj.ng+1:obj.ng+obj.nb)';
              obj.mpc.softlims.QMIN.idx   = (obj.ng+1:obj.ng+obj.nb)';
              obj.mpc.softlims.PMAX.idx   = (obj.ng+1:obj.ng+obj.nb)';
              obj.mpc.softlims.PMIN.idx   = (obj.ng+1:obj.ng+obj.nb)';
            elseif strcmp(on_off, 'off')
              obj.mpc.gen     = obj.mpc.gen(1:obj.ng, :);
              obj.mpc.gencost = obj.mpc.gencost(1:obj.ng, :);

              %% Convert to generators to shunt elements
              if isfield(obj.mpc.softlims.QMAX, 'overload')
                bsh = (obj.mpc.softlims.QMAX.overload(obj.ng+1:end) - obj.mpc.softlims.QMIN.overload(obj.ng+1:end))./obj.mpc.bus(:,VM).^2;
              else
                bsh = zeros(obj.nb,1);
              end
              if isfield(obj.mpc.softlims.PMIN, 'overload')
                % IMPORTANT: this could produce NEGATIVE real shunt elements. That is CLEARLY not realistic.
                % These elements will be removed at a later point, they are simply a way of indicating the added injections for a future
                % child object.
                gsh = (obj.mpc.softlims.PMIN.overload(obj.ng+1:end) - obj.mpc.softlims.PMAX.overload(obj.ng+1:end))./obj.mpc.bus(:,VM).^2;
              else
                gsh = zeros(obj.nb,1);
              end
              obj.mpc.bus(:, [GS, BS]) = [gsh, bsh];
            else
              error('sgvm_IndClass/toggle_var_support: on_off must be either ''on'' or ''off''.')
            end
        end

        function clear_shunts(obj)
            % remove shunt elements from mpc object
            define_constants;
            obj.mpc.bus(:, [GS, BS]) = 0;
        end

        function clean_opf_fields(obj)
            % remove opf fields that will not be accessed and are therefore taking up a lot of space
            fields = {'om', 'x', 'mu', 'var', 'lin', 'qdc', 'raw', 'nle', 'nli'};
            for f = fields
              if isfield(obj.mpc, f{1})
                obj.mpc = rmfield(obj.mpc, f{1});
              end
            end
        end

        function obj = mpc_from_pf(obj, r, softlims)
            % take a powerflow solved case, r, and convert it to what appears like
            % a solved opf case

            define_constants;
            % indicate that r solved but not exactly in the expected way.
            % by using 2 a test like (if r.success) still passes since r.success is
            % not 0.
            r.success = 2;
            cost = sum(totcost(r.gencost, r.gen(:, PG)));
            r.softlims = softlims;
            for prop = fieldnames(r.softlims).'
              if strcmp(r.softlims.(prop{:}).hl_mod, 'none')
                continue
              end
              switch prop{:}
                case 'RATE_A'
                  Sf = sqrt(r.branch(:,PF).^2 + r.branch(:,QF).^2);
                  St = sqrt(r.branch(:,PT).^2 + r.branch(:,QT).^2);
                  %maximum apparent flow on branch
                  S  = max(Sf,St);
                  idx = r.softlims.RATE_A.idx;
                  r.softlims.RATE_A.overload = zeros(size(r.branch, 1), 1);
                  r.softlims.RATE_A.overload(idx) = max(0, S(idx) - r.branch(idx, RATE_A));
                case {'PMAX', 'QMAX'}
                  idx = (1:size(r.gen,1)).'; %r.softlims.(prop{:}).idx;
                  r.softlims.(prop{:}).overload = zeros(size(r.gen,1),1);
                  r.softlims.(prop{:}).overload(idx) = max(0, ...
                      r.gen(idx, eval([prop{:}(1), 'G'])) - r.gen(idx, eval(prop{:})));
                case 'VMAX'
                  idx = r.softlims.VMAX.idx;
                  r.softlims.VMAX.overload = zeros(size(r.bus, 1), 1);
                  r.softlims.VMAX.overload(idx) = max(0, r.bus(idx, VM) - r.bus(idx, VMAX));
                case 'VMIN'
                  idx = r.softlims.VMIN.idx;
                  r.softlims.VMIN.overload = zeros(size(r.bus, 1), 1);
                  r.softlims.VMIN.overload(idx) = max(0, r.bus(idx, VMIN) - r.bus(idx, VM));
                case 'ANGMAX'
                  delta = calc_branch_angle(r);
                  idx = r.softlims.ANGMAX.idx;
                  r.softlims.ANGMAX.overload = zeros(size(r.branch, 1), 1);
                  r.softlims.ANGMAX.overload(idx) = max(0, delta(idx) - r.branch(idx,ANGMAX));
                case 'ANGMIN'
                  delta = calc_branch_angle(r);
                  idx = r.softlims.ANGMIN.idx;
                  r.softlims.ANGMIN.overload = zeros(size(r.branch, 1), 1);
                  r.softlims.ANGMIN.overload(idx) = max(0, delta(idx) - r.branch(idx,ANGMIN));
                case {'PMIN', 'QMIN'}
                  idx = (1:size(r.gen,1)).'; %r.softlims.(prop{:}).idx;
                  r.softlims.(prop{:}).overload = zeros(size(r.gen,1),1);
                  r.softlims.(prop{:}).overload(idx) = max(0, ...
                     r.gen(idx, eval(prop{:})) - r.gen(idx, eval([prop{:}(1), 'G'])));
              end
              cost = cost + r.softlims.(prop{:}).cost(1) * sum(r.softlims.(prop{:}).overload);
            end
            r.f = cost; % total cost at current solution
            obj.mpc = r;
        end

        function bool = solcheck(obj)
            % checks whether mpc has been solved and if so, whether it converged
            bool = 0;
            if isfield(obj.mpc, 'success')
              if obj.mpc.success
                bool = 1;
              end
            end
        end

        function ind = iscomplete(obj, level)
            % checks if mpc satisfies all the necessary constraint.
            if nargin < 2
              level = 1;
            end
            ind = obj.checkoverloads(obj.mpc);
            if level > 1
              define_constants;
              % check voltage constraints
              vtest = obj.mpc.bus(:,VM) <= (obj.mpc.bus(:,VMAX) + 1e-4);
              vtest = vtest & (obj.mpc.bus(:,VM) >= (obj.mpc.bus(:,VMIN) - 1e-4));
              ind = ind + all(vtest);
            end
        end

        function bool = comp_perm(obj, x)
            % check whether obj.mpc is the sampe as x.mpc by comparing their hash
            bool = isequal(obj.id, x.id);
        end

        function obj = strip_result(obj)
            % keep only bus, branch, gen and gencost, and baseMVA fields of mpc
            % and remove powerflow results
            % change all buses to PQ buses
            tmp.bus     = obj.mpc.bus(:,1:13);
            tmp.branch  = obj.mpc.branch(:,1:13);
            tmp.gen     = obj.mpc.gen(:, 1:21);
            tmp.gencost = obj.mpc.gencost;
            tmp.baseMVA = obj.mpc.baseMVA;
            obj.mpc = tmp;
        end

        function obj = assign_bustypes(obj)
            % all generator buses are PV, largest generator bus is REF,
            % and all others are PQ
            define_constants;
            obj.mpc.bus(:,BUS_TYPE) = PQ;
            % all gen buses are pv buses
            obj.mpc.bus(obj.mpc.gen(:, GEN_BUS), BUS_TYPE) = 2;

            % reference bus is bus with largest gen
            [~,tmpidx] = max(obj.mpc.gen(:, PMAX));
            refbus = obj.mpc.gen(tmpidx, GEN_BUS);
            obj.mpc.bus(refbus, BUS_TYPE) = 3;
        end

        function obj = add_shunts(obj, opt)
            % add shunts to the case to meet the voltage requirements and try to
            % avoid negative LMPS. The algorithm can fail in 2 ways:
            % 1) the add_shunts routine fails to solve the opf
            % 2) the could be branch flow violations at the end of the procedure
            % for case 1, the routine restores a backup of the original object
            % and returns.
            % for case 2 the overloads should be indicated by the softlims field
            % and handled elswhere.

            define_constants;
            bkup = obj;
            bkupflag = 1;
            cnt = 0;
            while true
                cnt = cnt + 1;
                obj.clear_shunts();
                if ~isempty(opt.vm.opflogpath) && strcmp(mpopt.opf.ac.solver, 'IPOPT')
                    fname = fullfile(opt.vm.opflogpath,sprintf('Ind%s_shunts.out', obj.id(1:6)));
                    mpopt.ipopt.opts.output_file =fname;
                end
                opt.mpopt.opf.start = 2;
                if opt.verbose > 1
                    fprintf('  Ind %s (child of %s): solving.\n', obj.id(1:6), obj.pid(1:6) );
                end
                [r, ~] = sgvm_add_shunts(obj.mpc, opt.mpopt, opt.vm.shunts);
                if ~r.success
                    obj = bkup;
                    obj.clean_opf_fields();
                    return
                end
                if opt.vm.shunts.verbose > 0
                    fprintf('  Ind %s (child of %s): sgvm_add_shunts complete.\n', obj.id(1:6), obj.pid(1:6));
                end
                if (obj.branch_violations(r) == 0) || (cnt > 5)
                    if isfield(r, 'softlims')
                        r = rmfield(r, 'softlims');
                    end
                    if toggle_softlims(r, 'status')
                        r = toggle_softlims(r, 'off');
                    end

                    % solve WITHOUT softlims
                    tmp = runopf(r, opt.mpopt);
                    if opt.vm.shunts.verbose > 1
                        fprintf('result with No softlimits:\n')
                        printpf(tmp)
                    end
                    % update the saved backup
                    if bkupflag
                      bkup.mpc = tmp;
                      bkupflag = 0;
                    elseif  tmp.success
                      bkup.mpc = tmp;
                    end
                    if (min(tmp.bus(:, LAM_P)) > 0 )
                        if opt.vm.shunts.verbose > 0
                            fprintf('  Ind %s (child of %s): successful completion.\n', obj.id(1:6), obj.pid(1:6));
                        end
                        break
                    elseif cnt > 5
                        if opt.vm.shunts.verbose > 0
                            fprintf('  Ind %s (child of %s): shunt iteration threshold exceeded.\n', obj.id(1:6), obj.pid(1:6));
                        end
                        break
                    elseif opt.vm.shunts.shift_in > 0.04
                        if opt.vm.shunts.verbose > 0
                            fprintf('  Ind %s (child of %s): Maximum shift_in of 0.5 reached.\n', obj.id(1:6), obj.pid(1:6));
                        end
                        break
                    else
                        opt.vm.shunts.shift_in = opt.vm.shunts.shift_in + 0.005;
                        if opt.vm.shunts.verbose > 0
                            fprintf('  Ind %s (child of %s): negative LMP detected, tightning opt.vm.shunts.shift_in to %0.3f.\n', obj.id(1:6), obj.pid(1:6), opt.vm.shunts.shift_in);
                        end
                        continue
                    end
                end
                obj.mpc = r;
                permcnt = 0;
                while ~obj.iscomplete() && (permcnt < 5)
                    obj.scale_s = 1;
                    obj.overload_frac = 1;
                    permcnt = permcnt + 1;
                    [nviolations, idx] = obj.branch_violations(obj.mpc);
                    if strcmp(obj.call, 'branch')
                        type = 'node';
                    elseif strcmp(obj.call, 'node')
                        type = 'branch';
                    elseif strcmp(obj.call, 'init')
                        type = 'branch';
                    end
                    if opt.vm.shunts.verbose > 0
                        fprintf('  Ind %s (child of %s): %d overloaded branches detected. Performing %s permutation.\n', obj.id(1:6), obj.pid(1:6), nviolations, type)
                        if nviolations < 10
                            obj.print_flow_stats(idx)
                        end
                    end
                    opttmp = opt;
                    opttmp.vm.softlims.RATE_A.cost = 2*opt.vm.softlims.QMAX.cost;
                    opttmp.vm.softlims.QMAX.cost   = 0.5*opt.vm.softlims.RATE_A.cost;
                    opttmp.vm.softlims.QMIN.cost   = opttmp.vm.softlims.QMAX.cost;
                    opttmp.vm.softlims.VMAX.cost   = opttmp.vm.softlims.QMAX.cost;
                    opttmp.vm.softlims.VMIN.cost   = opttmp.vm.softlims.QMAX.cost;
                    opttmp.vm.softlims.VMAX.hl_val = 1.1;
                    opttmp.vm.softlims.VMIN.hl_val = 0.85;
                    opttmp.vm.nodeperm.scale_s_factor = 1;
                    opttmp.vm.branchperm.overload_frac_factor = 1;
                    obj = sgvm_IndClass(obj, type, opt.vm.ea.generations + 1, opttmp);
                end
            end

            %if isfield(r, 'softlims')
            %   r = rmfield(r, 'softlims');
            %end
            %if toggle_softlims(r, 'status')
            %   r = toggle_softlims(r, 'off');
            %end
            %
            %% solve WITHOUT softlims
            %tmp = runopf(r, opt.mpopt);
                %fprintf('result with No softlimits:\n')
                %printpf(tmp)

            obj.mpc = tmp;
            obj.clean_opf_fields();
        end

        function print_flow_stats(obj, idx)
            if nargin == 1
                idx = (1:size(obj.mpc.branch, 1)).';
            end
            define_constants;
            sf = sqrt(obj.mpc.branch(idx, PF).^2 + obj.mpc.branch(idx, QF).^2);
            st = sqrt(obj.mpc.branch(idx, PT).^2 + obj.mpc.branch(idx, QT).^2);
            ra = obj.mpc.branch(idx, RATE_A);
            fprintf('----------------------------------------------------\n')
            fprintf('   flow statistic\n')
            fprintf('----------------------------------------------------\n')
            fprintf(' branch id  |  SF (MVA)  |  SF (MVA)  | RATE (MVA) |\n')
            fprintf('------------|------------|------------|------------|\n')
            fprintf('%11d |%11.4f |%11.4f |%11.4f |\n', [idx, sf, st, ra].')
        end

        %% ------  private methods  -----------
        function [bool, nviolations] = checkoverloads(obj, mpc)
            % checks if mpc satisfies all the necessary constraint.

            if isfield(mpc, 'softlims')
                if isfield(mpc.softlims, 'RATE_A')
                  nviolations = sum(mpc.softlims.RATE_A.overload > 1e-4);
                else
                  nviolations = obj.branch_violations(mpc);
                end
                if isfield(mpc.softlims, 'PMAX') && ~strcmp(mpc.softlims.PMAX.hl_mod, 'none')
                  genoverload = sum(mpc.softlims.PMAX.overload > 1e-4);
                else
                  genoverload = obj.gen_violations(mpc);
                end
            else
                nviolations = obj.branch_violations(mpc);
                genoverload = obj.gen_violations(mpc);
            end
            bool =  (nviolations == 0) && (genoverload == 0);
            bool = bool && mpc.success;
        end

        function [nviolations, idx] = branch_violations(obj, mpc)

            define_constants;
            Sf = sqrt(mpc.branch(:,PF).^2 + mpc.branch(:,QF).^2);
            St = sqrt(mpc.branch(:,PT).^2 + mpc.branch(:,QT).^2);
            %maximum apparent flow on branch in per-unit
            S  = max(Sf,St) / mpc.baseMVA;
            % line ratings in per-unit
            ra  = mpc.branch(:,RATE_A) / mpc.baseMVA;
            ra(ra == 0) = Inf;

            nviolations = sum(S > (ra + 1e-4));
            idx = find(S > (ra + 1e-4));
        end

        function genoverload = gen_violations(obj, mpc)
          define_constants;
          genoverload = sum(mpc.gen(:,PG) > mpc.gen(:,PMAX) + 1e-4);
        end    end
end
