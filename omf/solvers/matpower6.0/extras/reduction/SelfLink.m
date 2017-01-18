function [LinkPos,LinkArray,Counter] = SelfLink(Link,Start)
% FUNCTION SUMMARY:
%   Subroutine SelfLink search the Link array in by self referencing. The
%   searching process will stop until a zero is found. Every non-zero
%   element found in the searching process will be stored in LinkArray and
%   their corresponding index pointers will be stored in LinkPos. Couter
%   will count the number of numzero element in LinkArray.
%
%   [LinkPos,LinkArray,Counter] = SelfLink(Link,Start)
%
% INPUT DATA:
%   Link - N * 1 array containing the link list
%   Start- scalar is the starting point of the searching process
%
% OUTPUT DATA:
%   Counter - scalar, number of non-zero elements in LinkArray
%   LinkArray - N*1 array, containing the non-zero element found in the searching
%       process
%   LinkPos - N*1 array, containing the index pointers of the non-zero
%       elements stored in LinkArray
%
% INTERNAL DATA:
%   SelRef - scalar, used to do searching in Link list, which is equal to
%       the current found element and also pointer to the next element
%
% NOTE:
%   1. Initiate the SelfRef=Start and Counter=0. Go to step 2.
%   Note: The following steps until step 3 are done in the while loop
%   2. While the element found in the Link list (Link(SelfRef)) is not zero
%   go to step 2.1 if equal to zero go to step 3.
%       2.1 Increment Counter by 1. Go to step 2.2
%       2.2 Store SelfRef to LinkPos which is the index of current non-zero
%       element. Go to step 2.3
%       2.3 Update the SelfRef equal to Link(SelfRef). Go to step 2.4
%       2.4 Store the SelfRef value to LinkArray which is the value of
%       current element. Go to step 2.
%   3. End of the subroutine. Return.

%   MATPOWER
%   Copyright (c) 2014-2016, Power Systems Engineering Research Center (PSERC)
%   by Yujia Zhu, PSERC ASU
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.

    SelfRef = Start;
    Counter = 0;
    while Link(SelfRef)~=0
        Counter = Counter+1; % count how many linkage in this list
        LinkPos(Counter)=SelfRef;
        SelfRef = Link(SelfRef);
        LinkArray(Counter)=SelfRef; % create the array of the self referential link list
    end
end