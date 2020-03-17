function Zdr = sgvm_getZdr(mpc, full)
%SGVM_GETZDR calculate driving point impedances
%   ZDR = SGVM_GETZDR(MPC, FULL)
%
%   Calculate the driving point impedances for the admittance matrix
%   formed from the MATPOWER case, MPC. If FULL is true  the full inverse
%   of the Ybus is calculated, otherwise a PCA version of the Ybus is used.
%
%   Input
%       MPC     matpower case
%       FULL    1 for full inversion of Ybus,
%               0 for PCA inversion
%   Output
%       ZDR     nb x 1 vector of complex driving point impedances

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

if nargin < 2
    full = 0;
end

nb = size(mpc.bus,1);
if ~all(mpc.bus(:,1) == (1:nb)')
    error(['sgvm_getZdr: bus numbers must be in internal order',...
 ' (consecutive starting at 1), consider using ext2int'])
end

Ybus = makeYbus(mpc);
if full
    Zdr = diag(Ybus\speye(nb));
else
    npca = min(100, round(0.1*nb));
    if have_fcn('octave')
        [U,S,V] = svds(Ybus, npca, 0);
    else
        [U,S,V] = svds(Ybus, npca, 'smallest');
    end
    if nb < 1e4
        Zdr = diag(V*(S\U'));
    else
        tmp = S\U';
        Zdr = zeros(nb,1);
        for k = 1:nb
            Zdr(k) = V(k,:)*tmp(:,k);
        end
    end
end
