function [sdpvec]=mat2vec(sdpmat, Wref_dd, Wref_qq, Wref_dq, matidx_dd, matidx_qq, matidx_dq)
%MAT2VEC Converts a SDP matrix into a a list form used in the matrix
%completion decomposition.
%   [SDPVEC] = MAT2VEC(SDPMAT, WREF_DD, WREF_QQ, WREF_DQ, MATIDX_DD,MATIDX_QQ, MATIDX_DQ)
%
%   Used in the formation of the matrix completion decomposition for the
%   semidefinite programming relaxation of the optimal power flow. Converts
%   a 2*nbus by 2*nbus symmetric matrix sdpmat into a list form. For each
%   nonzero element of sdpmat, the list form in sdpvec gives the
%   appropriate matrix, the location in the matrix, and the value for that
%   element.
%
%   Inputs:
%       SDPMAT : Symmetric 2*nbus by 2*nbus matrix (intended to be Yk, Yk_,
%           Mk, Ylineft, Ylinetf, Y_lineft, Y_linetf from the semidefinite
%           programming relaxation).
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
%
%   Outputs:
%       SDPVEC : A matrix with four columns, with a row for each nonzero
%           element of sdpmat. The first column gives the index of the
%           decomposed matrix. The second and third columns give the row
%           and column, respectively, of the appropriate entry of the
%           decomposed matrix. The fourth column is the value of the entry.

%   MATPOWER
%   Copyright (c) 2013-2016 by Power System Engineering Research Center (PSERC)
%   by Daniel Molzahn, PSERC U of Wisc, Madison
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% Setup

nbus = size(sdpmat,1) / 2;
[matrow, matcol, matval] = find(triu(sdpmat));

% To speed up this function, rather than search throuh the entire Wref_dd,
% Wref_qq, Wref_dq vectors every time we look up a nonzero entry of sdpmat,
% filter out the entries that will actually be used in the rest of the
% function.

dd_buses = unique([matrow(matrow <= nbus); matcol(matcol <= nbus)]);
dd_rows = [];
for i=1:length(dd_buses)
    dd_rows = [dd_rows; find(Wref_dd(:,2) == dd_buses(i) | Wref_dd(:,3) == dd_buses(i))];
end
Wref_dd = Wref_dd(dd_rows,:);

qq_buses = unique([matrow(matrow > nbus); matcol(matcol > nbus)]) - nbus;
qq_rows = [];
for i=1:length(qq_buses)
    qq_rows = [qq_rows; find(Wref_qq(:,2) == qq_buses(i) | Wref_qq(:,3) == qq_buses(i))];
end
Wref_qq = Wref_qq(qq_rows,:);

dq_buses = unique([matrow(matrow > nbus)-nbus; matcol(matcol > nbus)-nbus; matrow(matrow <= nbus); matcol(matcol <= nbus)]);
dq_rows = [];
for i=1:length(dq_buses)
    dq_rows = [dq_rows; find(Wref_dq(:,2) == dq_buses(i) | Wref_dq(:,3) == dq_buses(i))];
end
Wref_dq = Wref_dq(dq_rows,:);


%% Form sdpvec

sdpvec = zeros(2*length(matrow),4);
idx = 0;
for m = 1:length(matrow);
    idx = idx + 1;
    if matrow(m) <= nbus && matcol(m) <= nbus % In the dd section of the W matrix
        Wref_dd_row = find( (Wref_dd(:,2) == matrow(m) & Wref_dd(:,3) == matcol(m)) | ... 
                            (Wref_dd(:,3) == matrow(m) & Wref_dd(:,2) == matcol(m)), 1);
        sdpvec(idx,:) = [matidx_dd(Wref_dd(Wref_dd_row,1),1) matidx_dd(Wref_dd(Wref_dd_row,1),2) matidx_dd(Wref_dd(Wref_dd_row,1),3) matval(m)];
        idx = idx + 1;
        sdpvec(idx,:) = [matidx_dd(Wref_dd(Wref_dd_row,1),1) matidx_dd(Wref_dd(Wref_dd_row,1),3) matidx_dd(Wref_dd(Wref_dd_row,1),2) matval(m)];
    elseif matrow(m) > nbus && matcol(m) > nbus % In the qq section of the W matrix
        Wref_qq_row = find( (Wref_qq(:,2) == (matrow(m)-nbus) & Wref_qq(:,3) == (matcol(m))-nbus) | ...
                            (Wref_qq(:,3) == (matrow(m)-nbus) & Wref_qq(:,2) == (matcol(m)-nbus)), 1);
        sdpvec(idx,:) = [matidx_qq(Wref_qq(Wref_qq_row,1),1) matidx_qq(Wref_qq(Wref_qq_row,1),2) matidx_qq(Wref_qq(Wref_qq_row,1),3) matval(m)];
        idx = idx + 1;
        sdpvec(idx,:) = [matidx_qq(Wref_qq(Wref_qq_row,1),1) matidx_qq(Wref_qq(Wref_qq_row,1),3) matidx_qq(Wref_qq(Wref_qq_row,1),2) matval(m)];
    elseif (matrow(m) > nbus && matcol(m) <= nbus) % In the dq section of the W matrix
        Wref_dq_row = find(Wref_dq(:,3) == (matrow(m)-nbus) & Wref_dq(:,2) == matcol(m), 1);
        
        sdpvec(idx,:) = [matidx_dq(Wref_dq(Wref_dq_row,1),1) matidx_dq(Wref_dq(Wref_dq_row,1),2) matidx_dq(Wref_dq(Wref_dq_row,1),3) matval(m)];
        idx = idx + 1;
        sdpvec(idx,:) = [matidx_dq(Wref_dq(Wref_dq_row,1),1) matidx_dq(Wref_dq(Wref_dq_row,1),3) matidx_dq(Wref_dq(Wref_dq_row,1),2) matval(m)];
    elseif (matrow(m) <= nbus && matcol(m) > nbus) % In the dq section of the W matrix
        Wref_dq_row = find(Wref_dq(:,2) == matrow(m) & Wref_dq(:,3) == (matcol(m)-nbus), 1);
        
        sdpvec(idx,:) = [matidx_dq(Wref_dq(Wref_dq_row,1),1) matidx_dq(Wref_dq(Wref_dq_row,1),2) matidx_dq(Wref_dq(Wref_dq_row,1),3) matval(m)];
        idx = idx + 1;
        sdpvec(idx,:) = [matidx_dq(Wref_dq(Wref_dq_row,1),1) matidx_dq(Wref_dq(Wref_dq_row,1),3) matidx_dq(Wref_dq(Wref_dq_row,1),2) matval(m)];
    else
        error('mat2vec: Invalid matrow or matcol for bus %i',k);
    end
end

sdpvec = unique(sdpvec,'rows'); % Don't double count diagonals
