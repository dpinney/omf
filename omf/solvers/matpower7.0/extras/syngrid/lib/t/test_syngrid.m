function success = test_syngrid(verbose, exit_on_fail)
%TEST_SYNGRID  Run all SynGrid tests.
%   TEST_SYNGRID
%   TEST_SYNGRID(VERBOSE)
%   TEST_SYNGRID(VERBOSE, EXIT_ON_FAIL)
%   SUCCESS = TEST_SYNGRID(...)
%
%   Runs all of the SynGrid tests. If VERBOSE is true (false by default),
%   it prints the details of the individual tests. If EXIT_ON_FAIL is true
%   (false by default), it will exit MATLAB or Octave with a status of 1
%   unless T_RUN_TESTS returns ALL_OK.
%
%   See also T_RUN_TESTS.

%   SynGrid
%   Copyright (c) 2017-2018, Power Systems Engineering Research Center (PSERC)
%   by Ray Zimmerman, PSERC Cornell
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if nargin < 2
    exit_on_fail = 0;
    if nargin < 1
        verbose = 0;
    end
end

tests = {};

%% SynGrid tests
tests{end+1} = 't_sg_options';
tests{end+1} = 't_sgvm_add_shunts';
tests{end+1} = 't_sgvm_data2mpc';
tests{end+1} = 't_syngrid';
tests{end+1} = 't_syngrid_vm';

%% run the tests
all_ok = t_run_tests( tests, verbose );

%% handle success/failure
if exit_on_fail && ~all_ok
    exit(1);
end
if nargout
    success = all_ok;
end
