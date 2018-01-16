%This function takes handles the inputs sent to the function to use device
%specific inputs and out_temp types
%out_temp : a csv file containing outdoor temperature
function VB_func(out_temp,device_type, device_parameters)
try
if out_temp == 94128 
    out_temp = 'outdoor_temperature_zipCode_94128.csv';
    tempData = csvread(which(out_temp));
    temperature_a=tempData(:,2);
elseif out_temp == 97218
    out_temp = 'outdoor_temperature_zipCode_97218.csv';
    tempData = csvread(which(out_temp));
    temperature_a=tempData(:,2);
elseif out_temp == 98158
    out_temp = 'outdoor_temperature_zipCode_98158.csv';
    tempData = csvread(which(out_temp));
    temperature_a=tempData(:,2);
elseif strcmp(out_temp,'default')
    out_temp = 'outdoor_temperature.csv';
    tempData = csvread(which(out_temp));
    temperature_a=tempData(:,2);
elseif strcmp(out_temp(end-2:end),'csv')
    tempData = csvread(out_temp);
    temperature_a=tempData(:,1);
else
    temperature_a = VB_TMY3(out_temp)';
end

if device_type == 3
    temperature_a = 20*ones(8760,1);
end

paraFile = device_parameters;

switch device_type
    case 1
        [P_lower, P_upper, E_UL] = VB_core_TCL(paraFile, temperature_a,device_type);
    case 2
        [P_lower, P_upper, E_UL] = VB_core_TCL(paraFile, temperature_a,device_type);
    case 3
        [P_lower, P_upper, E_UL] = VB_core_TCL(paraFile, temperature_a,device_type);
    case 4
        [P_upper, P_lower, E_UL] = VB_core_WH(paraFile);
end

if device_type == 4
    P_lower = P_lower';
    P_upper = P_upper';
end

P_lower
disp('n')
P_upper
disp('n')
E_UL
disp('')
catch error
    disp(error)
end
    
%% write output file
% if ischar(paraFile)
%     plotname = num2str(strrep(paraFile,'.csv',''));
% else
%     plotname = num2str(paraFile);
% end
% plotname = num2str(strrep(paraFile,'.csv',''));
% output_file = strcat('VB_output_', plotname, '.csv');
% output_file = 'VB_output.csv';
% fid = fopen(output_file,'w');
% fprintf(fid, 'upper_power(kW), lower_power(kW), upper_energy(kWh), lower_energy(kWh)\n');
% for i = 1:length(P_upper)
%     fprintf(fid, '%f, %f, %f, %f\n', P_upper(i), -P_lower(i), E_UL(i), -E_UL(i));    
% end
% fclose(fid);

%% plot
% plotname = strrep(plotname,'_',' ');
% 
% figure
% subplot(2,1,1)
% plot(P_upper)
% hold on
% plot(-P_lower,'r')
% plot(zeros(length(P_upper),1),'k--')
%                 % title(strcat(plotname,' Power'))
% ylabel('Power (kW)')
% xlabel('Time (timestep)')
% subplot(2,1,2)
% plot(E_UL)
% 
% hold on
% plot(-E_UL,'r')
% plot(zeros(length(E_UL),1),'k--')
%                     % title(strcat(plotname,' Energy'))
% ylabel('Energy (kWh)')
% xlabel('Time (timestep)')