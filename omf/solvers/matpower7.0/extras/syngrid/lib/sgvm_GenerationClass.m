classdef sgvm_GenerationClass < handle
%SGVM_GENERATIONCLASS collection of SGVM_INDCLASS objects
%   G = SGVM_GENERATIONCLASS(MPC, INDS, OPT) inializes a new generation of INDS
%   individuals (SGVM_INDCLASS objects) based on seed MATPOWER case MPC.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

    properties
        init
        inds
        soln
        solnlist
        node_progen
        branch_progen
        current_gen
        exitflag
        stash
        basempc
    end
    methods
        function obj = sgvm_GenerationClass(mpc, inds, opt)
            if isa(mpc, 'sgvm_GenerationClass')
              current_gen = mpc.current_gen;
              mpc = mpc.basempc;
            else
              current_gen = 0;
            end
            %% initialize generation class object
            if ~isempty(opt.vm.opflogpath)
              if ~exist(opt.vm.opflogpath,'dir')
                  mkdir(opt.vm.opflogpath)
              end
            end
            obj.basempc  = mpc;
            obj.exitflag = false;
            obj.solnlist      = {};
                obj.node_progen   = {};
                obj.branch_progen = {};
                obj.stash = sgvm_SolnStash(opt.vm.ea.select);
            obj.init = inds;
            % initials inds random branch permutations
                s = warning;
                warning('off','MATLAB:nearlySingularMatrix')
                warning('off','MATLAB:SingularMatrix')
            if ~opt.vm.parallel.use %isempty(gcp('nocreate'))
              obj.inds = cell(1,inds);
              for k = 1:inds
                  obj.inds{k} = sgvm_IndClass(mpc, 'init', current_gen, opt);
              end
            else
              tmpinds = cell(1,inds);
              parfor k = 1:inds
                  tmpinds{k} = sgvm_IndClass(mpc, 'init', current_gen, opt);
              end
              obj.inds = tmpinds;
            end
            obj.current_gen = current_gen;
            obj.soln = {};
            obj.expand_soln()
                warning(s); %restore normal warning state
        end

        function perm_loop(obj, type, opt)
            %% perform permutaton on individuals thereby generating offsprings

            % compare new parents with previous parents
            lstname = [type, '_progen'];
            new_parents = cellfun(@(x) x.id, obj.inds, 'UniformOutput', false);
            % only keep new parents
            new_parents = new_parents(~ismember(new_parents, obj.(lstname)));
            % add to list
            obj.(lstname) = horzcat(obj.(lstname), new_parents);

            % add solutions that are not on the old_parents list
            if (length(obj.soln) < obj.stash.size) && (length(obj.soln) > 0)
                tmplist = cellfun(@(x) x.id, obj.soln, 'UniformOutput', false);
                tmpmask = false(size(tmplist));
                for k = 1:length(obj.soln)
                    if ~ismember(obj.soln{k}.id, obj.(lstname))
                        tmpmask(k) = true;
                    end
                end
                obj.inds = horzcat(obj.inds, obj.soln(tmpmask));
                obj.(lstname) = horzcat(obj.(lstname), tmplist(tmpmask));
            end

            s = warning;
            warning('off','MATLAB:nearlySingularMatrix')
            warning('off','MATLAB:SingularMatrix')
            chldr = cell(1, length(obj.inds));
            niter = opt.vm.([type, 'perm']).niter;
            gen = obj.current_gen;
            if ~opt.vm.parallel.use %isempty(gcp('nocreate'))
                % loop over individuals
                for k = 1:length(obj.inds)
                    if ~ismember(obj.inds{k}.id, new_parents)
                        continue
                    end
                    % for each individuals perform permutation niter times
                    tmp = obj.evolve_children(obj.inds{k}, niter, type, gen, opt);
                    chldr{k} = tmp;
                end
            else
              tmpinds = obj.inds;
              parfor k = 1:length(tmpinds)
                if ~ismember(tmpinds{k}.id, new_parents)
                  continue
                end
                % for each individuals perform permutation niter times
                tmp = obj.evolve_children(tmpinds{k}, niter, type, gen, opt);
                chldr{k} = tmp;
              end
            end
            % merge children and orders based on objective
            obj.merge_children(chldr);
            obj.expand_soln()
                obj.stash.update(obj.inds);
                obj.clear_old_inds(type);
                warning(s); %restore normal warning state

            if isempty(obj.inds)
              if length(obj.soln) >= opt.vm.ea.select
                obj.exitflag = true;
              else
                if opt.verbose > 0
                  fprintf('Empty inds cell encountered, restarting with a new initial generation.\n')
                end
                  tmp = sgvm_GenerationClass(obj, opt.vm.ea.inds, opt);
                  obj.merge(tmp);
              end
            end
        end

        function update_gen(obj)
            obj.current_gen = obj.current_gen + 1;
        end

        function clear_old_inds(obj, type)
            % clear inds that will no longer produce new children
            % cases:
            %     curent gen | loop  completed | what is old?
            %   -----------|-----------------|--------------------------------------
            %       x      | branch            | anything from gen x-2 or x-1.branch
            %       x      | node            | anything from gen x-2 or x-1.node
            for k = 1:length(obj.inds)
                if obj.inds{k}.gen <= obj.current_gen-2
                  obj.inds{k} = [];
                elseif (obj.inds{k}.gen == obj.current_gen-1) && strcmp(obj.inds{k}.call, type)
                  obj.inds{k} = [];
                end
            end
            obj.inds = obj.inds(~cellfun(@isempty, obj.inds));
        end

        function reactive_planning(obj, opt)
            % add shunt elements to each individual in the soln field
            if ~opt.vm.parallel.use %isempty(gcp('nocreate'))
                for k = 1:length(obj.soln)
                    obj.soln{k}.add_shunts(opt);
                end
            else
                tmp = obj.soln;
                parfor k = 1:length(obj.soln)
                    tmp{k} = tmp{k}.add_shunts(opt);
                end
                obj.soln = tmp;
            end
        end

        function merge_children(obj, children)
            % merge children and inds objects.
            % In the process individuals that
            % have not been solved or failed to solved are removed
            % also sorts individuals based on their objective function.

            n = sum(cellfun(@length, children)) + length(obj.inds);
            tmp = cell(1,n);
            tmplist = cell(1,n);
            ptr = 1;
            for k = 1:length(obj.inds)
              if obj.inds{k}.solcheck() && ~ismember(obj.inds{k}.id, tmplist(1:ptr-1))
                tmp{ptr} = obj.inds{k};
                tmplist{ptr} = obj.inds{k}.id;
              else
                tmplist{ptr} = '';
              end
              ptr = ptr + 1;
              for h = 1:length(children{k})
                if children{k}{h}.solcheck() && ~ismember(children{k}{h}.id, tmplist(1:ptr-1))
                  tmp{ptr} = children{k}{h};
                  tmplist{ptr} = children{k}{h}.id;
                else
                  tmplist{ptr} = '';
                end
                ptr = ptr + 1;
              end
            end
            obj.inds = tmp(~cellfun(@isempty, tmp));

            % sort based on objective function
            [~, I] = sort(cellfun(@(x) x.mpc.f, obj.inds));
            obj.inds = obj.inds(I);
        end

        function merge_stash(obj)
            obj.inds = horzcat(obj.inds, obj.stash.inds(1:obj.stash.count));
            % sort based on objective function
            [~, I] = sort(cellfun(@(x) x.mpc.f, obj.inds));
            obj.inds = obj.inds(I);
        end

        function inds_remove_soln(obj)
            for k = 1:length(obj.inds)
                if ismember(obj.inds{k}.id, obj.solnlist)
                    obj.inds{k} = [];
                end
            end
            obj.inds = obj.inds(~cellfun(@isempty, obj.inds));
        end

        function select(obj, inds, randnew, opt)
            % Select the best inds out of obj.inds and create randnew individuals
            % based on mpc
            % assumes that obj.inds is ordered based on objective values
            % in ASCENDING order, therefore the best are simple obj.inds(1:inds)

            n = inds + randnew;
            if n <= 0
              obj.inds = {};
              return
            end
            if inds <= length(obj.inds)
              obj.inds = obj.inds(1:inds);
            end
            if nargin == 4 % don't create new individuals if not opt structure given
              if (randnew > 0) || (opt.vm.ea.initfill && (length(obj.inds) < inds))
                tmp = sgvm_GenerationClass(obj, n - length(obj.inds), opt);
                obj.merge(tmp);
              end
            end
        end

        function merge(obj, x)
            % merges the individuals in x into obj's inds
            obj.inds = horzcat(obj.inds, x.inds);
            obj.expand_soln();
        end

        function expand_soln(obj)
            % copy individual k from the inds array to the soln array
            for k = 1:length(obj.inds)
              if obj.inds{k}.iscomplete() && ~ismember(obj.inds{k}.id, obj.solnlist)
                obj.soln = horzcat(obj.soln, {obj.inds{k}});
                obj.solnlist = horzcat(obj.solnlist, obj.inds{k}.id);
              end
            end
            if ~isempty(obj.soln)
              [~, I] = sort(cellfun(@(x) x.mpc.f, obj.soln));
              obj.soln = obj.soln(I);
            end
        end

        function picksoln(obj, n)
            % pick n entries out of the solution array. Entries are already
            % sorted by cost, and by definition they have no overloaded branches.

            if length(obj.soln) <= n
              return
            end
            obj.soln = obj.soln(1:n);
            if ~any(cellfun(@(x) x.gen >= obj.current_gen-1, obj.inds)) || isempty(obj.inds)
              % if no individuals are from this or the previous generation, AND a
              % sufficient number of solutions has already been found, then exit.
              obj.exitflag = true;
            end
        end

        function [mpc_array, status] = mpc_export(obj, field)
            % Export the matpower cases from either soln (default) or inds, to a
            % cell array of matpower cases.
            if nargin == 1
              field = 'soln';
            end

            mpc_array = cellfun(@(x) x.mpc, obj.(field), 'UniformOutput', 0);
            status    = cellfun(@(x) x.mpc.success*x.iscomplete(2), obj.(field));
        end

        function stats(obj, field)
            if nargin == 1
              field = 'inds';
            end
            sgvm_collection_stats(obj, field);
        end

        %% ------  private methods  -----------
        function chldr = evolve_children(obj, parent, niter, type, gen, opt)
            % for each individual perform permutation
            % niter times

            chldr = cell(1,niter);
            breakflag = false;
            for h = 1:niter
                if parent.solcheck()
                  if h == 1
                      chldr{h} = sgvm_IndClass(parent, type, gen, opt);
                  elseif chldr{h-1}.solcheck()
                      chldr{h} = sgvm_IndClass(chldr{h-1}, type, gen, opt);
                  else
                      chldr{h} = sgvm_IndClass(parent.mpc, 'init', gen, opt);
                  end
                else
                  chldr{h} = sgvm_IndClass(parent.mpc, 'init', gen, opt);
                end

            %     if chldr{h}.iscomplete() && strcmp(type, 'branch')
            %         % check whether child satisfies all constraints
            %         breakflag = true;
            %     end

                if h > 1
                  if chldr{h-1}.comp_perm(chldr{h})
                    % permutation didn't change
                    chldr{h} = [];
                    breakflag = true;
                  end
                else
                  if parent.comp_perm(chldr{h})
                    % permutation didn't change
                    chldr{h} = [];
                    breakflag = true;
                  end
                end
                if breakflag
                  break
                end
            end
            chldr = chldr(~cellfun(@isempty, chldr));
        end
    end
end
