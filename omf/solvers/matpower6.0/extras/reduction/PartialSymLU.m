function [ERPU,CIndxU,ERPEQ,CIndxEQ] = PartialSymLU(CIndx,ERP,dim,Stop,BoundBus)
%FUNCTION SUMMARY:
%   Subroutine PartialSymLU do partial symbolic LU factorization. 
%
%   [ERPU,CIndxU,ERPEQ,CIndxEQ] = PartialSymLU(CIndx,ERP,dim,Stop,BoundBus)
%
% INPUT DATA:
%   CIndx - N*1 array containning the column index of the rows, N is the
%           number of non-zeros elements in the input data
%   ERP - (N_node+1)*1 array containning the end of row pointer data
%   dim - scalar, dimension of the input matrix
%   Stop - scalar, stop sign of the LU factorization (The LU factorization
%       in the reduction process is not complete but partial)
%   BoundBus- 1*n array, includes indices of boundary buses
%
%
% OUTPUT DATA:
%   ERPU -   N_dim*1 array containing end of row pointer of all rows except
%            the last row which doesn have any off diagonal element, N_dim is
%            the dimension of the input matrix A in the original Ax = b
%            problem
%   CIndxU - N*1 array containing the column index of off diagonal element
%            in each row in the U matrix. The length N depends on the
%            number of native plus filled non-zero elements in the off
%            diagonal position in U matrix. CIndxU is unordered.
%   ERPEQ, CIndxEQ, - both are N*1 arrays, together include the indices of
%            equivalent branches
%
%
%   Note: This subroutine will do:
%       1. Factorization of rows in the full model bus addmittance matrix
%       corresponding to the external buses. This process will only
%       generate the pointers of non-zeroes in L and U matrix;
%       2. Identify the equivalent branch indices. Identify the pointers
%       (ERPEQ, CIndxEQ)of fills generated from step 1 in the rows and
%       columns corresponding to the boundary buses. (The equivalent lines  
%       can only span the boundary buses).

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

%% Begin of the code
numRow = dim; % number of rows of given data matrix
% numCol = dim; % number of columns of given data matrix
%% Initialization
% the length of pos is equal to # of total non zero data - number of
% diagonal elements - the number of non zero element in last row'
%% step 0
CIndxU = 0;
ERPU= zeros(1,dim); % with aditional one digit for the 7th row
Switch = zeros(1,dim);
MinNod0 = inf; % This is a initiate large value of MinNod; not the MinNod used in building the symbolic struture
MinNod = MinNod0;
MinNod1=MinNod;
Link = ERPU;
CIndxEQ=0;
ERPEQ=zeros(1,Stop+length(BoundBus)+1);
Chain=zeros(1,Stop+length(BoundBus));
% preprocess the data by ordering the CIndx of every row in ascending order
for i = 2:numRow+1
    RowColInd = ERP(i-1)+1:ERP(i); % for every row the pointer of the column index
    CIndx(RowColInd)=sort(CIndx(RowColInd));
end
% initiate starting row 1
RowIndex = 1;
while RowIndex<=length(BoundBus)+Stop
    MinNod1=MinNod0;
    %% step 1
    if RowIndex<=Stop
        [CIndxU,ERPU,MinNod,Switch] = RODAssignment(ERP,CIndx,CIndxU,ERPU,MinNod,Switch,RowIndex,RowIndex);
        %% step 2
        % Check fill in ROD in current row
        SelfRef = RowIndex; % self referential link pointer to next availale link element
        while (Link(SelfRef)~=0)
            SelfRef = Link(SelfRef); % to refer for the next link element
            [CIndxU,ERPU,MinNod,Switch] = RODAssignment (ERPU,CIndxU,CIndxU,ERPU,MinNod,Switch,SelfRef,RowIndex);
        end
        Link(RowIndex) = 0; % zero the element in the Link list of current row
        %% step 3
        % update Link node (MinNod) to be current RowIndex
        if MinNod>RowIndex&&MinNod~=MinNod0
            SelfRef = MinNod; % start the assign value to Link
            while (Link(SelfRef)~=0)
                SelfRef = Link(SelfRef);
            end
            Link(SelfRef)=RowIndex;
        end
        %% step 4
        MinNod = MinNod0; % reset the MinNod value
    else
        if Link(RowIndex)~=0
            [LinkPos,LinkArray,Counter] = SelfLink(Link,RowIndex);
            for i = 1:Counter
                SelfRef=LinkArray(i);
                if SelfRef<=Stop
                    if CIndxEQ==0
                        StFlag=0;
                    end
                    [CIndxEQ,ERPEQ,MinNod,Switch,ChainFlag] = EQRODAssignment(ERPU,CIndxU,CIndxEQ,ERPEQ,MinNod,Switch,SelfRef,RowIndex,Chain,MinNod1);
                    if StFlag==0&&any(CIndxEQ)
                        StFlag=1;
                    end
                    if MinNod>RowIndex&&MinNod~=MinNod0||(MinNod1~=MinNod&&ChainFlag~=1)
                        if MinNod1~=MinNod0
                            if StFlag~=1&&MinNod1~=MinNod&&Chain(MinNod1)==0
                                Link(SelfRef1)=0;
                                % If the chain breaks, record where and which
                                % row to be reconected
                                Chain(MinNod1)=Link(MinNod1);
                            end
                        elseif StFlag~=1&&MinNod1~=MinNod&&ChainFlag==0
                            Link(SelfRef1)=0;
                            
                        end
                        
                        if MinNod~=MinNod0
                            SelfRef1=SelfRef;
                            FillIn = MinNod; % start the assign value to Link
                            while (Link(FillIn)~=0)&&Link(FillIn)~=FillIn;
                                FillIn = Link(FillIn);
                            end
                            %                         if Link(FillIn)==0
                            if FillIn~=SelfRef1
                                Link(FillIn)=SelfRef1;
                            else
                                MinNod=MinNod;
                            end
                            Chain(MinNod)=0;
                            %                         end
                        end
                    end
                    %% step 4
                    MinNod1=MinNod;
                    
                    MinNod = MinNod0; % reset the MinNod value
                end
            end
        else
            ERPEQ(RowIndex+1)=ERPEQ(RowIndex);
        end
        Link(RowIndex) = 0; % zero the element in the Link list of current row
    end  
    % ready for next loop
    RowIndex = RowIndex+1;
end
end