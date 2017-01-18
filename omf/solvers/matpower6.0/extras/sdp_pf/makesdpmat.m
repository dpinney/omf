function [Yk,Yk_,Mk,Ylineft,Ylinetf,Y_lineft,Y_linetf,YL,YL_] = makesdpmat(mpc)
%MAKESDPMAT Creates the matrix functions used in the semidefinite 
%programming relaxation of the optimal power flow problem.
%   [YK,YK_,MK,YLINEFT,YLINETF,Y_LINEFT,Y_LINETF] = MAKESDPMAT(MPC)
%
%   Creates functions that return the matrices used in the semidefinite
%   programming relaxation of the optimal power flow problem.
%
%   Inputs:
%       MPC : MATPOWER case variable with internal indexing.
%
%   Outputs:
%       YK : Function to create the matrix for active power injection.
%           Yk(i) is the matrix corresponding to the active power injection
%           at bus i.
%       YK_ : Function to create the matrix for reactive power injection.
%           Yk_(i) is the matrix corresponding to the reactive power
%           injection at bus i.
%       MK : Function to create the matrix for the square of voltage
%           magnitude. Mk(i) is the matrix corresponding to the square of
%           the voltage magnitude at bus i.
%       YLINEFT : Function to create the matrix for the active power flow
%           on the specified line, measured from the "from" bus to the "to" 
%           bus. Ylineft(i) is the matrix corresponding to the active power
%           flow on the line mpc.branch(i,:).
%       YLINETF : Function to create the matrix for the active power flow
%           on the specified line, measured from the "to" bus to the "from" 
%           bus. Ylinetf(i) is the matrix corresponding to the active power
%           flow on the line mpc.branch(i,:).
%       Y_LINEFT : Function to create the matrix for the reactive power
%           flow on the specified line, measured from the "from" bus to the 
%           "to" bus. Ylineft(i) is the matrix corresponding to the
%           reactive power flow on the line mpc.branch(i,:).
%       Y_LINETF : Function to create the matrix for the reactive power
%           flow on the specified line, measured from the "to" bus to the
%           "from" bus. Ylineft(i) is the matrix corresponding to the
%           reactive power flow on the line mpc.branch(i,:).
%       YL : Function to create the matrix for the active power loss
%           on the specified line (included for completeness, 
%           not used in the OPF formulation)
%       YL_ : Function to create the matrix for the reactive power loss
%           on the specified line (included for completeness, 
%           not used in the OPF formulation)

%   MATPOWER
%   Copyright (c) 2013-2016, Power Systems Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% Setup

[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, ...
    TAP, SHIFT, BR_STATUS, PF, QF, PT, QT, MU_SF, MU_ST, ...
    ANGMIN, ANGMAX, MU_ANGMIN, MU_ANGMAX] = idx_brch;

mpc = loadcase(mpc);
nbus = size(mpc.bus,1);
Y = makeYbus(mpc);

emat = speye(nbus);
e = @(k) emat(:,k); % kth standard basis vector
Yk_small = @(k) e(k)*e(k).'*Y;

% Set tau == 0 to 1 (tau == 0 indicates nominal voltage ratio)
mpc.branch(mpc.branch(:,TAP) == 0,TAP) = 1;

%% Matrices used in SDP relaxation of OPF problem

Yk = @(k) (1/2)*[real(Yk_small(k) + Yk_small(k).') imag(Yk_small(k).' - Yk_small(k));
    imag(Yk_small(k) - Yk_small(k).') real(Yk_small(k) + Yk_small(k).')];

Yk_ = @(k) -(1/2)*[imag(Yk_small(k) + Yk_small(k).') real(Yk_small(k) - Yk_small(k).');
    real(Yk_small(k).' - Yk_small(k)) imag(Yk_small(k) + Yk_small(k).')];

Mk = @(k) blkdiag(e(k)*e(k).', e(k)*e(k).');


% For the line limit matrices, specify a line index corresponding to the
% entries in mpc.branch
gl = @(lineidx) real( 1 / (mpc.branch(lineidx,BR_R)+1i*mpc.branch(lineidx,BR_X))); % Real part of line admittance
bl = @(lineidx) imag( 1 / (mpc.branch(lineidx,BR_R)+1i*mpc.branch(lineidx,BR_X))); % Imaginary part of line admittance
bsl= @(lineidx) mpc.branch(lineidx,BR_B); % Line shunt susceptance
Rl = @(lineidx) mpc.branch(lineidx,BR_R);
Xl = @(lineidx) mpc.branch(lineidx,BR_X);

% tau (col TAP)
% theta (col SHIFT)
% gbcosft = g*cos(theta)+b*cos(theta+pi/2)
% gbsinft = g*sin(theta)+b*sin(theta+pi/2)
% gbcostf = g*cos(-theta)+b*cos(-theta+pi/2)
% gbsintf = g*sin(-theta)+b*sin(-theta+pi/2)

