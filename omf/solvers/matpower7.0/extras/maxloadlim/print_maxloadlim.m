function print_maxloadlim(mpc,results)
% PRINT_MAXLOADLIM(MPC,RESULTS) prints the results in RESULTS of the 
% maximum loadability problems defined from the base case MPC.

%   MATPOWER
%   Copyright (c) 2015-2016, Power Systems Engineering Research Center (PSERC)
%   by Camille Hamon
%
%   This file is part of MATPOWER/mx-maxloadlim.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-maxloadlim/ for more info.

define_constants;

% Print some global information about the parameters and results of the
% maximum loadability limit problem
fprintf('\n');
fprintf('=======================================\n');
fprintf('      Maximum loadability problem\n');
fprintf('=======================================\n');
fprintf('The stability margin is %.2f MW\n',results.stab_marg*results.baseMVA);
fprintf('The type of bifurcation is %s (%s).\n',...
    results.bif.full_name,results.bif.short_name);
if strcmp(results.bif.short_name,'LIB')
    fprintf('Generator responsible for LIB: Gen %d connected at bus %d\n',...
        results.bif.gen_sll,results.gen(results.bif.gen_sll,GEN_BUS));
end
fprintf('\n--------------------------------------------------\n');
fprintf('   Bus nb    Direction     Load at MLL    Voltages \n');
fprintf('   ------    ---------     -----------    --------\n');
for i = 1:size(results.bus,1)
    fprintf('   %4d      %.2f         %8.2f         %4.3f\n',...
        results.bus(i,BUS_I),results.dir_mll(i),results.bus(i,PD),results.bus(i,VM));
end

% Print some global information about the generators and their limits
% First we extract the original voltage set points of the generators
gen_v_set = mpc.gen(:,VG);

fprintf('\n');
fprintf('=============================================================\n');
fprintf('Reactive power production and voltages at the generators\n');
fprintf('=============================================================\n');
fprintf(' Bus nb       Qgen        Qmin        Qmax       Vm      Vref\n');
fprintf('--------    --------    --------    --------    -----    -----\n');
for i = 1:size(results.gen,1)
    fprintf(' %4d       %8.2f    %8.2f    %8.2f    %4.3f    %4.3f',...
        results.gen(i,GEN_BUS),results.gen(i,QG),results.gen(i,QMIN),results.gen(i,QMAX),...
        results.bus(results.gen(i,GEN_BUS),VM),gen_v_set(i));
    if results.bus(results.gen(i,GEN_BUS),BUS_TYPE) == REF
        fprintf('    REF');
    end
    if strcmp(results.bif.short_name,'LIB') && any(results.bif.gen_sll == i)
        fprintf('    LIB');
    end
    fprintf('\n');
end
