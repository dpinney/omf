function t_sgvm_data2mpc(quiet)
%T_SGVM_DATA2MPC  Tests for sgvm_data2mpc().

if nargin < 1
    quiet = 0;
end

t_begin(11, quiet);
define_constants;
data = sgvm_mpc2data(loadcase('case_ACTIVSg2000'));
[~,topo] = sgvm_mpc2data(loadcase('case118'));

t = 'default options : ';
mpc = sgvm_data2mpc(data, topo);
t_ok( all(ismember(mpc.branch(:,[BR_R, BR_X, BR_B, RATE_A, TAP, SHIFT]), ...
      [data.branch(:,1:3), round(data.branch(:,4)), data.branch(:,5:6)], 'rows')), [t, 'branch']);
t_ok( all(ismember(mpc.gen(:,[QMAX, QMIN, PMAX, PMIN]), data.gen(:,2:end), 'rows')), [t, 'gen']);
t_ok( ~all(ismember(mpc.bus(:,[PD, QD]), data.load, 'rows')), [t, 'load']);

t = 'node direct : ';
opt = struct('node', 'direct');
mpc = sgvm_data2mpc(data, topo, opt);
t_ok( all(ismember(mpc.branch(:,[BR_R, BR_X, BR_B, RATE_A, TAP, SHIFT]), ...
      [data.branch(:,1:3), round(data.branch(:,4)), data.branch(:,5:6)], 'rows')), [t, 'branch']);
t_ok( all(ismember(mpc.gen(:,[QMAX, QMIN, PMAX, PMIN]), data.gen(:,2:end), 'rows')), [t, 'gen']);
t_ok( all(ismember(mpc.bus(:,[PD, QD]), data.load, 'rows')), [t, 'load']);
% test correct generator load pairing
tmpref = zeros(size(data.gen,1),6);
for k = 1:size(data.gen,1)
  tmpref(k,:) = [data.gen(k,2:end), data.load(data.gen(k,1),:)];
end
tmp = zeros(size(mpc.gen,1), 6);
for k = 1:size(mpc.gen,1)
  tmp(k,:) = [mpc.gen(k,[QMAX, QMIN, PMAX, PMIN]), mpc.bus(mpc.gen(k,GEN_BUS),[PD, QD])];
end
t_ok( all(ismember(tmp, tmpref, 'rows')), [t, 'load + gen'])

t = 'node direct (no genbus) : ';
opt = struct('node', 'direct', 'usegenbus', 0);
mpc = sgvm_data2mpc(data, topo, opt);
t_ok( all(ismember(mpc.branch(:,[BR_R, BR_X, BR_B, RATE_A, TAP, SHIFT]), ...
      [data.branch(:,1:3), round(data.branch(:,4)), data.branch(:,5:6)], 'rows')), [t, 'branch']);
t_ok( all(ismember(mpc.gen(:,[QMAX, QMIN, PMAX, PMIN]), data.gen(:,2:end), 'rows')), [t, 'gen']);
t_ok( all(ismember(mpc.bus(:,[PD, QD]), data.load, 'rows')), [t, 'load']);
% test generator load pairing
tmpref = zeros(size(data.gen,1),6);
for k = 1:size(data.gen,1)
  tmpref(k,:) = [data.gen(k,2:end), data.load(data.gen(k,1),:)];
end
tmp = zeros(size(mpc.gen,1), 6);
for k = 1:size(mpc.gen,1)
  tmp(k,:) = [mpc.gen(k,[QMAX, QMIN, PMAX, PMIN]), mpc.bus(mpc.gen(k,GEN_BUS),[PD, QD])];
end
t_ok( ~all(ismember(tmp, tmpref, 'rows')), [t, 'load + gen'])

t_end
