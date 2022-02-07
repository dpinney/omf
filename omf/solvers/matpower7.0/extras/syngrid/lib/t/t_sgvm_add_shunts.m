function t_sgvm_add_shunts(quiet)
%T_SGVM_ADD_SHUNTS  Tests for sgvm_add_shunts().

if nargin < 1
    quiet = 0;
end

%% turn off warnings
if have_fcn('octave')
    if have_fcn('octave', 'vnum') >= 4
        file_in_path_warn_id = 'Octave:data-file-in-path';
    else
        file_in_path_warn_id = 'Octave:load-file-in-path';
    end
    s1 = warning('query', file_in_path_warn_id);
    warning('off', file_in_path_warn_id);
end

t_begin(7, quiet);

define_constants;
%% set up a sample case
mpc = loadcase('case_ACTIVSg200');
e2i = sparse(mpc.bus(:,BUS_I), 1, 1:200);
mpc.bus(:,BUS_I) = e2i(mpc.bus(:,BUS_I));
mpc.branch(:, [F_BUS, T_BUS]) = e2i(mpc.branch(:, [F_BUS, T_BUS]));
mpc.gen(:,GEN_BUS) = e2i(mpc.gen(:,GEN_BUS));
mpc.bus(:, BS)  = 0; %remove shunts
mpc.bus(:,VMAX) = 1.03;
mpc.bus(:,VMIN) = 0.97;

opt = sgvm_shuntsopts();
%% tests
t = 'default run : ';
[out, bsh] = sgvm_add_shunts(mpc);
tmp = load('t_sgvm_shunts_default_run.mat');
t_is(bsh, tmp.bsh, 4, [t, 'bsh'])
t_ok(min(abs(bsh(bsh~=0))) >= opt.tmag, [t, 'min abs(bsh)'])
t_ok(min(out.bus(:,VM)) >= 0.95 + opt.shift_in, [t, 'VMIN'])
t_ok(max(out.bus(:,VM)) <= 1.05 - opt.shift_in, [t, 'VMAX'])

t = 'altered options : ';
opt = struct('shift_in', opt.shift_in+0.005, 'tmag', min(abs(bsh(bsh~=0))) + 0.1);
[out, bsh] = sgvm_add_shunts(mpc, [], opt);
t_ok(min(abs(bsh(bsh~=0))) >= opt.tmag, [t, 'min abs(bsh)'])
t_ok(min(out.bus(:,VM)) >= 0.95 + opt.shift_in, [t, 'VMIN'])
t_ok(max(out.bus(:,VM)) <= 1.05 - opt.shift_in, [t, 'VMAX'])

t_end

%% turn warnings back on
if have_fcn('octave')
    warning(s1.state, file_in_path_warn_id);
end
