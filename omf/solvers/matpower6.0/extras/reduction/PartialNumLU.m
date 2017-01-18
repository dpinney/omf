function [DataEQ,DataShunt] = PartialNumLU (CIndx,CIndxU,Data,dim,ERP,ERPU,stop,ERPEQ,CIndxEQ,BoundBus)
%FUNCTION SUMMARY:
%   Subroutine PartialNumLU does partial numerical LU factorization to
%   given full model bus addmittance matrix and calculate the equivalent
%   branch reactance and the equivalent shunts (generated in the
%   factorization process) added to the boundary buses.
%  
%   [DataEQ,DataShunt] = PartialNumLU (CIndx,CIndxU,Data,dim,ERP,ERPU,stop,ERPEQ,CIndxEQ,BoundBus)
%
% INPUT DATA:
%   CIndx - N*1 array containning the column index of the rows, N is the
%           number of non-zeros elements in the input data
%   CIndxU - N*1 array containing the column index of off diagonal element
%            in each row in the U matrix. The length N depends on the
%            number of native plus filled non-zero elements in the off
%            diagonal position in U matrix. CIndxU is unordered.
%   Data -N*1 array containing the data of matrix element in the original
%         input file.
%   dim - scalar, dimension of the input matrix
%   ERPU -   N_dim*1 array containing end of row pointer of all rows except
%            the last row which doesn have any off diagonal element, N_dim is
%            the dimension of the input matrix A in the original Ax = b
%            problem
%   ERP - (N_node+1)*1 array containning the end of row pointer data
%   stop - scalar, equal to the number of external buses
%   ERPEQ, CIndxEQ, 1*n arrays, together build the pointers of the
%       equivalent branches
%   BoundBus - 1*n array, list of boundary buses
%
% OUTPUT DATA:
%   DataEQ: 1*n array, includes reactance value of the equivalent branches
%   DataShunt: 1*n array, includes equivalent bus shunts of the boundary
%   buses

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

% do numerical factorization on input data
numRow = dim; % number of rows of given data matrix
ICPL = ERPU+1; % the initial column pointer equal to the last end of row pointer+1
ICPL(end) = [];
ICPL = [0,ICPL]; 
RX = 0; % Initiate the RX value;
Link = zeros(1,dim);
ExAcum = Link; % Initiate the ExAcum;
Diag = zeros(1,numRow); 
DataEQ=zeros(size(CIndxEQ));
DataShunt=zeros(1,length(BoundBus));
% Initialization based on ERPU, CindU;
% Sort the CIndxU to make it Ordered CindUU->CindUO
for i = 2:numRow
    RowColInd = ERPU(i-1)+1:ERPU(i); % for every row the pointer of the column index
    [CIndxU(RowColInd)] = sort(CIndxU(RowColInd)); % sort the CIndx of every row in ascending order
end
%% begin Numerical Factorization
RowIndex = 1; % Start at row 1
while RowIndex<=numRow
    %% step 1 a,b
    % zero ExAcum using Link and CIndxUO;
    % This give the active element of current row
    % get the array from the self referential link
     if RowIndex>stop
            ExAcumEQ=zeros(size(ExAcum));
        end
    if Link(RowIndex)~=0
        [LinkPos,LinkArray,LinkCounter] = SelfLink(Link,RowIndex);
    else LinkCounter=0;
    end
    if LinkCounter~=0
        if RowIndex<numRow % if this is the last row there will be nothing on the right of the diagonal in U only fills in row(numRow) of L
            ExAcum([LinkArray,CIndxU(ERPU(RowIndex)+1:ERPU(RowIndex+1))])=0;% zero non-zero position from both native and fill
        else
            ExAcum(LinkArray)=0; % for last row, fill only
        end
    else
        ExAcum(CIndxU(ERPU(RowIndex)+1:ERPU(RowIndex+1)))=0;
    end
    %% step 1c
    % load corresponding values to ExAcum
    ExAcum(CIndx(ERP(RowIndex)+1:ERP(RowIndex+1)))=Data(ERP(RowIndex)+1:ERP(RowIndex+1)); % Index in the original array is CIndx(ERP(RowIndex)+1:ERP(RowIndex+1))
    %% step 2a
    RX = 0; % initiate RX
    %% step 2b,c
    if LinkCounter~=0
        [LinkArray,LinkPosInd]=sort(LinkArray);
        LinkPos = LinkPos(LinkPosInd);
        Link(LinkPos)=0;
       
        for i = 1:LinkCounter
            RX = LinkArray(i); % assign RX value to current fill generating row
            %% step 2d
           if RowIndex>stop
            ExAcumEQ(CIndxU(ERPU(RX)+1:ERPU(RX+1)))=ExAcumEQ(CIndxU(ERPU(RX)+1:ERPU(RX+1)))-ExAcum(RX)*URO(ERPU(RX)+1:ERPU(RX+1));
           end
            ExAcum(CIndxU(ERPU(RX)+1:ERPU(RX+1)))=ExAcum(CIndxU(ERPU(RX)+1:ERPU(RX+1)))-ExAcum(RX)*URO(ERPU(RX)+1:ERPU(RX+1));
            
            %% step 2ef
            LCO(ICPL(RX+1))=ExAcum(RX)*Diag(RX);
            ICPL(RX+1) = ICPL(RX+1)+1;
%             Link(LinkPos(i))=0;
            %% step 2g
            if ICPL(RX+1)<=ERPU(RX+1)
                SelfRef=CIndxU(ICPL(RX+1));
                while Link(SelfRef)~=0
                    SelfRef = Link(SelfRef); % exhaust the link list and find a 0 position to store RX
                end
                Link(SelfRef)=RX;
            end
        end
    end
    if RowIndex>stop
    DataEQ(ERPEQ(RowIndex)+1:ERPEQ(RowIndex+1))=1./ExAcumEQ(CIndxEQ(ERPEQ(RowIndex)+1:ERPEQ(RowIndex+1)));
    DataShunt(RowIndex-stop)=ExAcumEQ(RowIndex);%+sum(ExAcumEQ(CIndxEQ(ERPEQ(RowIndex)+1:ERPEQ(RowIndex+1))));
    end
    %% step 4
if RowIndex<=stop
    Diag(RowIndex)=1/ExAcum(RowIndex); % Invert the diagonal value
    %% step 5
    if RowIndex<numRow
        URO(ERPU(RowIndex)+1:ERPU(RowIndex+1))=ExAcum(CIndxU(ERPU(RowIndex)+1:ERPU(RowIndex+1)))*Diag(RowIndex); % Multiply active ExAcum by Diag(1) & store in URO
        %% step 6
        SelfRef=CIndxU(ICPL(RowIndex+1));
        while Link(SelfRef)~=0
            SelfRef=Link(SelfRef);
        end
        Link(SelfRef)=RowIndex;
    end
   
elseif sum(Link)==0
    break;
end
 %% Prepare for next loop
RowIndex = RowIndex+1; % Increment the RowIndex
end
end