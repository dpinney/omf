% This function takes a city as an input and returns a set of 8760
% datapoints
function [paraTemp] = VB_TMY3(city)
load('geodata.mat');
temp = csvread(which('temp.csv'));
    for i = 1:length(geodata)
        if strcmp(geodata(i,2),city)
            paraTemp = temp(i,:);
        end  
    end
end