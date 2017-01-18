%TEST_MAXLOADLIM

%   MATPOWER
%   Copyright (c) 2015-2016, Power Systems Engineering Research Center (PSERC)
%   by Camille Hamon
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

classdef Test_maxloadlim < matlab.unittest.TestCase
    
    properties
        systems = {'case2','case9'};
        load_dir = struct('case2',[0 1],...
            'case9',[0 0 0 0 1 0 0 0 0;
            0 0 0 0 0 0 1 0 0;
            0 0 0 0 0 0 0 0 1;
            0 0 0 0 1 0 1 0 1;
            0 0 0 0 1 0 1 0 0;
            0 0 0 0 1 0 0 0 1;
            0 0 0 0 0 0 1 0 1]',...
            'case39',[eye(39);ones(1,39)]');
        gen_dir = struct('case9',[0 1 0;
            0 0 1;
            0 1 1]',...
            'case39',[zeros(9,1) eye(9);0 ones(1,9)]');
        % For the case 2 the theoretical result is P = E^2/(2*X)
        max_load_lims = struct('case2',5);
        threshold_MW = 1;
    end
    properties(TestParameter)
        idx_dir_ieee9 = num2cell(1:7);
        idx_dir_ieee39 = num2cell(1:40);
        gen_var_ieee9 = num2cell(1:3);
        gen_var_ieee39 = num2cell(1:10);
    end
    methods(TestClassSetup)
        function setuptests(testcase)
            % This is to turn off the warnings in the CPF when we get close
            % to the nose
            warning off MATLAB:singularMatrix
            warning off MATLAB:nearlySingularMatrix
        end
    end
    
    methods(TestClassTeardown)
        function teardownOnce(testcase)
            warning on MATLAB:singularMatrix
            warning on MATLAB:nearlySingularMatrix
        end
    end
    
    methods(Test)     
        function testAgainstCPF_case39(testCase,idx_dir_ieee39)
            define_constants;
            mpc = loadcase('case39');
            idx_nonzero_loads = mpc.bus(:,PD) > 0;
            dir_all = testCase.load_dir.('case39');
            dirCPF = dir_all(:,idx_dir_ieee39);
            dirCPF(~idx_nonzero_loads)=0;
            dirCPF2 = dirCPF(idx_nonzero_loads);
            if sum(dirCPF2) == 0
                % case of load increase in non-zero load
                testCase.verifyEqual(1,1);
            else
                switch idx_dir_ieee39
                    case 9
                        msg = ['This case fails because the load at bus 9 is capacitive' ...
                            ' which means that some generators hit their lower reactive limits' ...
                            ' , a case that is not handled by my CPF'];
                        fprintf(1,[msg '\n']);
                    case 31
                        msg = ['This case fails because the load at bus 31 is small'...
                            ' and is connected to the slack bus that absorbs any load increase'...
                            ' so that the CPF procedure reaches the maximum number of iterations'...
                            ' before reaching the MLL'];
                        fprintf(1,[msg '\n']);
                end
                results_cpf = ch_runCPF('case39','',0,dirCPF2);
                max_loads_cpf = results_cpf.bus(:,PD)*mpc.baseMVA;
                results_mll = maxloadlim(mpc,dirCPF,'verbose',0);
                max_loads_mll = results_mll.bus(:,PD);
                testCase.verifyEqual(max_loads_mll,max_loads_cpf,'RelTol',0.05);
                % NOTE: we used a 5% relative tolerance here, rather than
                % an absolute tolerance, because the base case of IEEE39 is
                % not feasible for the Q lims, which seem to bring about
                % small discrepancies.
            end
        end
        
        function testAgainstCPF_case9(testCase,idx_dir_ieee9)
            define_constants;
            % Loading the case
            mpc = loadcase('case9');
            dir_all = testCase.load_dir.('case9');
            dir = dir_all(:,idx_dir_ieee9);
            results_mll = maxloadlim(mpc,dir,'verbose',0);
            max_loads_mll = results_mll.bus(:,PD);
            % Remember to set chooseStartPoint to 0 in ch_runCPF
            idx_nonzero_loads = mpc.bus(:,PD) > 0;
            dirCPF = dir(idx_nonzero_loads);
            results_cpf = ch_runCPF('case9static','loads568',0,dirCPF);
            max_loads_cpf = results_cpf.bus(:,PD)*mpc.baseMVA;           
            testCase.verifyEqual(max_loads_mll,max_loads_cpf,'AbsTol',testCase.threshold_MW);
        end
        
        function testAgainstMatpowerCPF_case9(testCase,idx_dir_ieee9)
            define_constants;
            % Loading the case
            mpc = loadcase('case9');
            dir_all = testCase.load_dir.('case9');
            dir = dir_all(:,idx_dir_ieee9);
            % Preparing the target case for Matpower CPF
            mpc_target = mpc;
            nonzero_loads = mpc_target.bus(:,PD) ~= 0;
            Q_P = mpc_target.bus(nonzero_loads,QD)./mpc_target.bus(nonzero_loads,PD);
            mpc_target.bus(:,PD) = mpc_target.bus(:,PD)+2*dir*mpc_target.baseMVA;
            mpc_target.bus(nonzero_loads,QD) = Q_P.*mpc_target.bus(nonzero_loads,PD);
            % Run the CPF with matpower
            [results,~] = runcpf(mpc,mpc_target,mpoption('out.all',0));
            % Extract the maximum loads
            max_loads_cpf = results.bus(:,PD);
            % Solve the maximum loadability limit without considering
            % reactive power limits
            results_mll = maxloadlim(mpc,dir,'use_qlim',0);
            % Extract the maximum loads
            max_loads_mll = results_mll.bus(:,PD);
            % We compare with a precision of 0.5MW
            testCase.verifyEqual(max_loads_mll,max_loads_cpf,'AbsTol',testCase.threshold_MW);
        end
        
        function testAgainstMatpowerCPF_case39(testCase,idx_dir_ieee39)
            define_constants;
            % Loading the case
            mpc = loadcase('case39');
            idx_nonzero_loads = mpc.bus(:,PD) > 0;
            dir_all = testCase.load_dir.('case39');
            dir = dir_all(:,idx_dir_ieee39);
            dir(~idx_nonzero_loads)=0;
            if sum(dir) == 0 || idx_dir_ieee39 == 31
                % The code does not currently support load increase at
                % nonzero loads.
                % The MATPOWER CPF takes long time for increase at bus 31
                % which is the slack bus.
                testCase.verifyEqual(1,1);
            else
                % Preparing the target case for Matpower CPF
                mpc_target = mpc;
                nonzero_loads = mpc_target.bus(:,PD) ~= 0;
                Q_P = mpc_target.bus(nonzero_loads,QD)./mpc_target.bus(nonzero_loads,PD);
                mpc_target.bus(:,PD) = mpc_target.bus(:,PD)+2*dir*mpc_target.baseMVA;
                mpc_target.bus(nonzero_loads,QD) = Q_P.*mpc_target.bus(nonzero_loads,PD);
                % Run the CPF with matpower
                [results,~] = runcpf(mpc,mpc_target,mpoption('out.all',0));
                % Extract the maximum loads
                max_loads_cpf = results.bus(:,PD);
                % Solve the maximum loadability limit without considering
                % reactive power limits
                results_mll = maxloadlim(mpc,dir,'use_qlim',0);
                % Extract the maximum loads
                max_loads_mll = results_mll.bus(:,PD);
                % We compare with a precision of 0.5MW
                testCase.verifyEqual(max_loads_mll,max_loads_cpf,'AbsTol',testCase.threshold_MW);
            end
        end
        
        function testAgainstTheoretical_case2(testCase)
            define_constants;
            % Loading the case
            mpc = loadcase('case2');
            dir = testCase.load_dir.('case2');
            res_maxloadlim = maxloadlim(mpc,dir);
            % Get nonzero loads
            idx_nonzero_loads = res_maxloadlim.bus(:,PD) > 0;
            max_loads = res_maxloadlim.bus(idx_nonzero_loads,PD)/res_maxloadlim.baseMVA;
            max_loads_theo = testCase.max_load_lims.('case2');
            testCase.verifyEqual(max_loads,max_loads_theo,'AbsTol',testCase.threshold_MW);
        end
        
        function testVarGen_case9(testCase,idx_dir_ieee9,gen_var_ieee9)
            define_constants;
            % Loading the case
            mpc = loadcase('case9');
            idx_nonzero_loads = mpc.bus(:,PD) > 0;
            dir_all = testCase.load_dir.('case9');
            dir_load = dir_all(:,idx_dir_ieee9);
            dir_load(~idx_nonzero_loads)=0;
            dir_var_gen_all = testCase.gen_dir.('case9');
            dir_var_gen = dir_var_gen_all(:,gen_var_ieee9);
            idx_var_gen = find(dir_var_gen);
            dir_var_gen = dir_var_gen(idx_var_gen);
            % Normalizing with respect to both loads and gens
            gen_load_dir = [dir_load;dir_var_gen];
            dir_load = dir_load/norm(gen_load_dir);
            dir_var_gen = dir_var_gen/norm(dir_var_gen);
            % Find MLL in the direction of load and gen increase
            results_with_gens = maxloadlim(mpc,dir_load,'verbose',0,'idx_var_gen',idx_var_gen,'dir_var_gen',dir_var_gen);
            % Set gens to their values in previous results and re-run in
            % load space only
            mpc2 = mpc;
            mpc2.gen(:,PG) = results_with_gens.gen(:,PG);
            dir_load2 = dir_load/norm(dir_load);
            % Find MLL in the direction of load and gen increase
            results_without_gens = maxloadlim(mpc2,dir_load2,'verbose',0);
            % Compare the maximum loads
            mll_with_gen = results_with_gens.bus(:,PD);
            mll_without_gen = results_without_gens.bus(:,PD);
            testCase.verifyEqual(mll_with_gen,mll_without_gen,'AbsTol',testCase.threshold_MW);
        end
        
        function testVarGen_case39(testCase,idx_dir_ieee39,gen_var_ieee39)
            define_constants;
            % Loading the case
            mpc = loadcase('case39');
            idx_nonzero_loads = mpc.bus(:,PD) > 0;
            dir_all = testCase.load_dir.('case39');
            dir_load = dir_all(:,idx_dir_ieee39);
            dir_load(~idx_nonzero_loads)=0;
            dir_var_gen_all = testCase.gen_dir.('case39');
            % Switching rows 1 and 2 (gens 30 and 31) because row 1
            % is zero and corresponds to the slack bus which is gen 31
            dir_var_gen_all([1 2],:) = dir_var_gen_all([2 1],:);
            dir_var_gen = dir_var_gen_all(:,gen_var_ieee39);
            idx_var_gen = find(dir_var_gen);
            dir_var_gen = dir_var_gen(idx_var_gen);
            % Normalizing with respect to both loads and gens
            gen_load_dir = [dir_load;dir_var_gen];
            dir_load = dir_load/norm(gen_load_dir);
            dir_var_gen = dir_var_gen/norm(dir_var_gen);
            if sum(dir_load) == 0
                % case of load increase in non-zero load
                testCase.verifyEqual(1,1);
            else
                % Find MLL in the direction of load and gen increase
                results_with_gens = maxloadlim(mpc,dir_load,'verbose',0,'idx_var_gen',idx_var_gen,'dir_var_gen',dir_var_gen);
                % Set gens to their values in previous results and re-run in
                % load space only
                mpc2 = mpc;
                mpc2.gen(:,PG) = results_with_gens.gen(:,PG);
                dir_load2 = dir_load/norm(dir_load);
                % Find MLL in the direction of load and gen increase
                results_without_gens = maxloadlim(mpc2,dir_load2,'verbose',0);
                % Compare the maximum loads
                mll_with_gen = results_with_gens.bus(:,PD);
                mll_without_gen = results_without_gens.bus(:,PD);
                testCase.verifyEqual(mll_with_gen,mll_without_gen,'RelTol',0.05);
            end
        end
    end
end