function [A] = addToA(sdpmat, Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq, A, svar, maxclique)
%ADDTOA Adds a term to the decomposed A matrices
%   [A] = ADDTOA(SDPMAT, WREF_DD, WREF_QQ, WREF_DQ, MATIDX_DD, MATIDX_QQ, MATIDX_DQ, A, SDPVAR, MAXCLIQUE)
%
%   Adds a matrix multiplied by a sdp variable to the A matrices.
%
%   Inputs:
%       SDPMAT : A 2*nbus by 2*nbus matrix.
%       WREF_DD : Matrix with three columns. The first column is a 
%           numbering 1:size(Wref_dd,1). The second and third columns 
%           indicate the row and column indices of the elements of the 
%           matrix sdpmat, with the row of Wref_dd corresponding to the 
%           index of matidx_dd. That is, the element of sdpmat located in 
%           row Wref_dd(i,1), column Wref_dd(i,2) corresponds to 
%           matidx_dd(i).
%       WREF_QQ : Similar to Wref_dd, except for the qq entries of sdpmat.
%       WREF_DQ : Similar to Wref_dd, except for the dq entries of sdpmat.
%       MATIDX_DD : Matrix with three columns. Row i of matidx_dd indicates
%           the location of sdpmat(Wref_dd(i,1), Wref_dd(i,2)). The first
%           column indicates the index of the corresponding matrix. The
%           second and third columns indicate the row and column,
%           respectively, of the corresponding matrix. 
%       MATIDX_QQ : Similar to matidx_dd, except corresponding to the qq 
%           entries of sdpmat.
%       MATIDX_DQ : Similar to matidx_dd, except corresponding to the dq 
%           entries of sdpmat.
%       A : Cell array of decomposed A matrices corresponding to maxclique.
%       SVAR : SDP variable (sdpvar) that will be multiplied by sdpmat and
%           added to the decomposed A matrices.
%       MAXCLIQUE : Cell array of the buses in each maximal clique.
%
%   Outputs:
%       A : Cell array of decomposed A matrices with addition of
%       svar*sdpmat.

%   MATPOWER
%   Copyright (c) 2013-2019, Power Systems Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%
%   This file is part of MATPOWER/mx-sdp_pf.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See https://github.com/MATPOWER/mx-sdp_pf/ for more info.

[Ykvec] = mat2vec(sdpmat, Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq);

Amats = unique(Ykvec(:,1));
for m=1:length(Amats)
    Ykvec_rows = find(Ykvec(:,1) == Amats(m));
    A{Amats(m)} = A{Amats(m)} + svar * sparse(Ykvec(Ykvec_rows,2),Ykvec(Ykvec_rows,3),Ykvec(Ykvec_rows,4),2*length(maxclique{Amats(m)}),2*length(maxclique{Amats(m)}));
end
