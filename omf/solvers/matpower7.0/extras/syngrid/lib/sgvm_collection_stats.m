function sgvm_collection_stats(obj, field)
%SGVM_COLLECTION_STATS prints statistics for an array of mpc cases.
%   SGVM_COLLECTION_STATS(OBJ, FIELD)
%
%   Inputs
%     OBJ - object containting a collection of MATPOWER cases
%           i.e SGVM_GENERATIONCLASS or SGVM_SOLNSTASH
%     FIELD - the property of OBJ that contains a cell array of MATPOWER cases

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if nargin == 1
    field = 'inds';
end
fprintf(['===========================', repmat('===========', 1, length(obj.(field))), '\n']);
tmp  = cellfun(@(x) x.id(1:6), obj.(field), 'UniformOutput', false);
stmp = sprintf(['Ind #(id)                 |', repmat('%%2.1d(%6s)|',1, length(obj.(field))), '\n'],tmp{:});
fprintf(stmp, 1:length(obj.(field)));
%fprintf(['Ind #                     |', repmat('%10.1d|',1, length(obj.(field))), '\n'],...
%    1:length(obj.(field)));
fprintf(['--------------------------|', repmat('----------|', 1, length(obj.(field))), '\n']);

tmp  = cellfun(@(x) x.call, obj.(field), 'UniformOutput', false);
stmp = sprintf(['From Generation           |', repmat('%%3.1d%7s|', 1, length(obj.(field))), '\n'],tmp{:});
fprintf(stmp, cellfun(@(x) x.gen, obj.(field)));
fprintf(['Success flag              |', repmat('%10.1d|',1, length(obj.(field))), '\n'],...
    cellfun(@(x) double(x.mpc.success), obj.(field)));
