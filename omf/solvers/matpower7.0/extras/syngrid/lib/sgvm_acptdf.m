function [Hf, Ht, threshold] = sgvm_acptdf(mpc, bidx, pca)
%SGVM_ACPTDF Calculate line sensitivitis at a given operating point.
%   [HF, HT, THRESHOLD] = SGVM_ACPTDF(MPC, BIDX, PCA)
%
%   We want:
%          [dPf; dQf]  = Hf*[dPbus; dQbus]  (1)
%   Hf is a 2nl x 2(nb-1) sensitivity matrix:
%          | dPf/dPbus     dPf/dQbus |
%    Hf =  |                         |
%          | dQf/dPbus     dQf/dQbus |
%   now,
%          [dPbus; dQbus] = J*[dVa ; dVm]
%   and,
%          [dPf; dQf] = Kf*[dVa ; dVm]
%   where,
%          | dPbus/dVa     dPbus/dVm |
%     J =  |                         |
%          | dQbus/dVa     dQbus/dVm |
%   and,
%          | dPf/dVa       dPf/dVm |
%    Kf =  |                       |
%          | dQf/dVa       dQf/dVm |
%   Then (1) can be expressed as
%     Kf = Hf*J -----> Hf = Kf*J^-1
%   Note that as presented here, these calculations are slack bus
%   dependent.
%
%   Inputs
%     MPC  - MATPOWER case (should be in internal indexing mode)
%     BIDX - branch ids to use (default is all branches)
%     PCA  - Number of principle components to use when inverting the Jacobian matrix.
%              0 - use the full jacobian
%              pca > 0 - use the 'pca' smallest singular values of J to estimate J^-1
%
%   Outputs
%     HF        - line sensitivities matrix using from end powers.
%     HT        - line sensitivities matrix using to end powers.
%     THRESHOLD - values with absolute value below THRESHOLD are set to 0.
%                 The THRESHOLD is 5% of the maximum magnitude in HF or HF and HT
%                 if both are returned.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

%% define indices
[PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
nb = size(mpc.bus,1);
nl = size(mpc.branch,1);

if any(mpc.bus(:,BUS_I) ~= (1:nb)')
    error('sgvm_acptdf: bus matrix needs to have consecutive bus numbering.')
end

if nargin < 3
    pca = 0;
    if nargin < 2
        bidx = (1:nl).';
    else
        nl = length(bidx);
    end
end
%% calculate derivatives at operating point
[Ybus, Yf, Yt] = makeYbus(mpc);
V = mpc.bus(:,VM).*exp(1i*mpc.bus(:,VA)*pi/180);
[dsf_dva, dsf_dvm, dst_dva, dst_dvm] = dSbr_dV(mpc.branch, Yf, Yt, V);
[dsbus_dva, dsbus_dvm] = dSbus_dV(Ybus,V);

%% form matrices and solve
nonslack = find(mpc.bus(:,BUS_TYPE) ~= REF);
% make Jacobian
J = [real(dsbus_dva(nonslack,nonslack)), real(dsbus_dvm(nonslack,nonslack));
     imag(dsbus_dva(nonslack,nonslack)), imag(dsbus_dvm(nonslack,nonslack))];
% make branch Jacobian
Kf = [real(dsf_dva(bidx,nonslack)), real(dsf_dvm(bidx,nonslack));
      imag(dsf_dva(bidx,nonslack)), imag(dsf_dvm(bidx,nonslack))];
Kt = [real(dst_dva(bidx,nonslack)), real(dst_dvm(bidx,nonslack));
      imag(dst_dva(bidx,nonslack)), imag(dst_dvm(bidx,nonslack))];

% solve for sensitivities.
Hf = sparse(2*nl, 2*nb);
if pca > 0
    [U,S,V] = svds(J,pca,'smallest');
    Hf(:,[nonslack; nb+nonslack]) = Kf * (V*(S\U'));
else
    Hf(:,[nonslack; nb+nonslack]) = Kf / J;
end
if nargout > 1
    Ht = sparse(2*nl, 2*nb);
    if pca
        Ht(:,[nonslack; nb+nonslack]) = Kt * (V*(S\U'));
    else
        Ht(:,[nonslack; nb+nonslack]) = Kt / J;
    end
end

% threshold
if nargout > 1
%   threshold = full(0.05*max(abs([Hf(:);Ht(:)])));
%     threshold = min(0.01, threshold);
    threshold = 0.05*max(max(abs(Hf), abs(Ht)),[], 2);
    if have_fcn('octave')
        Ht(full(abs(Ht)) < full(threshold)) = 0;
    else
        Ht(abs(Ht) < threshold) = 0;
    end
else
%   threshold = full(0.05*max(abs(Hf(:))));
%   threshold = min(0.01, threshold);
    threshold = 0.05*max(abs(Hf),[], 2);
end
if have_fcn('octave')
    Hf(full(abs(Hf)) < full(threshold)) = 0;
else
    Hf(abs(Hf) < threshold) = 0;
end
