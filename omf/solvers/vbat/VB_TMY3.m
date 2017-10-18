function [paraTemp] = VB_TMY3(city)
load('geodata.mat');
temp = csvread('temp.csv');
    for i = 1:length(geodata)
        if strcmp(geodata(i,2),city)
            paraTemp = temp(i,:);
        end  
    end
end