function [data] = TaxFeederData(file_to_extract,region)
% This will contain data particular to each taxonomy feeder

% Secondary, or load side, of transformers
% I think its the same for every feeder, but just in case...
data.nom_volt2 = 480;

if (strcmp(file_to_extract,'GC-12.47-1.glm')~=0)
    % Nominal Voltage of the trunk of the feeder
    data.nom_volt = 12470;
    
    % substation rating in MVA - add'l 15% gives rated kW & pf = 0.87
    data.feeder_rating = 1.15*5.38; 
            
    % Determines how many houses to populate (bigger avg_house = less houses)
    data.avg_house = 8000;
    
    % Determines sizing of commercial loads (bigger = less houses)
    data.avg_commercial = 13000;
    
    % End-of-line measurements for each feeder
    % name of node, phases to measure
    data.EOL_points={'GC-12-47-1_node_7','ABC',1};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.regulators={'GC-12-47-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_r' num2str(region) '_vvo.player']};
    
    % Capacitor outtage information for each feeder
    % Name of capacitor , player file name
    data.capacitor_outtage={'GC-12-47-1_cap_1','GC-12-47-1_cap_1_outtage.player'};
        
    % Peak power of the feeder in kVA
    % these first values are special to GC since it spans 5 regions
    %  TODO: R6 values are not correct
    emissions_p = [5363;5754;6637;6321;5916;5916];
    data.emissions_peak = emissions_p(region);
    
    % TOU/CPP pricing information
    % these first values are special to GC since it spans 5 regions
    %   TODO: Unsure about R6 at this point, so numbers are "made-up"
    reg_TOU_prices = [0.06801189,0.13602378;
                      0.07036911,0.14073821;
                      0.05168987,0.10337974;
                      0.05682642,0.11365284;
                      0.05790918,0.11581836;
                      0.15000000,0.30000000];
    reg_CPP_prices = [0.06263140,0.12526279,0.62631396;
                      0.06309993,0.12619986,0.63099932;
                      0.04677589,0.09355179,0.46775893;
                      0.05122360,0.10244719,0.51223597;
                      0.05320724,0.10641447,0.53207237;
                      0.05000000,0.15000000,0.30000000];
    reg_TOU_hours = [12,12,6;
                     16,8,6;
                     15,9,6;
                     14,10,6;
                     16,8,6;
                     12,12,6];
    reg_TOU_stats = [0.10201783,0.03400643;
                     0.09965752,0.03468750;
                     0.07428654,0.02564036;
                     0.08285892,0.02831370;
                     0.08201163,0.02854555;
                     0.10000000,0.05000000];
    reg_CPP_stats = [0.09843910,0.03400643;
                     0.09431946,0.03468750;
                     0.07081883,0.02564036;
                     0.07853818,0.02831370;
                     0.07953222,0.02854555;
                     0.10000000,0.05000000];             
    data.TOU_prices = reg_TOU_prices(region,:); % 1st, 2nd tier price
    data.CPP_prices = reg_CPP_prices(region,:); % 1st, 2nd, and CPP tier prices
    data.TOU_hours = reg_TOU_hours(region,:); % hours at each tier (first 2 need to sum to 24)
    data.TOU_stats = reg_TOU_stats(region,:); % mean and stdev to be set in stub auction
    data.CPP_stats = reg_CPP_stats(region,:);
    data.TOU_price_player = {['GC_1247_1_t0_r' num2str(region) '_TOU.player']};
    data.CPP_price_player = {['GC_1247_1_t0_r' num2str(region) '_CPP.player']};
    data.CPP_flag = {['CPP_days_R' num2str(region) '.player']}; % player that specifies which day is a CPP day (critical_day)

    %Thermal override for commercial feeders - 1, 3, 4, and 5 at 10% still
    %  TODO: Region 6 is currently made-up
    comm_Thermal_override=[10; 18; 10; 10; 10; 10];
    data.thermal_override = comm_Thermal_override(region);
    % 0 residential, 0 commercial, 3 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R1-12.47-1.glm')~=0)
    data.nom_volt = 12500;
    data.feeder_rating = 1.15*7.272; % Peak in MW (Only transformer sizing)
    data.avg_house = 4000;
    data.avg_commercial = 20000;
    data.EOL_points={'R1-12-47-1_node_533','A',1;
                     'R1-12-47-1_node_311','B',1;
                     'R1-12-47-1_node_302','C',1};
    data.capacitor_outtage={'R1-12-47-1_cap_1','R1-12-47-1_cap_1_outtage.player';'R1-12-47-1_cap_2','R1-12-47-1_cap_2_outtage.player';'R1-12-47-1_cap_3','R1-12-47-1_cap_3_outtage.player'};
    data.regulators={'R1-12-47-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 7319; %Peak in kVa base .85 pf of 29 (For emissions)
    
    data.TOU_prices = [0.07590551,0.15181102];
    data.CPP_prices = [0.06998667,0.13997334,0.69986670];
    data.TOU_hours = [12,12,6];
    data.TOU_stats = [0.11385826,0.03795329];
    data.CPP_stats = [0.10999954,0.03795329];
    
    data.TOU_price_player = {'R1_1247_1_t0_TOU.player'};
    data.CPP_price_player = {'R1_1247_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R1.player'}; % player that specifies which day is a CPP day (critical_day)
    % 598 residential, 12 commercial, 0 industrial, 8 agricultural
elseif (strcmp(file_to_extract,'R1-12.47-2.glm')~=0)
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*2.733; 
    data.avg_house = 4500;
    data.avg_commercial = 30000;
    data.EOL_points={'R1-12-47-2_node_163','A',1;
                     'R1-12-47-2_node_292','B',1;
                     'R1-12-47-2_node_248','C',1};
    data.capacitor_outtage={'R1-12-47-2_cap_1','R1-12-47-2_cap_1_outtage.player' };
    data.regulators={'R1-12-47-2_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 2670;
    
    data.TOU_prices = [0.07377418,0.14754837];
    data.CPP_prices = [0.06809856,0.13619712,0.68098560];
    data.TOU_hours = [12,12,6];
    data.TOU_stats = [0.11066127,0.03688762];
    data.CPP_stats = [0.10703196,0.03688762];
    
    data.TOU_price_player = {'R1_1247_2_t0_TOU.player'};
    data.CPP_price_player = {'R1_1247_2_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R1.player'}; % player that specifies which day is a CPP day (critical_day)
    % 251 residential, 13 commercial, 0 indusrial, 0 agricultural
elseif (strcmp(file_to_extract,'R1-12.47-3.glm')~=0)
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*1.255; 
    data.avg_house = 8000;
    data.avg_commercial = 15000;
    data.EOL_points={'R1-12-47-3_node_48','AC',1;
                     'R1-12-47-3_node_38','B',1};
    data.capacitor_outtage={};
    data.regulators={'R1-12-47-3_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 1240;
    
    data.TOU_prices = [0.06611463,0.13222925];
    data.CPP_prices = [0.06048264,0.12096527,0.60482637];
    data.TOU_hours = [12,12,6];
    data.TOU_stats = [0.09917194,0.03305778];
    data.CPP_stats = [0.09506185,0.03305778];
    
    data.TOU_price_player = {'R1_1247_3_t0_TOU.player'};
    data.CPP_price_player = {'R1_1247_3_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R1.player'}; % player that specifies which day is a CPP day (critical_day)
    % 1 residential, 21 commercial, 0 indusrial, 0 agricultural
elseif (strcmp(file_to_extract,'R1-12.47-4.glm')~=0)    
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*4.960; 
    data.avg_house = 4000;
    data.avg_commercial = 15000;
    data.EOL_points={'R1-12-47-4_node_300','ABC',1};
    data.capacitor_outtage={'R1-12-47-4_cap_1','R1-12-47-4_cap_1_outtage.player'};
    data.regulators={'R1-12-47-4_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 5117;
    
    data.TOU_prices = [0.07156182,0.14312364];
    data.CPP_prices = [0.06610017,0.13220034,0.66100170];
    data.TOU_hours = [12,12,6];
    data.TOU_stats = [0.10734273,0.03578142];
    data.CPP_stats = [0.10389105,0.03578142];
    
    data.TOU_price_player = {'R1_1247_4_t0_TOU.player'};
    data.CPP_price_player = {'R1_1247_4_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R1.player'}; % player that specifies which day is a CPP day (critical_day)
    % 38 residential, 12 commercial, 0 indusrial, 0 agricultural
elseif (strcmp(file_to_extract,'R1-25.00-1.glm')~=0)    
    data.nom_volt = 24900;
    data.feeder_rating = 1.15*2.398; 
    data.avg_house = 6000;
    data.avg_commercial = 25000;
    data.EOL_points={'R1-25-00-1_node_76_2','ABC',1;
                     'R1-25-00-1_node_276','A',2;
                     'R1-25-00-1_node_227','B',2;
                     'R1-25-00-1_node_206','C',2}; %6 Measurements because of voltage regulator
    data.capacitor_outtage={'R1-25-00-1_cap_1','R1-25-00-1_cap_1_outtage.player'};
    data.regulators={'R1-25-00-1_reg_1';'R1-25-00-1_reg_2'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {14136;12000;16000;120;120};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 2339;
    
    data.TOU_prices = [0.06092879,0.12185759];
    data.CPP_prices = [0.05594083,0.11188167,0.55940834];
    data.TOU_hours = [12,12,6];
    data.TOU_stats = [0.09139319,0.03046483];
    data.CPP_stats = [0.08792340,0.03046483];

    data.TOU_price_player = {'R1_2500_1_t0_TOU.player'};
    data.CPP_price_player = {'R1_2500_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R1.player'}; % player that specifies which day is a CPP day (critical_day)
    % 25 residential, 21 commercial, 5 industrial, 64 agricultural
elseif (strcmp(file_to_extract,'R2-12.47-1.glm')~=0)    
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*6.256; 
    data.avg_house = 7000;
    data.avg_commercial = 20000;
    data.EOL_points={'R2-12-47-1_node_5','A',1;
                     'R2-12-47-1_node_17','BC',1};
    data.capacitor_outtage={'R2-12-47-1_cap_1','R2-12-47-1_cap_1_outtage.player'};
    data.regulators={'R2-12-47-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 6374;
    
    data.TOU_prices = [0.06819042,0.13638085];
    data.CPP_prices = [0.06108888,0.12217776,0.61088881];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.09657205,0.03361355];
    data.CPP_stats = [0.09131341,0.03361355];

    data.TOU_price_player = {'R2_1247_1_t0_TOU.player'};
    data.CPP_price_player = {'R2_1247_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R2.player'}; % player that specifies which day is a CPP day (critical_day)
    % 91 residential, 80 commercial, 0 industrial, 2 agricultural
elseif (strcmp(file_to_extract,'R2-12.47-2.glm')~=0)    
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*5.747; 
    data.avg_house = 7500;
    data.avg_commercial = 25000;
    data.EOL_points={'R2-12-47-2_node_146_2','ABC',1;
                     'R2-12-47-2_node_240','A',2;
                     'R2-12-47-2_node_103','B',2;
                     'R2-12-47-2_node_242','C',2}; %6 Measurements because of voltage regulator
    data.capacitor_outtage={'R2-12-47-2_cap_1','R2-12-47-2_cap_1_outtage.player';'R2-12-47-2_cap_2','R2-12-47-2_cap_2_outtage.player';'R2-12-47-2_cap_3','R2-12-47-2_cap_3_outtage.player';'R2-12-47-2_cap_4','R2-12-47-2_cap_4_outtage.player'};
    data.regulators={'R2-12-47-2_reg_1';'R2-12-47-2_reg_2'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 5889;
    
    data.TOU_prices = [0.07977903,0.15955807];
    data.CPP_prices = [0.07109568,0.14219136,0.71095681];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.11298397,0.03932600];
    data.CPP_stats = [0.10627121,0.03932600];
    
    data.TOU_price_player = {'R2_1247_2_t0_TOU.player'};
    data.CPP_price_player = {'R2_1247_2_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R2.player'}; % player that specifies which day is a CPP day (critical_day)
    % 192 residential, 8 commercial, 0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R2-12.47-3.glm')~=0)    
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*3.435; 
    data.avg_house = 5000;
    data.avg_commercial = 30000;
    data.EOL_points={'R2-12-47-3_node_36','A',1;
                     'R2-12-47-3_node_627','B',1;
                     'R2-12-47-3_node_813','C',1};
    data.capacitor_outtage={'R2-12-47-3_cap_1','R2-12-47-3_cap_1_outtage.player'};
    data.regulators={'R2-12-47-3_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 3424;
    
    data.TOU_prices = [0.08154810,0.16309620];
    data.CPP_prices = [0.07279286,0.14558571,0.72792855];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.11548934,0.04019803];
    data.CPP_stats = [0.10880808,0.04019803];

    data.TOU_price_player = {'R2_1247_3_t0_TOU.player'};
    data.CPP_price_player = {'R2_1247_3_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R2.player'}; % player that specifies which day is a CPP day (critical_day)
    % 485 residential, 6 commercial, 0 industrial, 5 agricultural
elseif (strcmp(file_to_extract,'R2-25.00-1.glm')~=0)    
    data.nom_volt = 24900;
    data.feeder_rating = 1.15*16.825; 
    data.avg_house = 6000;
    data.avg_commercial = 15000;
    data.EOL_points={'R2-25-00-1_node_288','A',1;
                     'R2-25-00-1_node_286','B',1;
                     'R2-25-00-1_node_211','C',1};
    data.capacitor_outtage={'R2-25-00-1_cap_1','R2-25-00-1_cap_1_outtage.player';'R2-25-00-1_cap_2','R2-25-00-1_cap_2_outtage.player';'R2-25-00-1_cap_3','R2-25-00-1_cap_3_outtage.player';'R2-25-00-1_cap_4','R2-25-00-1_cap_4_outtage.player';'R2-25-00-1_cap_5','R2-25-00-1_cap_5_outtage.player'};
    data.regulators={'R2-25-00-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {14136;12000;16000;120;120};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 17164;
    
    data.TOU_prices = [0.07248811,0.14497621];
    data.CPP_prices = [0.06495831,0.12991662,0.64958311];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.10265847,0.03573203];
    data.CPP_stats = [0.09709729,0.03573203];
    
    data.TOU_price_player = {'R2_2500_1_t0_TOU.player'};
    data.CPP_price_player = {'R2_2500_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R2.player'}; % player that specifies which day is a CPP day (critical_day)
    % 202 residential, 45 commercial, 0 industrial, 27 agricultural
elseif (strcmp(file_to_extract,'R2-35.00-1.glm')~=0)    
    data.nom_volt = 34500;
    data.feeder_rating = 1.15*12.638; 
    data.avg_house = 15000;
    data.avg_commercial = 30000;
    data.EOL_points={'R2-35-00-1_node_1030','ABC',1};
    data.capacitor_outtage={'R2-35-00-1_cap_1','R2-35-00-1_cap_1_outtage.player';'R2-35-00-1_cap_2','R2-35-00-1_cap_2_outtage.player';'R2-35-00-1_cap_3','R2-35-00-1_cap_3_outtage.player';'R2-35-00-1_cap_4','R2-35-00-1_cap_4_outtage.player';'R2-35-00-1_cap_5','R2-35-00-1_cap_5_outtage.player';'R2-35-00-1_cap_6','R2-35-00-1_cap_6_outtage.player';'R2-35-00-1_cap_7','R2-35-00-1_cap_7_outtage.player';'R2-35-00-1_cap_8','R2-35-00-1_cap_8_outtage.player';'R2-35-00-1_cap_9','R2-35-00-1_cap_9_outtage.player';'R2-35-00-1_cap_10','R2-35-00-1_cap_10_outtage.player';'R2-35-00-1_cap_11','R2-35-00-1_cap_11_outtage.player';'R2-35-00-1_cap_12','R2-35-00-1_cap_12_outtage.player';'R2-35-00-1_cap_13','R2-35-00-1_cap_13_outtage.player'};
    data.regulators={'R2-35-00-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {19526;15000;25000;166;166};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 12800;
    
    data.TOU_prices = [0.06255624,0.12511249];
    data.CPP_prices = [0.05599857,0.11199713,0.55998566];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.08859286,0.03083625];
    data.CPP_stats = [0.08370460,0.03083625];
    
    data.TOU_price_player = {'R2_3500_1_t0_TOU.player'};
    data.CPP_price_player = {'R2_3500_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R2.player'}; % player that specifies which day is a CPP day (critical_day)
    % 163 residential, 5 commercial, 0 industrial, 442 agricultural
elseif (strcmp(file_to_extract,'R3-12.47-1.glm')~=0)    
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*9.366; 
    data.avg_house = 12000;
    data.avg_commercial = 40000;
    data.EOL_points={'R3-12-47-1_node_358','ABC',1};
    data.capacitor_outtage={'R3-12-47-1_cap_1','R3-12-47-1_cap_1_outtage.player'};
    data.regulators={'R3-12-47-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 9387;
    
    data.TOU_prices = [0.05101788,0.10203575];
    data.CPP_prices = [0.04619900,0.09239799,0.46198996];
    data.TOU_hours = [15,9,6];
    data.TOU_stats = [0.07332077,0.02530702];
    data.CPP_stats = [0.06994541,0.02530702];

    data.TOU_price_player = {'R3_1247_1_t0_TOU.player'};
    data.CPP_price_player = {'R3_1247_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R3.player'}; % player that specifies which day is a CPP day (critical_day)
    % 408 residential, 59 commercial,0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R3-12.47-2.glm')~=0)    
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*4.462; 
    data.avg_house = 14000;
    data.avg_commercial = 30000;
    data.EOL_points={'R3-12-47-2_node_36','ABC',1};
    data.regulators={'R3-12-47-2_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.capacitor_outtage={};
    data.emissions_peak = 4412;
    
    data.TOU_prices = [0.04958586,0.09917172];
    data.CPP_prices = [0.04488632,0.08977263,0.44886316];
    data.TOU_hours = [15,9,6];
    data.TOU_stats = [0.07126274,0.02459668];
    data.CPP_stats = [0.06795800,0.02459668];

    data.TOU_price_player = {'R3_1247_2_t0_TOU.player'};
    data.CPP_price_player = {'R3_1247_2_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R3.player'}; % player that specifies which day is a CPP day (critical_day)
    % 0 residential, 57 commercial, 5 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R3-12.47-3.glm')~=0)
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*8.620; 
    data.avg_house = 7000;
    data.avg_commercial = 15000;
    data.EOL_points={'R3-12-47-3_node_871_2','A',1;
                     'R3-12-47-3_node_871_2','B',1;
                     'R3-12-47-3_node_871_2','C',1;
                     'R3-12-47-3_node_1844','A',2;
                     'R3-12-47-3_node_1845','B',2;
                     'R3-12-47-3_node_206','C',2};
    data.capacitor_outtage={'R3-12-47-3_cap_1','R3-12-47-3_cap_1_outtage.player';'R3-12-47-3_cap_2','R3-12-47-3_cap_2_outtage.player'};
    data.regulators={'R3-12-47-3_reg_1';'R3-12-47-3_reg_2'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 8594;
    
    data.TOU_prices = [0.04846374,0.09692747];
    data.CPP_prices = [0.04423643,0.08847287,0.44236433];
    data.TOU_hours = [15,9,6];
    data.TOU_stats = [0.06965007,0.02404006];
    data.CPP_stats = [0.06697408,0.02404006];
    
    data.TOU_price_player = {'R3_1247_3_t0_TOU.player'};
    data.CPP_price_player = {'R3_1247_3_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R3.player'}; % player that specifies which day is a CPP day (critical_day)
    data.thermal_override = 20;   %Overrides ts_penetration for the feeder
    % 1625 residential, 0 commercial, 0 industrial, 107 agricultural
elseif (strcmp(file_to_extract,'R4-12.47-1.glm')~=0)    
    data.nom_volt = 13800;
    data.feeder_rating = 1.15*5.55; 
    data.avg_house = 9000;
    data.avg_commercial = 30000;
    data.EOL_points={'R4-12-47-1_node_192','A',1;
                     'R4-12-47-1_node_198','BC',1};
    data.capacitor_outtage={'R4-12-47-1_cap_1','R4-12-47-1_cap_1_outtage.player';'R4-12-47-1_cap_2','R4-12-47-1_cap_2_outtage.player';'R4-12-47-1_cap_3','R4-12-47-1_cap_3_outtage.player';'R4-12-47-1_cap_4','R4-12-47-1_cap_4_outtage.player'};
    data.regulators={'R4-12-47-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7835;5000;10000;65;65};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 4769;
    
    data.TOU_prices = [0.05473129,0.10946257];
    data.CPP_prices = [0.04957273,0.09914547,0.49572733];
    data.TOU_hours = [14,10,6];
    data.TOU_stats = [0.07980400,0.02726980];
    data.CPP_stats = [0.07600701,0.02726980];

    data.TOU_price_player = {'R4_1247_1_t0_TOU.player'};
    data.CPP_price_player = {'R4_1247_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R4.player'}; % player that specifies which day is a CPP day (critical_day)
    data.thermal_override = 20;   %Overrides ts_penetration for the feeder
    % 476 residential, 75 commercial, 0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R4-12.47-2.glm')~=0)    
    data.nom_volt = 12500;
    data.feeder_rating = 1.15*2.249; 
    data.avg_house = 6000;
    data.avg_commercial = 20000;
    data.EOL_points={'R4-12-47-2_node_180','A',1;
                     'R4-12-47-2_node_264','B',1;
                     'R4-12-47-2_node_256','C',1};
    data.capacitor_outtage={};
    data.regulators={'R4-12-47-2_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 2316;
    
    data.TOU_prices = [0.06029197,0.12058393];
    data.CPP_prices = [0.05444187,0.10888374,0.54441871];
    data.TOU_hours = [14,10,6];
    data.TOU_stats = [0.08791206,0.03004040];
    data.CPP_stats = [0.08347258,0.03004040];

    data.TOU_price_player = {'R4_1247_2_t0_TOU.player'};
    data.CPP_price_player = {'R4_1247_2_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R4.player'}; % player that specifies which day is a CPP day (critical_day)
    % 176 residential, 21 commercial, 0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R4-25.00-1.glm')~=0)    
    data.nom_volt = 24900;
    data.feeder_rating = 1.15*0.934; 
    data.avg_house = 6000;
    data.avg_commercial = 20000;
    data.EOL_points={'R4-25-00-1_node_230','A',1;
                     'R4-25-00-1_node_122','B',1;
                     'R4-25-00-1_node_168','C',1};
    data.capacitor_outtage={};
    data.regulators={'R4-25-00-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {14136;12000;16000;120;120};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 962;
    
    data.TOU_prices = [0.06277164,0.12554328];
    data.CPP_prices = [0.05679098,0.11358196,0.56790981];
    data.TOU_hours = [14,10,6];
    data.TOU_stats = [0.09152768,0.03127590];
    data.CPP_stats = [0.08707433,0.03127590];

    data.TOU_price_player = {'R4_2500_1_t0_TOU.player'};
    data.CPP_price_player = {'R4_2500_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R4.player'}; % player that specifies which day is a CPP day (critical_day)
    data.thermal_override = 100;   %Overrides ts_penetration for the region to ensure at least one gets populated - percentage 
    % 140 residential, 1 commercial, 0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R5-12.47-1.glm')~=0)    
    data.nom_volt = 13800;
    data.feeder_rating = 1.15*9.473; 
    data.avg_house = 6500;
    data.avg_commercial = 20000;
    data.EOL_points={'R5-12-47-1_node_1','ABC',1};
    data.capacitor_outtage={'R5-12-47-1_cap_1','R5-12-47-1_cap_1_outtage.player';'R5-12-47-1_cap_2','R5-12-47-1_cap_2_outtage.player';'R5-12-47-1_cap_3','R5-12-47-1_cap_3_outtage.player'};
    data.regulators={'R5-12-47-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7835;5000;10000;65;65};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 9734;
    
    data.TOU_prices = [0.06130809,0.12261618];
    data.CPP_prices = [0.05615623,0.11231246,0.56156232];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.08682521,0.03022099];
    data.CPP_stats = [0.08394027,0.03022099];
    
    data.TOU_price_player = {'R5_1247_1_t0_TOU.player'};
    data.CPP_price_player = {'R5_1247_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R5.player'}; % player that specifies which day is a CPP day (critical_day)
    data.thermal_override = 20;   %Overrides ts_penetration for the feeder
    % 185 residential, 48 commercial, 0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R5-12.47-2.glm')~=0)    
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*4.878; 
    data.avg_house = 4500;
    data.avg_commercial = 15000;
    data.EOL_points={'R5-12-47-2_node_114','A',1;
                     'R5-12-47-2_node_158','B',1;
                     'R5-12-47-2_node_293','C',1};
    data.capacitor_outtage={'R5-12-47-2_cap_1','R5-12-47-2_cap_1_outtage.player'};
    data.regulators={'R5-12-47-2_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 5071;
    
    data.TOU_prices = [0.05898112,0.11796224];
    data.CPP_prices = [0.05387308,0.10774615,0.53873076];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.08352973,0.02907395];
    data.CPP_stats = [0.08052749,0.02907395];

    data.TOU_price_player = {'R5_1247_2_t0_TOU.player'};
    data.CPP_price_player = {'R5_1247_2_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R5.player'}; % player that specifies which day is a CPP day (critical_day)
    % 138 residential, 46 commercial, 0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R5-12.47-3.glm')~=0)    
    data.nom_volt = 13800;
    data.feeder_rating = 1.15*9.924; 
    data.avg_house = 4000;
    data.avg_commercial = 15000;
    data.EOL_points={'R5-12-47-3_node_294_2','ABC',1;
                     'R5-12-47-3_node_334_2','ABC',1;
                     'R5-12-47-3_node_974_2','ABC',1;
                     'R5-12-47-3_node_465','A',2;
                     'R5-12-47-3_node_68','B',2
                     'R5-12-47-3_node_470','C',2
                     'R5-12-47-3_node_1278','ABC',3;
                     'R5-12-47-3_node_749','ABC',4}; %18 Measurements because of voltage regulator
    data.capacitor_outtage={'R5-12-47-3_cap_1','R5-12-47-3_cap_1_outtage.player';'R5-12-47-3_cap_2','R5-12-47-3_cap_2_outtage.player';'R5-12-47-3_cap_3','R5-12-47-3_cap_3_outtage.player';'R5-12-47-3_cap_4','R5-12-47-3_cap_4_outtage.player';'R5-12-47-3_cap_5','R5-12-47-3_cap_5_outtage.player';'R5-12-47-3_cap_6','R5-12-47-3_cap_6_outtage.player';'R5-12-47-3_cap_7','R5-12-47-3_cap_7_outtage.player';'R5-12-47-3_cap_8','R5-12-47-3_cap_8_outtage.player';'R5-12-47-3_cap_9','R5-12-47-3_cap_9_outtage.player';'R5-12-47-3_cap_10','R5-12-47-3_cap_10_outtage.player';'R5-12-47-3_cap_11','R5-12-47-3_cap_11_outtage.player';'R5-12-47-3_cap_12','R5-12-47-3_cap_12_outtage.player';'R5-12-47-3_cap_13','R5-12-47-3_cap_13_outtage.player'};
    data.regulators={'R5-12-47-3_reg_1';'R5-12-47-3_reg_2';'R5-12-47-3_reg_3';'R5-12-47-3_reg_4'}; % The regulators are not coordinated because of their operation on parallel branches.
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7835;5000;10000;65;65};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 10734;
    
    data.TOU_prices = [0.06216276,0.12432553];
    data.CPP_prices = [0.05677767,0.11355535,0.56777673];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.08803561,0.03064229];
    data.CPP_stats = [0.08486918,0.03064229];

    data.TOU_price_player = {'R5_1247_3_t0_TOU.player'};
    data.CPP_price_player = {'R5_1247_3_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R5.player'}; % player that specifies which day is a CPP day (critical_day)
    data.thermal_override = 20;   %Overrides ts_penetration for the feeder
    % 1196 residential, 182 commercial, 0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R5-12.47-4.glm')~=0)    
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*7.612; 
    data.avg_house = 6000;
    data.avg_commercial = 30000;
    data.EOL_points={'R5-12-47-4_node_555','ABC',1};
    data.capacitor_outtage={'R5-12-47-4_cap_1','R5-12-47-4_cap_1_outtage.player';'R5-12-47-4_cap_2','R5-12-47-4_cap_2_outtage.player';'R5-12-47-4_cap_3','R5-12-47-4_cap_3_outtage.player'};
    data.regulators={'R5-12-47-4_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 7636;
    
    data.TOU_prices = [0.06255503,0.12511006];
    data.CPP_prices = [0.05717812,0.11435623,0.57178115];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.08859114,0.03083566];
    data.CPP_stats = [0.08546774,0.03083566];

    data.TOU_price_player = {'R5_1247_4_t0_TOU.player'};
    data.CPP_price_player = {'R5_1247_4_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R5.player'}; % player that specifies which day is a CPP day (critical_day)
    data.thermal_override = 20;   %Overrides ts_penetration for the feeder
    % 175 residential, 31 commercial, 0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R5-12.47-5.glm')~=0)    
    data.nom_volt = 12470;
    data.feeder_rating = 1.15*9.125; 
    data.avg_house = 4500;
    data.avg_commercial = 25000;
    data.EOL_points={'R5-12-47-5_node_61','A',1;
                     'R5-12-47-5_node_382','B',1;
                     'R5-12-47-5_node_559','C',1};
    data.capacitor_outtage={'R5-12-47-5_cap_1','R5-12-47-5_cap_1_outtage.player';'R5-12-47-5_cap_2','R5-12-47-5_cap_2_outtage.player';'R5-12-47-5_cap_3','R5-12-47-5_cap_3_outtage.player'};
    data.regulators={'R5-12-47-5_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {7080;5000;9000;60;60};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 9369;
    
    data.TOU_prices = [0.06498171,0.12996341];
    data.CPP_prices = [0.05933887,0.11867773,0.59338866];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.09202783,0.03203185];
    data.CPP_stats = [0.08869755,0.03203185];

    data.TOU_price_player = {'R5_1247_5_t0_TOU.player'};
    data.CPP_price_player = {'R5_1247_5_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R5.player'}; % player that specifies which day is a CPP day (critical_day)
    data.thermal_override = 20;   %Overrides ts_penetration for the feeder
    % 352 residential, 28 commercial, 0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R5-25.00-1.glm')~=0)    
    data.nom_volt = 22900;
    data.feeder_rating = 1.15*12.346; 
    data.avg_house = 3000;
    data.avg_commercial = 20000;
    data.EOL_points={'R5-25-00-1_node_469','A',1;
                     'R5-25-00-1_node_501','B',1;
                     'R5-25-00-1_node_785','C',1};
    data.capacitor_outtage={'R5-25-00-1_cap_1','R5-25-00-1_cap_1_outtage.player';'R5-25-00-1_cap_2','R5-25-00-1_cap_2_outtage.player';'R5-25-00-1_cap_3','R5-25-00-1_cap_3_outtage.player';'R5-25-00-1_cap_4','R5-25-00-1_cap_4_outtage.player'};
    data.regulators={'R5-25-00-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {13000;10000;16000;110;110};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 12691;
    
    data.TOU_prices = [0.06636210,0.13272419];
    data.CPP_prices = [0.06058412,0.12116824,0.60584119];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.09398275,0.03271230];
    data.CPP_stats = [0.09055891,0.03271230];
    
    data.TOU_price_player = {'R5_2500_1_t0_TOU.player'};
    data.CPP_price_player = {'R5_2500_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R5.player'}; % player that specifies which day is a CPP day (critical_day)
    % 370 residential, 14 commercial, 0 industrial, 0 agricultural
elseif (strcmp(file_to_extract,'R5-35.00-1.glm')~=0)
    data.nom_volt = 34500;
    data.feeder_rating = 1.15*12.819; 
    data.avg_house = 6000;
    data.avg_commercial = 25000;
    data.EOL_points={'R5-35-00-1_node_155','A',1;
                     'R5-35-00-1_node_184','B',1;
                     'R5-35-00-1_node_85','C',1};
    data.capacitor_outtage={'R5-35-00-1_cap_1','R5-35-00-1_cap_1_outtage.player'};
    data.regulators={'R5-35-00-1_reg_1'};
    data.peak_vvo_player = {[strrep(file_to_extract,'.glm','') '_vvo.player']};
    data.voltage_regulation = {19526;15000;25000;166;166};% desired;min;max;high deadband;low deadband
    data.emissions_peak = 12989;
    
    data.TOU_prices = [0.06599171,0.13198343];
    data.CPP_prices = [0.06024200,0.12048400,0.60242002];
    data.TOU_hours = [16,8,6];
    data.TOU_stats = [0.09345821,0.03252972];
    data.CPP_stats = [0.09004753,0.03252972];

    data.TOU_price_player = {'R5_3500_1_t0_TOU.player'};
    data.CPP_price_player = {'R5_3500_1_t0_CPP.player'};
    data.CPP_flag = {'CPP_days_R5.player'}; % player that specifies which day is a CPP day (critical_day)
    % 192 residential, 47 commercial, 0 industrial, 0 agricultural
end

end
    
    