function mpc = sgvm_nodeperm_init(mpc)
%SGVM_NODEPERM_INIT Initial node permutation (following branch assignment)
%   MPC = SGVM_NODEPERM_INIT(MPC)
%
%   Generator buses are targeted for buses with *larger* driving point
%   impedances, Zdr. Within the range of *larger* Zdr, larger generators
%   tend towards the *smaller* entries.

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

%% some constants
define_constants;
nb = size(mpc.bus,1);
ng = size(mpc.gen,1);

%% driving point impedances
Zdr = abs(sgvm_getZdr(mpc));
[Zdrsorted, idxz] = sort(Zdr);

%% generator capacity
gmap  = sparse(mpc.gen(:,GEN_BUS),1:ng, 1, nb, ng);
gvect = gmap*mpc.gen(:,PMAX); % nb x 1: generation capacity at each node
[idxp,~,Pcap] = find(gvect); % extract non-zero terms
ngp = length(idxp); % number of generators with non-zero PMAX
dirtmp = {'descend', 'desc'};
failcnt = 0;
for k = 1:2
    try
        [Pcap, tmp] = sort(Pcap, dirtmp{k}); % sort generation in descending order
        break
    catch
        failcnt = failcnt + 1;
    end
end
if failcnt == 2
    error('sgvm_nodeperm_init: something went wrong when sorting Pcap, neither ''descend'' nor ''desc'' worked')
end
idxp = idxp(tmp); % sort generator bus index vector to match the Pcap vector

%% Corrolate gen to zdr
nmap = zeros(nb,1); %initialize new mapping
% % idxz(end-ng+1) are the indecies of the ng largest Zdr in INCREASING order
% % idxp are the bus indecies of the generators in DECREASING order
% nmap(idxp) = idxz(end-ng+1:end);
% %% add some "noise"
% ngswap = round(0.25*ng);
% usedidx = nmap(idxp);
% genidx = 0;
% count  = 0;
% while true
%   newidx = randi(nb);
%   if genidx = 0;
%       genidx = idxp(randi(ng));
%   end
%   if ~ismember(newidx,usedidx)
%       % newly selected bus does not already have a generator assigned
%       nmap(genidx) = newidx;
%       genidx = 0;
%   else
%       % newly selected bus already has a generator assigned
%       tmp = find(nmap == newidx ); % index of generator being relpaced
%       nmap(genidx) = newidx; % map generator to new bus
%       genidx = tmp; % this way in next round the doulbed bus numbering will be handled
%   end
% 
%   % update list of used buses
%   usedidx = nmap(idxp);
%   count   = count + 1;
%   if (count >= ngswap) && genidx = 0;
%       break
%   end
% end

% idxtmp = unique(round(betarnd(8,3,ngp,1)*nb));
idxtmp = unique(round(sgvm_beta_variate(ngp, 8, 3)*nb));
if ngp - length(idxtmp) > 0
    ptr = length(idxtmp) + 1;
    idxtmp = [idxtmp; zeros(ngp - length(idxtmp), 1)];
%     while length(idxtmp) < ngp
    while ptr <= ngp
    %   tmp = round(betarnd(8,3)*nb);
        tmp = round(sgvm_beta_variate(1,8,3)*nb);
        if ~ismember(tmp, idxtmp)
            idxtmp(ptr) = tmp;
            ptr = ptr + 1;
%             idxtmp = [idxtmp; tmp];
        end
    end
end

idxtmp = sort(idxtmp);

% in its present form we would:
% map LARGEST generator to SMALLEST selected Zdr
% map SMALLEST generator to LARGEST selected Zdr

% to add some "noise" swap some entries in idxtmp
ngswap = round(0.1*ngp);
for k = 1:ngswap
    idx1 = randi(ngp);
    idx2 = randi(ngp);
    tmp = idxtmp(idx1);
    idxtmp(idx1) = idxtmp(idx2);
    idxtmp(idx2) = tmp;
end

% the generator buses are idxp sorted in DECREASING order
% idxz are the indices of the buses sorted by Zdr in INCREASING ORDER
% idxtmp is a vector of bus indices that are "roughly" in increasing order
% Therefore, idxz(idxtmp) returns a list of buses whose Zdr is generally in
% increasing magnitude, these are mapped to the generators in decreasing
% order.
nmap(idxp) = idxz(idxtmp);


%% complete permutation for non-gen buses
usedidx = nmap(idxp);
idxtmp = (1:nb)';
idxtmp = idxtmp(~ismember(idxtmp,usedidx)); %remove used inidices
idxtmp = idxtmp(randperm(length(idxtmp)));
nmap(nmap == 0) = idxtmp;

if length(unique(nmap)) ~= nb
    error('sgvm_nodeperm_init: error in generating nmap. Resulting map is not 1-to-1 and onto')
end
%% permute
mpc = sgvm_perform_permute(mpc, nmap, 'nmap');
