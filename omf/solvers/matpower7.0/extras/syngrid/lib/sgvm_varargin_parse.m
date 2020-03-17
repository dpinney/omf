function var = sgvm_varargin_parse(vargs, str, default)
%SGVM_VARARGIN_PARSE parses VARARGIN inputs
%   VAR = SGVM_VARARGIN_PARSE(VARGS, STR, DEFAULT)
%
%   Assuming key-value pairs, SGVM_VARARGIN_PARSE searches for key STR.
%   If STR is found in VARARGIN, the value in the subsequent index is
%   returned in VAR. Otherwise the DEFAULT is used.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

idx = find(strcmp(vargs, str), 1);
if ~isempty(idx)
    var = vargs{idx+1};
else
    var = default;
end