fprintf(['Objective                 |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
    cellfun(@(x) x.mpc.f, obj.(field)));
fprintf(['---------------------     |', repmat('      ----|', 1, length(obj.(field))), '\n']);
tmpcost = zeros(1, length(obj.(field)));
fprintf(['  Generation Cost         |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
    cellfun(@(x) sum(totcost(x.mpc.gencost, x.mpc.gen(:, 2))), obj.(field)));
tmpcost = tmpcost + cellfun(@(x) sum(totcost(x.mpc.gencost, x.mpc.gen(:, 2))), obj.(field));
if isfield(obj.(field){1}.mpc, 'softlims')
    fprintf(['  Line Violation Cost     |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
        cellfun(@(x) x.mpc.softlims.RATE_A.cost(1)*sum(x.mpc.softlims.RATE_A.overload), obj.(field)));
     tmpcost = tmpcost + cellfun(@(x) x.mpc.softlims.RATE_A.cost(1)*sum(x.mpc.softlims.RATE_A.overload), obj.(field));
    fprintf(['  VMAX Violation Cost     |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
        cellfun(@(x) x.mpc.softlims.VMAX.cost(1)*sum(x.mpc.softlims.VMAX.overload), obj.(field)));
     tmpcost = tmpcost + cellfun(@(x) x.mpc.softlims.VMAX.cost(1)*sum(x.mpc.softlims.VMAX.overload), obj.(field));
    fprintf(['  VMIN Violation Cost     |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
        cellfun(@(x) x.mpc.softlims.VMIN.cost(1)*sum(x.mpc.softlims.VMIN.overload), obj.(field)));
     tmpcost = tmpcost + cellfun(@(x) x.mpc.softlims.VMIN.cost(1)*sum(x.mpc.softlims.VMIN.overload), obj.(field));
    if ~strcmp(obj.(field){1}.mpc.softlims.QMAX.hl_mod, 'none')
        fprintf(['  QMAX Violation Cost     |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
            cellfun(@(x) x.mpc.softlims.QMAX.cost(1)*sum(x.mpc.softlims.QMAX.overload), obj.(field)));
             tmpcost = tmpcost + cellfun(@(x) x.mpc.softlims.QMAX.cost(1)*sum(x.mpc.softlims.QMAX.overload), obj.(field));
        fprintf(['  QMIN Violation Cost     |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
            cellfun(@(x) x.mpc.softlims.QMIN.cost(1)*sum(x.mpc.softlims.QMIN.overload), obj.(field)));
         tmpcost = tmpcost + cellfun(@(x) x.mpc.softlims.QMIN.cost(1)*sum(x.mpc.softlims.QMIN.overload), obj.(field));
    end
     try
        if ~strcmp(obj.(field){1}.mpc.softlims.PMAX.hl_mod, 'none')
            fprintf(['  PMAX Violation Cost     |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
                cellfun(@(x) x.mpc.softlims.PMAX.cost(1)*sum(x.mpc.softlims.PMAX.overload), obj.(field)));
                 tmpcost = tmpcost + cellfun(@(x) x.mpc.softlims.PMAX.cost(1)*sum(x.mpc.softlims.PMAX.overload), obj.(field));
            fprintf(['  PMIN Violation Cost     |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
                cellfun(@(x) x.mpc.softlims.PMIN.cost(1)*sum(x.mpc.softlims.PMIN.overload), obj.(field)));
            tmpcost = tmpcost + cellfun(@(x) x.mpc.softlims.PMIN.cost(1)*sum(x.mpc.softlims.PMIN.overload), obj.(field));
        end
     catch
    end
end
fprintf(['---------------------     |', repmat('      ----|', 1, length(obj.(field))), '\n']);
fprintf(['        Component Sum     |', repmat('%10.3g|',1, length(obj.(field))), '\n'], tmpcost);
fprintf(['--------------------------|', repmat('----------|', 1, length(obj.(field))), '\n']);
fprintf(['Min LMP                   |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
    cellfun(@(x) min(x.mpc.bus(:,14)), obj.(field)));
fprintf(['Max LMP                   |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
    cellfun(@(x) max(x.mpc.bus(:,14)), obj.(field)));
fprintf(['Avg LMP                   |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
    cellfun(@(x) mean(x.mpc.bus(:,14)), obj.(field)));
if isfield(obj.(field){1}.mpc, 'softlims')
         fprintf(['--------------------------|', repmat('----------|', 1, length(obj.(field))), '\n']);
    fprintf(['max line violations [MVA] |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
        cellfun(@(x) max(x.mpc.softlims.RATE_A.overload), obj.(field)));
    fprintf(['# line violations         |', repmat('%10.1d|',1, length(obj.(field))), '\n'],...
        cellfun(@(x) sum(x.mpc.softlims.RATE_A.overload > 1e-4), obj.(field)));
    fprintf(['Max |V| [p.u]             |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
        cellfun(@(x) max(x.mpc.bus(:,8)), obj.(field)));
    fprintf(['Min |V| [p.u]             |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
    cellfun(@(x) min(x.mpc.bus(:,8)), obj.(field)));
    if ~strcmp(obj.(field){1}.mpc.softlims.QMAX.hl_mod, 'none')
        fprintf(['Total up MVAr support     |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
            cellfun(@(x) sum(x.mpc.softlims.QMAX.overload), obj.(field)));
        fprintf(['Total down MVAr support   |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
            cellfun(@(x) sum(x.mpc.softlims.QMIN.overload), obj.(field)));
    end
     try
        if ~strcmp(obj.(field){1}.mpc.softlims.PMAX.hl_mod, 'none')
            fprintf(['Total up MW support       |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
                cellfun(@(x) sum(x.mpc.softlims.PMAX.overload), obj.(field)));
            fprintf(['Total down MW support     |', repmat('%10.3g|',1, length(obj.(field))), '\n'],...
                cellfun(@(x) sum(x.mpc.softlims.PMIN.overload), obj.(field)));
        end
    catch
    end
end
fprintf(['===========================', repmat('===========', 1, length(obj.(field))), '\n']);
end
