function success = test_smartmarket(verbose, exit_on_fail)
%TEST_SMARTMARKET  Run all MATPOWER smartmarket tests.
%   TEST_SMARTMARKET
%   TEST_SMARTMARKET(VERBOSE)
%   TEST_SMARTMARKET(VERBOSE, EXIT_ON_FAIL)
%   SUCCESS = TEST_SMARTMARKET(...)
%
%   Runs all MATPOWER smartmarket tests. If VERBOSE is true (false by default),
%   it prints the details of the individual tests. If EXIT_ON_FAIL is true
%   (false by default), it will exit MATLAB or Octave with a status of 1
%   unless T_RUN_TESTS returns ALL_OK.
%
%   See also T_RUN_TESTS.

%   MATPOWER
%   Copyright (c) 2004-2019, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of MATPOWER Extras.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/matpower-extras for more info.

if nargin < 2
    exit_on_fail = 0;
    if nargin < 1
        verbose = 0;
    end
end

tests = {};

%% smartmarket tests
tests{end+1} = 't_off2case';
if have_fcn('minopf')
    tests{end+1} = 't_auction_minopf';
end
tests{end+1} = 't_auction_mips';
if have_fcn('pdipmopf')
    tests{end+1} = 't_auction_tspopf_pdipm';
end
tests{end+1} = 't_runmarket';

%% run the tests
all_ok = t_run_tests( tests, verbose );

%% handle success/failure
if exit_on_fail && ~all_ok
    exit(1);
end
if nargout
    success = all_ok;
end