tau = @(lineidx) mpc.branch(lineidx,TAP); 
theta = @(lineidx) mpc.branch(lineidx,SHIFT)*pi/180;
gbcosft = @(lineidx) gl(lineidx)*cos(theta(lineidx)) + bl(lineidx)*cos(theta(lineidx)+pi/2);
gbsinft = @(lineidx) gl(lineidx)*sin(theta(lineidx)) + bl(lineidx)*sin(theta(lineidx)+pi/2);
gbcostf = @(lineidx) gl(lineidx)*cos(-theta(lineidx)) + bl(lineidx)*cos(-theta(lineidx)+pi/2);
gbsintf = @(lineidx) gl(lineidx)*sin(-theta(lineidx)) + bl(lineidx)*sin(-theta(lineidx)+pi/2);

Ylineft = @(lidx) 0.5*(sparse(    [mpc.branch(lidx,F_BUS)     mpc.branch(lidx,F_BUS)     mpc.branch(lidx,F_BUS)      mpc.branch(lidx,F_BUS)+nbus  mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus ], ...
                                  [mpc.branch(lidx,F_BUS)     mpc.branch(lidx,T_BUS)     mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus  mpc.branch(lidx,T_BUS)      mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [gl(lidx)/(tau(lidx)^2)     -gbcosft(lidx)/tau(lidx)   gbsinft(lidx)/tau(lidx)     gl(lidx)/(tau(lidx)^2)       -gbsinft(lidx)/tau(lidx)    -gbcosft(lidx)/tau(lidx)    ] ...
                                  ,2*nbus,2*nbus) + ...
                       sparse(    [mpc.branch(lidx,F_BUS)    mpc.branch(lidx,F_BUS)     mpc.branch(lidx,F_BUS)      mpc.branch(lidx,F_BUS)+nbus  mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus ], ...
                                  [mpc.branch(lidx,F_BUS)    mpc.branch(lidx,T_BUS)     mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus  mpc.branch(lidx,T_BUS)      mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [gl(lidx)/(tau(lidx)^2)    -gbcosft(lidx)/tau(lidx)   gbsinft(lidx)/tau(lidx)     gl(lidx)/(tau(lidx)^2)       -gbsinft(lidx)/tau(lidx)    -gbcosft(lidx)/tau(lidx)    ] ...
                                  ,2*nbus,2*nbus).');
                                                           
Y_lineft = @(lidx) 0.5*(sparse(     [mpc.branch(lidx,F_BUS)                mpc.branch(lidx,F_BUS)    mpc.branch(lidx,F_BUS)      mpc.branch(lidx,F_BUS)+nbus            mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus ], ...
                                    [mpc.branch(lidx,F_BUS)                mpc.branch(lidx,T_BUS)    mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus            mpc.branch(lidx,T_BUS)      mpc.branch(lidx,T_BUS)+nbus ], ...
                                    [-(bl(lidx)+bsl(lidx)/2)/(tau(lidx)^2) gbsinft(lidx)/tau(lidx)   gbcosft(lidx)/tau(lidx)     -(bl(lidx)+bsl(lidx)/2)/(tau(lidx)^2)  -gbcosft(lidx)/tau(lidx)    gbsinft(lidx)/tau(lidx)     ] ...
                                  ,2*nbus,2*nbus) + ...
                        sparse(     [mpc.branch(lidx,F_BUS)                mpc.branch(lidx,F_BUS)    mpc.branch(lidx,F_BUS)      mpc.branch(lidx,F_BUS)+nbus           mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus ], ...
                                    [mpc.branch(lidx,F_BUS)                mpc.branch(lidx,T_BUS)    mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus           mpc.branch(lidx,T_BUS)      mpc.branch(lidx,T_BUS)+nbus ], ...
                                    [-(bl(lidx)+bsl(lidx)/2)/(tau(lidx)^2) gbsinft(lidx)/tau(lidx)   gbcosft(lidx)/tau(lidx)     -(bl(lidx)+bsl(lidx)/2)/(tau(lidx)^2) -gbcosft(lidx)/tau(lidx)    gbsinft(lidx)/tau(lidx)     ] ...
                                  ,2*nbus,2*nbus).');

Ylinetf = @(lidx) 0.5*(sparse(    [mpc.branch(lidx,F_BUS)     mpc.branch(lidx,F_BUS)      mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,T_BUS) mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [mpc.branch(lidx,T_BUS)     mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,T_BUS)      mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,T_BUS) mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [-gbcostf(lidx)/tau(lidx)   -gbsintf(lidx)/tau(lidx)    gbsintf(lidx)/tau(lidx)     -gbcostf(lidx)/tau(lidx)    gl(lidx)               gl(lidx)                    ] ...
                                  ,2*nbus,2*nbus) + ...
                       sparse(    [mpc.branch(lidx,F_BUS)     mpc.branch(lidx,F_BUS)      mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,T_BUS) mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [mpc.branch(lidx,T_BUS)     mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,T_BUS)      mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,T_BUS) mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [-gbcostf(lidx)/tau(lidx)   -gbsintf(lidx)/tau(lidx)    gbsintf(lidx)/tau(lidx)     -gbcostf(lidx)/tau(lidx)    gl(lidx)               gl(lidx)                ] ...
                                  ,2*nbus,2*nbus).');
                              
Y_linetf = @(lidx) 0.5*(sparse(   [mpc.branch(lidx,F_BUS)    mpc.branch(lidx,F_BUS)      mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,T_BUS)  mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [mpc.branch(lidx,T_BUS)    mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,T_BUS)      mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,T_BUS)  mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [gbsintf(lidx)/tau(lidx)   -gbcostf(lidx)/tau(lidx)    gbcostf(lidx)/tau(lidx)     gbsintf(lidx)/tau(lidx)     -(bl(lidx)+bsl(lidx)/2) -(bl(lidx)+bsl(lidx)/2)     ] ...
                                  ,2*nbus,2*nbus) + ...
                       sparse(    [mpc.branch(lidx,F_BUS)    mpc.branch(lidx,F_BUS)      mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,F_BUS)+nbus mpc.branch(lidx,T_BUS)   mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [mpc.branch(lidx,T_BUS)    mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,T_BUS)      mpc.branch(lidx,T_BUS)+nbus mpc.branch(lidx,T_BUS)   mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [gbsintf(lidx)/tau(lidx)   -gbcostf(lidx)/tau(lidx)    gbcostf(lidx)/tau(lidx)     gbsintf(lidx)/tau(lidx)     -(bl(lidx)+bsl(lidx)/2)  -(bl(lidx)+bsl(lidx)/2)     ] ...
                                  ,2*nbus,2*nbus).');
                         
                              
% Matrices to calculate active and reactive power line losses
YL = @(lidx)          sparse(    [mpc.branch(lidx,F_BUS)    mpc.branch(lidx,F_BUS)      mpc.branch(lidx,F_BUS)+nbus      mpc.branch(lidx,F_BUS)+nbus   mpc.branch(lidx,T_BUS)  mpc.branch(lidx,T_BUS)  mpc.branch(lidx,T_BUS)+nbus  mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [mpc.branch(lidx,F_BUS)   mpc.branch(lidx,T_BUS)      mpc.branch(lidx,F_BUS)+nbus      mpc.branch(lidx,T_BUS)+nbus   mpc.branch(lidx,F_BUS)  mpc.branch(lidx,T_BUS)  mpc.branch(lidx,F_BUS)+nbus  mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [1                        -1                          1                                -1                            -1                      1                       -1                           1                           ] ...
                                  ,2*nbus,2*nbus) * Rl(lidx)*(gl(lidx)^2+bl(lidx)^2);
                              
YL_ = @(lidx)          sparse(    [mpc.branch(lidx,F_BUS)    mpc.branch(lidx,F_BUS)      mpc.branch(lidx,F_BUS)+nbus      mpc.branch(lidx,F_BUS)+nbus   mpc.branch(lidx,T_BUS)  mpc.branch(lidx,T_BUS)  mpc.branch(lidx,T_BUS)+nbus  mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [mpc.branch(lidx,F_BUS)    mpc.branch(lidx,T_BUS)      mpc.branch(lidx,F_BUS)+nbus      mpc.branch(lidx,T_BUS)+nbus   mpc.branch(lidx,F_BUS)  mpc.branch(lidx,T_BUS)  mpc.branch(lidx,F_BUS)+nbus  mpc.branch(lidx,T_BUS)+nbus ], ...
                                  [1                         -1                          1                                -1                            -1                      1                       -1                           1                           ] ...
                                  ,2*nbus,2*nbus) * Xl(lidx) * (gl(lidx)^2+bl(lidx)^2) + ...
                       -sparse(   [mpc.branch(lidx,F_BUS)    mpc.branch(lidx,F_BUS)+nbus   mpc.branch(lidx,T_BUS)   mpc.branch(lidx,T_BUS)+nbus   ], ...
                                  [mpc.branch(lidx,F_BUS)    mpc.branch(lidx,F_BUS)+nbus   mpc.branch(lidx,T_BUS)   mpc.branch(lidx,T_BUS)+nbus   ], ...
                                  [1                         1                             1                        1                             ] ...
                                  ,2*nbus,2*nbus) * bsl(lidx)/2;
