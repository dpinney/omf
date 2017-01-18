function [CindxU,ERPU,MinNod,Switch] = RODAssignment(ERP,CIndx,CindxU,ERPU,MinNod,Switch,SelfRef,RowIndex)
%FUNCTION SUMMARY:
%   Subroutine RODAssignment is called in the symbolic LU factorization to
%   assign column index of non-zero element on right of the diagonal in U
%   matrix. The non-zero element may come be native or filed.
%
%   [CindxU,ERPU,MinNod,Switch] = RODAssignment(ERP,CIndx,CindxU,ERPU,MinNod,Switch,SelfRef,RowIndex)
%
% INPUT DATA:
%   ERP - (N_node+1)*1 array containning the end of row pointer data
%   CIndx - N*1 array containning the column index of the rows, N is the
%           number of non-zeros elements in the input data
%   CIndxU- N*1 array containning the column index of rows in the U matrix.
%           The length N dedpends on the number of non-zero elements in
%           previous rows on right of diagonal.
%   Switch- N*1 array which is used to record the index off diagonal
%           element in CIndxU and avoid keep the indices disjoint
%   SelfRef-scalar, data value in the self refertial link also is the pointer 
%           point to next position in the self referential link
%   RowIndex-scalar, the index of the row in processing   
%   ERPU -  N_dim*1 array containing end of row pointer of all rows except
%           the last row which doesn have any off diagonal element, N_dim is
%           the dimension of the input matrix A in the original Ax = b
%           problem
%   MinNod -scalar, store the minimum index of non-zero element on the 
%           right of the diagonal
%
% OUTPUT DATA:
%   ERPU -   N_dim*1 array containing end of row pointer of all rows except
%            the last row which doesn have any off diagonal element, N_dim is
%            the dimension of the input matrix A in the original Ax = b
%            problem
%   CIndxU - N*1 array containing the column index of off diagonal element
%            in each row in the U matrix. The length N depends on the
%            number of native plus filled non-zero elements in the off
%            diagonal position in U matrix. CIndxU is ordered.
%   MinNod - scalar, store the minimum index of non-zero element on the 
%            right of the diagonal
%   Switch- N*1 array which is used to record the index off diagonal
%           element in CIndxU and avoid keep the indices disjoint
%  NOTE: in output data, ERPU, CIndxU, MinNod and Switch are updated in the
%  subroutine. The output will return the updated arrays.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% to assign value to ROD position
RowLen = ERP(SelfRef+1)-ERP(SelfRef); % number of non-zero element in current row
RowColInd = CIndx(ERP(SelfRef)+1:ERP(SelfRef+1));
% Initiate the ERPU to be the end of last row
if ERPU(RowIndex+1)==0
    ERPU(RowIndex+1)=ERPU(RowIndex); % In the loop every time read one ROD element ERPU(RowColInd)+1
end
for i = 1:RowLen % dealing with each non-zero native non-zero element first
    % Load the native non-zero ROD
    if RowColInd(i)>RowIndex&&(Switch(RowColInd(i))~=RowIndex) % check if current element is on ROD
        CindxU(ERPU(RowIndex+1)+1)=RowColInd(i);
        ERPU(RowIndex+1)=ERPU(RowIndex+1)+1; % increase 1 after reading one non-zero number;
        % Update the MinNod if MinNod greater than current column
        % index RowColInd(i)
        if MinNod>RowColInd(i)
            MinNod = RowColInd(i); % update the MinNod
        end
        % Update the Switch list
        Switch(RowColInd(i))=RowIndex;
    end
end
end