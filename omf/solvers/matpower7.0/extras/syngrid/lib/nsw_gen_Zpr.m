function [Zpr] = nsw_gen_Zpr(Zpr_pars, ms)
% generate the line impedances and form the network admittance matrix
% Input:
%   Zpr_pars - random variable model parameters for Zpr;
%   ms - the link numbers [m1,m2,m3]
%         m1 - total number of local links
%         m2 - total number of rewires inside islands
%         m3 - total number of lattice links between islands
% Output:
%   Zpr - line impedance vector (magnitude);
% by wzf, 2009

%   SynGrid
%   Copyright (c) 2009, 2017-2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

m1 = ms(1); m2 = ms(2); m3 = ms(3);
Zprs = Zpr_rnd(Zpr_pars, sum(ms)); % generate line impedances
Zprs = sort(Zprs,'descend');

Zprs_m1 = Zprs(1:m1); % local links
tmp = randperm(m1); Zprs_m1 = Zprs_m1(tmp);

Zprs_m2 = Zprs(m1+1:m1+m2); % rewiring links
tmp = randperm(m2); Zprs_m2 = Zprs_m2(tmp);

if(m3 > 0)
    Zprs_m3 = Zprs(m1+m2+1:sum(ms)); % lattice connection links
    tmp = randperm(m3); Zprs_m3 = Zprs_m3(tmp);
else
    Zprs_m3 = [];
end

Zpr = [Zprs_m1; Zprs_m2; Zprs_m3];
pos = find(Zpr<1e-6);
if(~isempty(pos))
    Zpr(pos) = 1e-6;
end

%--------------------------------------------------------------------------
%--------------------------------------------------------------------------
function yout = Zpr_rnd(Zpr_pars, m)
% given the random Var model parameter for line impedances Zpr, generate a
% set of sample data.
% Inputs:
%   Zpr_pars - line impedance parameters,
%               include {model name, model pars}
%   m - total number of line impedances
%Outputs:
%   yout - vector of line impedances (m by 1)
%
% by wzf, 2009


rv_model = Zpr_pars{1};
rv_pars = Zpr_pars{2};

% switch rv_model
%     case 'GAMMA'
%         a = rv_pars(1); b = rv_pars(2);
%         yout = gamrnd(a,b,m,1);
%     case 'GP'
%         k = rv_pars(1); d = rv_pars(2); t = rv_pars(3);
%         yout = gprnd(k,d,t,m,1);
%     case 'LOGN'
%         mu = rv_pars(1); d = rv_pars(2);
%         yout = lognrnd(mu,d,m,1);
%     case 'LOGN-clip'
        mu = rv_pars(1); d = rv_pars(2); Zmax = rv_pars(3);
        yout = lognclip_rnd(mu,d,Zmax, m,1);
%     case 'DPLN'
%         a = rv_pars(1); b = rv_pars(2);
%         mu = rv_pars(3); d = rv_pars(4);
%         yout = dpln_rnd(a,b,mu,d, m,1);
%     case 'DPLN-clip'
%         a = rv_pars(1); b = rv_pars(2);
%         mu = rv_pars(3); d = rv_pars(4); Zmax = rv_pars(5);
%         yout = dplnclip_rnd(a,b,mu,d, Zmax, m,1);
%     otherwise
%         disp(['There is not a Zpr model as "', rv_model,'" designed in this program!']);
%         yout = [];
% end

%--------------------------------------------------------------------------
%--------------------------------------------------------------------------
function yout = lognclip_rnd(mu,d,Zmax, m,n)
% generate sample data with distribution of LogNormal-clipped
y = sg_lognrnd(mu,d,m,n);
yout = Zmax*(1-exp(-y/Zmax));

%--------------------------------------------------------------------------
function yout = dplnclip_rnd(a,b,mu,d, Zmax, m,n)
% generate sample data with distribution of DPLN-clip
y = dpln_rnd(a,b,mu,d,m,n);
yout = Zmax*(1-exp(-y/Zmax));

%--------------------------------------------------------------------------
function yout = dpln_rnd(alph,bta,mu,tau, m,n)
% generate sample data with distribution of DPLN
pr = bta/(alph+bta);
z = binornd(1,pr,m,n);
ug = normrnd(mu,tau,m,n);
wg = (z+(z-1)*alph/bta).*sg_exprnd(1/alph,m,n); % note: Matlab EXP-pdf use 1/alph
yout = exp(ug+wg);
