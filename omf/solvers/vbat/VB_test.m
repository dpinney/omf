% Comment and uncomment to test
% VB_func(temperature,device#, custom_device_parameters)
% temperature is a csv containing a time stamp and a temperature
% custom_device_parameters

% VB_func('outdoor_temperature.csv',1,0) %AC

% VB_func('outdoor_temperature.csv',2,0) %HP

% VB_func('outdoor_temperature.csv',3,0) %RG

% VB_func('outdoor_temperature.csv',4,0) %WH

%%% User inputed parameters

% VB_func('outdoor_temperature.csv',2,'para_special.csv') 

% VB_func('outdoor_temperature.csv',2,[1,2,3,4,5,6,7]) 

%%% Zipcodes
% 94128
% 97218
% 98158

% VB_func(98158,1,0)

% VB_func(94128,1,[5.6,100,2,2.5,22.5,.625,50])

% VB_func(94128,4,[2,2,5.6,2.5,0.625,22.5,1])

VB_func('ALTURAS',1,[2,2,5.6,2.5,0.625,22.5,1])

% VB_func(94128,2,0)

% disp('Running VB_test.m')
% disp(num2str([1,4,5,3]))
% [1,4,5];
% fid = fopen('blah.csv','w');
% fprintf(fid, 'jiewflj wliejf lwijef')
