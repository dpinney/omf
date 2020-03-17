function s_phi = sg_random_stable (a_stab, b_stab, g_stab, d_stab, mm, nn)
%SG_RANDOM_STABLE  create MM x NN matrix of random numbers from stable dist
%   S_PHI = SG_RANDOM_STABLE(A_STAB, B_STAB, G_STAB, D_STAB, MM, NN)
%
%   Input:
%       a_stab - alpha, exponent
%       b_stab - beta, skewness
%       g_stab - gama, scale parameter
%       d_stab - delta, location parameter
%       mm,nn  - a mm by nn matrix
%
%   Output:
%       s_phi - matrix (mm by nn) of random numbers based on stable
%       distribution

%   SynGrid
%   Copyright (c) 2018, Electric Power and Energy Systems (EPES) Research Lab
%   by Hamidreza Sadeghian and Zhifang Wang, Virginia Commonwealth University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

W = - log( rand(mm,nn) );
V = pi/2 * (2*rand(mm,nn) - 1);
Cnst = b_stab * tan(pi*a_stab/2);
B = atan( Cnst );
S = (1 + Cnst * Cnst).^(1/(2*a_stab));
Rand = S * sin( a_stab*V + B ) ./ ( cos(V) ).^(1/a_stab) .*( cos( (1-a_stab) * V - B ) ./ W ).^((1-a_stab)/a_stab);
s_phi= g_stab * Rand + d_stab;
