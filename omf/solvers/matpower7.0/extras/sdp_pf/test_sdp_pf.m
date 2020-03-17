function success = test_sdp_pf(verbose, exit_on_fail)
%TEST_SDP_PF  Run all SDP_PF tests.
%   TEST_SDP_PF
%   TEST_SDP_PF(VERBOSE)
%   TEST_SDP_PF(VERBOSE, EXIT_ON_FAIL)
%   SUCCESS = TEST_SDP_PF(...)
%
%   Runs all of the SDP_PF tests. If VERBOSE is true (false by default),
%   it prints the details of the individual tests. If EXIT_ON_FAIL is true
%   (false by default), it will exit MATLAB or Octave with a status of 1
%   unless T_RUN_TESTS returns ALL_OK.
%
%   See also T_RUN_TESTS.

%   MATPOWER
%   Copyright (c) 2004-2019, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER/mx-sdp_pf.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-sdp_pf/ for more info.

if nargin < 2
    exit_on_fail = 0;
    if nargin < 1
        verbose = 0;
    end
end

tests = {};

if have_fcn('mosek') || have_fcn('sdpt3') || have_fcn('sedumi')
    tests{end+1} = 't_opf_sdpopf';
    tests{end+1} = 't_insolvablepf';
    tests{end+1} = 't_insolvablepf_limitQ';
    tests{end+1} = 't_insolvablepfsos';
    tests{end+1} = 't_insolvablepfsos_limitQ';
end
tests{end+1} = 't_testglobalopt';

%% run the tests
all_ok = t_run_tests( tests, verbose );

%% handle success/failure
if exit_on_fail && ~all_ok
    exit(1);
end
if nargout
    success = all_ok;
end
