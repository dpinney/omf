function qcqp_opf_test(casedata)
%QCQP_OPF_TEST Testing QCQP_OPF program with CVX 2.1 and SeDuMi 1.3
%   QCQP_OPF_TEST( CASEDATA )
%
%   Input:
%       CASEDATA : either a MATPOWER case struct or a string containing
%           the name of the file with the case data
%           (see also CASEFORMAT and LOADCASE)
%
%   NOTE: Requires CVX and SeDuMi.

%   MATPOWER
%   Copyright (c) 2016, Power Systems Engineering Research Center (PSERC)
%   by Cedric Josz, Jean Maeght, Stephane Fliscounakis, and Patrick Panciatici
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.


%% upload complex data using qcqp_opf (MODEL = 0)
[nVAR, nEQ, nINEQ, C, c, A, a, B, b, S] = qcqp_opf(casedata);

% compute convex relaxation of ACOPF using uploaded data
cvx_begin sdp
    cvx_precision best
    cvx_solver sedumi
    variable Z(nVAR,nVAR) hermitian
    
    minimize( vec(C)'*vec(Z) + c ) % objective function
    
    for k = 1:nEQ
        vec((A{k}+A{k}')/2)'*vec(Z)      == real(a(k)); % real part
        vec((A{k}-A{k}')/(2*1i))'*vec(Z) == imag(a(k)); % imaginary part
    end
    
    for k = 1:nINEQ
        if B{k}' == B{k} % checking whether B{k} is Hermitian
            vec(B{k})'*vec(Z) <= b(k); % inequality constraints
        else
            vec((B{k}+B{k}')/2)'*vec(Z)      <= real(b(k)); % real part
            vec((B{k}-B{k}')/(2*1i))'*vec(Z) <= imag(b(k)); % imaginary part 
        end
    end
    
    Z >= 0;
cvx_end

%% upload Hermitian data using qcqp_opf (MODEL = 1)
[nVAR, nEQ, nINEQ, C, c, A, a, B, b, S] = qcqp_opf(casedata,1);

% compute convex relaxation of ACOPF using uploaded data
cvx_begin sdp
    cvx_precision best
    cvx_solver sedumi
    variable Z(nVAR,nVAR) hermitian
    
    minimize( vec(C)'*vec(Z) + c ) % objective function
    
    for k = 1:nEQ
        vec(A{k})'*vec(Z) == a(k); % equality constraints
    end
     
    for k = 1:nINEQ
        vec(B{k})'*vec(Z) <= b(k); % inequality constraints
    end
    
    Z >= 0;
cvx_end

%% upload symmetric data using qcqp_opf (MODEL = 2)
[nVAR, nEQ, nINEQ, C, c, A, a, B, b, S] = qcqp_opf(casedata,2);

% compute convex relaxation of ACOPF using uploaded data
cvx_begin sdp
    cvx_precision best
    cvx_solver sedumi
    variable Z(nVAR,nVAR) symmetric
    
    minimize( vec(C)'*vec(Z) + c ) % objective function
    
    for k = 1:nEQ
        vec(A{k})'*vec(Z) == a(k); % equality constraints
    end
     
    for k = 1:nINEQ
        vec(B{k})'*vec(Z) <= b(k); % inequality constraints
    end
    
    Z >= 0;
cvx_end
