function [P_upper_wh, P_lower_wh, E_UL_wh] = VB_core_WH(paraFile)
% Author: He Hao (PNNL)
% Last update time: September 19, 2017
% This function is used to characterize VB capacity from a population of WH considering water draw

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

N_wh = size(para,1); % number of TCL
C_wh = para(:,1); % thermal capacitance
R_wh = para(:,2); % thermal resistance
P_wh = para(:,3); % rated power (kW) of each TCL
delta_wh = para(:,5); % temperature deadband
theta_s_wh = para(:,6); % temperature setpoint

% theta_a is the ambient temperature
theta_a = (72-32)*5/9*ones(365,24*60);
[nRow,nCol] = size(theta_a);
theta_a = reshape(theta_a,nRow*nCol,1);

% h is the model time discretization step in seconds
h = 60;

% T is the number of time step considered, i.e., T = 365*24*60 means a year
% with 1 minute time discretization
T = length(theta_a);

% theta_lower is the temperature lower bound
theta_lower_wh = theta_s_wh - delta_wh/2;
% theta_upper is the temperature upper bound
theta_upper_wh = theta_s_wh + delta_wh/2;

% m_water is the water draw in unit of gallon per minute
m_water = csvread('Flow_raw_1minute_BPA.csv', 1, 1)*0.00378541178*1000/h;
%load m_water

water_draw = m_water;
for i = 1:N_wh
    k = unidrnd(size(m_water,2));
    water_draw(:,i) = circshift(m_water(:, k), [1, unidrnd(15)-15]) + m_water(:, k)*0.1*(rand-0.5);
end

Po=-(theta_a*ones(1,N_wh)-ones(T,1)*theta_s_wh')./(ones(T,1)*R_wh')-4.2*water_draw.*((55-32)*5/9 -ones(T,1)*theta_s_wh');

% Po_total is the analytically predicted aggregate baseline power
Po_total = sum(Po,2);
Po_total(find(Po_total>sum(P_wh))) = sum(P_wh);

% theta is the temperature of TCLs
theta = zeros(N_wh, T);
theta(:,1) = theta_s_wh;

% m is the indicator of on-off state: 1 is on, 0 is off
m = ones(N_wh,T);
m(1:floor(N_wh*0.8),1) = 0;

for t=1:1:T-1
    theta(:,t+1) = (1-h./(C_wh*3600)./R_wh).*theta(:,t) + h./(C_wh*3600)./R_wh*theta_a(t) + h./(C_wh*3600).*m(:,t).*P_wh;
    m(theta(:,t+1) > theta_upper_wh,t+1)=0;
    m(theta(:,t+1) < theta_lower_wh,t+1)=1;
    m(theta(:,t+1) >= theta_lower_wh & theta(:,t+1) <= theta_upper_wh,t+1)=m(theta(:,t+1) >= theta_lower_wh & theta(:,t+1) <= theta_upper_wh,t);
end

theta(:,1) = theta(:,end);
m(:,1) = m(:,end);

% Po_total_sim is the predicted aggregate baseline power using simulations
Po_total_sim = zeros(T,1);
Po_total_sim(1) = sum(m(:,1).*P_wh);

for t=1:1:T-1
        theta(:,t+1) = (1-h./(C_wh*3600)./R_wh).*theta(:,t) + h./(C_wh*3600)./R_wh*theta_a(t)...
            + h./(C_wh*3600).*m(:,t).*P_wh + h*4.2.*water_draw(t,:)'.*((55-32)*5/9 - theta(:,t))./(C_wh*3600);
      m(theta(:,t+1) > theta_upper_wh,t+1)=0;
      m(theta(:,t+1) < theta_lower_wh,t+1)=1;
      m(theta(:,t+1) >= theta_lower_wh & theta(:,t+1) <= theta_upper_wh,t+1)=m(theta(:,t+1) >= theta_lower_wh & theta(:,t+1) <= theta_upper_wh,t);
    Po_total_sim(t+1) = sum(m(:,t+1).*P_wh);
end
%
index_available = ones(N_wh, T);

for t=1:1:T-1
    index_available(theta(:,t) < theta_lower_wh-0.5 | theta(:,t) > theta_upper_wh+0.5,t)=0;
end

% Virtual battery parameters
P_upper_wh1 = sum(P_wh) - Po_total_sim;
P_lower_wh1 = Po_total_sim;
E_UL_wh1 = sum((C_wh*ones(1, T).*(delta_wh*ones(1, T))/2).*index_available)';

% calculate hourly average data from minute output for power
P_upper_wh1 = reshape(P_upper_wh1, [60,8760]);
P_upper_wh = mean(P_upper_wh1);
P_lower_wh1 = reshape(P_lower_wh1, [60,8760]);
P_lower_wh = mean(P_lower_wh1);
% extract hourly data from minute output for energy
E_UL_wh = E_UL_wh1(60:60:length(E_UL_wh1));

end