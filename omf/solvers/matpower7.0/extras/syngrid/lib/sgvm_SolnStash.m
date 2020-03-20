classdef sgvm_SolnStash < handle
%SGVM_SOLNSTASH collection of successfully solved SGVM_INDCLASS object.
%   S = SGVM_SOLNSTASH(N) sets up a stash object that will hold N individuals
%   i.e, SGVM_INDCLASS objects.
%
%   The SGVM_SOLNSTASH is a helper class that keeps the best n individuals.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

    properties
        size
        inds
        ids
        count
        maxobj
    end
    methods
        function obj = sgvm_SolnStash(n)
            obj.size = n;
            obj.inds = cell(1,n);
            obj.ids  = cell(1,n);
            obj.count = 0;
            obj.maxobj = Inf;
        end

        function update(obj, inds)
            for k = 1:length(inds)
            if (inds{k}.mpc.f < obj.maxobj) && ~ismember(inds{k}.id, obj.ids(1:obj.count))
                if obj.count < obj.size
                        obj.count = obj.count + 1;
                    end
                    obj.inds{obj.count} = inds{k};
                    obj.ids{obj.count}  = inds{k}.id;
                end
                obj.sort();
                if obj.count == obj.size
                    obj.maxobj = obj.inds{end}.mpc.f;
                end
            end
        end

        function obj = sort(obj)
            [~, tmp] = sort(cellfun(@(x) x.mpc.f, obj.inds(1:obj.count)));
            obj.inds(1:obj.count) = obj.inds(tmp);
            obj.ids(1:obj.count)  = obj.ids(tmp);
        end

        function stats(obj)
            sgvm_collection_stats(obj, 'inds');
        end
    end
end
