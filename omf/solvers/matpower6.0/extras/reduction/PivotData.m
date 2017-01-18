function [DataB,ERP,CIndx,PivOrd,PivInd] = PivotData(DataB,ERP,CIndx,ExBus,NUMB,BoundBus)
% Subroutine PivotData do pivotting to the input addmittance matrix. Two
% pivotting will be done: 1. columns and rows corresponding to external
% buses will be pivotted to the top left corner of the input matrix. 2.
% Tinney One optimal ordering strategy will be applied to pivot the data in
% order to reduce fills during (Partial) LU factorization.
%
%   [DataB,ERP,CIndx,PivOrd,PivInd] = PivotData(DataB,ERP,CIndx,ExBus,NUMB,BoundBus)
%
% INPUT DATA:
%   DataB: 1*n array, includes addmittance data of the full model before
%   pivotting
%   ERP: 1*n array, includes end of row pointer before pivotting
%   CIndx: 1*n array, includes column index pointer before pivotting
%   ExBus: 1*n array, includes external bus indices in internal numbering
%   NUMB: 1*n array, includes bus numbers in internal numbering
%
% OUTPUT DATA:
%   DataB: 1*n array, includes pivotted addmittance data of the full model
%   ERP: 1*n array, includes end of row pointer before pivotting
%   CIndx: 1*n array, includes column index pointer
%   PivOrd: 1*n array, includes bus indices after pivotting
%   PivInd: 1*n array, includes bus ordering after pivotting

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

DataBO = zeros(size(DataB));
CIndxO = zeros(size(CIndx));
ERPO = zeros(size(ERP));

% do pivot
ExBus = sort(ExBus);
tf1 = ismember(NUMB,ExBus);
tf2 = ismember(NUMB,BoundBus);
PivInd = [sort(NUMB(tf1==1))',sort(NUMB(tf2==1))',sort(NUMB(tf1==0&tf2==0))'];
PivOrd = zeros(size(PivInd));

for i = 1:length(PivInd)
    PivOrd(PivInd(i))=i;
end

%% Do Tinnney One ordering to reduce fills
[PivOrd,PivInd] = TinneyOne(ERP,PivInd,PivOrd,ExBus);

%% Generate the datas in compact storage format
for i = 1:length(NUMB)
    len = ERP(PivInd(i)+1)-ERP(PivInd(i));
    ERPO(i+1)=ERPO(i)+len;
    CIndxO((ERPO(i)+1):ERPO(i+1))=PivOrd(CIndx(ERP(PivInd(i))+1:ERP(PivInd(i)+1)));
    DataBO((ERPO(i)+1):ERPO(i+1))=DataB(ERP(PivInd(i))+1:ERP(PivInd(i)+1));
end

%% Generate the output data
DataB = DataBO;
CIndx = CIndxO;
ERP = ERPO;

end