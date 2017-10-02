function [P_lower, P_upper, E_UL] = VB_core_TCL(paraFile, theta_a,TCL_idx)
% Author: Di Wu and He Hao (PNNL)
% Last update time: September 19, 2017
% This function is used to characterize VB capacity from a population of AC, HP, or RG

if ischar(paraFile) == 1
    if isempty(version('-release')) == 1
        para = csvread(paraFile);
        para(1,:)=[];
    else
        para = xlsread(paraFile);
    end
else
    para = repmat(paraFile(1:6),paraFile(7),1);
end

N = size(para,1); % number of TCL
C = para(:,1); % thermal capacitance
R = para(:,2); % thermal resistance
P = para(:,3); % rated power (kW) of each TCL
eta = para(:,4); % COP
delta = para(:,5); % temperature deadband
theta_s = para(:,6); % temperature setpoint

%% heuristic function of participation
if TCL_idx==1 % AC
    Ta = 20:0.5:45;
    participation =  (atan(theta_a-27) - atan(Ta(1)-27))/((atan(Ta(end)-27) - atan(Ta(1)-27)));
elseif TCL_idx==2 %HP
    Ta = 0:0.5:25;
    participation = 1-(atan(theta_a-10) - atan(Ta(1)-10))/((atan(Ta(end)-10) - atan(Ta(1)-10)));
elseif TCL_idx==3 %RG
    participation=ones(size(theta_a));
end
k = find(participation < 0);
if(~isempty(k))
    participation(k)=0;
end
k = find(participation >1);
if(~isempty(k))
    participation(k) =1;
end

%%
if TCL_idx==1 || TCL_idx==3 %AC or RG
    P0 = (theta_a - mean(theta_s))/mean(R)/mean(eta); % average baseline power consumption for the given temperature setpoint
elseif TCL_idx==2 %HP
    P0 =(mean(theta_s)- theta_a)/mean(R)/mean(eta);
end
P0= max(P0,0); % set negative power consumption to 0
P_lower = N*participation.*P0; % aggregated baseline power consumption considering participation

P_upper = N*participation.*(mean(P) - P0);
P_upper=max(P_upper,0); % set negative power upper bound to 0
E_UL = N*participation*mean(C)*mean(delta)/2/mean(eta);

end