clear;
clc;

% Set technology to test
TechnologyToTest=15;
    % 0 - Base
    % 1 - CVR for Energy Reduction
    % 101 - CVR for Peak Reduction
    % 2 - Automation
    % 3 - FDIR
    % 4 - TOU/CPP w/ tech
    % 5 - TOU/CPP w/o tech
    % 6 - TOU w/ tech
    % 7 - TOU w/o tech
    % 8 - DLC
    % 9 - Thermal
    % 10 - PHEV
    % 11 - Solar Residential
    % 12 - Solar Commercial
    % 13 - Solar Combined
    % 14 - Wind Commercial
    % 15 - CVR, TOU/CPP, Solar, PHEV, Energy Storage

% Load the user configuration for different files, flags, etc.
[LUSolverVal,taxonomy_files,taxonomy_directory,output_directory,my_region] = user_configuration('Andy');

%% Start extraction
[no_of_tax,junk] = size(taxonomy_files);
region_count = 0; % for commercial feeders

for tax_ind=1:no_of_tax 
    % File to extract   
    file_to_extract = taxonomy_files{tax_ind};
    extraction_file = [taxonomy_directory,file_to_extract];
    
    % Get the region - this will only work automatically with the taxonomy feeders
    %    otherwise, use the my_region flag     
    token = strtok(file_to_extract,'-');
    token2 = strrep(token,'R','');
    if (strcmp(token2,'GC') ~= 0) %commercial
        region_count = region_count + 1;
        region = region_count;
    else
        region = str2double(token2);
    end
    
    if (my_region ~= 0)
        old_region = region;
        region = my_region;
    end
    
    % Load in the regional information
    regional_data = regionalization(region);

    % Get information particular to each of the taxonomy feeders
    taxonomy_data = TaxFeederData(file_to_extract,region);

    % Weather Data
    tmy = regional_data.weather;

    %% These are the default flag settings 
    %  They get overridden inside of TechnologyParameters.m, if a tech_flag is set

    % Residential Homes? - FINISHED
    use_flags.use_homes = 1;

    % Batteries? - FINISHED
    use_flags.use_batt = 0; %1 = add a battery at every center tap, 2 = add at substation, 0 = none
                  % also creates the correct file name
                  % Define the size of the battery - distributed will divide by the number of batts created

    % Markets? - NOT FINISHED
    use_flags.use_market = 0; % 0 = NONE, 1 = BIDDING, 2 = PASSIVE (NON-BIDDING)
                    % NOTE: using passive overrides statistics in market_info
                    % and defaults to 24 hour statistics

    % Commercial Buildings - FINISHED
    % these may be used to represent large 3-ph loads as ziploads (0) or buildings (1)
    use_flags.use_commercial = 1; 

    % VVC? - FINISHED
    use_flags.use_vvc = 0; % 0 = NONE, 1 = TRUE

    % Customer Billing? - NOT FINISHED
    use_flags.use_billing = 0; %0 = NONE, 1 = FLAT, 2 = TIERED, 3 = RTP (gets price from auction)

    % Solar? - FINISHED
    use_flags.use_solar = 0;  % for combined res & comm solar
    use_flags.use_solar_res = 0;  % for residential solar
    use_flags.use_solar_com = 0; % for commercial solar
    
    
    % Energy Storage - Finished
    use_flags.use_energy_storage = 0;
    use_flags.use_energy_storage_res = 0;
    use_flags.use_energy_storage_com = 0;
    
    % PHEV? - FINISHED
    use_flags.use_phev = 0;

    % Distribution Automation? - FINISHED
    use_flags.use_da = 0;

    % Wind turbines - NOT FINISHED
    use_flags.use_wind = 0;
    
    % Use the emissions object? - FINISHED
    use_flags.use_emissions = 0;
    
    % Use the Thermal Storage object? - FINISHED
    use_flags.use_ts = 0;
    %1 = add thermal storage using the defaults, 2 = add thermal storage with a randomized schedule, 0 = none
    %3 = add thermal storage to all houses using defaults, 4 = add thermal storage to all houses with a randomized schedule

    %% Get the technical parameters
    [tech_data,use_flags] = TechnologyParameters(use_flags,TechnologyToTest);

    %% NO MODIFICATIONS AFTER HERE
    file2 = strrep(file_to_extract,'.glm','');
    file3 = strrep(file2,'.','');
    file4 = strrep(file3,'-','_');

    if (strcmp(token2,'GC') ~= 0) %commercial
        tech_file = [file4,'_t',num2str(tech_data.tech_flag),'_r',num2str(region)];
    elseif (my_region == 0)
        tech_file = [file4,'_t',num2str(tech_data.tech_flag)];
    else
        file5 = strrep(file4,['R' num2str(old_region)],'R6');
        tech_file = [file5,'_t',num2str(tech_data.tech_flag)];
    end
    filename = [tech_file,'.glm'];

    read_file = fopen(extraction_file,'r');

    no = num2str(2);
    fid_name = [output_directory,filename];
    write_file = fopen(fid_name,'w');

    test = textscan(read_file,'%s %s %s %s %s %s %s %s');
    [c,d] = size(test);
    [a,b] = size(test{1});

    % Initialize pseudo-random numbers
    [s1,s2,s3,s4,s5,s6,s7] = RandStream.create('mrg32k3a','NumStreams',7);
    RandStream.setGlobalStream(s1);

    % Split up the configurations and feeder information into 2 different
    % arrays
    for i=1:a
        %TODO: add in catches for new objects (relays, etc.)
        % -- Definitely reclosers

        % Fill in the last line, cuz the array isn't almost never the same size 
        if (i == a)
            if (length(strfind(test{1}{i},'}')) ~= 0)
                for jindex = 2:d
                    test{jindex}{i} = '';
                end
            end
            break;
        end
        % Store the name, just in case I need it
        if (length(strfind(char(test{1}{i}),'name')) ~= 0)
            my_name = char(test{2}{i});
        end

        % Remove id references and replace with names as neccessary
        if (length(strfind(char(test{2}{i}),'fuse:')) ~= 0)
            test{2}{i} = 'fuse';
    %     elseif (length(strfind(char(test{1}{i}),'current_limit')) ~= 0)
    %         test{2}{i} = '1000;';
        elseif (length(strfind(char(test{2}{i}),'load:')) ~= 0)
            test{2}{i} = 'load';
        elseif (length(strfind(char(test{2}{i}),'triplex_meter:')) ~= 0)
            test{2}{i} = 'triplex_meter';
        elseif (length(strfind(char(test{2}{i}),'meter:')) ~= 0)
            test{2}{i} = 'meter';
        elseif (length(strfind(char(test{2}{i}),'triplex_node:')) ~= 0)
            test{2}{i} = 'triplex_node';
        elseif (length(strfind(char(test{2}{i}),'node:')) ~= 0)
            test{2}{i} = 'node';
        elseif (length(strfind(char(test{2}{i}),'switch:')) ~= 0)
            test{2}{i} = 'switch';
        elseif (length(strfind(char(test{2}{i}),'recloser:')) ~= 0)
            test{2}{i} = 'recloser';
        elseif (length(strfind(char(test{2}{i}),'overhead_line:')) ~= 0)
            test{2}{i} = 'overhead_line';
        elseif (length(strfind(char(test{2}{i}),'regulator:')) ~= 0)
            test{2}{i} = 'regulator';
        elseif (length(strfind(char(test{2}{i}),'transformer:')) ~= 0)
            test{2}{i} = 'transformer';
        elseif (length(strfind(char(test{2}{i}),'capacitor:')) ~= 0)
            test{2}{i} = 'capacitor';
        elseif (length(strfind(char(test{2}{i}),'triplex_line_conductor:')) ~= 0)
            if (length(strfind(char(test{1}{i}),'object')) ~= 0)
                m = 0;
                while (strcmp(char(test{1}{i+m}),'}') ~= 1)
                    for r=1:d
                        config{r}{i+m} = test{r}{i+m};
                        test{r}{i+m} = '';
                    end
                    m = m+1;
                end
                if (strcmp(char(test{1}{i+m}),'}') == 1)
                    config{1}{i+m} = test{1}{i+m};
                    for p=2:d
                        test{p}{i+m}= '';
                        config{p}{i+m}= '';
                    end
                    test{1}{i+m} = '';
                end
            elseif (length(strfind(char(test{1}{i}),'configuration')) ~= 0)
                temp = strrep(test{2}{i},'triplex_line_conductor:','');
                temp2 = strcat('triplex_line_conductor_',temp);
                test{2}{i} = temp2;
            else
                disp('I missed something. Check line 75ish, i = %d',i);
            end
        elseif (length(strfind(char(test{2}{i}),'triplex_line:')) ~= 0)
            test{2}{i} = 'triplex_line';
        elseif (length(strfind(char(test{2}{i}),'underground_line:')) ~= 0)
            test{2}{i} = 'underground_line';
        % Move all of the configuration files into a different array
        elseif (length(strfind(char(test{2}{i}),'triplex_line_configuration:')) ~= 0)
            if (length(strfind(char(test{1}{i}),'object')) ~= 0)
                m = 0;
                while (strcmp(char(test{1}{i+m}),'}') ~= 1)
                    for r=1:d
                        config{r}{i+m} = test{r}{i+m};
                        test{r}{i+m} = '';
                    end
                    m = m+1;
                end
                if (strcmp(char(test{1}{i+m}),'}') == 1)
                    config{1}{i+m} = test{1}{i+m};
                    for p=2:d
                        test{p}{i+m}= '';
                        config{p}{i+m}= '';
                    end
                    test{1}{i+m} = '';
                end
            elseif (length(strfind(char(test{1}{i}),'configuration')) ~= 0)
                temp = strrep(test{2}{i},'triplex_line_configuration:','');
                temp2 = strcat('triplex_line_configuration_',temp);
                test{2}{i} = temp2;
            else
                disp('I missed something. Check line 50ish, i = %d',i);
            end
        elseif (length(strfind(char(test{2}{i}),'line_configuration:')) ~= 0)
            if (length(strfind(char(test{1}{i}),'object')) ~= 0)
                m = 0;
                while (strcmp(char(test{1}{i+m}),'}') ~= 1)
                    for r=1:d
                        config{r}{i+m} = test{r}{i+m};
                        test{r}{i+m} = '';
                    end
                    m = m+1;
                end
                if (strcmp(char(test{1}{i+m}),'}') == 1)
                    config{1}{i+m} = test{1}{i+m};
                    for p=2:d
                        test{p}{i+m}= '';
                        config{p}{i+m}= '';
                    end
                    test{1}{i+m} = '';
                end
            elseif (length(strfind(char(test{1}{i}),'configuration')) ~= 0)
                temp = strrep(test{2}{i},'line_configuration:','');
                temp2 = strcat('line_configuration_',temp);
                test{2}{i} = temp2;
            else
                disp('I missed something. Check line 131ish, i = %d',i);
            end
        elseif (length(strfind(char(test{2}{i}),'line_spacing:')) ~= 0)
            if (length(strfind(char(test{1}{i}),'object')) ~= 0)
                m = 0;
                while (strcmp(char(test{1}{i+m}),'}') ~= 1)
                    for r=1:d
                        config{r}{i+m} = test{r}{i+m};
                        test{r}{i+m} = '';
                    end
                    m = m+1;
                end
                if (strcmp(char(test{1}{i+m}),'}') == 1)
                    config{1}{i+m} = test{1}{i+m};
                    for p=2:d
                        test{p}{i+m}= '';
                        config{p}{i+m}= '';
                    end
                    test{1}{i+m} = '';
                end
            else
                disp('I missed something. Check line 152ish, i = %d',i);
            end
        elseif (length(strfind(char(test{2}{i}),'overhead_line_conductor:')) ~= 0)
            if (length(strfind(char(test{1}{i}),'object')) ~= 0)
                m = 0;
                while (strcmp(char(test{1}{i+m}),'}') ~= 1)
                    for r=1:d
                        config{r}{i+m} = test{r}{i+m};
                        test{r}{i+m} = '';
                    end
                    m = m+1;
                end
                if (strcmp(char(test{1}{i+m}),'}') == 1)
                    config{1}{i+m} = test{1}{i+m};
                    for p=2:d
                        test{p}{i+m}= '';
                        config{p}{i+m}= '';
                    end
                    test{1}{i+m} = '';
                end
            else
                disp('I missed something. Check line 173ish, i = %d',i);
            end
        elseif (length(strfind(char(test{2}{i}),'underground_line_conductor:')) ~= 0)
            if (length(strfind(char(test{1}{i}),'object')) ~= 0)
                m = 0;
                while (strcmp(char(test{1}{i+m}),'}') ~= 1)
                    for r=1:d
                        config{r}{i+m} = test{r}{i+m};
                        test{r}{i+m} = '';
                    end
                    m = m+1;
                end
                if (strcmp(char(test{1}{i+m}),'}') == 1)
                    config{1}{i+m} = test{1}{i+m};
                    for p=2:d
                        test{p}{i+m}= '';
                        config{p}{i+m}= '';
                    end
                    test{1}{i+m} = '';
                end
            else
                disp('I missed something. Check line 194ish, i = %d',i);
            end 
        elseif (length(strfind(char(test{2}{i}),'regulator_configuration:')) ~= 0)
            if (length(strfind(char(test{1}{i}),'object')) ~= 0)
                m = 0;
                while (strcmp(char(test{1}{i+m}),'}') ~= 1)
                    for r=1:d
                        config{r}{i+m} = test{r}{i+m};
                        test{r}{i+m} = '';
                    end
                    m = m+1;
                end
                if (strcmp(char(test{1}{i+m}),'}') == 1)
                    config{1}{i+m} = test{1}{i+m};
                    for p=2:d
                        test{p}{i+m}= '';
                        config{p}{i+m}= '';
                    end
                    test{1}{i+m} = '';
                end
            elseif (length(strfind(char(test{1}{i}),'configuration')) ~= 0)
                temp = strrep(test{2}{i},'regulator_configuration:','');
                temp2 = strcat('regulator_configuration_',temp);
                test{2}{i} = temp2;    
            else
                disp('I missed something. Check line 220ish, i = %d',i);
            end
            elseif (length(strfind(char(test{2}{i}),'transformer_configuration:')) ~= 0)
            if (length(strfind(char(test{1}{i}),'object')) ~= 0)
                m = 0;
                while (strcmp(char(test{1}{i+m}),'}') ~= 1)
                    for r=1:d
                        config{r}{i+m} = test{r}{i+m};
                        test{r}{i+m} = '';
                    end
                    m = m+1;
                end
                if (strcmp(char(test{1}{i+m}),'}') == 1)
                    config{1}{i+m} = test{1}{i+m};
                    for p=2:d
                        test{p}{i+m}= '';
                        config{p}{i+m}= '';
                    end
                    test{1}{i+m} = '';
                end
            elseif (length(strfind(char(test{1}{i}),'configuration')) ~= 0)
                temp = strrep(test{2}{i},'transformer_configuration:','');
                temp2 = strcat('transformer_configuration_',temp);
                test{2}{i} = temp2;
            else
                disp('I missed something. Check line 245ish, i = %d',i);
            end
        elseif (length(strfind(char(test{2}{i}),'SWING')) ~= 0)
            for kk=1:d
                test{kk}{i}='';
            end

            swing_node = my_name;
        elseif (length(strfind(char(test{2}{i}),'recorder')) ~= 0)
            if (length(strfind(char(test{1}{i}),'object')) ~= 0)
                m = 0;
                while (strcmp(char(test{1}{i+m}),'};') ~= 1)
                    for r=1:d
                        %config{r}{i+m} = test{r}{i+m};
                        test{r}{i+m} = '';
                    end
                    m = m+1;
                end
                if (strcmp(char(test{1}{i+m}),'};') == 1)
                    %config{1}{i+m} = test{1}{i+m};
                    for p=2:d
                        test{p}{i+m}= '';
                        %config{p}{i+m}= '';
                    end
                    test{1}{i+m} = '';
                end

                if (m == 0) %do the same without the ';'
                    while (strcmp(char(test{1}{i+m}),'}') ~= 1)
                        for r=1:d
                            %config{r}{i+m} = test{r}{i+m};
                            test{r}{i+m} = '';
                        end
                        m = m+1;
                    end
                    if (strcmp(char(test{1}{i+m}),'}') == 1)
                        %config{1}{i+m} = test{1}{i+m};
                        for p=2:d
                            test{p}{i+m}= '';
                            %config{p}{i+m}= '';
                        end
                        test{1}{i+m} = '';
                    end
                end
            end
        end


        % Strip off all of the stuff I don't want
        if (length(strfind(char(test{1}{i}),'//')) ~= 0)
            for n=1:d
                test{n}{i} = '';
            end
        elseif (length(strfind(char(test{1}{i}),'clock')) ~= 0)
            for n=1:d
                test{n}{i} = '';
            end
        elseif (length(strfind(char(test{1}{i}),'solver_method')) ~= 0)
            for n=1:d
                test{n}{i} = '';
            end
        elseif (length(strfind(char(test{1}{i}),'module')) ~= 0)
            for n=1:d
                test{n}{i} = '';
            end
        elseif (length(strfind(char(test{1}{i}),'timestamp')) ~= 0)
            for n=1:d
                test{n}{i} = '';
            end
        elseif (length(strfind(char(test{1}{i}),'stoptime')) ~= 0)
            for n=1:d
                test{n}{i} = '';
            end
        elseif (length(strfind(char(test{1}{i}),'#set')) ~= 0)
            for n=1:d
                test{n}{i} = '';
            end
        elseif (length(strfind(char(test{1}{i}),'timezone')) ~= 0)
            for n=1:d
                test{n}{i} = '';
                test{n}{i+1} = '';
            end
        elseif (length(strfind(char(test{1}{i}),'default_maximum_voltage_error')) ~= 0)
            for n=1:d
                test{n}{i} = '';
                test{n}{i+1} = '';
            end
        end
    end

    % Get rid of all those pesky spaces in the "feeder" file
    nn=1;
    for i=1:a
        test_me = 0;
        for j=1:d
            if (strcmp(char(test{j}{i}),'')~=0)
                test_me = test_me+1;
            end
        end
        if (test_me == d)
            %do nothing cuz the lines are blank
        elseif (length(strfind(char(test{3}{i}),'{')) ~= 0)
            for j=1:d
                glm_final{j}{nn} = test{j}{i};
            end
            nn = nn + 1;
        elseif (length(strfind(char(test{1}{i}),'}')) ~= 0)
            for j=1:d
                glm_final{j}{nn} = test{j}{i};
            end
            nn = nn + 1;
        else
            for j=1:d
                if (j==1)
                    glm_final{j}{nn} = '     ';
                else
                    glm_final{j}{nn} = test{j-1}{i};
                end
            end
            nn = nn + 1;
        end

    end

    % Get rid of those nasty blank lines in the configuration file and re-name
    % the configurations to get rid of all id references and use names
    mm=1;
    [x,y]=size(config{1});
    for i=1:y
        test_me = 0;
        for j=1:d
            if (strcmp(char(config{j}{i}),'')~=0)
                test_me = test_me+1;
            end
        end
        if (test_me == d)
            %do nothing cuz the lines are blank
        elseif (length(strfind(char(config{2}{i}),'triplex_line_configuration:')) ~= 0)
            for j=1:d
                if (j==3)
                    config_final{j}{mm} = config{j}{i};
                    temp = strrep(config{2}{i},'triplex_line_configuration:','');
                    temp2 = strcat('triplex_line_configuration_',temp,';');
                    config_final{j}{mm+1} = temp2;
                elseif (j==2)
                    config_final{2}{mm} = 'triplex_line_configuration';
                    config_final{2}{mm+1} = 'name';
                elseif (j==1)
                    config_final{j}{mm} = config{j}{i};
                    config_final{j}{mm+1} ='     ';
                else    
                    config_final{j}{mm} = config{j}{i};
                    config_final{j}{mm+1} ='';
                end
            end
            mm = mm + 2;
        elseif (length(strfind(char(config{2}{i}),'line_configuration:')) ~= 0)
            for j=1:d
                if (j==3)
                    config_final{j}{mm} = config{j}{i};
                    temp = strrep(config{2}{i},'line_configuration:','');
                    temp2 = strcat('line_configuration_',temp,';');
                    config_final{j}{mm+1} = temp2;
                elseif (j==2)
                    config_final{2}{mm} = 'line_configuration';
                    config_final{2}{mm+1} = 'name';
                elseif (j==1)
                    config_final{j}{mm} = config{j}{i};
                    config_final{j}{mm+1} ='     ';
                else    
                    config_final{j}{mm} = config{j}{i};
                    config_final{j}{mm+1} ='';
                end
            end
            mm = mm + 2;
        elseif (length(strfind(char(config{2}{i}),'transformer_configuration:')) ~= 0)
            for j=1:d
                if (j==3)
                    config_final{j}{mm} = config{j}{i};
                    temp = strrep(config{2}{i},'transformer_configuration:','');
                    temp2 = strcat('transformer_configuration_',temp,';');
                    config_final{j}{mm+1} = temp2;
                elseif (j==2)
                    config_final{2}{mm} = 'transformer_configuration';
                    config_final{2}{mm+1} = 'name';
                elseif (j==1)
                    config_final{j}{mm} = config{j}{i};
                    config_final{j}{mm+1} ='     ';
                else    
                    config_final{j}{mm} = config{j}{i};
                    config_final{j}{mm+1} ='';
                end
            end
            mm = mm + 2;
        elseif (length(strfind(char(config{1}{i}),'}')) ~= 0)
            for j=1:d
                config_final{j}{mm} = config{j}{i};
            end
            mm = mm + 1;
        elseif (length(strfind(char(config{2}{i}),'triplex_line_conductor:')) ~= 0)
            for j=1:d
                if (j==2)
                    config_final{j}{mm} = 'triplex_line_conductor';
                else
                    config_final{j}{mm} = config{j}{i};
                end
            end
            mm = mm + 1;
        elseif (length(strfind(char(config{2}{i}),'underground_line_conductor:')) ~= 0)
            if (length(strfind(char(config{1}{i}),'object')) ~= 0)
                for j=1:d
                    if (j==2)
                        config_final{j}{mm} = 'underground_line_conductor';
                        config_final{j}{mm+1} = 'name';
                    elseif (j==1)
                        config_final{j}{mm} = config{j}{i};
                        config_final{j}{mm+1} = '     ';
                    elseif (j==3)
                        config_final{j}{mm} = config{j}{i};
                        temp = strrep(config{2}{i},'underground_line_conductor:','');
                        temp2 = strcat('underground_line_conductor_',temp,';');
                        config_final{j}{mm+1} = temp2;
                    else
                        config_final{j}{mm} = config{j}{i};
                    end
                end
                mm = mm + 1;
            else
                for j=1:d
                    if (j==3)
                        temp = strrep(config{2}{i},'underground_line_conductor:','');
                        temp2 = strcat('underground_line_conductor_',temp);
                        config_final{j}{mm} = temp2;
                    elseif (j==1)
                        config_final{j}{mm} = '     ';
                    else
                        config_final{j}{mm} = config{j-1}{i};
                    end
                end
            end
            mm = mm + 1;
        elseif (length(strfind(char(config{2}{i}),'overhead_line_conductor:')) ~= 0)
            if (length(strfind(char(config{1}{i}),'object')) ~= 0)
                for j=1:d
                    if (j==2)
                        config_final{j}{mm} = 'overhead_line_conductor';
                        config_final{j}{mm+1} = 'name';
                    elseif (j==1)
                        config_final{j}{mm} = config{j}{i};
                        config_final{j}{mm+1} = '     ';
                    elseif (j==3)
                        config_final{j}{mm} = config{j}{i};
                        temp = strrep(config{2}{i},'overhead_line_conductor:','');
                        temp2 = strcat('overhead_line_conductor_',temp,';');
                        config_final{j}{mm+1} = temp2;
                    else
                        config_final{j}{mm} = config{j}{i};
                    end
                end
                mm = mm + 1;
            else
                for j=1:d
                    if (j==3)
                        temp = strrep(config{2}{i},'overhead_line_conductor:','');
                        temp2 = strcat('overhead_line_conductor_',temp);
                        config_final{j}{mm} = temp2;
                    elseif (j==1)
                        config_final{j}{mm} = '     ';
                    else
                        config_final{j}{mm} = config{j-1}{i};
                    end
                end
            end
            mm = mm + 1;
        elseif (length(strfind(char(config{2}{i}),'regulator_configuration:')) ~= 0)
            for j=1:d
                if (j==2)
                    config_final{j}{mm} = 'regulator_configuration';
                    config_final{j}{mm+1} = 'name';
                elseif (j==1)
                    config_final{j}{mm} = config{j}{i};
                    config_final{j}{mm+1} = '     ';
                elseif (j==3)
                    config_final{j}{mm} = config{j}{i};
                    temp = strrep(config{2}{i},'regulator_configuration:','');
                    temp2 = strcat('regulator_configuration_',temp,';');
                    config_final{j}{mm+1} = temp2;
                else
                    config_final{j}{mm} = config{j}{i};
                end
            end
            mm = mm + 2;
        elseif (length(strfind(char(config{2}{i}),'line_spacing:')) ~= 0)
            if (length(strfind(char(config{1}{i}),'spacing')) ~= 0)
                for j=1:d
                    if (j==3)
                        temp = strrep(config{2}{i},'line_spacing:','');
                        temp2 = strcat('line_spacing_',temp);
                        config_final{j}{mm} = temp2;
                    elseif (j==1)
                        config_final{j}{mm} = '     ';
                    else
                        config_final{j}{mm} = config{j-1}{i};
                    end
                end
                mm = mm + 1;
            else
                for j=1:d
                    if (j==3)
                        temp = strrep(config{2}{i},'line_spacing:','');
                        temp2 = strcat('line_spacing_',temp,';');
                        config_final{j}{mm+1} = temp2;
                        config_final{j}{mm} = config{j}{i};
                    elseif (j==1)
                        config_final{j}{mm+1} = '     ';
                        config_final{j}{mm} = config{j}{i};
                    elseif (j==2)
                        config_final{j}{mm+1} = 'name';
                        config_final{j}{mm} = 'line_spacing';
                    else
                        config_final{j}{mm} = config{j}{i};
                        config_final{j}{mm+1} = '';
                    end
                end
                mm = mm + 2;
            end
        else
            for j=1:d
                if (j==1)
                    config_final{j}{mm} = '     '; %#ok<*SAGROW>
                else
                    config_final{j}{mm} = config{j-1}{i};
                end
            end
            mm = mm + 1;
        end

    end

    % now have all info info in config_final{8}{mm} & glm_final{8}{nn}
    fprintf(write_file,'//Input feeder information for Taxonomy Feeders with different cases.\n');
    fprintf(write_file,'//Started on 10/21/09. This version created %s.\n',datestr(now));
    fprintf(write_file,'// This version was created to perform FY11 Department of Energy\n');
    fprintf(write_file,'// analysis on the benefits of the SGIG grant projects.\n\n');

    fprintf(write_file,'clock {\n');
    fprintf(write_file,'     timezone %s;\n',regional_data.timezone);
    fprintf(write_file,'     starttime ''%s'';\n',tech_data.start_date);
    fprintf(write_file,'     stoptime ''%s'';\n',tech_data.end_date);
    fprintf(write_file,'}\n\n');

    if (use_flags.use_homes ~= 0)
        fprintf(write_file,'#include "appliance_schedules.glm";\n');
        fprintf(write_file,'#include "water_and_setpoint_schedule_v5.glm";\n');
    end
    if (use_flags.use_emissions ~= 0)
        %fprintf(write_file,'#include "emissions_schedules_r%d.glm";\n',region);
    end

    if (use_flags.use_batt == 1 || use_flags.use_batt == 2)
        fprintf(write_file,'#include "battery_schedule.glm";\n');
    end
    if (use_flags.use_commercial == 1)
        fprintf(write_file,'#include "commercial_schedules.glm";\n');
    end
    if (use_flags.use_market == 1 || use_flags.use_market == 2)
        fprintf(write_file,'#include "daily_elasticity_schedules.glm";\n');
    end
    if ((use_flags.use_ts == 2) || (use_flags.use_ts == 4))
        fprintf(write_file,'#include "thermal_storage_schedule_R%d.glm";\n',region);
    end

    fprintf(write_file,'//#define stylesheet=http://gridlab-d.svn.sourceforge.net/viewvc/gridlab-d/trunk/core/gridlabd-2_0\n');
    fprintf(write_file,'#set minimum_timestep=60;\n');
    fprintf(write_file,'#set profiler=1;\n');
    fprintf(write_file,'#set relax_naming_rules=1;\n\n');

    fprintf(write_file,'module tape;\n');
    if ((use_flags.use_solar~=0) || (use_flags.use_solar_res~=0) || (use_flags.use_solar_com~=0))
        fprintf(write_file,'module generators;\n');
    end
    fprintf(write_file,'module climate;\n');
    fprintf(write_file,'module residential {\n');
    fprintf(write_file,'     implicit_enduses NONE;\n');
    fprintf(write_file,'};\n');

    if (use_flags.use_batt == 1 || use_flags.use_batt == 2)
        fprintf(write_file,'module generators;\n');
    end

    fprintf(write_file,'module powerflow {\n');
    fprintf(write_file,'     solver_method NR;\n');
    fprintf(write_file,'     NR_iteration_limit 50;\n');
    if (LUSolverVal==1) %KLU 64-bit build
        fprintf(write_file,'     lu_solver "KLU_x64";\n');
    elseif (LUSolverVal==2) %KLU 32-bit build
        fprintf(write_file,'     lu_solver "KLU";\n');
    end
    fprintf(write_file,'};\n\n');
    
    % So people can use player transforms if needed
    fprintf(write_file,'class player {\n');
    fprintf(write_file,'     double value;\n');
    fprintf(write_file,'};\n\n');

    if (use_flags.use_market ~= 0)
        fprintf(write_file,'module market;\n\n');
        
        % create some new variables in stub auction that I can use to put
        % my values of std and mean, instead of rolling 24 hour
        fprintf(write_file,'class auction {\n');
        fprintf(write_file,'     double my_avg;\n');
        fprintf(write_file,'     double my_std;\n');
        fprintf(write_file,'};\n\n');
        

        
            CPP_flag_name = strrep(taxonomy_data.CPP_flag,'.player','');
        fprintf(write_file,'object player {\n');
        fprintf(write_file,'     name %s;\n',char(CPP_flag_name));
        fprintf(write_file,'     file %s;\n',char(taxonomy_data.CPP_flag));
        fprintf(write_file,'};\n\n');
        
        fprintf(write_file,'object auction {\n');
        fprintf(write_file,'     name %s;\n',tech_data.market_info{1});
        fprintf(write_file,'     period %.0f;\n',tech_data.market_info{2});
        fprintf(write_file,'     special_mode BUYERS_ONLY;\n');
        fprintf(write_file,'     unit kW;\n');
        
        if (use_flags.use_market == 1) %TOU
            temp_avg = taxonomy_data.TOU_stats(1);
            temp_std = taxonomy_data.TOU_stats(2);
        elseif (use_flags.use_market == 2 || use_flags.use_market == 3) %TOU/CPP
            temp_avg = taxonomy_data.CPP_stats(1);
            temp_std = taxonomy_data.CPP_stats(2);
        end
        
        fprintf(write_file,'     my_avg %f;\n',temp_avg);
        fprintf(write_file,'     my_std %f;\n',temp_std);
        fprintf(write_file,'     object player {\n');
        
        if (use_flags.use_market == 1) %TOU
            fprintf(write_file,'          file %s;\n',char(taxonomy_data.TOU_price_player));
        elseif (use_flags.use_market == 2 || use_flags.use_market == 3) %TOU/CPP or DLC
            fprintf(write_file,'          file %s;\n',char(taxonomy_data.CPP_price_player));    
        end
        
        fprintf(write_file,'          loop 10;\n');
        fprintf(write_file,'          property current_market.clearing_price;\n');
        fprintf(write_file,'     };\n');
        fprintf(write_file,'}\n\n');
    end

    fprintf(write_file,'object climate {\n');
    fprintf(write_file,'     name "%s";\n',tmy);
    fprintf(write_file,'     tmyfile "%s.tmy2";\n',tmy);
    fprintf(write_file,'     interpolate QUADRATIC;\n');
    fprintf(write_file,'};\n\n');
    
    fprintf(write_file,'//Configurations\n\n');

    for i=1:(mm-1)
        if (strcmp(char(config_final{1}{i}),'}') == 1)
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n\n',char(config_final{1}{i}),char(config_final{2}{i}),char(config_final{3}{i}),char(config_final{4}{i}),char(config_final{5}{i}),char(config_final{6}{i}),char(config_final{7}{i}),char(config_final{8}{i}));    
        else
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(config_final{1}{i}),char(config_final{2}{i}),char(config_final{3}{i}),char(config_final{4}{i}),char(config_final{5}{i}),char(config_final{6}{i}),char(config_final{7}{i}),char(config_final{8}{i}));
        end
    end

    fprintf(write_file,'object transformer_configuration {\n');
    fprintf(write_file,'     name trans_config_to_feeder;\n');
    fprintf(write_file,'     connect_type WYE_WYE;\n');
    fprintf(write_file,'     install_type PADMOUNT;\n');
    fprintf(write_file,'     primary_voltage 230000;\n');
    fprintf(write_file,'     secondary_voltage %.3f;\n',taxonomy_data.nom_volt);
    fprintf(write_file,'     power_rating %.1f MVA;\n',taxonomy_data.feeder_rating);
    fprintf(write_file,'     impedance 0.00033+0.0022j;\n');
    fprintf(write_file,'}\n\n');

    house_no_A = 1;
    house_no_B = 1;
    house_no_C = 1;
    house_no_S = 1;
    total_houses = 0;
    no_of_center_taps = 0;

    %% Create the feeder

    if (use_flags.use_vvc == 1)
       disp('Adding CVR Controller')
       % TODO: pull all of these out and put into tech parameters
       fprintf(write_file,'//Volt-Var object \n');
       fprintf(write_file,'object volt_var_control {\n');
       fprintf(write_file,'        name volt_var_control; \n');
       if (TechnologyToTest == 101)
            fprintf(write_file,'        control_method STANDBY; \n');
            fprintf(write_file,'        object player {\n');
            fprintf(write_file,'             property contol_method;\n');
            fprintf(write_file,'             file %s;\n',taxonomy_data.peak_vvo_player);
            fprintf(write_file,'        };\n');
       else
            fprintf(write_file,'        control_method ACTIVE; \n');
       end
       fprintf(write_file,'        capacitor_delay 60.0; \n');
       fprintf(write_file,'        regulator_delay 60.0; \n');
       fprintf(write_file,'        desired_pf 0.99; \n');
       fprintf(write_file,'        d_max 0.8; \n');
       fprintf(write_file,'        d_min 0.1; \n');
       fprintf(write_file,'        substation_link "substation_transformer"; \n');
       
       [num_regs,junk]=size(taxonomy_data.regulators);
       fprintf(write_file,'        regulator_list "');
       for reg_index=1:num_regs
           if reg_index==num_regs
               fprintf(write_file,'%s";\n',taxonomy_data.regulators{reg_index,1});
           else
               fprintf(write_file,'%s,',taxonomy_data.regulators{reg_index,1});
           end
       end

       [num_caps,junk]=size(taxonomy_data.capacitor_outtage);
       if num_caps ~=0
           fprintf(write_file,'        capacitor_list "');
           for cap_index=1:num_caps
               if cap_index==num_caps
                   fprintf(write_file,'%s";\n',taxonomy_data.capacitor_outtage{cap_index,1});
               else
                   fprintf(write_file,'%s,',taxonomy_data.capacitor_outtage{cap_index,1});
               end
           end
       else
           fprintf(write_file,'        capacitor_list "";\n');
       end
       fprintf(write_file,'        voltage_measurements "');
       [num_eol,junk]=size(taxonomy_data.EOL_points);
       for eol_index=1:num_eol
           if eol_index==num_eol
               fprintf(write_file,'%s,%d";\n',taxonomy_data.EOL_points{eol_index,1},taxonomy_data.EOL_points{eol_index,3});
           else
               fprintf(write_file,'%s,%d,',taxonomy_data.EOL_points{eol_index,1},taxonomy_data.EOL_points{eol_index,3});
           end
       end
       
       
       
       fprintf(write_file,'        maximum_voltages %.2f; \n',taxonomy_data.voltage_regulation{3,1});% Turns of controller is voltage is 2000V greater than desired regulation
       fprintf(write_file,'        minimum_voltages %.2f; \n',taxonomy_data.voltage_regulation{2,1});% Turns of controller is voltage is 2000V less than desired regulation
       fprintf(write_file,'        max_vdrop 50; \n');
       fprintf(write_file,'        high_load_deadband %.2f; \n',taxonomy_data.voltage_regulation{5,1});% Sets a 1 volt deadband
       fprintf(write_file,'        desired_voltages %.2f; \n',taxonomy_data.voltage_regulation{1,1});
       fprintf(write_file,'        low_load_deadband %.2f; \n',taxonomy_data.voltage_regulation{4,1});% Sets a 1 volt deadband
       fprintf(write_file,'}\n');
       fprintf(write_file,'        \n');
    end

    fprintf(write_file,'//Start actual feeder\n\n');
    fprintf(write_file,'object meter {\n');
    fprintf(write_file,'     name network_node;\n');
    fprintf(write_file,'     bustype SWING;\n');
    fprintf(write_file,'     nominal_voltage 230000;\n');
    fprintf(write_file,'     object player {\n');
    fprintf(write_file,'          property voltage_A;\n');
    fprintf(write_file,'          loop 100;\n');
    fprintf(write_file,'          file V_A.player;\n');
    fprintf(write_file,'     };\n');
    fprintf(write_file,'     object player {\n');
    fprintf(write_file,'          property voltage_B;\n');
    fprintf(write_file,'          loop 100;\n');
    fprintf(write_file,'          file V_B.player;\n');
    fprintf(write_file,'     };\n');
    fprintf(write_file,'     object player {\n');
    fprintf(write_file,'          property voltage_C;\n');
    fprintf(write_file,'          loop 100;\n');
    fprintf(write_file,'          file V_C.player;\n');
    fprintf(write_file,'     };\n');
    fprintf(write_file,'     phases ABCN;\n');
    fprintf(write_file,'}\n\n');

    fprintf(write_file,'object transformer {\n');
    fprintf(write_file,'     name substation_transformer;\n');
    fprintf(write_file,'     from network_node;\n');
    fprintf(write_file,'     to %s\n',swing_node);
    fprintf(write_file,'     phases ABCN;\n');
    fprintf(write_file,'     configuration trans_config_to_feeder;\n');  
    fprintf(write_file,'}\n\n');

    transformer = 0;
    no_of_houses = 0;
    m = 0;
    no_loads = 0;
    cap_n = 0;
    reg_n = 0;
    
    no_triplines = 0;
    no_ugls = 0;
    no_ohls = 0;

    for j=1:(nn-1)
        if (m >= j)
            continue; % this is used to skip over certain lines
        end
        if (strcmp(char(glm_final{2}{j}),'name') ~= 0)
            named_object = char(glm_final{3}{j});
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
        elseif (strcmp(char(glm_final{2}{j}),'to') ~= 0)
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
        elseif (strcmp(char(glm_final{2}{j}),'from') ~= 0)
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
%         elseif (strcmp(char(glm_final{2}{j}),'triplex_node') ~= 0)
%             fprintf(write_file,'object triplex_meter {\n');
        elseif (strcmp(char(glm_final{2}{j}),'capacitor') ~= 0)
            c = j;
            while (strcmp(char(glm_final{1}{c}),'}') == 0)
                c = c+1;
                if(strcmp(char(glm_final{2}{c}),'name') ~= 0)
                    cap_n = cap_n+1;
                    cap_name = strrep(glm_final{3}{c},';','');
                    capacitor_list{cap_n} = char(cap_name);
                    break;
                end
            end       
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
        elseif (strcmp(char(glm_final{2}{j}),'regulator') ~= 0)
            r = j;
            while (strcmp(char(glm_final{1}{r}),'}') == 0)
                r = r+1;
                if(strcmp(char(glm_final{2}{r}),'name') ~= 0)
                    reg_n = reg_n+1;
                    reg_name = strrep(glm_final{3}{r},';','');
                    regulator_list{reg_n} = char(reg_name);
                    break;
                end
            end  
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
        elseif (strcmp(char(glm_final{2}{j}),'parent') ~= 0)
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
            parent_object = char(glm_final{3}{j});
        elseif (strcmp(char(glm_final{2}{j}),'transformer') ~= 0)
            m = j;
            if (0 && use_flags.use_commercial == 1) % TODO not sure why I did this, but I won't throw it away until I'm sure
                while (strcmp(char(glm_final{1}{m}),'}') == 0)
                    m = m+1;
                    if(strcmp(char(glm_final{2}{m}),'WYE_WYE') ~= 0)

                    end
                end
            else
                fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
                fprintf(write_file,'      groupid Distribution_Trans;\n');
            end

        elseif (strcmp(char(glm_final{2}{j}),'triplex_line') ~= 0)
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
            fprintf(write_file,'      groupid Triplex_Line;\n');
            no_triplines = no_triplines + 1;
        elseif (strcmp(char(glm_final{2}{j}),'overhead_line') ~= 0)
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
            fprintf(write_file,'      groupid Distribution_Line;\n');
            no_ohls = no_ohls + 1;
        elseif (strcmp(char(glm_final{2}{j}),'underground_line') ~= 0)
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
            fprintf(write_file,'      groupid Distribution_Line;\n');
            no_ugls = no_ugls + 1;
        elseif (strcmp(char(glm_final{2}{j}),'phases') ~= 0)
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
            phase = char(glm_final{3}{j});
        elseif (strcmp(char(glm_final{2}{j}),'load') ~= 0)
            if (use_flags.use_commercial == 1) % Building Commercial
                fprintf(write_file,'\nobject node {\n');
                m = j;
                no_houses_A = 0;
                no_houses_B = 0;
                no_houses_C = 0;
                
                load_A = 0;
                load_B = 0;
                load_C = 0;
                
                while (strcmp(char(glm_final{1}{m}),'}') == 0)
                    if (strcmp(char(glm_final{2}{m}),'constant_power_A') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        load_A = load_A + sqrt(bb_real^2 + bb_imag^2);
                        no_houses_A = no_houses_A + ceil( sqrt(bb_real^2 + bb_imag^2) / taxonomy_data.avg_commercial);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_power_B') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        load_B = load_B + sqrt(bb_real^2 + bb_imag^2);
                        no_houses_B = no_houses_B + ceil( sqrt(bb_real^2 + bb_imag^2) / taxonomy_data.avg_commercial);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_power_C') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        load_C = load_C + sqrt(bb_real^2 + bb_imag^2);
                        no_houses_C = no_houses_C + ceil( sqrt(bb_real^2 + bb_imag^2) / taxonomy_data.avg_commercial);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_impedance_A') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_A = abs(taxonomy_data.nom_volt2^2 / 3 / (bb_real * 1i*bb_imag));

                        load_A = load_A + S_A;
                        no_houses_A = no_houses_A + ceil(S_A / taxonomy_data.avg_commercial);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_impedance_B') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_B = abs(taxonomy_data.nom_volt2^2 / 3 / (bb_real * 1i*bb_imag));

                        load_B = load_B + S_B;
                        no_houses_B = no_houses_B + ceil(S_B / taxonomy_data.avg_commercial);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_impedance_C') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_C = abs(taxonomy_data.nom_volt2^2 / 3 / (bb_real * 1i*bb_imag));

                        load_C = load_C + S_C;
                        no_houses_C = no_houses_C + ceil(S_C / taxonomy_data.avg_commercial);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_current_A') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_A = abs(taxonomy_data.nom_volt2 * (bb_real * 1i*bb_imag));

                        load_A = load_A + S_A;
                        no_houses_A = no_houses_A + ceil(S_A / taxonomy_data.avg_commercial);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_current_B') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_B = abs(taxonomy_data.nom_volt2 * (bb_real * 1i*bb_imag));

                        load_B = load_B + S_B;
                        no_houses_B = no_houses_B + ceil(S_B / taxonomy_data.avg_commercial);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_current_C') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_C = abs(taxonomy_data.nom_volt2 * (bb_real * 1i*bb_imag));

                        load_C = load_C + S_C;
                        no_houses_C = no_houses_C + ceil(S_C / taxonomy_data.avg_commercial);
                    elseif (strcmp(char(glm_final{2}{m}),'name') ~= 0)
                        parent_name = char(glm_final{3}{m});
                        fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{m}),char(glm_final{2}{m}),char(glm_final{3}{m}),char(glm_final{4}{m}),char(glm_final{5}{m}),char(glm_final{6}{m}),char(glm_final{7}{m}),char(glm_final{8}{m}));
                    elseif (strcmp(char(glm_final{2}{m}),'phases') ~= 0)
                        parent_phase = char(glm_final{3}{m});
                        fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{m}),char(glm_final{2}{m}),char(glm_final{3}{m}),char(glm_final{4}{m}),char(glm_final{5}{m}),char(glm_final{6}{m}),char(glm_final{7}{m}),char(glm_final{8}{m}));
                    elseif (strcmp(char(glm_final{2}{m}),'nominal_voltage') ~= 0)
                        fprintf(write_file,'      nominal_voltage %.2f;\n',taxonomy_data.nom_volt2);
                    elseif (strcmp(char(glm_final{2}{m}),'parent') ~= 0)
                        my_parent = char(glm_final{3}{m});
                        fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{m}),char(glm_final{2}{m}),char(glm_final{3}{m}),char(glm_final{4}{m}),char(glm_final{5}{m}),char(glm_final{6}{m}),char(glm_final{7}{m}),char(glm_final{8}{m}));        
                    end   

                    m = m + 1;
                end
                fprintf(write_file,'}\n\n');
                no_loads = no_loads + 1;

                if (load_A < tech_data.load_cutoff)
                    load_houses{1}{no_loads} = 0;
                else
                    load_houses{1}{no_loads} = no_houses_A;
                end
                if (load_B < tech_data.load_cutoff)
                    load_houses{2}{no_loads} = 0;
                else
                    load_houses{2}{no_loads} = no_houses_B;
                end
                if (load_C < tech_data.load_cutoff)
                    load_houses{3}{no_loads} = 0;
                else
                    load_houses{3}{no_loads} = no_houses_C;
                end
                
                load_houses{4}{no_loads} = parent_name;
                load_houses{5}{no_loads} = parent_phase;
                load_houses{6}{no_loads} = load_A;
                load_houses{7}{no_loads} = load_B;
                load_houses{8}{no_loads} = load_C;
                load_houses{9}{no_loads} = my_parent;
                
            else % ZIP load commercial
                fprintf(write_file,'\nobject load {\n');
                m = j;

                load_A = 0;
                load_B = 0;
                load_C = 0;

                % Add up all of the loads at that node on each phase
                while (strcmp(char(glm_final{1}{m}),'}') == 0)
                    if (strcmp(char(glm_final{2}{m}),'constant_power_A') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        load_A = load_A + abs(bb_real + 1i*bb_imag);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_power_B') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        load_B = load_B + abs(bb_real + 1i*bb_imag);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_power_C') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        load_C = load_C + abs(bb_real + 1i*bb_imag);
                    elseif (strcmp(char(glm_final{2}{m}),'constant_impedance_A') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_A = abs(taxonomy_data.nom_volt2^2 / 3 / (bb_real * 1i*bb_imag));

                        load_A = load_A + S_A;
                    elseif (strcmp(char(glm_final{2}{m}),'constant_impedance_B') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_B = abs(taxonomy_data.nom_volt2^2 / 3 / (bb_real * 1i*bb_imag));

                        load_B = load_B + S_B;
                    elseif (strcmp(char(glm_final{2}{m}),'constant_impedance_C') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_C = abs(taxonomy_data.nom_volt2^2 / 3 / (bb_real * 1i*bb_imag));

                        load_C = load_C + S_C;
                    elseif (strcmp(char(glm_final{2}{m}),'constant_current_A') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_A = abs(taxonomy_data.nom_volt2 * (bb_real * 1i*bb_imag));

                        load_A = load_A + S_A;
                    elseif (strcmp(char(glm_final{2}{m}),'constant_current_B') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_B = abs(taxonomy_data.nom_volt2 * (bb_real * 1i*bb_imag));

                        load_B = load_B + S_B;
                    elseif (strcmp(char(glm_final{2}{m}),'constant_current_C') ~= 0)
                        bb_real = real(str2num(glm_final{3}{m}));
                        bb_imag = imag(str2num(glm_final{3}{m}));

                        S_C = abs(taxonomy_data.nom_volt2 * (bb_real * 1i*bb_imag));

                        load_C = load_C + S_C;
                    elseif (strcmp(char(glm_final{2}{m}),'name') ~= 0)
                        parent_name = char(glm_final{3}{m});
                        fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{m}),char(glm_final{2}{m}),char(glm_final{3}{m}),char(glm_final{4}{m}),char(glm_final{5}{m}),char(glm_final{6}{m}),char(glm_final{7}{m}),char(glm_final{8}{m}));
                    elseif (strcmp(char(glm_final{2}{m}),'phases') ~= 0)
                        parent_phase = char(glm_final{3}{m});
                        fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{m}),char(glm_final{2}{m}),char(glm_final{3}{m}),char(glm_final{4}{m}),char(glm_final{5}{m}),char(glm_final{6}{m}),char(glm_final{7}{m}),char(glm_final{8}{m}));
                    elseif (strcmp(char(glm_final{2}{m}),'nominal_voltage') ~= 0)
                        fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{m}),char(glm_final{2}{m}),char(glm_final{3}{m}),char(glm_final{4}{m}),char(glm_final{5}{m}),char(glm_final{6}{m}),char(glm_final{7}{m}),char(glm_final{8}{m}));        
                    elseif (strcmp(char(glm_final{2}{m}),'parent') ~= 0)
                        fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{m}),char(glm_final{2}{m}),char(glm_final{3}{m}),char(glm_final{4}{m}),char(glm_final{5}{m}),char(glm_final{6}{m}),char(glm_final{7}{m}),char(glm_final{8}{m}));        
                    end   

                    m = m + 1;
                end

                % Re-make the loads using the specified ZIP fractions & pf
                if (load_A > 0)
                    fprintf(write_file,'      base_power_A %f;\n',load_A);
                    fprintf(write_file,'      power_pf_A %f;\n',tech_data.c_p_pf);
                    fprintf(write_file,'      current_pf_A %f;\n',tech_data.c_i_pf);
                    fprintf(write_file,'      impedance_pf_A %f;\n',tech_data.c_z_pf);
                    fprintf(write_file,'      power_fraction_A %f;\n',tech_data.c_pfrac);
                    fprintf(write_file,'      current_fraction_A %f;\n',tech_data.c_ifrac);
                    fprintf(write_file,'      impedance_fraction_A %f;\n',tech_data.c_zfrac);
                end
                if (load_B > 0)
                    fprintf(write_file,'      base_power_B %f;\n',load_B);
                    fprintf(write_file,'      power_pf_B %f;\n',tech_data.c_p_pf);
                    fprintf(write_file,'      current_pf_B %f;\n',tech_data.c_i_pf);
                    fprintf(write_file,'      impedance_pf_B %f;\n',tech_data.c_z_pf);
                    fprintf(write_file,'      power_fraction_B %f;\n',tech_data.c_pfrac);
                    fprintf(write_file,'      current_fraction_B %f;\n',tech_data.c_ifrac);
                    fprintf(write_file,'      impedance_fraction_B %f;\n',tech_data.c_zfrac);
                end
                if (load_C > 0)
                    fprintf(write_file,'      base_power_C %f;\n',load_C);
                    fprintf(write_file,'      power_pf_C %f;\n',tech_data.c_p_pf);
                    fprintf(write_file,'      current_pf_C %f;\n',tech_data.c_i_pf);
                    fprintf(write_file,'      impedance_pf_C %f;\n',tech_data.c_z_pf);
                    fprintf(write_file,'      power_fraction_C %f;\n',tech_data.c_pfrac);
                    fprintf(write_file,'      current_fraction_C %f;\n',tech_data.c_ifrac);
                    fprintf(write_file,'      impedance_fraction_C %f;\n',tech_data.c_zfrac);
                end
                fprintf(write_file,'}\n\n');
            end

        elseif (strcmp(char(glm_final{2}{j}),'power_1') ~= 0 || strcmp(char(glm_final{2}{j}),'power_12') ~= 0)
            if (use_flags.use_homes == 1)
                bb_real = real(str2num(glm_final{3}{j}));
                bb_imag = imag(str2num(glm_final{3}{j}));

                bb = sqrt(bb_real^2 + bb_imag^2);
                % round to single decimal place
                no_of_houses = round(bb/taxonomy_data.avg_house);
                % determine whether we rounded down or up to help determine
                % the square footage (neg. # => small homes)
                lg_vs_sm = bb/taxonomy_data.avg_house - no_of_houses;

                if (no_of_houses > 0)
                    name = named_object;

                    no_of_center_taps = no_of_center_taps + 1;
                    center_taps{no_of_center_taps,1} = name;
    
                    phase_S_houses{house_no_S,1} = num2str(no_of_houses);
                    phase_S_houses{house_no_S,2} = name;
                    phase_S_houses{house_no_S,3} = phase;
                    phase_S_houses{house_no_S,4} = num2str(lg_vs_sm);
                    phase_S_houses{house_no_S,5} = parent_object;

                    house_no_S = house_no_S + 1;
                    
                    
                    
                    total_houses = total_houses + no_of_houses;

                else
                    if (tech_data.get_IEEE_stats == 0)
                        fprintf(write_file,'      // Load was too small to convert to a house (less than 1/2 avg_house)\n');
                        fprintf(write_file,'      power_12_real street_lighting*%.4f;\n',bb_real*tech_data.light_scalar_res);
                        fprintf(write_file,'      power_12_reac street_lighting*%.4f;\n',bb_imag*tech_data.light_scalar_res);
                    end
                end
            else
                fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
            end
        elseif (strcmp(char(glm_final{2}{j}),'}') ~= 0)
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
        else
            fprintf(write_file,'%s %s %s %s %s %s %s %s\n',char(glm_final{1}{j}),char(glm_final{2}{j}),char(glm_final{3}{j}),char(glm_final{4}{j}),char(glm_final{5}{j}),char(glm_final{6}{j}),char(glm_final{7}{j}),char(glm_final{8}{j}));
        end
    end

    %Initializing some counters for implementing different solar
    %penetrations
    countSOLAR = 0;
    countSOLAR_stripmall = 0;
    countSOLAR_office = 0;
    countSOLAR_bigbox = 0;
    
    %Initializing some counters for implementing different energy storage
    %penetrations
    countES = 0;
    countES_stripmall = 0;
    countES_office = 0;
    countES_bigbox = 0;
    
    %Initializing some counters for implementing different energy storage
    %penetrations
    countPHEV = 0;
    
    % Initialize pseudo-random numbers - put this before each technology where 
    % random numbers are needed, so they are not effected by other changes
    % (s1-s6)
    if (use_flags.use_market ~= 0)
        RandStream.setGlobalStream(s1);

        if (total_houses ~= 0)
            [aa,junk] = size(phase_S_houses);

            % Make a big array so we don't run out
            bb = total_houses * aa;
            
            market_penetration_random = rand(bb,1);            
            dlc_rand = rand(bb,1); % used for dlc randomization
            
            % 10 - 25% increase over normal cycle
            pool_pump_recovery_random = 0.1 + 0.15.*rand(bb,1);
            
            % limit slider randomization to Olypen style
            slider_random = 0.45 + (0.2).*randn(bb,1);
                sl1 = find(slider_random > tech_data.market_info{5});
            slider_random(sl1) = tech_data.market_info{5};
                sl2 = find(slider_random < 0);
            slider_random(sl1) = 0;            
            
            % random elasticity values for responsive loads - this is a multiplier
            % used to randomized individual building responsiveness - very similar
            % to a lognormal, so we'll use one that has a mean of ~1, max of
            % ~1.2, and median of ~1.12
            sigma=1.2;
            mu = 0.7;
            multiplier = 3.6;
            xval = rand(bb,1);
            elasticity_random = multiplier * 1 ./ ( xval * sigma * sqrt(2*pi)) .* exp( -1/(2*sigma^2) .* (log(xval) - mu).^2);
        end
        
        if (no_loads ~= 0)
            [bb,junk] = size(no_loads);
            aa = 15*bb*100;
            
             % limit slider randomization to Olypen style
            comm_slider_random = 0.45 + (0.2).*randn(aa,1);
                sl1 = find(comm_slider_random > tech_data.market_info{5});
            comm_slider_random(sl1) = tech_data.market_info{5};
                sl2 = find(comm_slider_random < 0);
            comm_slider_random(sl1) = 0; 
            
            dlc_c_rand = rand(aa,1); % used for dlc randomization
            dlc_c_rand2 = rand(aa,1); % used for dlc randomization
        end
    end
    
    % Initialize pseudo-random numbers - put this before each technology where 
    % random numbers are needed, so they are not effected by other changes
    % (s1-s6)
    RandStream.setGlobalStream(s2);

    count_house = 1;
    
    %Store solar information for EOF dump calculations - set accumulators
    if (use_flags.use_solar~=0 || use_flags.use_solar_res~=0 || use_flags.use_solar_com~=0)
        ResSolarArea=0;
        ComSolarAreaStripMall=0;
        ComSolarAreaBigBox=0;
        ComSolarAreaOffice=0;
    end
    
    % Phase S - residential homes
    if (use_flags.use_homes == 1 && total_houses ~= 0)
        [aS,bS] = size(phase_S_houses);

        % Create a histogram of what the thermal integrity of the houses should be
          % Ceiling function will create a few extra houses in histogram, but its needed
        thermal_integrity = ceil(regional_data.thermal_percentages * total_houses);

        total_houses_by_type = sum(thermal_integrity');

        %only allow pool pumps on single family homes
        no_pool_pumps = total_houses_by_type(1);

        for typeind=1:3
            cool_sp(:,typeind) = ceil(regional_data.cooling_setpoint{typeind}(:,1) * total_houses_by_type(typeind));
            heat_sp(:,typeind) = ceil(regional_data.heating_setpoint{typeind}(:,1) * total_houses_by_type(typeind));
        end
        if (tech_data.get_IEEE_stats == 0)
            for jj=1:aS
                parent = char(phase_S_houses(jj,2)); %name of node
                parent2 = char(phase_S_houses(jj,5)); %name of node's parent
                no_houses = str2num(char(phase_S_houses(jj,1)));
                phase = char(phase_S_houses(jj,3));
                lg_v_sm = str2num(char(phase_S_houses(jj,4)));

                for kk=1:no_houses
                    
                    fprintf(write_file,'object triplex_meter {\n');
                    fprintf(write_file,'      phases %s\n',phase);
                    fprintf(write_file,'      name tpm%d_%s\n',kk,parent2);
                    fprintf(write_file,'      parent %s\n',parent2);
                    fprintf(write_file,'      groupid Residential_Meter;\n');
                    fprintf(write_file,'      meter_power_consumption %s;\n',tech_data.res_meter_cons);
                    if (use_flags.use_billing == 1) %Fixed price
                        fprintf(write_file,'      bill_mode UNIFORM;\n');
                        fprintf(write_file,'      price %.5f;\n',tech_data.flat_price(region));
                        fprintf(write_file,'      monthly_fee %.2f;\n',tech_data.monthly_fee);
                        fprintf(write_file,'      bill_day 1;\n');
                    elseif (use_flags.use_billing == 2) % TIERED
                        error('use_flag.use_billing == 2 not functional at this time');
                    elseif (use_flags.use_billing == 3) % TOU or RTP
                        fprintf(write_file,'      bill_mode HOURLY;\n');
                        fprintf(write_file,'      monthly_fee %.2f;\n',tech_data.monthly_fee);
                        fprintf(write_file,'      bill_day 1;\n');
                        fprintf(write_file,'      power_market %s;\n',tech_data.market_info{1});
                    end
                    fprintf(write_file,'      nominal_voltage 120;\n');
                    fprintf(write_file,'}\n');
                    
                    fprintf(write_file,'object house {\n');
                    fprintf(write_file,'     parent tpm%d_%s\n',kk,parent2);
                    fprintf(write_file,'     name house%d_%s\n',kk,parent2);
                    fprintf(write_file,'     groupid Residential;\n');

                    %TODO - aspect ratio?, window wall ratio?

                    if (use_flags.use_ts~=0)
                        %Create array of parents for thermal storage devices
                        ts_residential_array{jj}{kk} = ['house' num2str(kk) '_' parent2];
                    end
                    
                    skew_value = tech_data.residential_skew_std*randn(1);
                    if (skew_value < -tech_data.residential_skew_max)
                        skew_value = -tech_data.residential_skew_max;
                    elseif (skew_value > tech_data.residential_skew_max)
                        skew_value = tech_data.residential_skew_max;
                    end

                    wh_skew_value = 3*tech_data.residential_skew_std*randn(1);
                    if (wh_skew_value < -6*tech_data.residential_skew_max)
                        wh_skew_value = -6*tech_data.residential_skew_max;
                    elseif (wh_skew_value > 6*tech_data.residential_skew_max)
                        wh_skew_value = 6*tech_data.residential_skew_max;
                    end

                    % scale this skew up to weeks
                    pp_skew_value = 128*tech_data.residential_skew_std*randn(1);
                    if (pp_skew_value < -128*tech_data.residential_skew_max)
                        pp_skew_value = -128*tech_data.residential_skew_max;
                    elseif (pp_skew_value > 128*tech_data.residential_skew_max)
                        pp_skew_value = 128*tech_data.residential_skew_max;
                    end

                    fprintf(write_file,'     schedule_skew %.0f;\n',skew_value);

                        % Choose what type of building we are going to use
                        % and set the thermal integrity of said building
                        [size_a,size_b] = size(thermal_integrity);

                        therm_int = ceil(size_a * size_b * rand(1));

                        row_ti = mod(therm_int,size_a) + 1;
                        col_ti = mod(therm_int,size_b) + 1;
                        while ( thermal_integrity(row_ti,col_ti) < 1 )
                            therm_int = ceil(size_a * size_b * rand(1));

                            row_ti = mod(therm_int,size_a) + 1;
                            col_ti = mod(therm_int,size_b) + 1;
                        end

                        thermal_integrity(row_ti,col_ti) = thermal_integrity(row_ti,col_ti) - 1;

                        thermal_temp = regional_data.thermal_properties(row_ti,col_ti);

                        %TODO check this variance on the floor area
                        % As it is now, this will shift mean of low integrity
                        % single family homes to a smaller square footage and vice
                        % versa for high integrity homes-is NOT mathematically correct
                        f_area = regional_data.floor_area(row_ti);
                        story_rand = rand(1);
                        height_rand = randi(2);
                        fa_rand = rand(1);
                        if (col_ti == 1) % SF homes
                            floor_area = f_area + (f_area/2) * fa_rand * (row_ti - 4)/3;
                            if (story_rand < regional_data.one_story(region))
                                stories = 1;
                            else
                                stories = 2;
                            end

                        else
                            floor_area = f_area + (f_area/2) * (0.5 - fa_rand); %+/- 50%
                            stories = 1;
                            height_rand = 0;
                        end

                        % Now also adjust square footage as a factor of whether
                        % the load modifier (avg_house) rounded up or down
                        floor_area = (1 + lg_v_sm) * floor_area;

                        if (floor_area > 4000)
                            floor_area = 3800 + fa_rand*200;
                        elseif (floor_area < 300)
                            floor_area = 300 + fa_rand*100;
                        end

                        fl_area(count_house) = floor_area;
                        count_house = count_house + 1;
                    if (use_flags.use_solar~=0 ||use_flags.use_solar_res~=0)
                        %Create array of parents for residential solar
                        solar_residential_array{jj}{kk} = ['house' num2str(kk) '_' parent2];
                        solar_residential_array_fa{jj}{kk} = floor_area;
                        solar_residential_array_parent{jj}{kk} = [parent2];
                        solar_residential_array_phase{jj}{kk} = [phase];
                    end
                    if (use_flags.use_energy_storage_res ~= 0 || use_flags.use_energy_storage ~= 0)
                        es_residential_array{jj}{kk} = ['house' num2str(kk) '_' parent2];
                        es_residential_array_parent{jj}{kk} = [parent2];
                        es_residential_array_phase{jj}{kk} = [phase];
                    end
                    if (use_flags.use_phev ~= 0)
                        phev_residential_array{jj}{kk} = ['house' num2str(kk) '_' parent2];
                    end
                    if (use_flags.use_wind ~= 0)
                        wind_residential_array{jj}{kk} = ['house' num2str(kk) '_' parent2];
                        wind_residential_array_parent{jj}{kk} = [parent2];
                        wind_residential_array_phase{jj}{kk} = [phase];
                    end
                    

                    fprintf(write_file,'     floor_area %.0f;\n',floor_area);
                    fprintf(write_file,'     number_of_stories %.0f;\n',stories); 
                        ceiling_height = 8 + height_rand;
                    fprintf(write_file,'     ceiling_height %.0f;\n',ceiling_height);
                        os_rand = regional_data.over_sizing_factor * (.8 + 0.4*rand);
                    fprintf(write_file,'     over_sizing_factor %.1f;\n',os_rand);

                        %TODO do I want to handle apartment walls differently?
                        building_type = {'Single Family';'Apartment';'Mobile Home'};
                    fprintf(write_file,'     //Thermal integrity -> %s %.0f\n',building_type{row_ti},col_ti);

                        rroof = thermal_temp{1}(1)*(0.8 + 0.4*rand(1));
                    fprintf(write_file,'     Rroof %.2f;\n',rroof);

                        rwall = thermal_temp{1}(2)*(0.8 + 0.4*rand(1));
                    fprintf(write_file,'     Rwall %.2f;\n',rwall);

                        rfloor = thermal_temp{1}(3)*(0.8 + 0.4*rand(1));
                    fprintf(write_file,'     Rfloor %.2f;\n',rfloor);                   
                    fprintf(write_file,'     glazing_layers %.0f;\n',thermal_temp{1}(4));
                    fprintf(write_file,'     glass_type %.0f;\n',thermal_temp{1}(5));
                    fprintf(write_file,'     glazing_treatment %.0f;\n',thermal_temp{1}(6));
                    fprintf(write_file,'     window_frame %.0f;\n',thermal_temp{1}(7));

                        rdoor = thermal_temp{1}(8)*(0.8 + 0.4*rand(1));
                    fprintf(write_file,'     Rdoors %.2f;\n',rdoor);           

                        airchange = thermal_temp{1}(9)*(0.8 + 0.4*rand(1));
                    fprintf(write_file,'     airchange_per_hour %.2f;\n',airchange);

                        c_COP = thermal_temp{1}(11) + rand(1)*(thermal_temp{1}(10) - thermal_temp{1}(11));          
                    fprintf(write_file,'     cooling_COP %.1f;\n',c_COP);

                        init_temp = 68 + 4*rand(1);
                    fprintf(write_file,'     air_temperature %.2f;\n',init_temp);
                    fprintf(write_file,'     mass_temperature %.2f;\n',init_temp);

                        % This is a bit of a guess from Rob's estimates
                        mass_floor = 2.5 + 1.5*rand(1); 
                    fprintf(write_file,'     total_thermal_mass_per_floor_area %.3f;\n',mass_floor);

                        heat_type = rand(1);
                        cool_type = rand(1);
                        h_COP = c_COP;

                        ct = 'NONE';
                    if (heat_type <= regional_data.perc_gas)
                        fprintf(write_file,'     heating_system_type GAS;\n');
                        if (cool_type <= regional_data.perc_AC)
                            fprintf(write_file,'     cooling_system_type ELECTRIC;\n');
                            ct = 'ELEC';
						else
							fprintf(write_file,'     cooling_system_type NONE;\n');
                        end
                        ht = 'GAS';           
                    elseif (heat_type <= (regional_data.perc_gas + regional_data.perc_pump))
                        fprintf(write_file,'     heating_system_type HEAT_PUMP;\n');                   
                        fprintf(write_file,'     heating_COP %.1f;\n',h_COP);
                        fprintf(write_file,'     cooling_system_type ELECTRIC;\n');
                        fprintf(write_file,'     auxiliary_strategy DEADBAND;\n');
                        fprintf(write_file,'     auxiliary_system_type ELECTRIC;\n');
                        fprintf(write_file,'     motor_model BASIC;\n');
                        fprintf(write_file,'     motor_efficiency AVERAGE;\n');
                        ht = 'HP';
                        ct = 'ELEC';
                    elseif (floor_area*ceiling_height > 12000 ) % No resistive homes over with large volumes
                        fprintf(write_file,'     heating_system_type GAS;\n');
                        if (cool_type <= regional_data.perc_AC)
                            fprintf(write_file,'     cooling_system_type ELECTRIC;\n');
                            ct = 'ELEC';
						else
							fprintf(write_file,'     cooling_system_type NONE;\n');
                        end
                        ht = 'GAS';
                    else
                        fprintf(write_file,'     heating_system_type RESISTANCE;\n');
                        if (cool_type <= regional_data.perc_AC)
                            fprintf(write_file,'     cooling_system_type ELECTRIC;\n');
                            fprintf(write_file,'     motor_model BASIC;\n');
                            fprintf(write_file,'     motor_efficiency GOOD;\n');
                            ct = 'ELEC';
						else
							fprintf(write_file,'     cooling_system_type NONE;\n');
                        end
                        ht = 'ELEC';
                    end


                        fprintf(write_file,'     breaker_amps 1000;\n');
                        fprintf(write_file,'     hvac_breaker_rating 1000;\n');

                        % choose a cooling & heating schedule
                        cooling_set = ceil(regional_data.no_cool_sch*rand(1));           
                        heating_set = ceil(regional_data.no_heat_sch*rand(1));

                        % choose a cooling bin
                        coolsp = regional_data.cooling_setpoint{row_ti};
                        [no_cool_bins,junk] = size(coolsp);

                        % see if we have that bin left
                        cool_bin = randi(no_cool_bins);
                        while (cool_sp(cool_bin,row_ti) < 1)
                            cool_bin = randi(no_cool_bins);
                        end
                        cool_sp(cool_bin,row_ti) = cool_sp(cool_bin,row_ti) - 1;

                        % choose a heating bin
                        heatsp = regional_data.heating_setpoint{row_ti};
                        [no_heat_bins,junk] = size(heatsp);

                        heat_bin = randi(no_heat_bins);
                        heat_count = 1;

                        % see if we have that bin left, then check to make sure
                        % upper limit of chosen bin is not greater than lower limit
                        % of cooling bin
                        while (heat_sp(heat_bin,row_ti) < 1 || (heatsp(heat_bin,3) >= coolsp(cool_bin,4)))
                            heat_bin = randi(no_heat_bins);

                            % if we tried a few times, give up and take an extra
                            % draw from the lowest bin
                            if (heat_count > 20)
                                heat_bin = 1;
                                break;
                            end

                            heat_count = heat_count + 1;
                        end
                        heat_sp(heat_bin,row_ti) = heat_sp(heat_bin,row_ti) - 1;

                        % randomly choose within the bin, then +/- one
                        % degree to seperate the deadbands
                        cool_night = (coolsp(cool_bin,3) - coolsp(cool_bin,4))*rand(1) + coolsp(cool_bin,4) + 1;
                        heat_night = (heatsp(heat_bin,3) - heatsp(heat_bin,4))*rand(1) + heatsp(heat_bin,4) - 1;

                        cool_night_diff = coolsp(cool_bin,2) * 2 * rand(1);
                        heat_night_diff = heatsp(heat_bin,2) * 2 * rand(1);

                    % If we have markets, put in a controller (maybe)
                    if (use_flags.use_market == 0 || use_flags.use_market == 3) % normal and dlc
                        fprintf(write_file,'     cooling_setpoint cooling%d*%.2f+%.2f;\n',cooling_set,cool_night_diff,cool_night);
                        fprintf(write_file,'     heating_setpoint heating%d*%.2f+%.2f;\n',heating_set,heat_night_diff,heat_night);
                        
                        if (use_flags.use_market == 3)
                            fprintf(write_file,'     dlc_offset 6;\n');
                            fprintf(write_file,'     object passive_controller {\n');
                            fprintf(write_file,'          control_mode DIRECT_LOAD_CONTROL;\n');
                            fprintf(write_file,'          dlc_mode CYCLING;\n');
                                c_on = 300 + 600*dlc_rand((kk-1)*aS + jj);
                                    temp_c = 0.3+0.4*xval((kk-1)*aS + jj);
                                c_off = c_on * ( temp_c / (1 - temp_c) ); % 30-70% of the total time should be "off"
                            fprintf(write_file,'          cycle_length_on %.0f;\n',c_on);
                            fprintf(write_file,'          cycle_length_off %.0f;\n',c_off);
                            fprintf(write_file,'          period 0;\n');
                            fprintf(write_file,'          state_property override;\n');
                            fprintf(write_file,'          observation_object %s;\n',tech_data.market_info{1});
                            fprintf(write_file,'          observation_property past_market.clearing_price;\n');
                            fprintf(write_file,'          second_tier_price %f;\n',taxonomy_data.CPP_prices(3));
                            fprintf(write_file,'     };\n');
                        end
                    elseif ( (use_flags.use_market == 1 || use_flags.use_market == 2) && market_penetration_random((kk-1)*aS + jj) <= tech_data.market_info{7} && tech_data.use_tech == 1)
                        % TOU or TOU/CPP with technology
                                                
                        % pull in the slider response level
                        slider = slider_random((kk-1)*aS + jj);
                        
                        % set the pre-cool / pre-heat range to really small
                        % to get rid of it.
                        s_tstat = 2;
                        hrh = -5+5*(1-slider);
                        crh = 5-5*(1-slider);
                        hrl = -0.005+0*(1-slider);
                        crl = -0.005+0*(1-slider);
                        
                        hrh2 = -s_tstat - (1 - slider) * (3 - s_tstat);
                        crh2 = s_tstat + (1 - slider) * (3 - s_tstat);
                        hrl2 = -s_tstat - (1 - slider) * (3 - s_tstat);
                        crl2 = s_tstat + (1 - slider) * (3 - s_tstat);
                        
                        if (strcmp(ht,'HP') ~= 0) % Control both therm setpoints
                            fprintf(write_file,'     cooling_setpoint %.2f;\n',cool_night);
                            fprintf(write_file,'     heating_setpoint %.2f;\n',cool_night-3);
                            fprintf(write_file,'\n     object controller {\n');   
                            fprintf(write_file,'           schedule_skew %.0f;\n',skew_value);
                            fprintf(write_file,'           market %s;\n',tech_data.market_info{1});
                            fprintf(write_file,'           bid_mode OFF;\n');
                            fprintf(write_file,'           control_mode DOUBLE_RAMP;\n');
                            fprintf(write_file,'           resolve_mode DEADBAND;\n');
                            fprintf(write_file,'           heating_range_high %.3f;\n',hrh);
                            fprintf(write_file,'           cooling_range_high %.3f;\n',crh);
                            fprintf(write_file,'           heating_range_low %.3f;\n',hrl);
                            fprintf(write_file,'           cooling_range_low %.3f;\n',crl);
                            fprintf(write_file,'           heating_ramp_high %.3f;\n',hrh2);
                            fprintf(write_file,'           cooling_ramp_high %.3f;\n',crh2);
                            fprintf(write_file,'           heating_ramp_low %.3f;\n',hrl2);
                            fprintf(write_file,'           cooling_ramp_low %.3f;\n',crl2);
                            fprintf(write_file,'           cooling_base_setpoint cooling%d*%.2f+%.2f;\n',cooling_set,cool_night_diff,cool_night);
                            fprintf(write_file,'           heating_base_setpoint heating%d*%.2f+%.2f;\n',heating_set,heat_night_diff,heat_night);
                            fprintf(write_file,'           period %.0f;\n',tech_data.market_info{2});
                            fprintf(write_file,'           average_target %s;\n','my_avg');
                            fprintf(write_file,'           standard_deviation_target %s;\n','my_std');
                            fprintf(write_file,'           target air_temperature;\n');
                            fprintf(write_file,'           heating_setpoint heating_setpoint;\n');
                            fprintf(write_file,'           heating_demand last_heating_load;\n');
                            fprintf(write_file,'           cooling_setpoint cooling_setpoint;\n');
                            fprintf(write_file,'           cooling_demand last_cooling_load;\n');
                            fprintf(write_file,'           deadband thermostat_deadband;\n');
                            fprintf(write_file,'           total hvac_load;\n');
                            fprintf(write_file,'           load hvac_load;\n');
                            fprintf(write_file,'           state power_state;\n');
                            fprintf(write_file,'       };\n\n');
                        elseif (strcmp(ht,'ELEC') ~= 0) % Control the heat, but check to see if we have AC
                            if (strcmp(ct,'ELEC') ~= 0) % get to control just like a heat pump
                                fprintf(write_file,'     cooling_setpoint %.2f;\n',cool_night);
                                fprintf(write_file,'     heating_setpoint %.2f;\n',cool_night-3);
                                fprintf(write_file,'\n     object controller {\n');   
                                fprintf(write_file,'           schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'           market %s;\n',tech_data.market_info{1});
                                fprintf(write_file,'           bid_mode OFF;\n');
                                fprintf(write_file,'           control_mode DOUBLE_RAMP;\n');
                                fprintf(write_file,'           resolve_mode DEADBAND;\n');
                                fprintf(write_file,'           heating_range_high %.3f;\n',hrh);
                                fprintf(write_file,'           cooling_range_high %.3f;\n',crh);
                                fprintf(write_file,'           heating_range_low %.3f;\n',hrl);
                                fprintf(write_file,'           cooling_range_low %.3f;\n',crl);
                                fprintf(write_file,'           heating_ramp_high %.3f;\n',hrh2);
                                fprintf(write_file,'           cooling_ramp_high %.3f;\n',crh2);
                                fprintf(write_file,'           heating_ramp_low %.3f;\n',hrl2);
                                fprintf(write_file,'           cooling_ramp_low %.3f;\n',crl2);
                                fprintf(write_file,'           cooling_base_setpoint cooling%d*%.2f+%.2f;\n',cooling_set,cool_night_diff,cool_night);
                                fprintf(write_file,'           heating_base_setpoint heating%d*%.2f+%.2f;\n',heating_set,heat_night_diff,heat_night);
                                fprintf(write_file,'           period %.0f;\n',tech_data.market_info{2});
                                fprintf(write_file,'           average_target %s;\n','my_avg');
                                fprintf(write_file,'           standard_deviation_target %s;\n','my_std');
                                fprintf(write_file,'           target air_temperature;\n');
                                fprintf(write_file,'           heating_setpoint heating_setpoint;\n');
                                fprintf(write_file,'           heating_demand last_heating_load;\n');
                                fprintf(write_file,'           cooling_setpoint cooling_setpoint;\n');
                                fprintf(write_file,'           cooling_demand last_cooling_load;\n');
                                fprintf(write_file,'           deadband thermostat_deadband;\n');
                                fprintf(write_file,'           total hvac_load;\n');
                                fprintf(write_file,'           load hvac_load;\n');
                                fprintf(write_file,'           state power_state;\n');
                                fprintf(write_file,'       };\n\n');
                            else % control only the heat
                                fprintf(write_file,'     cooling_setpoint %.2f;\n',cool_night);
                                fprintf(write_file,'     heating_setpoint %.2f;\n',cool_night-3);
                                fprintf(write_file,'\n     object controller {\n');
                                fprintf(write_file,'           schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'           market %s;\n',tech_data.market_info{1});
                                fprintf(write_file,'           bid_mode OFF;\n');
                                fprintf(write_file,'           control_mode RAMP;\n');
                                fprintf(write_file,'           range_high %.3f;\n',hrh);
                                fprintf(write_file,'           range_low %.3f;\n',hrl);
                                fprintf(write_file,'           ramp_high %.3f;\n',hrh2);
                                fprintf(write_file,'           ramp_low %.3f;\n',hrl2);
                                fprintf(write_file,'           base_setpoint heating%d*%.2f+%.2f;\n',heating_set,heat_night_diff,heat_night);
                                fprintf(write_file,'           period %.0f;\n',tech_data.market_info{2});
                                fprintf(write_file,'           average_target %s;\n','my_avg');
                                fprintf(write_file,'           standard_deviation_target %s;\n','my_std');
                                fprintf(write_file,'           target air_temperature;\n');
                                fprintf(write_file,'           setpoint heating_setpoint;\n');
                                fprintf(write_file,'           demand last_heating_load;\n');
                                fprintf(write_file,'           deadband thermostat_deadband;\n');
                                fprintf(write_file,'           total hvac_load;\n');
                                fprintf(write_file,'           load hvac_load;\n');
                                fprintf(write_file,'           state power_state;\n');
                                fprintf(write_file,'       };\n\n');
                            end
                        elseif (strcmp(ct,'ELEC') ~= 0) % gas heat, but control the AC
                            fprintf(write_file,'     heating_setpoint heating%d*%.2f+%.2f;\n',heating_set,heat_night_diff,heat_night);
                            fprintf(write_file,'\n     object controller {\n');
                            fprintf(write_file,'           schedule_skew %.0f;\n',skew_value);
                            fprintf(write_file,'           market %s;\n',tech_data.market_info{1});
                            fprintf(write_file,'           bid_mode OFF;\n');
                            fprintf(write_file,'           control_mode RAMP;\n');
                            fprintf(write_file,'           range_high %.3f;\n',crh);
                            fprintf(write_file,'           range_low %.3f;\n',crl);
                            fprintf(write_file,'           ramp_high %.3f;\n',crh2);
                            fprintf(write_file,'           ramp_low %.3f;\n',crl2);
                            fprintf(write_file,'           base_setpoint cooling%d*%.2f+%.2f;\n',cooling_set,cool_night_diff,cool_night);
                            fprintf(write_file,'           period %.0f;\n',tech_data.market_info{2});
                            fprintf(write_file,'           average_target %s;\n','my_avg');
                            fprintf(write_file,'           standard_deviation_target %s;\n','my_std');
                            fprintf(write_file,'           target air_temperature;\n');
                            fprintf(write_file,'           setpoint cooling_setpoint;\n');
                            fprintf(write_file,'           demand last_cooling_load;\n');
                            fprintf(write_file,'           deadband thermostat_deadband;\n');
                            fprintf(write_file,'           total hvac_load;\n');
                            fprintf(write_file,'           load hvac_load;\n');
                            fprintf(write_file,'           state power_state;\n');
                            fprintf(write_file,'       };\n\n'); 
                        else % gas heat, no AC, so no control
                            fprintf(write_file,'     cooling_setpoint cooling%d*%.2f+%.2f;\n',cooling_set,cool_night_diff,cool_night);
                            fprintf(write_file,'     heating_setpoint heating%d*%.2f+%.2f;\n',heating_set,heat_night_diff,heat_night);
                        end
                    elseif ( (use_flags.use_market == 1 || use_flags.use_market == 2) && tech_data.use_tech == 0)
                        % TOU/CPP w/o technology - assumes people offset
                        % their thermostats a little more
                        new_rand = 1 + slider_random((kk-1)*aS + jj);
                        fprintf(write_file,'     cooling_setpoint cooling%d*%.2f+%.2f;\n',cooling_set,cool_night_diff*new_rand,cool_night);
                        fprintf(write_file,'     heating_setpoint heating%d*%.2f+%.2f;\n',heating_set,heat_night_diff/new_rand,heat_night);
                    end

                    % scale all of the end-use loads
                    scalar1 = 324.9/8907 * floor_area^0.442;
                    scalar2 = 0.8 + 0.4 * rand(1);
                    scalar3 = 0.8 + 0.4 * rand(1);
                    resp_scalar = scalar1 * scalar2;
                    unresp_scalar = scalar1 * scalar3;

                    % average size is 1.36 kW
                    % Energy Savings through Automatic Seasonal Run-Time Adjustment of Pool Filter Pumps 
                    % Stephen D Allen, B.S. Electrical Engineering
                    pool_pump_power = 1.36 + .36*rand(1);
                    pool_pump_perc = rand(1);

                    % average 4-12 hours / day -> 1/6-1/2 duty cycle
                    % typically run for 2 - 4 hours at a time
                    pp_dutycycle = 1/6 + (1/2 - 1/6)*rand(1);
                    pp_period = 4 + 4*rand(1);
                    pp_init_phase = rand(1);
                  
                    fprintf(write_file,'     object ZIPload {\n');
                    fprintf(write_file,'           name house%d_resp_%s\n',kk,parent);
                    fprintf(write_file,'           // Responsive load\n');           
                    fprintf(write_file,'           schedule_skew %.0f;\n',skew_value);
                    fprintf(write_file,'           base_power responsive_loads*%.2f;\n',resp_scalar);
                    fprintf(write_file,'           heatgain_fraction %.3f;\n',tech_data.heat_fraction);
                    fprintf(write_file,'           power_pf %.3f;\n',tech_data.p_pf);
                    fprintf(write_file,'           current_pf %.3f;\n',tech_data.i_pf);
                    fprintf(write_file,'           impedance_pf %.3f;\n',tech_data.z_pf);
                    fprintf(write_file,'           impedance_fraction %f;\n',tech_data.zfrac);
                    fprintf(write_file,'           current_fraction %f;\n',tech_data.ifrac);
                    fprintf(write_file,'           power_fraction %f;\n',tech_data.pfrac);
                    if (use_flags.use_market == 1 || use_flags.use_market == 2)                        
                        fprintf(write_file,'           object passive_controller {\n');
                        fprintf(write_file,'                period %.0f;\n',tech_data.market_info{2});
                        fprintf(write_file,'                control_mode ELASTICITY_MODEL;\n');
                        fprintf(write_file,'                two_tier_cpp %s;\n',tech_data.two_tier_cpp);
                        fprintf(write_file,'                observation_object %s;\n',tech_data.market_info{1});
                        fprintf(write_file,'                observation_property past_market.clearing_price;\n');
                        fprintf(write_file,'                state_property multiplier;\n');
                        fprintf(write_file,'                linearize_elasticity true;\n');
                        fprintf(write_file,'                price_offset 0.01;\n');
                        if (use_flags.use_market == 2) %CPP
                            fprintf(write_file,'                critical_day %s.value;\n',char(CPP_flag_name));
                            fprintf(write_file,'                first_tier_hours %.0f;\n',taxonomy_data.TOU_hours(1)); 
                            fprintf(write_file,'                second_tier_hours %.0f;\n',taxonomy_data.TOU_hours(2));
                            fprintf(write_file,'                third_tier_hours %.0f;\n',taxonomy_data.TOU_hours(3)); 
                            fprintf(write_file,'                first_tier_price %.6f;\n',taxonomy_data.CPP_prices(1));
                            fprintf(write_file,'                second_tier_price %.6f;\n',taxonomy_data.CPP_prices(2));
                            fprintf(write_file,'                third_tier_price %.6f;\n',taxonomy_data.CPP_prices(3));
                            fprintf(write_file,'                old_first_tier_price %.6f;\n',tech_data.flat_price(region));
                            fprintf(write_file,'                old_second_tier_price %.6f;\n',tech_data.flat_price(region));
                            fprintf(write_file,'                old_third_tier_price %.6f;\n',tech_data.flat_price(region));
                        else
                            fprintf(write_file,'                critical_day 0;\n');
                            fprintf(write_file,'                first_tier_hours %.0f;\n',taxonomy_data.TOU_hours(1)); 
                            fprintf(write_file,'                second_tier_hours %.0f;\n',taxonomy_data.TOU_hours(2));
                            fprintf(write_file,'                first_tier_price %.6f;\n',taxonomy_data.TOU_prices(1));
                            fprintf(write_file,'                second_tier_price %.6f;\n',taxonomy_data.TOU_prices(2));
                            fprintf(write_file,'                old_first_tier_price %.6f;\n',tech_data.flat_price(region));
                            fprintf(write_file,'                old_second_tier_price %.6f;\n',tech_data.flat_price(region));
                        end
                        fprintf(write_file,'                daily_elasticity %s*%.4f;\n',char(tech_data.daily_elasticity),elasticity_random((kk-1)*aS + jj));
                        fprintf(write_file,'                sub_elasticity_first_second %.4f;\n',tech_data.sub_elas_12*elasticity_random((kk-1)*aS + jj));
                        fprintf(write_file,'                sub_elasticity_first_third %.4f;\n',tech_data.sub_elas_13*elasticity_random((kk-1)*aS + jj));                       
                        fprintf(write_file,'            };\n');
                    end
                    fprintf(write_file,'     };\n');

                    fprintf(write_file,'     object ZIPload {\n');
                    fprintf(write_file,'           // Unresponsive load\n');           
                    fprintf(write_file,'           schedule_skew %.0f;\n',skew_value);
                    fprintf(write_file,'           base_power unresponsive_loads*%.2f;\n',unresp_scalar);
                    fprintf(write_file,'           heatgain_fraction %.3f;\n',tech_data.heat_fraction);
                    fprintf(write_file,'           power_pf %.3f;\n',tech_data.p_pf);
                    fprintf(write_file,'           current_pf %.3f;\n',tech_data.i_pf);
                    fprintf(write_file,'           impedance_pf %.3f;\n',tech_data.z_pf);
                    fprintf(write_file,'           impedance_fraction %f;\n',tech_data.zfrac);
                    fprintf(write_file,'           current_fraction %f;\n',tech_data.ifrac);
                    fprintf(write_file,'           power_fraction %f;\n',tech_data.pfrac);
                    fprintf(write_file,'     };\n');

                    % pool pumps only on single-family homes
                    if (pool_pump_perc < 2*regional_data.perc_poolpumps && no_pool_pumps >= 1 && row_ti == 1)
                        fprintf(write_file,'     object ZIPload {\n');
                        fprintf(write_file,'           name house%d_ppump_%s\n',kk,parent);
                        fprintf(write_file,'           // Pool Pump\n');           
                        fprintf(write_file,'           schedule_skew %.0f;\n',pp_skew_value);
                        fprintf(write_file,'           base_power pool_pump_season*%.2f;\n',pool_pump_power);
                        fprintf(write_file,'           duty_cycle %.2f;\n',pp_dutycycle);
                        fprintf(write_file,'           phase %.2f;\n',pp_init_phase);
                        fprintf(write_file,'           period %.2f;\n',pp_period);
                        fprintf(write_file,'           heatgain_fraction 0.0;\n');
                        fprintf(write_file,'           power_pf %.3f;\n',tech_data.p_pf);
                        fprintf(write_file,'           current_pf %.3f;\n',tech_data.i_pf);
                        fprintf(write_file,'           impedance_pf %.3f;\n',tech_data.z_pf);
                        fprintf(write_file,'           impedance_fraction %f;\n',tech_data.zfrac);
                        fprintf(write_file,'           current_fraction %f;\n',tech_data.ifrac);
                        fprintf(write_file,'           power_fraction %f;\n',tech_data.pfrac);
                        fprintf(write_file,'           is_240 TRUE;\n');
                        
                        if ( (use_flags.use_market == 1 || use_flags.use_market == 2) && tech_data.use_tech == 1) % TOU
                            fprintf(write_file,'           recovery_duty_cycle %.2f;\n',pp_dutycycle*(1+pool_pump_recovery_random((kk-1)*aS + jj)));
                            fprintf(write_file,'           object passive_controller {\n');
                            fprintf(write_file,'                period %.0f;\n',tech_data.market_info{2});
                            fprintf(write_file,'                control_mode DUTYCYCLE;\n');
                            fprintf(write_file,'                pool_pump_model true;\n');
                            fprintf(write_file,'                observation_object %s;\n',tech_data.market_info{1});
                            fprintf(write_file,'                observation_property past_market.clearing_price;\n');
                            fprintf(write_file,'                state_property override;\n');
                            fprintf(write_file,'                base_duty_cycle %.2f;\n',pp_dutycycle);
                            fprintf(write_file,'                setpoint duty_cycle;\n');
                            if (use_flags.use_market == 2) %CPP
                                fprintf(write_file,'                first_tier_hours %.0f;\n',taxonomy_data.TOU_hours(1)); 
                                fprintf(write_file,'                second_tier_hours %.0f;\n',taxonomy_data.TOU_hours(2));
                                fprintf(write_file,'                third_tier_hours %.0f;\n',taxonomy_data.TOU_hours(3)); 
                                fprintf(write_file,'                first_tier_price %.6f;\n',taxonomy_data.CPP_prices(1));
                                fprintf(write_file,'                second_tier_price %.6f;\n',taxonomy_data.CPP_prices(2));
                                fprintf(write_file,'                third_tier_price %.6f;\n',taxonomy_data.CPP_prices(3));
                            else
                                fprintf(write_file,'                first_tier_hours %.0f;\n',taxonomy_data.TOU_hours(1)); 
                                fprintf(write_file,'                second_tier_hours %.0f;\n',taxonomy_data.TOU_hours(2));
                                fprintf(write_file,'                first_tier_price %.6f;\n',taxonomy_data.TOU_prices(1));
                                fprintf(write_file,'                second_tier_price %.6f;\n',taxonomy_data.TOU_prices(2));
                            end
                            fprintf(write_file,'           };\n');
                        elseif (use_flags.use_market == 3) % DLC
                            fprintf(write_file,'          object passive_controller {\n');
                            fprintf(write_file,'               control_mode DIRECT_LOAD_CONTROL;\n');
                            fprintf(write_file,'               dlc_mode OFF;\n');
                            fprintf(write_file,'               period 0;\n');
                            fprintf(write_file,'               state_property override;\n');
                            fprintf(write_file,'               observation_object %s;\n',tech_data.market_info{1});
                            fprintf(write_file,'               observation_property past_market.clearing_price;\n');
                            fprintf(write_file,'               second_tier_price %f;\n',taxonomy_data.CPP_prices(3));
                            fprintf(write_file,'         };\n');
                        end
                        
                        fprintf(write_file,'     };\n');

                        no_pool_pumps = no_pool_pumps - 1;
                        
                        %store_pool_pumps
                    end

                        heat_element = 3.0 + 0.5*randi(5);
                        tank_set = 120 + 16*rand(1);
                        therm_dead = 4 + 4*rand(1);
                        tank_UA = 2 + 2*rand(1);
                        water_sch = ceil(regional_data.no_water_sch*rand(1));
                        water_var = 0.95 + rand(1) * 0.1; % +/-5% variability
                        wh_size_test = rand(1);
                        wh_size_rand = randi(3);

                    if (heat_type > (1 - regional_data.wh_electric) && tech_data.use_wh == 1)
                        fprintf(write_file,'     object waterheater {\n');        
                        fprintf(write_file,'          schedule_skew %.0f;\n',wh_skew_value);   
                        fprintf(write_file,'          heating_element_capacity %.1f kW;\n',heat_element);
                        fprintf(write_file,'          tank_setpoint %.1f;\n',tank_set);
                        fprintf(write_file,'          temperature 132;\n');                   
                        fprintf(write_file,'          thermostat_deadband %.1f;\n',therm_dead);
                        fprintf(write_file,'          location INSIDE;\n');                    
                        fprintf(write_file,'          tank_UA %.1f;\n',tank_UA);
                        
                        if (wh_size_test < regional_data.wh_size(1))
                            fprintf(write_file,'          demand small_%.0f*%.02f;\n',water_sch,water_var);
                                whsize = 20 + (wh_size_rand-1) * 5;
                            fprintf(write_file,'          tank_volume %.0f;\n',whsize);
                        elseif (wh_size_test < (regional_data.wh_size(1) + regional_data.wh_size(2)))
                            if(floor_area < 2000)
                                fprintf(write_file,'          demand small_%.0f*%.02f;\n',water_sch,water_var);
                            else
                                fprintf(write_file,'          demand large_%.0f*%.02f;\n',water_sch,water_var);
                            end
                                whsize = 30 + (wh_size_rand - 1)*10;
                            fprintf(write_file,'          tank_volume %.0f;\n',whsize);
                        elseif (floor_area > 2000)
                                whsize = 50 + (wh_size_rand - 1)*10;
                            fprintf(write_file,'          demand large_%.0f*%.02f;\n',water_sch,water_var);
                            fprintf(write_file,'          tank_volume %.0f;\n',whsize);
                        else
                            fprintf(write_file,'          demand large_%.0f*%.02f;\n',water_sch,water_var);
                                whsize = 30 + (wh_size_rand - 1)*10;
                            fprintf(write_file,'          tank_volume %.0f;\n',whsize);
                        end
                        
                        if (use_flags.use_market == 1 || use_flags.use_market == 2 || use_flags.use_market == 3)
                            fprintf(write_file,'          object passive_controller {\n');
                            fprintf(write_file,'	            period %.0f;\n',tech_data.market_info{2});
                            fprintf(write_file,'	            control_mode PROBABILITY_OFF;\n');
                            fprintf(write_file,'	            distribution_type NORMAL;\n');
                            fprintf(write_file,'	            observation_object %s;\n',tech_data.market_info{1});
                            fprintf(write_file,'	            observation_property past_market.clearing_price;\n');
                            fprintf(write_file,'	            stdev_observation_property %s;\n','my_std');
                            fprintf(write_file,'	            expectation_object %s;\n',tech_data.market_info{1});
                            fprintf(write_file,'	            expectation_property %s;\n','my_avg');
                            if (use_flags.use_market == 3) %DLC
                                fprintf(write_file,'	            comfort_level %.2f;\n',9999);
                            else
                            	fprintf(write_file,'	            comfort_level %.2f;\n',slider_random((kk-1)*aS + jj));
                            end
                            fprintf(write_file,'	            state_property override;\n');
                            fprintf(write_file,'          };\n');     
                        elseif (use_flags.use_market == 3)
                            fprintf(write_file,'          object passive_controller {\n');
                            fprintf(write_file,'               control_mode DIRECT_LOAD_CONTROL;\n');
                            fprintf(write_file,'               dlc_mode CYCLING;\n');
                                c_on = 180 + 120*dlc_rand((kk-1)*aS + jj);
                                c_off = 1080 + 720*xval((kk-1)*aS + jj); % 30-70% of the total time should be "off"
                            fprintf(write_file,'               cycle_length_on %.0f;\n',c_on);
                            fprintf(write_file,'               cycle_length_off %.0f;\n',c_off);
                            fprintf(write_file,'               period 0;\n');
                            fprintf(write_file,'               state_property override;\n');
                            fprintf(write_file,'               observation_object %s;\n',tech_data.market_info{1});
                            fprintf(write_file,'               observation_property past_market.clearing_price;\n');
                            fprintf(write_file,'               second_tier_price %f;\n',taxonomy_data.CPP_prices(3));
                            fprintf(write_file,'          };\n');
                        end
                        fprintf(write_file,'     };\n\n');
                    end

                    fprintf(write_file,'}\n\n'); %end house
                end   
            end
        end
        
        %disp(['Mean floor area = ',num2str(mean(fl_area))]);
    end

    % clean up some variables
    clear elasticity_random slider_random market_penetration_random dlc_rand pool_pump_recovery_random
    
    % Initialize pseudo-random numbers - put this before each technology where 
    % random numbers are needed, so they are not effected by other changes
    % (s1-s6)
    RandStream.setGlobalStream(s3);

    % Phase ABC - convert to "commercial buildings" 
    %  if number of "houses" > 15, then create a large office
    %  if number of "houses" < 15 but > 6, create a big box commercial
    %  else, create a residential strip mall
    ph3_meter = 0;
    ph1_meter = 0;
    
    if (no_loads ~= 0 && use_flags.use_commercial == 1)

        % setup all of the line configurations we may need
        fprintf(write_file,'object triplex_line_configuration {\n');
        fprintf(write_file,'      name commercial_line_config;\n');
        fprintf(write_file,'      conductor_1 object triplex_line_conductor {\n');
        fprintf(write_file,'            resistance 0.48;\n');
        fprintf(write_file,'            geometric_mean_radius 0.0158;\n');
        fprintf(write_file,'            };\n');
        fprintf(write_file,'      conductor_2 object triplex_line_conductor {\n');
        fprintf(write_file,'            resistance 0.48;\n');
        fprintf(write_file,'            geometric_mean_radius 0.0158;\n');
        fprintf(write_file,'            };\n');
        fprintf(write_file,'      conductor_N object triplex_line_conductor {\n');
        fprintf(write_file,'            resistance 0.48;\n');
        fprintf(write_file,'            geometric_mean_radius 0.0158;\n');
        fprintf(write_file,'            };\n');
        fprintf(write_file,'      insulation_thickness 0.08;\n');
        fprintf(write_file,'      diameter 0.522;\n');
        fprintf(write_file,'}\n\n');

        fprintf(write_file,'object line_spacing {\n');     
        fprintf(write_file,'      name line_spacing_commABC;\n');     
        fprintf(write_file,'      distance_AB 53.19999999996 in;\n');    
        fprintf(write_file,'      distance_BC 53.19999999996 in;\n');    
        fprintf(write_file,'      distance_AC 53.19999999996 in;\n');    
        fprintf(write_file,'      distance_AN 69.80000000004 in;\n');    
        fprintf(write_file,'      distance_BN 69.80000000004 in;\n');    
        fprintf(write_file,'      distance_CN 69.80000000004 in;\n');    
        fprintf(write_file,'}\n\n'); 

        fprintf(write_file,'object overhead_line_conductor {\n');     
        fprintf(write_file,'      name overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      //name 336.4;\n');    
        fprintf(write_file,'      rating.summer.continuous 443.0;\n');     
        fprintf(write_file,'      geometric_mean_radius 0.02270 ft;\n');    
        fprintf(write_file,'      resistance 0.05230;\n');     
        fprintf(write_file,'}\n\n');

        fprintf(write_file,'object line_configuration {\n');     
        fprintf(write_file,'      name line_configuration_commABC;\n');     
        fprintf(write_file,'      conductor_A overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      conductor_B overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      conductor_C overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      conductor_N overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      spacing line_spacing_commABC;\n');     
        fprintf(write_file,'}\n\n');  

        fprintf(write_file,'object line_configuration {\n');     
        fprintf(write_file,'      name line_configuration_commAB;\n');     
        fprintf(write_file,'      conductor_A overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      conductor_B overhead_line_conductor_comm;\n');         
        fprintf(write_file,'      conductor_N overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      spacing line_spacing_commABC;\n');     
        fprintf(write_file,'}\n\n');  

        fprintf(write_file,'object line_configuration {\n');     
        fprintf(write_file,'      name line_configuration_commAC;\n');     
        fprintf(write_file,'      conductor_A overhead_line_conductor_comm;\n');          
        fprintf(write_file,'      conductor_C overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      conductor_N overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      spacing line_spacing_commABC;\n');     
        fprintf(write_file,'}\n\n');  

        fprintf(write_file,'object line_configuration {\n');     
        fprintf(write_file,'      name line_configuration_commBC;\n');         
        fprintf(write_file,'      conductor_B overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      conductor_C overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      conductor_N overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      spacing line_spacing_commABC;\n');     
        fprintf(write_file,'}\n\n');  

        fprintf(write_file,'object line_configuration {\n');     
        fprintf(write_file,'      name line_configuration_commA;\n');     
        fprintf(write_file,'      conductor_A overhead_line_conductor_comm;\n');        
        fprintf(write_file,'      conductor_N overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      spacing line_spacing_commABC;\n');     
        fprintf(write_file,'}\n\n');  

        fprintf(write_file,'object line_configuration {\n');     
        fprintf(write_file,'      name line_configuration_commB;\n');        
        fprintf(write_file,'      conductor_B overhead_line_conductor_comm;\n');         
        fprintf(write_file,'      conductor_N overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      spacing line_spacing_commABC;\n');     
        fprintf(write_file,'}\n\n'); 

        fprintf(write_file,'object line_configuration {\n');     
        fprintf(write_file,'      name line_configuration_commC;\n');        
        fprintf(write_file,'      conductor_C overhead_line_conductor_comm;\n');         
        fprintf(write_file,'      conductor_N overhead_line_conductor_comm;\n');     
        fprintf(write_file,'      spacing line_spacing_commABC;\n');     
        fprintf(write_file,'}\n\n');      

        [r1,r2] = size(load_houses{5});
        for iii = 1:r2
            total_comm_houses = load_houses{1,1}{iii} + load_houses{1,2}{iii} + load_houses{1,3}{iii};

            my_phases = {'A';'B';'C'};
            % read through the phases and do some bit-wise math
            has_phase_A = 0;
            has_phase_B = 0;
            has_phase_C = 0;
            ph = '';
            if (length(strfind(load_houses{1,5}{iii},'A')) ~= 0)
                has_phase_A = 1;
                ph = strcat(ph,'A');
            end
            if (length(strfind(load_houses{1,5}{iii},'B')) ~= 0)
                has_phase_B = 1;
                ph = strcat(ph,'B');
            end
            if (length(strfind(load_houses{1,5}{iii},'C')) ~= 0)
                has_phase_C = 1;
                ph = strcat(ph,'C');
            end

            no_of_phases = has_phase_A + has_phase_B + has_phase_C;

            if (no_of_phases == 0)
                error('The phases in commercial buildings did not add up right.');
            end

            % Same for everyone - TODO: move to tech specs?
                air_heat_fraction = 0;
                mass_solar_gain_fraction = 0.5;
                mass_internal_gain_fraction = 0.5;
                fan_type = 'ONE_SPEED';
                heat_type = 'GAS';
                cool_type = 'ELECTRIC';
                aux_type = 'NONE';
                cooling_design_temperature = 100;
                heating_design_temperature = 1;
                over_sizing_factor = 0.3;
                no_of_stories = 1;

                surface_heat_trans_coeff = 0.59;

            % Office building - must have all three phases and enough load for
            % 15 zones
            if (total_comm_houses > 15 && no_of_phases == 3)
                no_of_offices = round(total_comm_houses / 15);
                ph3_meter = ph3_meter + 1;
                
                my_name = strrep(load_houses{1,4}{iii},';','');

                fprintf(write_file,'object transformer_configuration {\n');
                fprintf(write_file,'     name CTTF_config_A_%s;\n',my_name);
                fprintf(write_file,'     connect_type SINGLE_PHASE_CENTER_TAPPED;\n');
                fprintf(write_file,'     install_type POLETOP;\n');
                fprintf(write_file,'     impedance 0.00033+0.0022j;\n');
                fprintf(write_file,'     shunt_impedance 10000+10000j;\n');
                fprintf(write_file,'     primary_voltage %.3f;\n',taxonomy_data.nom_volt2);
                fprintf(write_file,'     secondary_voltage %.3f;\n',120*sqrt(3));
                fprintf(write_file,'     powerA_rating %.0f kVA;\n',50);
                fprintf(write_file,'};\n');

                fprintf(write_file,'object transformer_configuration {\n');
                fprintf(write_file,'     name CTTF_config_B_%s;\n',my_name);
                fprintf(write_file,'     connect_type SINGLE_PHASE_CENTER_TAPPED;\n');
                fprintf(write_file,'     install_type POLETOP;\n');
                fprintf(write_file,'     impedance 0.00033+0.0022j;\n');
                fprintf(write_file,'     shunt_impedance 10000+10000j;\n');
                fprintf(write_file,'     primary_voltage %.3f;\n',taxonomy_data.nom_volt2);
                fprintf(write_file,'     secondary_voltage %.3f;\n',120*sqrt(3));
                fprintf(write_file,'     powerB_rating %.0f kVA;\n',50);
                fprintf(write_file,'};\n');

                fprintf(write_file,'object transformer_configuration {\n');
                fprintf(write_file,'     name CTTF_config_C_%s;\n',my_name);
                fprintf(write_file,'     connect_type SINGLE_PHASE_CENTER_TAPPED;\n');
                fprintf(write_file,'     install_type POLETOP;\n');
                fprintf(write_file,'     impedance 0.00033+0.0022j;\n');
                fprintf(write_file,'     shunt_impedance 10000+10000j;\n');
                fprintf(write_file,'     primary_voltage %.3f;\n',taxonomy_data.nom_volt2);
                fprintf(write_file,'     secondary_voltage %.3f;\n',120*sqrt(3));
                fprintf(write_file,'     powerC_rating %.0f kVA;\n',50);
                fprintf(write_file,'};\n');

                for jjj = 1:no_of_offices
                    floor_area_choose = 40000 * (0.5 * rand(1) + 0.5); %up to -50%
                    fprintf(write_file,'// %f\n',floor_area_choose);
                    ceiling_height = 13;
                    airchange_per_hour = 0.69;
                    Rroof = 19;
                    Rwall = 18.3;
                    Rfloor = 46;
                    Rdoors = 3;
                    glazing_layers = 'TWO';
                    glass_type = 'GLASS';
                    glazing_treatment = 'LOW_S';
                    window_frame = 'NONE';
                    int_gains = 3.24; %W/sf

                    fprintf(write_file,'object overhead_line {\n');
                    fprintf(write_file,'     from %s;\n',my_name);
                    fprintf(write_file,'     to %s_office_meter%.0f;\n',my_name,jjj);
                    fprintf(write_file,'     phases %s\n',load_houses{1,5}{iii});
                    fprintf(write_file,'     length 50ft;\n');
                    fprintf(write_file,'     configuration line_configuration_comm%s;\n',ph);
                    fprintf(write_file,'};\n\n');
                    no_ohls = no_ohls + 1;

                    fprintf(write_file,'object meter {\n');            
                    fprintf(write_file,'     phases %s\n',load_houses{1,5}{iii});
                    fprintf(write_file,'     name %s_office_meter%.0f;\n',my_name,jjj);
                    fprintf(write_file,'     groupid Commercial_Meter;\n');
                    fprintf(write_file,'     meter_power_consumption %s;\n',tech_data.comm_meter_cons);
                    fprintf(write_file,'     nominal_voltage %f;\n',taxonomy_data.nom_volt2);
                    if (use_flags.use_billing == 1)
                        fprintf(write_file,'     bill_mode UNIFORM;\n');
                        fprintf(write_file,'     price %.5f;\n',tech_data.comm_flat_price(region));
                        fprintf(write_file,'     monthly_fee %.2f;\n',tech_data.comm_monthly_fee);
                        fprintf(write_file,'     bill_day 1;\n');
                    elseif (use_flags.use_billing == 2) % TIERED
                        error('use_flag.use_billing == 2 not functional at this time');
                    elseif (use_flags.use_billing == 3) % TOU or RTP
                        fprintf(write_file,'      bill_mode HOURLY;\n');
                        fprintf(write_file,'      monthly_fee %.2f;\n',tech_data.comm_monthly_fee);
                        fprintf(write_file,'      bill_day 1;\n');
                        fprintf(write_file,'      power_market %s;\n',tech_data.market_info{1});
                    end
                    fprintf(write_file,'}\n\n');
                    
                    if (tech_data.get_IEEE_stats == 0)
                        for phind = 1:3                  
                            fprintf(write_file,'object transformer {\n');
                            fprintf(write_file,'     name %s_CTTF_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'     phases %sS;\n',my_phases{phind});
                            fprintf(write_file,'     from %s_office_meter%.0f;\n',my_name,jjj);
                            fprintf(write_file,'     to %s_tm_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'     groupid %s;\n','Distribution_Trans');
                            fprintf(write_file,'     configuration CTTF_config_%s_%s;\n',my_phases{phind},my_name);
                            fprintf(write_file,'}\n\n');


                            fprintf(write_file,'object triplex_meter {\n');
                            fprintf(write_file,'     name %s_tm_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'     phases %sS;\n',my_phases{phind});
                            fprintf(write_file,'     nominal_voltage 120;\n');
                            fprintf(write_file,'}\n\n');

                            % skew each office zone identically per floor
                            sk = round(2*randn(1));
                            skew_value = tech_data.commercial_skew_std * sk;
                            if (skew_value < -tech_data.commercial_skew_max)
                                skew_value = -tech_data.commercial_skew_max;
                            elseif (skew_value > tech_data.commercial_skew_max)
                                skew_value = tech_data.commercial_skew_max;
                            end

                            for zoneind=1:5
                                total_depth = sqrt(floor_area_choose / (3 * 1.5));
                                total_width = 1.5 * total_depth;

                                if (phind < 3)
                                    exterior_ceiling_fraction = 0;
                                else
                                    exterior_ceiling_fraction = 1;
                                end

                                if (zoneind == 5)
                                    exterior_wall_fraction = 0;
                                    w = total_depth - 30;
                                    d = total_width - 30;
                                    floor_area = w*d;
                                    aspect_ratio = w/d;
                                else
                                    window_wall_ratio = 0.33;

                                    if (zoneind == 1 || zoneind == 3)
                                        w = total_width - 15;
                                        d = 15;
                                        floor_area = w*d;
                                        exterior_wall_fraction = w / (2 * (w+d));
                                        aspect_ratio = w/d;
                                    else
                                        w = total_depth - 15;
                                        d = 15;
                                        floor_area = w*d;                        
                                        exterior_wall_fraction = w / (2 * (w+d));
                                        aspect_ratio = w/d;
                                    end
                                end

                                if (phind > 1)
                                    exterior_floor_fraction = 0;
                                else
                                    exterior_floor_fraction = w / (2*(w+d)) / (floor_area / (floor_area_choose/3));
                                end

                                thermal_mass_per_floor_area = 3.9 * (0.5 + 1 * rand(1)); %+/- 50%
                                interior_exterior_wall_ratio = (floor_area * (2 - 1) + 0*20) / (no_of_stories * ceiling_height * 2 * (w+d)) - 1 + window_wall_ratio*exterior_wall_fraction;
                                no_of_doors = 0.1; % will round to zero

                                fprintf(write_file,'object house {\n');
                                fprintf(write_file,'     name office%s_%s%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'     parent %s_tm_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                                fprintf(write_file,'     groupid Commercial;\n');
                                fprintf(write_file,'     schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'     floor_area %.0f;\n',floor_area);
                                fprintf(write_file,'     design_internal_gains %.0f;\n',int_gains*floor_area*3.413);
                                fprintf(write_file,'     number_of_doors %.0f;\n',no_of_doors);
                                fprintf(write_file,'     aspect_ratio %.2f;\n',aspect_ratio);
                                fprintf(write_file,'     total_thermal_mass_per_floor_area %1.2f;\n',thermal_mass_per_floor_area);
                                fprintf(write_file,'     interior_surface_heat_transfer_coeff %1.2f;\n',surface_heat_trans_coeff);
                                fprintf(write_file,'     interior_exterior_wall_ratio %2.1f;\n',interior_exterior_wall_ratio);
                                fprintf(write_file,'     exterior_floor_fraction %.3f;\n',exterior_floor_fraction);
                                fprintf(write_file,'     exterior_ceiling_fraction %.3f;\n',exterior_ceiling_fraction);
                                fprintf(write_file,'     Rwall %2.1f;\n',Rwall);
                                fprintf(write_file,'     Rroof %2.1f;\n',Rroof);
                                fprintf(write_file,'     Rfloor %.2f;\n',Rfloor);
                                fprintf(write_file,'     Rdoors %2.1f;\n',Rdoors);
                                fprintf(write_file,'     exterior_wall_fraction %.2f;\n',exterior_wall_fraction);
                                fprintf(write_file,'     glazing_layers %s;\n',glazing_layers);
                                fprintf(write_file,'     glass_type %s;\n',glass_type);
                                fprintf(write_file,'     glazing_treatment %s;\n',glazing_treatment);
                                fprintf(write_file,'     window_frame %s;\n',window_frame);            
                                fprintf(write_file,'     airchange_per_hour %.2f;\n',airchange_per_hour);    
                                fprintf(write_file,'     window_wall_ratio %0.3f;\n',window_wall_ratio);    
                                fprintf(write_file,'     heating_system_type %s;\n',heat_type);
                                fprintf(write_file,'     auxiliary_system_type %s;\n',aux_type);
                                fprintf(write_file,'     fan_type %s;\n',fan_type);
                                fprintf(write_file,'     cooling_system_type %s;\n',cool_type);

                                init_temp = 68 + 4*rand(1);
                                fprintf(write_file,'     air_temperature %.2f;\n',init_temp);
                                fprintf(write_file,'     mass_temperature %.2f;\n',init_temp);

                                    os_rand = regional_data.over_sizing_factor * (.8 + 0.4*rand);
                                fprintf(write_file,'     over_sizing_factor %.1f;\n',os_rand);

                                    COP_A = tech_data.cooling_COP * (0.8 + 0.4*rand(1));
                                fprintf(write_file,'     cooling_COP %2.2f;\n',COP_A);

                                if (use_flags.use_ts~=0)
                                    %Create array of parents for thermal storage devices
                                    ts_office_array{iii}{jjj}{phind}{zoneind} = ['office' my_name '_' my_phases{phind} num2str(jjj) '_zone' num2str(zoneind)];
                                end
                                
                                if (use_flags.use_solar~=0 || use_flags.use_solar_com ~=0)
                                    %Create array of parents for office solar generators 
                                    solar_office_array{iii}{jjj}{phind}{zoneind} = ['office' my_name '_' my_phases{phind} num2str(jjj) '_zone' num2str(zoneind)];
                                    solar_office_array_parent{iii}{jjj}{phind} = [my_name '_tm_' my_phases{phind} '_' num2str(jjj)];
                                    solar_office_array_phases{iii}{jjj}{phind} = [my_phases{phind}];
                                end
                                
                                if (use_flags.use_energy_storage ~= 0 || use_flags.use_energy_storage_com ~= 0)
                                    es_office_array{iii}{jjj}{phind}{zoneind} = ['office' my_name '_' my_phases{phind} num2str(jjj) '_zone' num2str(zoneind)];
                                    es_office_array_parent{iii}{jjj}{phind} = [my_name '_tm_' my_phases{phind} '_' num2str(jjj)];
                                    es_office_array_phases{iii}{jjj}{phind} = [my_phases{phind}];
                                end
                                
                                if ( (use_flags.use_market == 1 || use_flags.use_market == 2) && tech_data.use_tech == 1)
                                    % pull in the slider response level
                                        slider = comm_slider_random(jjj);

                                        s_tstat = 2;
                                        hrh = -5+5*(1-slider);
                                        crh = 5-5*(1-slider);
                                        hrl = -0.005+0*(1-slider);
                                        crl = -0.005+0*(1-slider);

                                        hrh2 = -s_tstat - (1 - slider) * (3 - s_tstat);
                                        crh2 = s_tstat + (1 - slider) * (3 - s_tstat);
                                        hrl2 = -s_tstat - (1 - slider) * (3 - s_tstat);
                                        crl2 = s_tstat + (1 - slider) * (3 - s_tstat);
                                    fprintf(write_file,'\n     object controller {\n');
                                    fprintf(write_file,'           schedule_skew %.0f;\n',skew_value);
                                    fprintf(write_file,'           market %s;\n',tech_data.market_info{1});
                                    fprintf(write_file,'           bid_mode OFF;\n');
                                    fprintf(write_file,'           control_mode RAMP;\n');
                                    fprintf(write_file,'           range_high %.3f;\n',crh);
                                    fprintf(write_file,'           range_low %.3f;\n',crl);
                                    fprintf(write_file,'           ramp_high %.3f;\n',crh2);
                                    fprintf(write_file,'           ramp_low %.3f;\n',crl2);
                                    fprintf(write_file,'           base_setpoint office_cooling;\n');
                                    fprintf(write_file,'           period %.0f;\n',tech_data.market_info{2});
                                    fprintf(write_file,'           average_target %s;\n','my_avg');
                                    fprintf(write_file,'           standard_deviation_target %s;\n','my_std');
                                    fprintf(write_file,'           target air_temperature;\n');
                                    fprintf(write_file,'           setpoint cooling_setpoint;\n');
                                    fprintf(write_file,'           demand last_cooling_load;\n');
                                    fprintf(write_file,'           deadband thermostat_deadband;\n');
                                    fprintf(write_file,'           total hvac_load;\n');
                                    fprintf(write_file,'           load hvac_load;\n');
                                    fprintf(write_file,'           state power_state;\n');
                                    fprintf(write_file,'       };\n\n'); 
                                    fprintf(write_file,'     cooling_setpoint 85;\n');
                                else
                                    fprintf(write_file,'     cooling_setpoint office_cooling;\n');
                                    if (use_flags.use_market == 3)    
                                        fprintf(write_file,'          object passive_controller {\n');
                                        fprintf(write_file,'               control_mode DIRECT_LOAD_CONTROL;\n');
                                        fprintf(write_file,'               dlc_mode CYCLING;\n');
                                            c_on = 600 + 600*dlc_c_rand( (iii-1) * no_of_offices + jjj );
                                                temp_c = 0.2+0.3*dlc_c_rand2((iii-1)*no_of_offices + jjj);
                                            c_off = c_on * ( temp_c / (1 - temp_c) ); % 30-50% of the total time should be "off"
                                        fprintf(write_file,'               cycle_length_on %.0f;\n',c_on);
                                        fprintf(write_file,'               cycle_length_off %.0f;\n',c_off);
                                        fprintf(write_file,'               period 0;\n');
                                        fprintf(write_file,'               state_property override;\n');
                                        fprintf(write_file,'               observation_object %s;\n',tech_data.market_info{1});
                                        fprintf(write_file,'               observation_property past_market.clearing_price;\n');
                                        fprintf(write_file,'               second_tier_price %f;\n',taxonomy_data.CPP_prices(3));
                                        fprintf(write_file,'          };\n');
                                    end
                                end

                                fprintf(write_file,'     heating_setpoint office_heating;\n');


                                % Need all of the "appliances"
                                fprintf(write_file,'     // Lights\n');
                                fprintf(write_file,'     object ZIPload {\n');
                                fprintf(write_file,'          name lights_%s_%s_%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'          heatgain_fraction 1.0;\n');
                                fprintf(write_file,'          power_fraction %.2f;\n',tech_data.c_pfrac);
                                fprintf(write_file,'          impedance_fraction %.2f;\n',tech_data.c_zfrac);
                                fprintf(write_file,'          current_fraction %.2f;\n',tech_data.c_ifrac);
                                fprintf(write_file,'          power_pf %.2f;\n',tech_data.c_p_pf);
                                fprintf(write_file,'          current_pf %.2f;\n',tech_data.c_i_pf);
                                fprintf(write_file,'          impedance_pf %.2f;\n',tech_data.c_z_pf);

                                    adj_lights = (0.9 + 0.1*rand(1)) * floor_area / 1000; % randomize 10% then convert W/sf -> kW 
                                fprintf(write_file,'          base_power office_lights*%.2f;\n',adj_lights);
                                fprintf(write_file,'     };\n\n');

                                fprintf(write_file,'     // Plugs\n');
                                fprintf(write_file,'     object ZIPload {\n');
                                fprintf(write_file,'          name plugs_%s_%s_%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'          heatgain_fraction 1.0;\n');
                                fprintf(write_file,'          power_fraction %.2f;\n',tech_data.c_pfrac);
                                fprintf(write_file,'          impedance_fraction %.2f;\n',tech_data.c_zfrac);
                                fprintf(write_file,'          current_fraction %.2f;\n',tech_data.c_ifrac);
                                fprintf(write_file,'          power_pf %.2f;\n',tech_data.c_p_pf);
                                fprintf(write_file,'          current_pf %.2f;\n',tech_data.c_i_pf);
                                fprintf(write_file,'          impedance_pf %.2f;\n',tech_data.c_z_pf);

                                    adj_plugs = (0.9 + 0.2*rand(1)) * floor_area / 1000; % randomize 20% then convert W/sf -> kW 
                                fprintf(write_file,'          base_power office_plugs*%.2f;\n',adj_plugs);
                                fprintf(write_file,'     };\n\n');

                                fprintf(write_file,'     // Gas Waterheater\n');
                                fprintf(write_file,'     object ZIPload {\n');
                                fprintf(write_file,'          name wh_%s_%s_%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'          heatgain_fraction 1.0;\n');
                                fprintf(write_file,'          power_fraction 0.0;\n');
                                fprintf(write_file,'          impedance_fraction 0.0;\n');
                                fprintf(write_file,'          current_fraction 0.0;\n');
                                fprintf(write_file,'          power_pf 1.0;\n');  

                                    adj_gas = (0.9 + 0.2*rand(1)) * floor_area / 1000; % randomize 20% then convert W/sf -> kW 
                                fprintf(write_file,'          base_power office_gas*%.2f;\n',adj_gas);
                                fprintf(write_file,'     };\n\n');

                                fprintf(write_file,'     // Exterior Lighting\n');
                                fprintf(write_file,'     object ZIPload {\n');
                                fprintf(write_file,'          name ext_%s_%s_%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'          heatgain_fraction 0.0;\n');
                                fprintf(write_file,'          power_fraction %.2f;\n',tech_data.c_pfrac);
                                fprintf(write_file,'          impedance_fraction %.2f;\n',tech_data.c_zfrac);
                                fprintf(write_file,'          current_fraction %.2f;\n',tech_data.c_ifrac);
                                fprintf(write_file,'          power_pf %.2f;\n',tech_data.c_p_pf);
                                fprintf(write_file,'          current_pf %.2f;\n',tech_data.c_i_pf);
                                fprintf(write_file,'          impedance_pf %.2f;\n',tech_data.c_z_pf); 

                                    adj_ext = (0.9 + 0.1*rand(1)) * floor_area / 1000; % randomize 10% then convert W/sf -> kW 
                                fprintf(write_file,'          base_power office_exterior*%.2f;\n',adj_ext);
                                fprintf(write_file,'     };\n\n');

                                fprintf(write_file,'     // Occupancy\n');
                                fprintf(write_file,'     object ZIPload {\n');
                                fprintf(write_file,'          name occ_%s_%s_%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'          heatgain_fraction 1.0;\n');
                                fprintf(write_file,'          power_fraction 0.0;\n');
                                fprintf(write_file,'          impedance_fraction 0.0;\n');
                                fprintf(write_file,'          current_fraction 0.0;\n');
                                fprintf(write_file,'          power_pf 1.0;\n');  

                                    adj_occ = (0.9 + 0.1*rand(1)) * floor_area / 1000; % randomize 10% then convert W/sf -> kW 
                                fprintf(write_file,'          base_power office_occupancy*%.2f;\n',adj_occ);
                                fprintf(write_file,'     };\n');
                                fprintf(write_file,'}\n\n');
                            end % office zones (1-5)        
                        end % office phases (A-C)
                    end
                end % total offices needed

            % Big box - has at least 2 phases and enough load for 6 zones
            elseif (total_comm_houses > 6 && no_of_phases >= 2)
                no_of_bigboxes = round(total_comm_houses / 6);
                ph3_meter = ph3_meter + 1;
                
                my_name = strrep(load_houses{1,4}{iii},';','');

                if (has_phase_A == 1)
                    fprintf(write_file,'object transformer_configuration {\n');
                    fprintf(write_file,'     name CTTF_config_A_%s;\n',my_name);
                    fprintf(write_file,'     connect_type SINGLE_PHASE_CENTER_TAPPED;\n');
                    fprintf(write_file,'     install_type POLETOP;\n');
                    fprintf(write_file,'     impedance 0.00033+0.0022j;\n');
                    fprintf(write_file,'     shunt_impedance 10000+10000j;\n');
                    fprintf(write_file,'     primary_voltage %.3f;\n',taxonomy_data.nom_volt2);
                    fprintf(write_file,'     secondary_voltage %.3f;\n',120*sqrt(3));
                    fprintf(write_file,'     powerA_rating %.0f kVA;\n',50);
                    fprintf(write_file,'};\n');
                end

                if (has_phase_B == 1)
                    fprintf(write_file,'object transformer_configuration {\n');
                    fprintf(write_file,'     name CTTF_config_B_%s;\n',my_name);
                    fprintf(write_file,'     connect_type SINGLE_PHASE_CENTER_TAPPED;\n');
                    fprintf(write_file,'     install_type POLETOP;\n');
                    fprintf(write_file,'     impedance 0.00033+0.0022j;\n');
                    fprintf(write_file,'     shunt_impedance 10000+10000j;\n');
                    fprintf(write_file,'     primary_voltage %.3f;\n',taxonomy_data.nom_volt2);
                    fprintf(write_file,'     secondary_voltage %.3f;\n',120*sqrt(3));
                    fprintf(write_file,'     powerB_rating %.0f kVA;\n',50);
                    fprintf(write_file,'};\n');
                end

                if (has_phase_C == 1)
                    fprintf(write_file,'object transformer_configuration {\n');
                    fprintf(write_file,'     name CTTF_config_C_%s;\n',my_name);
                    fprintf(write_file,'     connect_type SINGLE_PHASE_CENTER_TAPPED;\n');
                    fprintf(write_file,'     install_type POLETOP;\n');
                    fprintf(write_file,'     impedance 0.00033+0.0022j;\n');
                    fprintf(write_file,'     shunt_impedance 10000+10000j;\n');
                    fprintf(write_file,'     primary_voltage %.3f;\n',taxonomy_data.nom_volt2);
                    fprintf(write_file,'     secondary_voltage %.3f;\n',120*sqrt(3));
                    fprintf(write_file,'     powerC_rating %.0f kVA;\n',50);
                    fprintf(write_file,'};\n');
                end

                for jjj = 1:no_of_bigboxes
                    floor_area_choose = 20000 * (0.5 + 1 * rand(1)); %+/- 50%
                    ceiling_height = 14;
                    airchange_per_hour = 1.5;
                    Rroof = 19;
                    Rwall = 18.3;
                    Rfloor = 46;
                    Rdoors = 3;
                    glazing_layers = 'TWO';
                    glass_type = 'GLASS';
                    glazing_treatment = 'LOW_S';
                    window_frame = 'NONE';
                    int_gains = 3.6; %W/sf

                    fprintf(write_file,'object overhead_line {\n');
                    fprintf(write_file,'     from %s;\n',my_name);
                    fprintf(write_file,'     to %s_bigbox_meter%.0f;\n',my_name,jjj);
                    fprintf(write_file,'     phases %s\n',load_houses{1,5}{iii});
                    fprintf(write_file,'     length 50ft;\n');
                    fprintf(write_file,'     configuration line_configuration_comm%s;\n',ph);
                    fprintf(write_file,'};\n\n');
                    no_ohls = no_ohls + 1;

                    fprintf(write_file,'object meter {\n');            
                    fprintf(write_file,'     phases %s\n',load_houses{1,5}{iii});
                    fprintf(write_file,'     name %s_bigbox_meter%.0f;\n',my_name,jjj);
                    fprintf(write_file,'     groupid Commercial_Meter;\n');
                    fprintf(write_file,'     nominal_voltage %f;\n',taxonomy_data.nom_volt2);
                    fprintf(write_file,'     meter_power_consumption %s;\n',tech_data.comm_meter_cons);
                    if (use_flags.use_billing == 1)
                        fprintf(write_file,'     bill_mode UNIFORM;\n');
                        fprintf(write_file,'     price %.5f;\n',tech_data.comm_flat_price(region));
                        fprintf(write_file,'     monthly_fee %.2f;\n',tech_data.comm_monthly_fee);
                        fprintf(write_file,'     bill_day 1;\n');
                    elseif (use_flags.use_billing == 2) % TIERED
                        error('use_flag.use_billing == 2 not functional at this time');
                    elseif (use_flags.use_billing == 3) % TOU or RTP
                        fprintf(write_file,'      bill_mode HOURLY;\n');
                        fprintf(write_file,'      monthly_fee %.2f;\n',tech_data.comm_monthly_fee);
                        fprintf(write_file,'      bill_day 1;\n');
                        fprintf(write_file,'      power_market %s;\n',tech_data.market_info{1});
                    end
                    fprintf(write_file,'}\n\n');
                    
                    % skew each big box zone identically
                    sk = round(2*randn(1));
                    skew_value = tech_data.commercial_skew_std * sk;
                    if (skew_value < -tech_data.commercial_skew_max)
                        skew_value = -tech_data.commercial_skew_max;
                    elseif (skew_value > tech_data.commercial_skew_max)
                        skew_value = tech_data.commercial_skew_max;
                    end

                    total_index = 0;
                    
                    if (tech_data.get_IEEE_stats == 0)
                        for phind=1:3
                            % skip outta the for-loop if the phase is missing
                            if (phind==1 && has_phase_A == 0)
                                continue;
                            elseif (phind==2 && has_phase_B == 0)
                                continue;
                            elseif (phind==3 && has_phase_C == 0)
                                continue;
                            end

                            fprintf(write_file,'object transformer {\n');
                            fprintf(write_file,'     name %s_CTTF_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'     phases %sS;\n',my_phases{phind});
                            fprintf(write_file,'     from %s_bigbox_meter%.0f;\n',my_name,jjj);
                            fprintf(write_file,'     to %s_tm_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'     groupid %s;\n','Distribution_Trans');
                            fprintf(write_file,'     configuration CTTF_config_%s_%s;\n',my_phases{phind},my_name);
                            fprintf(write_file,'}\n\n');


                            fprintf(write_file,'object triplex_meter {\n');
                            fprintf(write_file,'     name %s_tm_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'     phases %sS;\n',my_phases{phind});
                            fprintf(write_file,'     nominal_voltage 120;\n');
                            fprintf(write_file,'}\n\n');

                            zones_per_phase = 6 / no_of_phases;
                            for zoneind=1:zones_per_phase
                                total_index = total_index + 1;
                                thermal_mass_per_floor_area = 3.9 * (0.8 + 0.4 * rand(1)); %+/- 20%
                                floor_area = floor_area_choose / 6;
                                exterior_ceiling_fraction = 1;
                                aspect_ratio = 1.28301275561855;

                                total_depth = sqrt(floor_area_choose / aspect_ratio);
                                total_width = aspect_ratio * total_depth;
                                d = total_width / 3;               
                                w = total_depth / 2;
                                if (total_index == 2 || total_index == 5)
                                    exterior_wall_fraction = d / (2*(d + w));
                                    exterior_floor_fraction = (0 + d) / (2*(total_width + total_depth)) / (floor_area / (floor_area_choose));
                                else
                                    exterior_wall_fraction = 0.5;
                                    exterior_floor_fraction = (w + d) / (2*(total_width + total_depth)) / (floor_area / (floor_area_choose));
                                end

                                if (total_index == 2)
                                    window_wall_ratio = 0.76;
                                else
                                    window_wall_ratio = 0;
                                end

                                if (total_index < 4)
                                    no_of_doors = 0.1; % this will round to 0
                                elseif (j == 4 || j== 6)
                                    no_of_doors = 1;
                                else
                                    no_of_doors = 24;
                                end
                                interior_exterior_wall_ratio = (floor_area * (2 - 1) + no_of_doors*20) / (no_of_stories * ceiling_height * 2 * (w+d)) - 1 + window_wall_ratio*exterior_wall_fraction;

                                if (total_index > 6)
                                    error('Something wrong in the indexing of the retail strip.');
                                end

                                fprintf(write_file,'object house {\n');
                                fprintf(write_file,'     name bigbox%s_%s%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'     groupid Commercial;\n');
                                fprintf(write_file,'     schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'     parent %s_tm_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                                fprintf(write_file,'     floor_area %.0f;\n',floor_area);
                                fprintf(write_file,'     design_internal_gains %.0f;\n',int_gains*floor_area*3.413);
                                fprintf(write_file,'     number_of_doors %.0f;\n',no_of_doors);
                                fprintf(write_file,'     aspect_ratio %.2f;\n',aspect_ratio);
                                fprintf(write_file,'     total_thermal_mass_per_floor_area %1.2f;\n',thermal_mass_per_floor_area);
                                fprintf(write_file,'     interior_surface_heat_transfer_coeff %1.2f;\n',surface_heat_trans_coeff);
                                fprintf(write_file,'     interior_exterior_wall_ratio %2.1f;\n',interior_exterior_wall_ratio);
                                fprintf(write_file,'     exterior_floor_fraction %.3f;\n',exterior_floor_fraction);
                                fprintf(write_file,'     exterior_ceiling_fraction %.3f;\n',exterior_ceiling_fraction);
                                fprintf(write_file,'     Rwall %2.1f;\n',Rwall);
                                fprintf(write_file,'     Rroof %2.1f;\n',Rroof);
                                fprintf(write_file,'     Rfloor %.2f;\n',Rfloor);
                                fprintf(write_file,'     Rdoors %2.1f;\n',Rdoors);
                                fprintf(write_file,'     exterior_wall_fraction %.2f;\n',exterior_wall_fraction);
                                fprintf(write_file,'     glazing_layers %s;\n',glazing_layers);
                                fprintf(write_file,'     glass_type %s;\n',glass_type);
                                fprintf(write_file,'     glazing_treatment %s;\n',glazing_treatment);
                                fprintf(write_file,'     window_frame %s;\n',window_frame);            
                                fprintf(write_file,'     airchange_per_hour %.2f;\n',airchange_per_hour);    
                                fprintf(write_file,'     window_wall_ratio %0.3f;\n',window_wall_ratio);    
                                fprintf(write_file,'     heating_system_type %s;\n',heat_type);
                                fprintf(write_file,'     auxiliary_system_type %s;\n',aux_type);
                                fprintf(write_file,'     fan_type %s;\n',fan_type);
                                fprintf(write_file,'     cooling_system_type %s;\n',cool_type);

                                    init_temp = 68 + 4*rand(1);
                                fprintf(write_file,'     air_temperature %.2f;\n',init_temp);
                                fprintf(write_file,'     mass_temperature %.2f;\n',init_temp);

                                    os_rand = regional_data.over_sizing_factor * (.8 + 0.4*rand);
                                fprintf(write_file,'     over_sizing_factor %.1f;\n',os_rand);

                                    COP_A = tech_data.cooling_COP * (0.8 + 0.4*rand(1));
                                fprintf(write_file,'     cooling_COP %2.2f;\n',COP_A);

                                if (use_flags.use_ts~=0)
                                    %Create array of parents for thermal storage devices
                                    ts_bigbox_array{iii}{jjj}{phind}{zoneind} = ['bigbox' my_name '_' my_phases{phind} num2str(jjj) '_zone' num2str(zoneind)];
                                end
                                
                                if (use_flags.use_solar~=0 ||use_flags.use_solar_com ~=0)
                                    %Create array of parents for bigbox solar generators
                                                                      
                                    solar_bigbox_array{iii}{jjj}{phind}{zoneind} = ['bigbox' my_name '_' my_phases{phind} num2str(jjj) '_zone' num2str(zoneind)];
                                    solar_bigbox_array_parent{iii}{jjj}{phind} = [my_name '_tm_' my_phases{phind} '_' num2str(jjj)];
                                    solar_bigbox_array_phases{iii}{jjj}{phind} = [my_phases{phind}];
                                end
                                
                                if (use_flags.use_energy_storage ~= 0 || use_flags.use_energy_storage_com ~= 0)
                                    es_bigbox_array{iii}{jjj}{phind}{zoneind} = ['bigbox' my_name '_' my_phases{phind} num2str(jjj) '_zone' num2str(zoneind)];
                                    es_bigbox_array_parent{iii}{jjj}{phind} = [my_name '_tm_' my_phases{phind} '_' num2str(jjj)];
                                    es_bigbox_array_phases{iii}{jjj}{phind} = [my_phases{phind}];
                                end
                                
                                if ( (use_flags.use_market == 1 || use_flags.use_market == 2) && tech_data.use_tech == 1)
                                    % pull in the slider response level
                                        slider = comm_slider_random(jjj);

                                        s_tstat = 2;
                                        hrh = -5+5*(1-slider);
                                        crh = 5-5*(1-slider);
                                        hrl = -0.005+0*(1-slider);
                                        crl = -0.005+0*(1-slider);

                                        hrh2 = -s_tstat - (1 - slider) * (3 - s_tstat);
                                        crh2 = s_tstat + (1 - slider) * (3 - s_tstat);
                                        hrl2 = -s_tstat - (1 - slider) * (3 - s_tstat);
                                        crl2 = s_tstat + (1 - slider) * (3 - s_tstat);
                                    fprintf(write_file,'\n     object controller {\n');
                                    fprintf(write_file,'           schedule_skew %.0f;\n',skew_value);
                                    fprintf(write_file,'           market %s;\n',tech_data.market_info{1});
                                    fprintf(write_file,'           bid_mode OFF;\n');
                                    fprintf(write_file,'           control_mode RAMP;\n');
                                    fprintf(write_file,'           range_high %.3f;\n',crh);
                                    fprintf(write_file,'           range_low %.3f;\n',crl);
                                    fprintf(write_file,'           ramp_high %.3f;\n',crh2);
                                    fprintf(write_file,'           ramp_low %.3f;\n',crl2);
                                    fprintf(write_file,'           base_setpoint bigbox_cooling;\n');
                                    fprintf(write_file,'           period %.0f;\n',tech_data.market_info{2});
                                    fprintf(write_file,'           average_target %s;\n','my_avg');
                                    fprintf(write_file,'           standard_deviation_target %s;\n','my_std');
                                    fprintf(write_file,'           target air_temperature;\n');
                                    fprintf(write_file,'           setpoint cooling_setpoint;\n');
                                    fprintf(write_file,'           demand last_cooling_load;\n');
                                    fprintf(write_file,'           deadband thermostat_deadband;\n');
                                    fprintf(write_file,'           total hvac_load;\n');
                                    fprintf(write_file,'           load hvac_load;\n');
                                    fprintf(write_file,'           state power_state;\n');
                                    fprintf(write_file,'       };\n\n'); 
                                    fprintf(write_file,'     cooling_setpoint 85;\n');
                                else
                                    fprintf(write_file,'     cooling_setpoint bigbox_cooling;\n');
                                    if (use_flags.use_market == 3)    
                                        fprintf(write_file,'          object passive_controller {\n');
                                        fprintf(write_file,'               control_mode DIRECT_LOAD_CONTROL;\n');
                                        fprintf(write_file,'               dlc_mode CYCLING;\n');
                                            c_on = 600 + 600*dlc_c_rand( (iii-1) * no_of_bigboxes + jjj + phind);
                                                temp_c = 0.2+0.3*dlc_c_rand2((iii-1)*no_of_bigboxes + jjj +phind);
                                            c_off = c_on * ( temp_c / (1 - temp_c) ); % 30-50% of the total time should be "off"
                                        fprintf(write_file,'               cycle_length_on %.0f;\n',c_on);
                                        fprintf(write_file,'               cycle_length_off %.0f;\n',c_off);
                                        fprintf(write_file,'               period 0;\n');
                                        fprintf(write_file,'               state_property override;\n');
                                        fprintf(write_file,'               observation_object %s;\n',tech_data.market_info{1});
                                        fprintf(write_file,'               observation_property past_market.clearing_price;\n');
                                        fprintf(write_file,'               second_tier_price %f;\n',taxonomy_data.CPP_prices(3));
                                        fprintf(write_file,'          };\n');
                                    end
                                        
                                end

                                fprintf(write_file,'     heating_setpoint bigbox_heating;\n');

                                % Need all of the "appliances"
                                fprintf(write_file,'     // Lights\n');
                                fprintf(write_file,'     object ZIPload {\n');
                                fprintf(write_file,'          name lights_%s_%s_%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'          heatgain_fraction 1.0;\n');
                                fprintf(write_file,'          power_fraction %.2f;\n',tech_data.c_pfrac);
                                fprintf(write_file,'          impedance_fraction %.2f;\n',tech_data.c_zfrac);
                                fprintf(write_file,'          current_fraction %.2f;\n',tech_data.c_ifrac);
                                fprintf(write_file,'          power_pf %.2f;\n',tech_data.c_p_pf);
                                fprintf(write_file,'          current_pf %.2f;\n',tech_data.c_i_pf);
                                fprintf(write_file,'          impedance_pf %.2f;\n',tech_data.c_z_pf); 

                                    adj_lights = 1.2 * (0.9 + 0.1*rand(1)) * floor_area / 1000; % randomize 10% then convert W/sf -> kW 
                                fprintf(write_file,'          base_power bigbox_lights*%.2f;\n',adj_lights);
                                fprintf(write_file,'     };\n\n');

                                fprintf(write_file,'     // Plugs\n');
                                fprintf(write_file,'     object ZIPload {\n');
                                fprintf(write_file,'          name plugs_%s_%s_%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'          heatgain_fraction 1.0;\n');
                                fprintf(write_file,'          power_fraction %.2f;\n',tech_data.c_pfrac);
                                fprintf(write_file,'          impedance_fraction %.2f;\n',tech_data.c_zfrac);
                                fprintf(write_file,'          current_fraction %.2f;\n',tech_data.c_ifrac);
                                fprintf(write_file,'          power_pf %.2f;\n',tech_data.c_p_pf);
                                fprintf(write_file,'          current_pf %.2f;\n',tech_data.c_i_pf);
                                fprintf(write_file,'          impedance_pf %.2f;\n',tech_data.c_z_pf);

                                    adj_plugs = (0.9 + 0.2*rand(1)) * floor_area / 1000; % randomize 20% then convert W/sf -> kW 
                                fprintf(write_file,'          base_power bigbox_plugs*%.2f;\n',adj_plugs);
                                fprintf(write_file,'     };\n\n');

                                fprintf(write_file,'     // Gas Waterheater\n');
                                fprintf(write_file,'     object ZIPload {\n');
                                fprintf(write_file,'          name wh_%s_%s_%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'          heatgain_fraction 1.0;\n');
                                fprintf(write_file,'          power_fraction 0.0;\n');
                                fprintf(write_file,'          impedance_fraction 0.0;\n');
                                fprintf(write_file,'          current_fraction 0.0;\n');
                                fprintf(write_file,'          power_pf 1.0;\n');  

                                    adj_gas = (0.9 + 0.2*rand(1)) * floor_area / 1000; % randomize 20% then convert W/sf -> kW 
                                fprintf(write_file,'          base_power bigbox_gas*%.2f;\n',adj_gas);
                                fprintf(write_file,'     };\n\n');

                                fprintf(write_file,'     // Exterior Lighting\n');
                                fprintf(write_file,'     object ZIPload {\n');
                                fprintf(write_file,'          name ext_%s_%s_%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'          heatgain_fraction 0.0;\n');
                                fprintf(write_file,'          power_fraction %.2f;\n',tech_data.c_pfrac);
                                fprintf(write_file,'          impedance_fraction %.2f;\n',tech_data.c_zfrac);
                                fprintf(write_file,'          current_fraction %.2f;\n',tech_data.c_ifrac);
                                fprintf(write_file,'          power_pf %.2f;\n',tech_data.c_p_pf);
                                fprintf(write_file,'          current_pf %.2f;\n',tech_data.c_i_pf);
                                fprintf(write_file,'          impedance_pf %.2f;\n',tech_data.c_z_pf);

                                    adj_ext = (0.9 + 0.1*rand(1)) * floor_area / 1000; % randomize 10% then convert W/sf -> kW 
                                fprintf(write_file,'          base_power bigbox_exterior*%.2f;\n',adj_ext);
                                fprintf(write_file,'     };\n\n');

                                fprintf(write_file,'     // Occupancy\n');
                                fprintf(write_file,'     object ZIPload {\n');
                                fprintf(write_file,'          name occ_%s_%s_%.0f_zone%.0f;\n',my_name,my_phases{phind},jjj,zoneind);
                                fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'          heatgain_fraction 1.0;\n');
                                fprintf(write_file,'          power_fraction 0.0;\n');
                                fprintf(write_file,'          impedance_fraction 0.0;\n');
                                fprintf(write_file,'          current_fraction 0.0;\n');
                                fprintf(write_file,'          power_pf 1.0;\n');  

                                    adj_occ = (0.9 + 0.1*rand(1)) * floor_area / 1000; % randomize 10% then convert W/sf -> kW 
                                fprintf(write_file,'          base_power bigbox_occupancy*%.2f;\n',adj_occ);
                                fprintf(write_file,'     };\n');
                                fprintf(write_file,'}\n\n');
                            end %zone index
                        end %phase index    
                    end
                end %number of big boxes
            % Strip mall
            elseif (total_comm_houses > 0)
                no_of_strip = total_comm_houses;
                ph1_meter = ph1_meter + 1;
                
                my_name = strrep(load_houses{1,4}{iii},';','');

                strip_per_phase = ceil(no_of_strip / no_of_phases);

                if (has_phase_A == 1)
                    fprintf(write_file,'object transformer_configuration {\n');
                    fprintf(write_file,'     name CTTF_config_A_%s;\n',my_name);
                    fprintf(write_file,'     connect_type SINGLE_PHASE_CENTER_TAPPED;\n');
                    fprintf(write_file,'     install_type POLETOP;\n');
                    fprintf(write_file,'     impedance 0.00033+0.0022j;\n');
                    fprintf(write_file,'     shunt_impedance 100000+100000j;\n');
                    fprintf(write_file,'     primary_voltage %.3f;\n',taxonomy_data.nom_volt2);
                    fprintf(write_file,'     secondary_voltage %.3f;\n',120*sqrt(3));
                    fprintf(write_file,'     powerA_rating %.0f kVA;\n',50*strip_per_phase);
                    fprintf(write_file,'};\n');
                end

                if (has_phase_B == 1)
                    fprintf(write_file,'object transformer_configuration {\n');
                    fprintf(write_file,'     name CTTF_config_B_%s;\n',my_name);
                    fprintf(write_file,'     connect_type SINGLE_PHASE_CENTER_TAPPED;\n');
                    fprintf(write_file,'     install_type POLETOP;\n');
                    fprintf(write_file,'     impedance 0.00033+0.0022j;\n');
                    fprintf(write_file,'     shunt_impedance 100000+100000j;\n');
                    fprintf(write_file,'     primary_voltage %.3f;\n',taxonomy_data.nom_volt2);
                    fprintf(write_file,'     secondary_voltage %.3f;\n',120*sqrt(3));
                    fprintf(write_file,'     powerB_rating %.0f kVA;\n',50*strip_per_phase);
                    fprintf(write_file,'};\n');
                end

                if (has_phase_C == 1)
                    fprintf(write_file,'object transformer_configuration {\n');
                    fprintf(write_file,'     name CTTF_config_C_%s;\n',my_name);
                    fprintf(write_file,'     connect_type SINGLE_PHASE_CENTER_TAPPED;\n');
                    fprintf(write_file,'     install_type POLETOP;\n');
                    fprintf(write_file,'     impedance 0.00033+0.0022j;\n');
                    fprintf(write_file,'     shunt_impedance 100000+100000j;\n');
                    fprintf(write_file,'     primary_voltage %.3f;\n',taxonomy_data.nom_volt2);
                    fprintf(write_file,'     secondary_voltage %.3f;\n',120*sqrt(3));
                    fprintf(write_file,'     powerC_rating %.0f kVA;\n',50*strip_per_phase);
                    fprintf(write_file,'};\n');
                end

                fprintf(write_file,'object overhead_line {\n');
                fprintf(write_file,'     from %s;\n',my_name);
                fprintf(write_file,'     to %s_strip_node;\n',my_name);
                fprintf(write_file,'     phases %s\n',load_houses{1,5}{iii});
                fprintf(write_file,'     length 50ft;\n');
                fprintf(write_file,'     configuration line_configuration_comm%s;\n',ph);
                fprintf(write_file,'};\n\n');
                no_ohls = no_ohls + 1;

                fprintf(write_file,'object node {\n');            
                fprintf(write_file,'     phases %s\n',load_houses{1,5}{iii});
                fprintf(write_file,'     name %s_strip_node;\n',my_name);
                fprintf(write_file,'     nominal_voltage %f;\n',taxonomy_data.nom_volt2);
                fprintf(write_file,'}\n\n');


                for phind=1:3
                    % skip outta the for-loop if the phase is missing
                    if (phind==1 && has_phase_A == 0)
                        continue;
                    elseif (phind==2 && has_phase_B == 0)
                        continue;
                    elseif (phind==3 && has_phase_C == 0)
                        continue;
                    end

                    floor_area_choose = 2400 * (0.7 + 0.6 * rand(1)); %+/- 30%
                    ceiling_height = 12;
                    airchange_per_hour = 1.76;
                    Rroof = 19;
                    Rwall = 18.3;
                    Rfloor = 40;
                    Rdoors = 3;
                    glazing_layers = 'TWO';
                    glass_type = 'GLASS';
                    glazing_treatment = 'LOW_S';
                    window_frame = 'NONE';
                    int_gains = 3.6; %W/sf
                    thermal_mass_per_floor_area = 3.9 * (0.5 + 1 * rand(1)); %+/- 50%
                    exterior_ceiling_fraction = 1;

                    for jjj = 1:strip_per_phase
                        
                        % skew each office zone identically per floor
                        sk = round(2*randn(1));
                        skew_value = tech_data.commercial_skew_std * sk;
                        if (skew_value < -tech_data.commercial_skew_max)
                            skew_value = -tech_data.commercial_skew_max;
                        elseif (skew_value > tech_data.commercial_skew_max)
                            skew_value = tech_data.commercial_skew_max;
                        end
                        
                        if (jjj == 1 || jjj == (floor(strip_per_phase/2)+1))
                            floor_area = floor_area_choose;
                            aspect_ratio = 1.5;
                            window_wall_ratio = 0.05;

                            if (j == jjj)
                                exterior_wall_fraction = 0.7;
                                exterior_floor_fraction = 1.4;                    
                            else
                                exterior_wall_fraction = 0.4;
                                exterior_floor_fraction = 0.8;
                            end

                            interior_exterior_wall_ratio = -0.05;
                        else
                            floor_area = floor_area_choose/2;
                            aspect_ratio = 3.0;
                            window_wall_ratio = 0.03;

                            if (jjj == strip_per_phase)
                                exterior_wall_fraction = 0.63;
                                exterior_floor_fraction = 2;
                            else
                                exterior_wall_fraction = 0.25;
                                exterior_floor_fraction = 0.8;
                            end

                            interior_exterior_wall_ratio = -0.40;
                        end

                        no_of_doors = 1;

                        fprintf(write_file,'object transformer {\n');
                        fprintf(write_file,'     name %s_CTTF_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                        fprintf(write_file,'     phases %sS;\n',my_phases{phind});
                        fprintf(write_file,'     from %s_strip_node;\n',my_name);
                        fprintf(write_file,'     to %s_tn_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                        fprintf(write_file,'     groupid %s;\n','Distribution_Trans');
                        fprintf(write_file,'     configuration CTTF_config_%s_%s;\n',my_phases{phind},my_name);
                        fprintf(write_file,'}\n\n');


                        fprintf(write_file,'object triplex_node {\n');
                        fprintf(write_file,'     name %s_tn_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                        fprintf(write_file,'     phases %sS;\n',my_phases{phind});
                        fprintf(write_file,'     nominal_voltage 120;\n');
                        fprintf(write_file,'}\n\n');

                        fprintf(write_file,'object triplex_meter {\n');
                        fprintf(write_file,'     parent %s_tn_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                        fprintf(write_file,'     name %s_tm_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                        fprintf(write_file,'     phases %sS;\n',my_phases{phind});
                        fprintf(write_file,'     groupid Commercial_Meter;\n');
                        % divide by 3 since these are smaller units
                            my_variable = str2num(tech_data.comm_meter_cons)/3;
                        fprintf(write_file,'     meter_power_consumption %f+%fj;\n',real(my_variable),imag(my_variable)); 
                        fprintf(write_file,'     nominal_voltage 120;\n');
                        if (use_flags.use_billing == 1)
                            fprintf(write_file,'     bill_mode UNIFORM;\n');
                            fprintf(write_file,'     price %.5f;\n',tech_data.comm_flat_price(region));
                            fprintf(write_file,'     monthly_fee %.2f;\n',tech_data.comm_monthly_fee);
                            fprintf(write_file,'     bill_day 1;\n');
                        elseif (use_flags.use_billing == 2) % TIERED
                            error('use_flag.use_billing == 2 not functional at this time');
                        elseif (use_flags.use_billing == 3) % TOU or RTP
                            fprintf(write_file,'      bill_mode HOURLY;\n');
                            fprintf(write_file,'      monthly_fee %.2f;\n',tech_data.comm_monthly_fee);
                            fprintf(write_file,'      bill_day 1;\n');
                            fprintf(write_file,'      power_market %s;\n',tech_data.market_info{1});
                        end
                        fprintf(write_file,'}\n\n');

                        if (tech_data.get_IEEE_stats == 0)
                            fprintf(write_file,'object house {\n');
                            fprintf(write_file,'     name stripmall%s_%s%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'     groupid Commercial;\n');
                            fprintf(write_file,'     schedule_skew %.0f;\n',skew_value);
                            fprintf(write_file,'     parent %s_tm_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'     floor_area %.0f;\n',floor_area);
                            fprintf(write_file,'     design_internal_gains %.0f;\n',int_gains*floor_area*3.413);
                            fprintf(write_file,'     number_of_doors %.0f;\n',no_of_doors);
                            fprintf(write_file,'     aspect_ratio %.2f;\n',aspect_ratio);
                            fprintf(write_file,'     total_thermal_mass_per_floor_area %1.2f;\n',thermal_mass_per_floor_area);
                            fprintf(write_file,'     interior_surface_heat_transfer_coeff %1.2f;\n',surface_heat_trans_coeff);
                            fprintf(write_file,'     interior_exterior_wall_ratio %2.1f;\n',interior_exterior_wall_ratio);
                            fprintf(write_file,'     exterior_floor_fraction %.3f;\n',exterior_floor_fraction);
                            fprintf(write_file,'     exterior_ceiling_fraction %.3f;\n',exterior_ceiling_fraction);
                            fprintf(write_file,'     Rwall %2.1f;\n',Rwall);
                            fprintf(write_file,'     Rroof %2.1f;\n',Rroof);
                            fprintf(write_file,'     Rfloor %.2f;\n',Rfloor);
                            fprintf(write_file,'     Rdoors %2.1f;\n',Rdoors);
                            fprintf(write_file,'     exterior_wall_fraction %.2f;\n',exterior_wall_fraction);
                            fprintf(write_file,'     glazing_layers %s;\n',glazing_layers);
                            fprintf(write_file,'     glass_type %s;\n',glass_type);
                            fprintf(write_file,'     glazing_treatment %s;\n',glazing_treatment);
                            fprintf(write_file,'     window_frame %s;\n',window_frame);            
                            fprintf(write_file,'     airchange_per_hour %.2f;\n',airchange_per_hour);    
                            fprintf(write_file,'     window_wall_ratio %0.3f;\n',window_wall_ratio);    
                            fprintf(write_file,'     heating_system_type %s;\n',heat_type);
                            fprintf(write_file,'     auxiliary_system_type %s;\n',aux_type);
                            fprintf(write_file,'     fan_type %s;\n',fan_type);
                            fprintf(write_file,'     cooling_system_type %s;\n',cool_type);

                                init_temp = 68 + 4*rand(1);
                            fprintf(write_file,'     air_temperature %.2f;\n',init_temp);
                            fprintf(write_file,'     mass_temperature %.2f;\n',init_temp);

                                os_rand = regional_data.over_sizing_factor * (.8 + 0.4*rand);
                            fprintf(write_file,'     over_sizing_factor %.1f;\n',os_rand);

                                COP_A = tech_data.cooling_COP * (0.8 + 0.4*rand(1));
                            fprintf(write_file,'     cooling_COP %2.2f;\n',COP_A);

                            if (use_flags.use_ts~=0)
                                %Create array of parents for thermal storage devices
                                ts_stripmall_array{iii}{jjj}{phind} = ['stripmall' my_name '_' my_phases{phind} num2str(jjj)];
                            end
                            if (use_flags.use_solar~=0 || use_flags.use_solar_com ~=0)
                                %Create array of parents for stripmall solar generators
                                solar_stripmall_array{iii}{jjj}{phind} = ['stripmall' my_name '_' my_phases{phind} num2str(jjj)];
                                solar_stripmall_array_fa{iii}{jjj}{phind} = floor_area;                                                                
                                solar_stripmall_array_parent{iii}{jjj}{phind} = [my_name '_tn_' my_phases{phind} '_' num2str(jjj)];
                                solar_stripmall_array_phases{iii}{jjj}{phind} = [my_phases{phind}];
                            end
                            
                            if (use_flags.use_energy_storage ~= 0 || use_flags.use_energy_storage_com ~= 0)
                                es_stripmall_array{iii}{jjj}{phind} = ['stripmall' my_name '_' my_phases{phind} num2str(jjj)];
                                es_stripmall_array_parent{iii}{jjj}{phind} = [my_name '_tm_' my_phases{phind} '_' num2str(jjj)];
                                es_stripmall_array_phases{iii}{jjj}{phind} = [my_phases{phind}];
                            end

                            if ( (use_flags.use_market == 1 || use_flags.use_market == 2) && tech_data.use_tech == 1)
                                % pull in the slider response level
                                    slider = comm_slider_random(jjj);

                                    s_tstat = 2;
                                    hrh = -5+5*(1-slider);
                                    crh = 5-5*(1-slider);
                                    hrl = -0.005+0*(1-slider);
                                    crl = -0.005+0*(1-slider);

                                    hrh2 = -s_tstat - (1 - slider) * (3 - s_tstat);
                                    crh2 = s_tstat + (1 - slider) * (3 - s_tstat);
                                    hrl2 = -s_tstat - (1 - slider) * (3 - s_tstat);
                                    crl2 = s_tstat + (1 - slider) * (3 - s_tstat);
                                fprintf(write_file,'\n     object controller {\n');
                                fprintf(write_file,'           schedule_skew %.0f;\n',skew_value);
                                fprintf(write_file,'           market %s;\n',tech_data.market_info{1});
                                fprintf(write_file,'           bid_mode OFF;\n');
                                fprintf(write_file,'           control_mode RAMP;\n');
                                fprintf(write_file,'           range_high %.3f;\n',crh);
                                fprintf(write_file,'           range_low %.3f;\n',crl);
                                fprintf(write_file,'           ramp_high %.3f;\n',crh2);
                                fprintf(write_file,'           ramp_low %.3f;\n',crl2);
                                fprintf(write_file,'           base_setpoint stripmall_cooling;\n');
                                fprintf(write_file,'           period %.0f;\n',tech_data.market_info{2});
                                fprintf(write_file,'           average_target %s;\n','my_avg');
                                fprintf(write_file,'           standard_deviation_target %s;\n','my_std');
                                fprintf(write_file,'           target air_temperature;\n');
                                fprintf(write_file,'           setpoint cooling_setpoint;\n');
                                fprintf(write_file,'           demand last_cooling_load;\n');
                                fprintf(write_file,'           deadband thermostat_deadband;\n');
                                fprintf(write_file,'           total hvac_load;\n');
                                fprintf(write_file,'           load hvac_load;\n');
                                fprintf(write_file,'           state power_state;\n');
                                fprintf(write_file,'       };\n\n'); 
                                fprintf(write_file,'     cooling_setpoint 85;\n');
                            else
                                fprintf(write_file,'     cooling_setpoint stripmall_cooling;\n');
                                if (use_flags.use_market == 3)    
                                    fprintf(write_file,'          object passive_controller {\n');
                                    fprintf(write_file,'               control_mode DIRECT_LOAD_CONTROL;\n');
                                    fprintf(write_file,'               dlc_mode CYCLING;\n');
                                        c_on = 600 + 600*dlc_c_rand( (iii-1) * strip_per_phase + jjj + phind );
                                            temp_c = 0.2+0.3*dlc_c_rand2((iii-1)*strip_per_phase + jjj + phind);
                                        c_off = c_on * ( temp_c / (1 - temp_c) ); % 30-50% of the total time should be "off"
                                    fprintf(write_file,'               cycle_length_on %.0f;\n',c_on);
                                    fprintf(write_file,'               cycle_length_off %.0f;\n',c_off);
                                    fprintf(write_file,'               period 0;\n');
                                    fprintf(write_file,'               state_property override;\n');
                                    fprintf(write_file,'               observation_object %s;\n',tech_data.market_info{1});
                                    fprintf(write_file,'               observation_property past_market.clearing_price;\n');
                                    fprintf(write_file,'               second_tier_price %f;\n',taxonomy_data.CPP_prices(3));
                                    fprintf(write_file,'          };\n');
                                end
                            end

                            fprintf(write_file,'     heating_setpoint stripmall_heating;\n');

                            %TODO Fix the commercial zip loads
                            % Need all of the "appliances"
                            fprintf(write_file,'     // Lights\n');
                            fprintf(write_file,'     object ZIPload {\n');
                            fprintf(write_file,'          name lights_%s_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                            fprintf(write_file,'          heatgain_fraction 1.0;\n');
                            fprintf(write_file,'          power_fraction %.2f;\n',tech_data.c_pfrac);
                            fprintf(write_file,'          impedance_fraction %.2f;\n',tech_data.c_zfrac);
                            fprintf(write_file,'          current_fraction %.2f;\n',tech_data.c_ifrac);
                            fprintf(write_file,'          power_pf %.2f;\n',tech_data.c_p_pf);
                            fprintf(write_file,'          current_pf %.2f;\n',tech_data.c_i_pf);
                            fprintf(write_file,'          impedance_pf %.2f;\n',tech_data.c_z_pf);

                                adj_lights = (0.8 + 0.4*rand(1)) * floor_area / 1000; % randomize 10% then convert W/sf -> kW 
                            fprintf(write_file,'          base_power stripmall_lights*%.2f;\n',adj_lights);
                            fprintf(write_file,'     };\n\n');

                            fprintf(write_file,'     // Plugs\n');
                            fprintf(write_file,'     object ZIPload {\n');
                            fprintf(write_file,'          name plugs_%s_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                            fprintf(write_file,'          heatgain_fraction 1.0;\n');
                            fprintf(write_file,'          power_fraction %.2f;\n',tech_data.c_pfrac);
                            fprintf(write_file,'          impedance_fraction %.2f;\n',tech_data.c_zfrac);
                            fprintf(write_file,'          current_fraction %.2f;\n',tech_data.c_ifrac);
                            fprintf(write_file,'          power_pf %.2f;\n',tech_data.c_p_pf);
                            fprintf(write_file,'          current_pf %.2f;\n',tech_data.c_i_pf);
                            fprintf(write_file,'          impedance_pf %.2f;\n',tech_data.c_z_pf);

                                adj_plugs = (0.8 + 0.4*rand(1)) * floor_area / 1000; % randomize 20% then convert W/sf -> kW 
                            fprintf(write_file,'          base_power stripmall_plugs*%.2f;\n',adj_plugs);
                            fprintf(write_file,'     };\n\n');

                            fprintf(write_file,'     // Gas Waterheater\n');
                            fprintf(write_file,'     object ZIPload {\n');
                            fprintf(write_file,'          name wh_%s_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                            fprintf(write_file,'          heatgain_fraction 1.0;\n');
                            fprintf(write_file,'          power_fraction 0.0;\n');
                            fprintf(write_file,'          impedance_fraction 0.0;\n');
                            fprintf(write_file,'          current_fraction 0.0;\n');
                            fprintf(write_file,'          power_pf 1.0;\n');  

                                adj_gas = (0.8 + 0.4*rand(1)) * floor_area / 1000; % randomize 20% then convert W/sf -> kW 
                            fprintf(write_file,'          base_power stripmall_gas*%.2f;\n',adj_gas);
                            fprintf(write_file,'     };\n\n');

                            fprintf(write_file,'     // Exterior Lighting\n');
                            fprintf(write_file,'     object ZIPload {\n');
                            fprintf(write_file,'          name ext_%s_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                            fprintf(write_file,'          heatgain_fraction 0.0;\n');
                            fprintf(write_file,'          power_fraction %.2f;\n',tech_data.c_pfrac);
                            fprintf(write_file,'          impedance_fraction %.2f;\n',tech_data.c_zfrac);
                            fprintf(write_file,'          current_fraction %.2f;\n',tech_data.c_ifrac);
                            fprintf(write_file,'          power_pf %.2f;\n',tech_data.c_p_pf);
                            fprintf(write_file,'          current_pf %.2f;\n',tech_data.c_i_pf);
                            fprintf(write_file,'          impedance_pf %.2f;\n',tech_data.c_z_pf); 

                                adj_ext = (0.8 + 0.4*rand(1)) * floor_area / 1000; % randomize 10% then convert W/sf -> kW 
                            fprintf(write_file,'          base_power stripmall_exterior*%.2f;\n',adj_ext);
                            fprintf(write_file,'     };\n\n');

                            fprintf(write_file,'     // Occupancy\n');
                            fprintf(write_file,'     object ZIPload {\n');
                            fprintf(write_file,'          name occ_%s_%s_%.0f;\n',my_name,my_phases{phind},jjj);
                            fprintf(write_file,'          schedule_skew %.0f;\n',skew_value);
                            fprintf(write_file,'          heatgain_fraction 1.0;\n');
                            fprintf(write_file,'          power_fraction 0.0;\n');
                            fprintf(write_file,'          impedance_fraction 0.0;\n');
                            fprintf(write_file,'          current_fraction 0.0;\n');
                            fprintf(write_file,'          power_pf 1.0;\n');  

                                adj_occ = (0.8 + 0.4*rand(1)) * floor_area / 1000; % randomize 10% then convert W/sf -> kW 
                            fprintf(write_file,'          base_power stripmall_occupancy*%.2f;\n',adj_occ);
                            fprintf(write_file,'     };\n');
                            fprintf(write_file,'}\n\n');
                        end
                    end %number of strip zones
                end %phase index
            end %commercial selection
            
            % add the "street light" loads
            % parent them to the METER as opposed to the node, so we don't
            % have any "grandchildren"
            for phind = 1:3
                if (load_houses{1,phind}{iii} == 0 && load_houses{1,phind+5}{iii} > 0)    
                    
                    fprintf(write_file,'object load {\n');
                    fprintf(write_file,'     parent %s\n',load_houses{1,9}{iii});
                    fprintf(write_file,'     name str_light_%s%s\n',my_phases{phind},load_houses{1,4}{iii});
                    fprintf(write_file,'     nominal_voltage %.2f;\n',taxonomy_data.nom_volt2);
                    fprintf(write_file,'     phases %s;\n',my_phases{phind});
                    fprintf(write_file,'     base_power_%s street_lighting*%f;\n',my_phases{phind},tech_data.light_scalar_comm*load_houses{1,phind+5}{iii});
                    fprintf(write_file,'     power_pf_%s %f;\n',my_phases{phind},tech_data.c_p_pf);
                    fprintf(write_file,'     current_pf_%s %f;\n',my_phases{phind},tech_data.c_i_pf);
                    fprintf(write_file,'     impedance_pf_%s %f;\n',my_phases{phind},tech_data.c_z_pf);
                    fprintf(write_file,'     power_fraction_%s %f;\n',my_phases{phind},tech_data.c_pfrac);
                    fprintf(write_file,'     current_fraction_%s %f;\n',my_phases{phind},tech_data.c_ifrac);
                    fprintf(write_file,'     impedance_fraction_%s %f;\n',my_phases{phind},tech_data.c_zfrac);
                    fprintf(write_file,'}\n\n');
                    
                end
            end
        end
    end

    if (use_flags.use_batt == 2) %centralized
        fprintf(write_file,'object meter {\n');
        fprintf(write_file,'     parent %s\n',swing_node);
        fprintf(write_file,'     name battery_meter;\n');
        fprintf(write_file,'     nominal_voltage %.2f;\n',taxonomy_data.nom_volt/sqrt(3));
        fprintf(write_file,'     phases ABCN;\n');
        fprintf(write_file,'}\n\n');

        fprintf(write_file,'object battery {\n');
        fprintf(write_file,'	 parent battery_meter;\n');
        fprintf(write_file,'	 name battery_central;\n');
        fprintf(write_file,'     generator_mode CONSTANT_PQ;\n');
        fprintf(write_file,'     V_Max 8000;\n');
        fprintf(write_file,'     I_Max 250;\n');
        fprintf(write_file,'     P_Max %.0f;\n',tech_data.battery_power);
        fprintf(write_file,'     E_Max %.0f;\n',tech_data.battery_energy);
        fprintf(write_file,'     base_efficiency %.2f;\n',tech_data.efficiency);
        fprintf(write_file,'     parasitic_power_draw %.0f W;\n',tech_data.parasitic_draw*(no_of_center_taps+no_of_center_taps2));
        fprintf(write_file,'     power_type DC;\n');
        fprintf(write_file,'     generator_status ONLINE;\n');
        fprintf(write_file,'     Energy %.0f;\n',tech_data.battery_energy); 
        fprintf(write_file,'	 scheduled_power battery_schedule*%.0f;\n',tech_data.battery_power);
        fprintf(write_file,'	 power_factor 1.0;\n');
        fprintf(write_file,'}\n\n');

    elseif (use_flags.use_batt == 1) %decentralized
        for jj=1:no_of_center_taps
            parent = center_taps{jj,1};

            fprintf(write_file,'object battery {\n');
            fprintf(write_file,'	 parent %s\n',parent);
            fprintf(write_file,'	 name battery_%.0f;\n',jj);
            fprintf(write_file,'     generator_mode CONSTANT_PQ;\n');
            fprintf(write_file,'     V_Max 260;\n');
            fprintf(write_file,'     I_Max 100;\n');
            fprintf(write_file,'     P_Max %.0f;\n',tech_data.battery_power/no_of_center_taps);
            fprintf(write_file,'     E_Max %.0f;\n',tech_data.battery_energy/no_of_center_taps);
            fprintf(write_file,'     base_efficiency %.2f;\n',tech_data.efficiency);
            fprintf(write_file,'     parasitic_power_draw %.0f W;\n',tech_data.parasitic_draw);
            fprintf(write_file,'     power_type DC;\n');
            fprintf(write_file,'     generator_status ONLINE;\n');
            fprintf(write_file,'     Energy %.0f;\n',tech_data.battery_energy/no_of_center_taps); 
            fprintf(write_file,'	 scheduled_power battery_schedule*%.0f;\n',tech_data.battery_power/no_of_center_taps);
            fprintf(write_file,'	 power_factor 1.0;\n');
            fprintf(write_file,'}\n\n');
        end

        for jj=1:no_of_center_taps2
            parent = center_taps2{jj,1};

            fprintf(write_file,'object battery {\n');
            fprintf(write_file,'	 parent %s\n',parent);
            fprintf(write_file,'	 name battery_%.0f;\n',jj);
            fprintf(write_file,'     generator_mode CONSTANT_PQ;\n');
            fprintf(write_file,'     V_Max 260;\n');
            fprintf(write_file,'     I_Max 100;\n');
            fprintf(write_file,'     P_Max %.0f;\n',tech_data.battery_power/no_of_center_taps2);
            fprintf(write_file,'     E_Max %.0f;\n',tech_data.battery_energy/no_of_center_taps2);
            fprintf(write_file,'     base_efficiency %.2f;\n',tech_data.efficiency);
            fprintf(write_file,'     parasitic_power_draw %.0f W;\n',tech_data.parasitic_draw);
            fprintf(write_file,'     power_type DC;\n');
            fprintf(write_file,'     generator_status ONLINE;\n');
            fprintf(write_file,'     Energy %.0f;\n',tech_data.battery_energy/no_of_center_taps2); 
            fprintf(write_file,'	 scheduled_power battery_schedule*%.0f;\n',tech_data.battery_power/no_of_center_taps2);
            fprintf(write_file,'	 power_factor 1.0;\n');
            fprintf(write_file,'}\n\n');
        end
    end

    % Initialize pseudo-random numbers - put this before each technology where 
    % random numbers are needed, so they are not effected by other changes
    % (s1-s6)
        RandStream.setGlobalStream(s4);
          
    %Populating solar as percentage of feeder peak load
    
    if (use_flags.use_solar~=0  ||use_flags.use_solar_com ~=0)
        
         if (exist('solar_bigbox_array','var') == 0) && (exist('solar_office_array','var') == 0)
             
            penetration_stripmall = regional_data.solar_penetration(region);
            penetration_bigbox = 0;
            penetration_office = 0;
         elseif (exist('solar_bigbox_array','var')) && (exist('solar_office_array','var') == 0)
             
             penetration_stripmall = regional_data.solar_penetration(region)/2;
             penetration_bigbox = regional_data.solar_penetration(region)/2;
             penetration_office = 0;
             
         elseif (exist('solar_bigbox_array','var') == 0) && (exist('solar_office_array','var')) && (exist('solar_stripmall_array','var'))
             
             penetration_stripmall = regional_data.solar_penetration(region)/2;
             penetration_bigbox = 0;
             penetration_office = regional_data.solar_penetration(region)/2;
         
         elseif (exist('solar_office_array', 'var')) && (exist('solar_bigbox_array','var') == 0) && (exist('solar_stripmall_array','var') == 0)
            penetration_stripmall = 0;
            penetration_bigbox = 0;
            penetration_office = regional_data.solar_penetration(region);
         
         else
             penetration_stripmall = regional_data.solar_penetration(region)/3;
             penetration_bigbox = regional_data.solar_penetration(region)/3;
             penetration_office = regional_data.solar_penetration(region)/3;
             
         end
        
        if (exist('solar_office_array','var'))
            total_no_office_length=length(solar_office_array);
            total_no_office=0;
            for solar_office_count_val=1:total_no_office_length
                if (~isempty(solar_office_array{solar_office_count_val}))
                    for small_loop_var=1:length(solar_office_array{solar_office_count_val})
                        if (~isempty(solar_office_array{solar_office_count_val}{small_loop_var}))
                            for small_1_loop_var=1:length(solar_office_array{solar_office_count_val}{small_loop_var})
                                if (~isempty(solar_office_array{solar_office_count_val}{small_loop_var}{small_1_loop_var}))
                                    total_no_office=total_no_office+sum(~cellfun('isempty',solar_office_array{solar_office_count_val}{small_loop_var}{small_1_loop_var}));
                                end
                            end
                        end
                    end
                end
            end
            office_penetration = rand(total_no_office,1);
            office_count=1;
                     
%             
            for jj=1:total_no_office_length
                if (~isempty(solar_office_array{jj}))
                    if (use_flags.use_solar ~= 0 || use_flags.use_solar_com ~= 0 )
                                                                     
                            number_solar_office =  (taxonomy_data.emissions_peak * penetration_office)/(tech_data.solar_averagepower_office);
                       
                    end
                    for jjj=1:length(solar_office_array{jj})
                        
                            for jjjj=1:length(solar_office_array{jj}{jjj})
                                for jjjjj=1:length(solar_office_array{jj}{jjj}{jjjj})
                                    if (~isempty(solar_office_array{jj}{jjj}{jjjj}{jjjjj}))
                                            if  (office_penetration(office_count) < (number_solar_office/(total_no_office)))

                                            parent = solar_office_array_parent{jj}{jjj}{jjjj};   
                                            parent1 = solar_office_array{jj}{jjj}{jjjj}{jjjjj};
                                            phase1 = solar_office_array_phases{jj}{jjj}{jjjj};                                             
                                                                                       
                                            countSOLAR_office = countSOLAR_office + 1;  
                                            fprintf(write_file,'object triplex_meter {\n');
                                            fprintf(write_file,'      phases %sS;\n',phase1);
                                            fprintf(write_file,'      name officeSolar_tm_%s;\n', parent1);
                                            fprintf(write_file,'      parent %s;\n',parent);
                                            fprintf(write_file,'      nominal_voltage 120;\n');
                                            fprintf(write_file,'      groupid Commercial_tm_solar_office;\n\n');
                    
                                                    fprintf(write_file,'      object inverter {\n');
                                                    fprintf(write_file,'            name inv_%s;\n',parent1);
                                                    fprintf(write_file,'            phases %sS;\n',phase1);
                                                    fprintf(write_file,'            generator_mode CONSTANT_PF;\n');
                                                    fprintf(write_file,'            generator_status ONLINE;\n');
                                                    fprintf(write_file,'            inverter_type PWM;\n');
                                                    fprintf(write_file,'            power_factor 1.0;\n\n');
                                               
                                                            fprintf(write_file,'            object solar {\n');                    
                                                            fprintf(write_file,'                  name sol_inv_%s;\n',parent1);
                                                            fprintf(write_file,'                  generator_mode SUPPLY_DRIVEN;\n');
                                                            fprintf(write_file,'                  generator_status ONLINE;\n');
                                                            fprintf(write_file,'                  panel_type SINGLE_CRYSTAL_SILICON;\n');
                                                            fprintf(write_file,'                  efficiency 0.2;\n');
                                                
                                                            floor_area = 5382;
                                                            
                                                    
                                                   fprintf(write_file,'                  area %.0f;\n',floor_area);
                                                   
                                                            %Add the size to the accumulator
                                                            ComSolarAreaOffice=ComSolarAreaOffice+floor_area;

                                                   fprintf(write_file,'            };\n');
                            
                                             fprintf(write_file,'      };\n');
                    
                    fprintf(write_file,'}\n');
                    
                    
                                             end
                                     office_count = office_count + 1;

                                    end
                                end
                            end
                    
                    end
                end
            end
         end
%         
        if (exist('solar_bigbox_array','var'))
            total_no_bigbox_length=length(solar_bigbox_array);
            total_no_bigbox=0;
            for solar_bigbox_count_val=1:total_no_bigbox_length
                if (~isempty(solar_bigbox_array{solar_bigbox_count_val}))
                    for small_loop_var=1:length(solar_bigbox_array{solar_bigbox_count_val})
                        if (~isempty(solar_bigbox_array{solar_bigbox_count_val}{small_loop_var}))
                            for small_1_loop_var=1:length(solar_bigbox_array{solar_bigbox_count_val}{small_loop_var})
                                if (~isempty(solar_bigbox_array{solar_bigbox_count_val}{small_loop_var}{small_1_loop_var}))
                                    total_no_bigbox=total_no_bigbox+sum(~cellfun('isempty',solar_bigbox_array{solar_bigbox_count_val}{small_loop_var}{small_1_loop_var}));
                                end
                            end
                        end
                    end
                end
            end
            bigbox_penetration = rand(total_no_bigbox,1);
            bigbox_count=1;

            for jj=1:total_no_bigbox_length
                if (~isempty(solar_bigbox_array{jj}))
                    if (use_flags.use_solar ~= 0 || use_flags.use_solar_com ~= 0)
                    number_solar_bigbox =  (taxonomy_data.emissions_peak * penetration_bigbox)/(tech_data.solar_averagepower_bigbox);
                    end
                    for jjj=1:length(solar_bigbox_array{jj})
                        
                            for jjjj=1:length(solar_bigbox_array{jj}{jjj})
                                for jjjjj=1:length(solar_bigbox_array{jj}{jjj}{jjjj})
                                    if (~isempty(solar_bigbox_array{jj}{jjj}{jjjj}{jjjjj}))
                                            if  (bigbox_penetration(bigbox_count) < (number_solar_bigbox/(total_no_bigbox)))

                                            parent = solar_bigbox_array_parent{jj}{jjj}{jjjj};   
                                            parent1 = solar_bigbox_array{jj}{jjj}{jjjj}{jjjjj}; 
                                            phase1 = solar_bigbox_array_phases{jj}{jjj}{jjjj}; 
                                            
                                            countSOLAR_bigbox = countSOLAR_bigbox + 1;   
                                            fprintf(write_file,'object triplex_meter {\n');
                                            fprintf(write_file,'      phases %sS;\n',phase1);
                                            fprintf(write_file,'      name bigboxSolar_tm_%s;\n', parent1);
                                            fprintf(write_file,'      parent %s;\n',parent);
                                            fprintf(write_file,'      nominal_voltage 120;\n');
                                            fprintf(write_file,'      groupid Commercial_tm_solar_bigbox;\n\n');
                    
                                                    fprintf(write_file,'      object inverter {\n');
                                                    fprintf(write_file,'            name inv_%s;\n',parent1);
                                                    fprintf(write_file,'            phases %sS;\n',phase1);
                                                    fprintf(write_file,'            generator_mode CONSTANT_PF;\n');
                                                    fprintf(write_file,'            generator_status ONLINE;\n');
                                                    fprintf(write_file,'            inverter_type PWM;\n');
                                                    fprintf(write_file,'            power_factor 1.0;\n\n');
                                               
                                                            fprintf(write_file,'            object solar {\n');                    
                                                            fprintf(write_file,'                  name sol_inv_%s;\n',parent1);
                                                            fprintf(write_file,'                  generator_mode SUPPLY_DRIVEN;\n');
                                                            fprintf(write_file,'                  generator_status ONLINE;\n');
                                                            fprintf(write_file,'                  panel_type SINGLE_CRYSTAL_SILICON;\n');
                                                            fprintf(write_file,'                  efficiency 0.2;\n');
                                                
                                                            floor_area = 5382;
                                                            
                                                    
                                                fprintf(write_file,'                  area %.0f;\n',floor_area);
                                                %fprintf(write_file,'      groupid Residential_Meter_Solar;\n\n');
                                                
                                                            %Add the size to the accumulator
                                                            ComSolarAreaBigBox=ComSolarAreaBigBox+floor_area;
                    
                                                    fprintf(write_file,'            };\n');
                            
                                             fprintf(write_file,'      };\n');
                    
                    fprintf(write_file,'}\n');
                    
                                             end
                                     bigbox_count = bigbox_count + 1;

                                    end
                                end
                            end
                    end
                end
            end
        end
% 
        if (exist('solar_stripmall_array','var'))
            total_no_stripmall_length=length(solar_stripmall_array);
            total_no_stripmall=0;
            for solar_strip_count_val=1:total_no_stripmall_length
                if (~isempty(solar_stripmall_array{solar_strip_count_val}))
                    for small_loop_var=1:length(solar_stripmall_array{solar_strip_count_val})
                        if (~isempty(solar_stripmall_array{solar_strip_count_val}{small_loop_var}))
                            total_no_stripmall=total_no_stripmall+sum(~cellfun('isempty',solar_stripmall_array{solar_strip_count_val}{small_loop_var}));
                        end
                    end
                end
            end
            stripmall_penetration = rand(total_no_stripmall,1);
            stripmall_count=1;
            
            for jj=1:total_no_stripmall_length
                    if (~isempty(solar_stripmall_array{jj}))
                   
                    if (use_flags.use_solar ~= 0 ||use_flags.use_solar_com ~= 0)
                    number_solar_stripmall =  (taxonomy_data.emissions_peak * penetration_stripmall)/(tech_data.solar_averagepower_stripmall);
                    end
                                        
                        for jjj=1:length(solar_stripmall_array{jj})
                            for jjjj=1:length(solar_stripmall_array{jj}{jjj})
                                if (~isempty(solar_stripmall_array{jj}{jjj}{jjjj}))
                                    if  (stripmall_penetration(stripmall_count) < (number_solar_stripmall/(total_no_stripmall)))
                                    
                                    parent = solar_stripmall_array_parent{jj}{jjj}{jjjj};
                                    parent1 = solar_stripmall_array{jj}{jjj}{jjjj};
                                    phase1 = solar_stripmall_array_phases{jj}{jjj}{jjjj}; 
                                   
                                countSOLAR_stripmall = countSOLAR_stripmall + 1;   
                                fprintf(write_file,'object triplex_meter {\n');
                                fprintf(write_file,'      phases %sS;\n',phase1);
                                fprintf(write_file,'      name stripmallSolar_tm_%s;\n', parent1);
                                fprintf(write_file,'      parent %s;\n',parent);
                                fprintf(write_file,'      nominal_voltage 120;\n');
                                fprintf(write_file,'      groupid Commercial_tm_solar_stripmall;\n\n');
                    
                                        fprintf(write_file,'      object inverter {\n');
                                        fprintf(write_file,'            name inv_%s;\n',parent1);
                                        fprintf(write_file,'            phases %sS;\n',phase1);
                                        fprintf(write_file,'            generator_mode CONSTANT_PF;\n');
                                        fprintf(write_file,'            generator_status ONLINE;\n');
                                        fprintf(write_file,'            inverter_type PWM;\n');
                                        fprintf(write_file,'            power_factor 1.0;\n\n');
                                               
                                                fprintf(write_file,'            object solar {\n');                    
                                                fprintf(write_file,'                  name sol_inv_%s;\n',parent1);
                                                fprintf(write_file,'                  generator_mode SUPPLY_DRIVEN;\n');
                                                fprintf(write_file,'                  generator_status ONLINE;\n');
                                                fprintf(write_file,'                  panel_type SINGLE_CRYSTAL_SILICON;\n');
                                                fprintf(write_file,'                  efficiency 0.2;\n');
                                                

                                                    floor_area = 538;

                                                    
                                                fprintf(write_file,'                  area %.0f;\n',floor_area);
                                                
                                                %Add the size to the accumulator
                                                ComSolarAreaStripMall=ComSolarAreaStripMall+floor_area;

                                                fprintf(write_file,'            };\n');
                            
                                             fprintf(write_file,'      };\n');
                    
                                 fprintf(write_file,'}\n');
                    
                                    end
                                     stripmall_count = stripmall_count + 1;
                                end
                            end
                        end
                    end                  
             end
        end
    end

      %populating solar residential houses 
      
    if (use_flags.use_solar ~=0 || use_flags.use_solar_res ~=0)
         if (exist('solar_residential_array','var'))
            total_no_residential_length=length(solar_residential_array);
            total_no_residential=sum(cellfun('prodofsize',solar_residential_array));
            residential_penetration = rand(total_no_residential,1);
          
           residential_count=1;
            
            for jj=1:total_no_residential_length
                
                if (~isempty(solar_residential_array{jj}))            
                                  
                    if (use_flags.use_solar ~= 0 ||use_flags.use_solar_res ~= 0)
                    number_solar_house =  (taxonomy_data.emissions_peak * regional_data.solar_penetration(region))/(tech_data.solar_averagepower);
                    end
                                                                                  
                    for jjj=1:length(solar_residential_array{jj})
                        
                        if (~isempty(solar_residential_array{jj}{jjj}))
                            
                            if  (residential_penetration(residential_count) < (number_solar_house/total_no_residential))
                                
                                parent = solar_residential_array_parent{jj}{jjj};  
                                  parent1 = solar_residential_array{jj}{jjj}; 
                                  phase1 = solar_residential_array_phase{jj}{jjj}; 
                                countSOLAR = countSOLAR + 1;   
                                fprintf(write_file,'object triplex_meter {\n');
                                fprintf(write_file,'      phases %s\n',phase1);
                                fprintf(write_file,'      name resSolar_tm_%s\n', parent1);
                                fprintf(write_file,'      parent %s\n',parent);
                                fprintf(write_file,'      nominal_voltage 120;\n');
                                fprintf(write_file,'      groupid Residential_tm_solar;\n\n');
                    
                                        fprintf(write_file,'      object inverter {\n');
                                        fprintf(write_file,'           name inv_%s\n',parent1);
                                        fprintf(write_file,'           phases %s\n',phase1);
                                        fprintf(write_file,'           generator_mode CONSTANT_PF;\n');
                                        fprintf(write_file,'           generator_status ONLINE;\n');
                                        fprintf(write_file,'           inverter_type PWM;\n');
                                        fprintf(write_file,'           power_factor 1.0;\n\n');
                                               
                                                fprintf(write_file,'           object solar {\n');                    
                                                fprintf(write_file,'                 name sol_inv_%s\n',parent1);
                                                fprintf(write_file,'                 generator_mode SUPPLY_DRIVEN;\n');
                                                fprintf(write_file,'                 generator_status ONLINE;\n');
                                                fprintf(write_file,'                 panel_type SINGLE_CRYSTAL_SILICON;\n');
                                                fprintf(write_file,'                 efficiency 0.2;\n');
                                                
                                                floor_area = solar_residential_array_fa{jj}{jjj};
                                                                                                
                                                if ((0.1*floor_area > 162) && (0.1*floor_area < 270))
                                                    floor_area = 0.1*floor_area;
                                                elseif  0.1*floor_area < 162
                                                    floor_area = 162;
                                                else
                                                    floor_area = 270;
                                                end
                                                    
                                                fprintf(write_file,'                 area %.0f;\n',floor_area);
                                                
                                                %Add the size to the accumulator
                                                ResSolarArea=ResSolarArea+floor_area;

                                                fprintf(write_file,'          };\n');
                            
                                             fprintf(write_file,'     };\n');
                    
                    fprintf(write_file,'}\n\n');
                    
                            end
                            residential_count = residential_count + 1;
                    
                


                        end
                    end             
                end
            end
        end
    end
       
    % Initialize pseudo-random numbers - put this before each technology where 
    % random numbers are needed, so they are not effected by other changes
    % (s1-s6)
    RandStream.setGlobalStream(s5);

    if (use_flags.use_ts~=0)
        
        if (exist('ts_office_array','var'))
            no_ts_office_length=length(ts_office_array);
            no_ts_office=sum(cellfun('prodofsize',ts_office_array));
            office_penetration = rand(no_ts_office,1);
            office_count=1;
            
            for jj=1:no_ts_office_length
                if (~isempty(ts_office_array{jj}))
                    for jjj=1:length(ts_office_array{jj})
                        if (isfield(taxonomy_data,'thermal_override'))
                            thermal_storage_penetration_level=taxonomy_data.thermal_override/100;
                        else %No exist, use regional value
                            thermal_storage_penetration_level = regional_data.ts_penetration/100;
                        end
                        
                        if (office_penetration(office_count) <= thermal_storage_penetration_level)
                            for jjjj=1:length(ts_office_array{jj}{jjj})
                                for jjjjj=1:length(ts_office_array{jj}{jjj}{jjjj})
                                    if (~isempty(ts_office_array{jj}{jjj}{jjjj}{jjjjj}))
                                        parent = ts_office_array{jj}{jjj}{jjjj}{jjjjj};
                                        fprintf(write_file,'object thermal_storage {\n');
                                        fprintf(write_file,'	 parent %s;\n',parent);
                                        fprintf(write_file,'	 name thermal_storage_office_%.0f_%.0f_%.0f_%.0f;\n',jj,jjj,jjjj,jjjjj);
                                        fprintf(write_file,'	 SOC %0.2f;\n', tech_data.ts_SOC);
                                        fprintf(write_file,'	 k %.2f;\n', tech_data.k_ts);
                                        if ((use_flags.use_ts==2) || (use_flags.use_ts==4))
                                            fprintf(write_file,'     discharge_schedule_type EXTERNAL;\n');
                                            fprintf(write_file,'     recharge_schedule_type EXTERNAL;\n');
                                            fprintf(write_file,'	 schedule_skew %.0f; \n', 900*(9*rand(1)-4));
                                            fprintf(write_file,'	 recharge_time ts_recharge_schedule*1;\n');
                                            fprintf(write_file,'	 discharge_time ts_discharge_schedule*1;\n');
                                        end
                                        fprintf(write_file,'}\n\n');
                                    end
                                end
                            end
                        end
                    office_count = office_count + 1;
                    end
                end
            end
        end
        
        if (exist('ts_bigbox_array','var'))
            no_ts_bigbox_length=length(ts_bigbox_array);
            no_ts_bigbox=sum(~cellfun('isempty',ts_bigbox_array));
            bigbox_penetration = rand(no_ts_bigbox,1);
            bigbox_count=1;

            for jj=1:no_ts_bigbox_length
                if (~isempty(ts_bigbox_array{jj}))
                    if (isfield(taxonomy_data,'thermal_override'))
                        thermal_storage_penetration_level=taxonomy_data.thermal_override/100;
                    else %No exist, use regional value
                        thermal_storage_penetration_level = regional_data.ts_penetration/100;
                    end
                    
                    if (bigbox_penetration(bigbox_count) <= thermal_storage_penetration_level)
                        for jjj=1:length(ts_bigbox_array{jj})
                            for jjjj=1:length(ts_bigbox_array{jj}{jjj})
                                for jjjjj=1:length(ts_bigbox_array{jj}{jjj}{jjjj})
                                    if (~isempty(ts_bigbox_array{jj}{jjj}{jjjj}{jjjjj}))
                                        parent = ts_bigbox_array{jj}{jjj}{jjjj}{jjjjj};
                                        fprintf(write_file,'object thermal_storage {\n');
                                        fprintf(write_file,'	 parent %s;\n',parent);
                                        fprintf(write_file,'	 name thermal_storage_bigbox_%.0f_%.0f_%.0f_%.0f;\n',jj,jjj,jjjj,jjjjj);
                                        fprintf(write_file,'	 SOC %0.2f;\n', tech_data.ts_SOC);
                                        fprintf(write_file,'	 k %.2f;\n', tech_data.k_ts);
                                        if ((use_flags.use_ts==2) || (use_flags.use_ts==4))
                                            fprintf(write_file,'     discharge_schedule_type EXTERNAL;\n');
                                            fprintf(write_file,'     recharge_schedule_type EXTERNAL;\n');
                                            fprintf(write_file,'	 schedule_skew %.0f; \n', 900*(9*rand(1)-4));
                                            fprintf(write_file,'	 recharge_time ts_recharge_schedule*1;\n');
                                            fprintf(write_file,'	 discharge_time ts_discharge_schedule*1;\n');
                                        end
                                        fprintf(write_file,'}\n\n');
                                    end
                                end
                            end
                        end
                    end
                    bigbox_count = bigbox_count + 1;
                end
            end
        end

        if (exist('ts_stripmall_array','var'))
            no_ts_stripmall_length=length(ts_stripmall_array);
            no_ts_stripmall=sum(~cellfun('isempty',ts_stripmall_array));
            stripmall_penetration = rand(no_ts_stripmall,1);
            stripmall_count=1;
            
            for jj=1:no_ts_stripmall_length
                if (~isempty(ts_stripmall_array{jj}))
                    if (isfield(taxonomy_data,'thermal_override'))
                        thermal_storage_penetration_level=taxonomy_data.thermal_override/100;
                    else %No exist, use regional value
                        thermal_storage_penetration_level = regional_data.ts_penetration/100;
                    end

                    if (stripmall_penetration(stripmall_count) <= thermal_storage_penetration_level)
                        for jjj=1:length(ts_stripmall_array{jj})
                            for jjjj=1:length(ts_stripmall_array{jj}{jjj})
                                if (~isempty(ts_stripmall_array{jj}{jjj}{jjjj}))
                                    parent = ts_stripmall_array{jj}{jjj}{jjjj};
                                    fprintf(write_file,'object thermal_storage {\n');
                                    fprintf(write_file,'	 parent %s;\n',parent);
                                    fprintf(write_file,'	 name thermal_storage_stripmall_%.0f_%.0f_%.0f;\n',jj,jjj,jjjj);
                                    fprintf(write_file,'	 SOC %0.2f;\n', tech_data.ts_SOC);
                                    fprintf(write_file,'	 k %.2f;\n', tech_data.k_ts);
                                    if ((use_flags.use_ts==2) || (use_flags.use_ts==4))
                                        fprintf(write_file,'     discharge_schedule_type EXTERNAL;\n');
                                        fprintf(write_file,'     recharge_schedule_type EXTERNAL;\n');
                                        fprintf(write_file,'	 schedule_skew %.0f; \n', 900*(9*rand(1)-4));
                                        fprintf(write_file,'	 recharge_time ts_recharge_schedule*1;\n');
                                        fprintf(write_file,'	 discharge_time ts_discharge_schedule*1;\n');
                                    end
                                    fprintf(write_file,'}\n\n');
                                end
                            end
                        end
                    end
                    stripmall_count = stripmall_count + 1;
                end
            end
        end
        
        if (exist('ts_residential_array','var') && ((use_flags.use_ts==3) || (use_flags.use_ts==4)))
            no_ts_residential_length=length(ts_residential_array);
            no_ts_residential=sum(cellfun('prodofsize',ts_residential_array));
            residential_penetration = rand(no_ts_residential,1);
            residential_count=1;

            for jj=1:no_ts_residential_length
                if (~isempty(ts_residential_array{jj}))
                    for jjj=1:length(ts_residential_array{jj})
                        if (~isempty(ts_residential_array{jj}{jjj}))
                            if (isfield(taxonomy_data,'thermal_override'))
                                thermal_storage_penetration_level=taxonomy_data.thermal_override/100;
                            else %No exist, use regional value
                                thermal_storage_penetration_level = regional_data.ts_penetration/100;
                            end
                            
                            if (residential_penetration(residential_count) <= thermal_storage_penetration_level)
                                parent = ts_residential_array{jj}{jjj};
                                fprintf(write_file,'object thermal_storage {\n');
                                fprintf(write_file,'	 parent %s;\n',parent);
                                fprintf(write_file,'	 name thermal_storage_residential_%.0f_%.0f;\n',jj,jjj);
                                fprintf(write_file,'	 SOC %0.2f;\n', tech_data.ts_SOC);
                                fprintf(write_file,'	 k %.2f;\n', tech_data.k_ts);
                                if ((use_flags.use_ts==2) || (use_flags.use_ts==4))
                                    fprintf(write_file,'     discharge_schedule_type EXTERNAL;\n');
                                    fprintf(write_file,'     recharge_schedule_type EXTERNAL;\n');
                                    fprintf(write_file,'	 schedule_skew %.0f; \n', 900*(9*rand(1)-4));
                                    fprintf(write_file,'	 recharge_time ts_recharge_schedule*1;\n');
                                    fprintf(write_file,'	 discharge_time ts_discharge_schedule*1;\n');
                                end
                                fprintf(write_file,'}\n\n');
                            end
                            residential_count = residential_count + 1;
                        end
                    end
                end
            end
        end
    end
    % Initialize pseudo-random numbers - put this before each technology where 
    % random numbers are needed, so they are not effected by other changes
    % (s1-s6)
    RandStream.setGlobalStream(s6);
    
    if(use_flags.use_phev == 1)
        if(exist('phev_residential_array', 'var'))
            no_phev_residential_length = length(phev_residential_array);
            no_phev_residential=sum(cellfun('prodofsize',phev_residential_array));
            phev_residential_penetration = rand(no_phev_residential,1);
            phev_vehicle_index_array = randi(tech_data.phev_index, [no_phev_residential, 1]);
            no_phev = ceil(taxonomy_data.emissions_peak * regional_data.phev_penetration(region) * tech_data.phev_charging_efficiency * 1000 / tech_data.phev_maximum_charge_rate);
            res_count = 1;

            for jj=1:no_phev_residential_length
                if(~isempty(phev_residential_array{jj}))
                    for jjj=1:length(phev_residential_array{jj})
                        if(~isempty(phev_residential_array{jj}{jjj}))
                            if(phev_residential_penetration(res_count) <= (no_phev / no_phev_residential))
                                parent = phev_residential_array{jj}{jjj};
                                fprintf(write_file, 'object evcharger_det {\n');
                                fprintf(write_file, '     name ev_%s\n', parent);
                                fprintf(write_file, '     parent %s\n', parent);
                                fprintf(write_file, '     data_file PHEV_schedules.csv;\n');
                                fprintf(write_file, '     vehicle_index %d;\n', phev_vehicle_index_array(res_count));
                                fprintf(write_file, '     charging_efficiency %.6f;\n', tech_data.phev_charging_efficiency);
                                fprintf(write_file, '     mileage_classification %.6f;\n', tech_data.phev_mileage_classification);
                                fprintf(write_file, '     mileage_efficiency %.6f;\n', tech_data.phev_mileage_efficiency);
                                fprintf(write_file, '     maximum_charge_rate %.6f;\n', tech_data.phev_maximum_charge_rate);
                                fprintf(write_file, '     work_charging_available %s;\n', tech_data.phev_work_charging_available);
                                fprintf(write_file, '}\n\n');
                                countPHEV = countPHEV + 1;
                            end
                            res_count = res_count + 1;
                        end
                    end
                end
            end
        end
    end
    if (use_flags.use_wind == 1)
        disp('Adding Wind Generator')
        % TODO: pull all of these out and put into tech parameters
        total_wind = total_wind + ceil((taxonomy_data.emissions_peak * regional_data.wind_penetration(region))/(tech_data.wind_unit_rated_power));
        
        fprintf(write_file, 'object meter { \n');    
        fprintf(write_file, 'parent GC-12-47-1_node_16;\n');
        fprintf(write_file, 'name GC-12-47-1_meter_16;\n');     
        fprintf(write_file, 'phases ABCN;\n');     
        fprintf(write_file, 'nominal_voltage 7200;\n');     
        fprintf(write_file, 'voltage_A 7200+0.0j; \n');    
        fprintf(write_file, 'voltage_B -3600-6235j;\n');     
        fprintf(write_file, 'voltage_C -3600+6235j;\n'); 
        fprintf(write_file, '} \n');

        fprintf(write_file,'object windturb_dg { \n');
        fprintf(write_file,'parent GC-12-47-1_meter_16;\n');
        fprintf(write_file,'name GC-12-47-1_node_16_wdg; \n');
        fprintf(write_file,'phases "ABCN"; \n');
        fprintf(write_file,'Gen_status ONLINE;\n');
        fprintf(write_file,'Gen_type SYNCHRONOUS; \n');
        fprintf(write_file,'Gen_mode CONSTANTP; \n');
        fprintf(write_file,'Turbine_Model VESTAS_V82;\n');
        fprintf(write_file,'     object recorder { \n');
        fprintf(write_file,'     file %s_wind_power.csv;\n',tech_file);
        fprintf(write_file,'     interval 900; \n');
        fprintf(write_file,'     property TotalRealPow; \n');
        fprintf(write_file,'     }; \n');
        fprintf(write_file,'  } \n');
    end
    % Initialize pseudo-random numbers - put this before each technology where 
    % random numbers are needed, so they are not effected by other changes
    % (s1-s6)
    RandStream.setGlobalStream(s7);
    
    % calculate total installed capacity
    total_es_batteries_office = 0;
    total_es_batteries_bigbox = 0;
    total_es_batteries_stripmall = 0;
    total_es_batteries_com = 0;
    total_es_batteries_res = 0;
    
    if (use_flags.use_energy_storage ~=0  || use_flags.use_energy_storage_com ~=0 || use_flags.use_energy_storage_res ~= 0)
        if (exist('es_bigbox_array','var') == 0) && (exist('es_office_array','var') == 0)
            penetration_stripmall = regional_data.es_penetration(region);
            penetration_bigbox = 0;
            penetration_office = 0;
        elseif (exist('es_bigbox_array','var')) && (exist('es_office_array','var') == 0)
            penetration_stripmall = regional_data.es_penetration(region)/2;
            penetration_bigbox = regional_data.es_penetration(region)/2;
            penetration_office = 0;
        elseif (exist('es_bigbox_array','var') == 0) && (exist('es_office_array','var')) && (exist('es_stripmall_array','var'))
            penetration_stripmall = regional_data.es_penetration(region)/2;
            penetration_bigbox = 0;
            penetration_office = regional_data.es_penetration(region)/2;
        elseif (exist('es_office_array', 'var')) && (exist('es_bigbox_array','var') == 0) && (exist('es_stripmall_array','var') == 0)
            penetration_stripmall = 0;
            penetration_bigbox = 0;
            penetration_office = regional_data.es_penetration(region);
        else
            penetration_stripmall = regional_data.es_penetration(region)/3;
            penetration_bigbox = regional_data.es_penetration(region)/3;
            penetration_office = regional_data.es_penetration(region)/3;
        end
        total_es_batteries_office = ceil((taxonomy_data.emissions_peak * penetration_office)/(tech_data.es_com_unit_rated_power));
        total_es_batteries_bigbox = ceil((taxonomy_data.emissions_peak * penetration_bigbox)/(tech_data.es_com_unit_rated_power));
        total_es_batteries_stripmall = ceil((taxonomy_data.emissions_peak * penetration_stripmall)/(tech_data.es_com_unit_rated_power));
        total_es_batteries_com = total_es_batteries_office + total_es_batteries_bigbox + total_es_batteries_stripmall;
        
        if (use_flags.use_energy_storage ~=0  || use_flags.use_energy_storage_res ~=0)
            total_es_batteries_res = total_es_batteries_res + ceil((taxonomy_data.emissions_peak * regional_data.es_penetration(region))/(tech_data.es_res_unit_rated_power));
        end

        total_no_office=0;
        if(exist('es_office_array','var'))
            total_no_office_length=length(es_office_array);
            for es_office_count_val=1:total_no_office_length
                if (~isempty(es_office_array{es_office_count_val}))
                    for small_loop_var=1:length(es_office_array{es_office_count_val})
                        if (~isempty(es_office_array{es_office_count_val}{small_loop_var}))
                            for small_1_loop_var=1:length(es_office_array{es_office_count_val}{small_loop_var})
                                if (~isempty(es_office_array{es_office_count_val}{small_loop_var}{small_1_loop_var}))
                                    total_no_office=total_no_office+sum(~cellfun('isempty',es_office_array{es_office_count_val}{small_loop_var}{small_1_loop_var}));
                                end
                            end
                        end
                    end
                end
            end
        end
        total_no_bigbox=0;
        if (exist('es_bigbox_array','var'))
            total_no_bigbox_length=length(es_bigbox_array);
            for es_bigbox_count_val=1:total_no_bigbox_length
                if (~isempty(es_bigbox_array{es_bigbox_count_val}))
                    for small_loop_var=1:length(es_bigbox_array{es_bigbox_count_val})
                        if (~isempty(es_bigbox_array{es_bigbox_count_val}{small_loop_var}))
                            for small_1_loop_var=1:length(es_bigbox_array{es_bigbox_count_val}{small_loop_var})
                                if (~isempty(es_bigbox_array{es_bigbox_count_val}{small_loop_var}{small_1_loop_var}))
                                    total_no_bigbox=total_no_bigbox+sum(~cellfun('isempty',es_bigbox_array{es_bigbox_count_val}{small_loop_var}{small_1_loop_var}));
                                end
                            end
                        end
                    end
                end
            end
        end
        total_no_stripmall=0;
        if (exist('es_stripmall_array','var'))
            total_no_stripmall_length=length(es_stripmall_array);
            for es_strip_count_val=1:total_no_stripmall_length
                if (~isempty(es_stripmall_array{es_strip_count_val}))
                    for small_loop_var=1:length(es_stripmall_array{es_strip_count_val})
                        if (~isempty(es_stripmall_array{es_strip_count_val}{small_loop_var}))
                            total_no_stripmall=total_no_stripmall+sum(~cellfun('isempty',es_stripmall_array{es_strip_count_val}{small_loop_var}));
                        end
                    end
                end
            end
        end
        if (total_es_batteries_com > (total_no_stripmall + total_no_bigbox + total_no_office))
            total_es_batteries_com = total_no_stripmall + total_no_bigbox + total_no_office;
        end
        total_no_residential = 0;
        if (exist('es_residential_array','var'))
            total_no_residential_length=length(es_residential_array);
            total_no_residential=sum(cellfun('prodofsize',es_residential_array));
        end
        if (total_es_batteries_res > total_no_residential)
            total_es_batteries_res = total_no_residential;
        end
        total_es_power = (total_es_batteries_com * tech_data.es_com_unit_rated_power) + (total_es_batteries_res * tech_data.es_res_unit_rated_power);
    end

    % populating energy storage as a percentage of feeder peak
    
    if (use_flags.use_energy_storage ~=0  || use_flags.use_energy_storage_com ~=0)      
        if (exist('es_office_array','var'))
            office_penetration = rand(total_no_office,1);
            off_cnt = 0;
            for off_ind=1:total_no_office
                if (office_penetration(off_ind) <= (total_es_batteries_office/(total_no_office)))
                    off_cnt = off_cnt + 1;
                end
            end
            if (off_cnt < total_es_batteries_office)
                off_diff = total_es_batteries_office - off_cnt;
                for off_ind=1:total_no_office
                    if (office_penetration(off_ind) > (total_es_batteries_office/(total_no_office)) && off_diff > 0)
                        office_penetration(off_ind) = (total_es_batteries_office/(total_no_office));
                        off_diff = off_diff - 1;
                    end
                end
            elseif (off_cnt > total_es_batteries_office)
                off_diff = off_cnt - total_es_batteries_office;
                for off_ind=1:total_no_office
                    if (office_penetration(off_ind) <= (total_es_batteries_office/(total_no_office)) && off_diff > 0)
                        office_penetration(off_ind) = (total_es_batteries_office/(total_no_office)) + 0.1;
                        off_diff = off_diff - 1;
                    end
                end
            end
            office_count=1;
            
            for jj=1:total_no_office_length
                if (~isempty(es_office_array{jj}))
                    for jjj=1:length(es_office_array{jj})
                        for jjjj=1:length(es_office_array{jj}{jjj})
                            for jjjjj=1:length(es_office_array{jj}{jjj}{jjjj})
                                if (~isempty(es_office_array{jj}{jjj}{jjjj}{jjjjj}))
                                    if (office_penetration(office_count) <= (total_es_batteries_office/(total_no_office)))
                                        parent = es_office_array_parent{jj}{jjj}{jjjj};   
                                        parent1 = es_office_array{jj}{jjj}{jjjj}{jjjjj};
                                        phase1 = es_office_array_phases{jj}{jjj}{jjjj};                                             
                                        countES_office = countES_office + 1;  
                                        fprintf(write_file,'object triplex_meter {\n');
                                        fprintf(write_file,'      phases %sS;\n',phase1);
                                        fprintf(write_file,'      name officeES_tm_%s;\n', parent1);
                                        fprintf(write_file,'      parent %s;\n',parent);
                                        fprintf(write_file,'      nominal_voltage 120;\n');
                                        fprintf(write_file,'      groupid Commercial_tm_es_office;\n');
                                        fprintf(write_file,'      object inverter {\n');
                                        fprintf(write_file,'            name batt_inv_%s;\n',parent1);
                                        fprintf(write_file,'            phases %sS;\n',phase1);
                                        fprintf(write_file,'            generator_mode CONSTANT_PQ;\n');
                                        fprintf(write_file,'            generator_status ONLINE;\n');
                                        fprintf(write_file,'            inverter_type FOUR_QUADRANT;\n');
                                        fprintf(write_file,'            four_quadrant_control_mode GROUP_LOAD_FOLLOWING;\n');
                                        fprintf(write_file,'            sense_object substation_transformer;\n');
                                        fprintf(write_file,'            max_charge_rate %.0f kW;\n', tech_data.es_com_unit_rated_power);
                                        fprintf(write_file,'            max_discharge_rate %.0f kW;\n', tech_data.es_com_unit_rated_power);
                                        fprintf(write_file,'            rated_power %.0f kW;\n', tech_data.es_com_unit_rated_power);
                                        fprintf(write_file,'            group_max_charge_rate %.0f kW;\n', total_es_power);
                                        fprintf(write_file,'            group_max_discharge_rate %.0f kW;\n', total_es_power);
                                        fprintf(write_file,'            group_rated_power %.0f kW;\n', total_es_power);
                                        fprintf(write_file,'            charge_threshold %.0f kW;\n', (taxonomy_data.emissions_peak*tech_data.es_charge_setting));
                                        fprintf(write_file,'            discharge_threshold %.0f kW;\n', (taxonomy_data.emissions_peak*tech_data.es_discharge_setting));
                                        fprintf(write_file,'            inverter_efficiency %.1f;\n', (tech_data.es_inv_efficiency));
                                        fprintf(write_file,'            charge_lockout_time 60;\n');
                                        fprintf(write_file,'            discharge_lockout_time 60;\n');
                                        fprintf(write_file,'            object battery {\n');                    
                                        fprintf(write_file,'                  name es_batt_%s;\n',parent1);
                                        fprintf(write_file,'                  generator_mode SUPPLY_DRIVEN;\n');
                                        fprintf(write_file,'                  generator_status ONLINE;\n');
                                        fprintf(write_file,'                  use_internal_battery_model TRUE;\n');
                                        fprintf(write_file,'                  battery_type LI_ION;\n');
                                        fprintf(write_file,'                  round_trip_efficiency %.2f;\n', tech_data.es_battery_efficiency);
                                        fprintf(write_file,'                  battery_capacity %.2f kWh;\n', tech_data.es_battery_capacity_com);
                                        fprintf(write_file,'            };\n');
                                        fprintf(write_file,'      };\n');
                                        fprintf(write_file,'}\n');
                                    end
                                    office_count = office_count + 1;
                                end
                            end
                        end
                    end
                end
            end
        end

        if (exist('es_bigbox_array','var'))
            bigbox_penetration = rand(total_no_bigbox,1);
            off_cnt = 0;
            for off_ind=1:total_no_bigbox
                if (bigbox_penetration(off_ind) <= (total_es_batteries_bigbox/(total_no_bigbox)))
                    off_cnt = off_cnt + 1;
                end
            end
            if (off_cnt < total_es_batteries_bigbox)
                off_diff = total_es_batteries_bigbox - off_cnt;
                for off_ind=1:total_no_bigbox
                    if (bigbox_penetration(off_ind) > (total_es_batteries_bigbox/(total_no_bigbox)) && off_diff > 0)
                        bigbox_penetration(off_ind) = (total_es_batteries_bigbox/(total_no_bigbox));
                        off_diff = off_diff - 1;
                    end
                end
            elseif (off_cnt > total_es_batteries_bigbox)
                off_diff = off_cnt - total_es_batteries_bigbox;
                for off_ind=1:total_no_bigbox
                    if (bigbox_penetration(off_ind) <= (total_es_batteries_bigbox/(total_no_bigbox)) && off_diff > 0)
                        bigbox_penetration(off_ind) = (total_es_batteries_bigbox/(total_no_bigbox)) + 0.1;
                        off_diff = off_diff - 1;
                    end
                end
            end
            bigbox_count=1;

            for jj=1:total_no_bigbox_length
                if (~isempty(es_bigbox_array{jj}))
                    for jjj=1:length(es_bigbox_array{jj})
                        for jjjj=1:length(es_bigbox_array{jj}{jjj})
                            for jjjjj=1:length(es_bigbox_array{jj}{jjj}{jjjj})
                                if (~isempty(es_bigbox_array{jj}{jjj}{jjjj}{jjjjj}))
                                    if (bigbox_penetration(bigbox_count) < (total_es_batteries_bigbox/(total_no_bigbox)))
                                        parent = es_bigbox_array_parent{jj}{jjj}{jjjj};   
                                        parent1 = es_bigbox_array{jj}{jjj}{jjjj}{jjjjj}; 
                                        phase1 = es_bigbox_array_phases{jj}{jjj}{jjjj}; 
                                        countES_bigbox = countES_bigbox + 1;   
                                        fprintf(write_file,'object triplex_meter {\n');
                                        fprintf(write_file,'      phases %sS;\n',phase1);
                                        fprintf(write_file,'      name bigboxES_tm_%s;\n', parent1);
                                        fprintf(write_file,'      parent %s;\n',parent);
                                        fprintf(write_file,'      nominal_voltage 120;\n');
                                        fprintf(write_file,'      groupid Commercial_tm_es_bigbox;\n');
                                        fprintf(write_file,'      object inverter {\n');
                                        fprintf(write_file,'            name batt_inv_%s;\n',parent1);
                                        fprintf(write_file,'            phases %sS;\n',phase1);
                                        fprintf(write_file,'            generator_mode CONSTANT_PQ;\n');
                                        fprintf(write_file,'            generator_status ONLINE;\n');
                                        fprintf(write_file,'            inverter_type FOUR_QUADRANT;\n');
                                        fprintf(write_file,'            four_quadrant_control_mode GROUP_LOAD_FOLLOWING;\n');
                                        fprintf(write_file,'            sense_object substation_transformer;\n');
                                        fprintf(write_file,'            max_charge_rate %.0f kW;\n', tech_data.es_com_unit_rated_power);
                                        fprintf(write_file,'            max_discharge_rate %.0f kW;\n', tech_data.es_com_unit_rated_power);
                                        fprintf(write_file,'            rated_power %.0f kW;\n', tech_data.es_com_unit_rated_power);
                                        fprintf(write_file,'            group_max_charge_rate %.0f kW;\n', total_es_power);
                                        fprintf(write_file,'            group_max_discharge_rate %.0f kW;\n', total_es_power);
                                        fprintf(write_file,'            group_rated_power %.0f kW;\n', total_es_power);
                                        fprintf(write_file,'            charge_threshold %.0f kW;\n', (taxonomy_data.emissions_peak*tech_data.es_charge_setting));
                                        fprintf(write_file,'            discharge_threshold %.0f kW;\n', (taxonomy_data.emissions_peak*tech_data.es_discharge_setting));
                                        fprintf(write_file,'            inverter_efficiency %.1f;\n', (tech_data.es_inv_efficiency));
                                        fprintf(write_file,'            charge_lockout_time 60;\n');
                                        fprintf(write_file,'            discharge_lockout_time 60;\n');
                                        fprintf(write_file,'            object battery {\n');                    
                                        fprintf(write_file,'                  name es_batt_%s;\n',parent1);
                                        fprintf(write_file,'                  generator_mode SUPPLY_DRIVEN;\n');
                                        fprintf(write_file,'                  generator_status ONLINE;\n');
                                        fprintf(write_file,'                  use_internal_battery_model TRUE;\n');
                                        fprintf(write_file,'                  battery_type LI_ION;\n');
                                        fprintf(write_file,'                  round_trip_efficiency %.2f;\n', tech_data.es_battery_efficiency);
                                        fprintf(write_file,'                  battery_capacity %.2f kWh;\n', tech_data.es_battery_capacity_com);
                                        fprintf(write_file,'            };\n');
                                        fprintf(write_file,'      };\n');
                                        fprintf(write_file,'}\n');
                                    end
                                    bigbox_count = bigbox_count + 1;
                                end
                            end
                        end
                    end
                end
            end
        end

        if (exist('es_stripmall_array','var'))
            stripmall_penetration = rand(total_no_stripmall,1);
            off_cnt = 0;
            for off_ind=1:total_no_stripmall
                if (stripmall_penetration(off_ind) <= (total_es_batteries_stripmall/(total_no_stripmall)))
                    off_cnt = off_cnt + 1;
                end
            end
            if (off_cnt < total_es_batteries_stripmall)
                off_diff = total_es_batteries_stripmall - off_cnt;
                for off_ind=1:total_no_stripmall
                    if (stripmall_penetration(off_ind) > (total_es_batteries_stripmall/(total_no_stripmall)) && off_diff > 0)
                        stripmall_penetration(off_ind) = (total_es_batteries_stripmall/(total_no_stripmall));
                        off_diff = off_diff - 1;
                    end
                end
            elseif (off_cnt > total_es_batteries_stripmall)
                off_diff = off_cnt - total_es_batteries_stripmall;
                for off_ind=1:total_no_stripmall
                    if (stripmall_penetration(off_ind) <= (total_es_batteries_stripmall/(total_no_stripmall)) && off_diff > 0)
                        stripmall_penetration(off_ind) = (total_es_batteries_stripmall/(total_no_stripmall)) + 0.1;
                        off_diff = off_diff - 1;
                    end
                end
            end
            stripmall_count=1;
            
            for jj=1:total_no_stripmall_length
                if (~isempty(es_stripmall_array{jj}))
                    for jjj=1:length(es_stripmall_array{jj})
                        for jjjj=1:length(es_stripmall_array{jj}{jjj})
                            if (~isempty(es_stripmall_array{jj}{jjj}{jjjj}))
                                if (stripmall_penetration(stripmall_count) < (total_es_batteries_stripmall/(total_no_stripmall)))
                                    parent = es_stripmall_array_parent{jj}{jjj}{jjjj};
                                    parent1 = es_stripmall_array{jj}{jjj}{jjjj};
                                    phase1 = es_stripmall_array_phases{jj}{jjj}{jjjj}; 
                                    countES_stripmall = countES_stripmall + 1;   
                                    fprintf(write_file,'object triplex_meter {\n');
                                    fprintf(write_file,'      phases %sS;\n',phase1);
                                    fprintf(write_file,'      name stripmallES_tm_%s;\n', parent1);
                                    fprintf(write_file,'      parent %s;\n',parent);
                                    fprintf(write_file,'      nominal_voltage 120;\n');
                                    fprintf(write_file,'      groupid Commercial_tm_es_stripmall;\n');
                                    fprintf(write_file,'      object inverter {\n');
                                    fprintf(write_file,'            name batt_inv_%s;\n',parent1);
                                    fprintf(write_file,'            phases %sS;\n',phase1);
                                    fprintf(write_file,'            generator_mode CONSTANT_PQ;\n');
                                    fprintf(write_file,'            generator_status ONLINE;\n');
                                    fprintf(write_file,'            inverter_type FOUR_QUADRANT;\n');
                                    fprintf(write_file,'            four_quadrant_control_mode GROUP_LOAD_FOLLOWING;\n');
                                    fprintf(write_file,'            sense_object substation_transformer;\n');
                                    fprintf(write_file,'            max_charge_rate %.0f kW;\n', tech_data.es_com_unit_rated_power);
                                    fprintf(write_file,'            max_discharge_rate %.0f kW;\n', tech_data.es_com_unit_rated_power);
                                    fprintf(write_file,'            rated_power %.0f kW;\n', tech_data.es_com_unit_rated_power);
                                    fprintf(write_file,'            group_max_charge_rate %.0f kW;\n', total_es_power);
                                    fprintf(write_file,'            group_max_discharge_rate %.0f kW;\n', total_es_power);
                                    fprintf(write_file,'            group_rated_power %.0f kW;\n', total_es_power);
                                    fprintf(write_file,'            charge_threshold %.0f kW;\n', (taxonomy_data.emissions_peak*tech_data.es_charge_setting));
                                    fprintf(write_file,'            discharge_threshold %.0f kW;\n', (taxonomy_data.emissions_peak*tech_data.es_discharge_setting));
                                    fprintf(write_file,'            inverter_efficiency %.1f;\n', (tech_data.es_inv_efficiency));
                                    fprintf(write_file,'            charge_lockout_time 60;\n');
                                    fprintf(write_file,'            discharge_lockout_time 60;\n');
                                    fprintf(write_file,'            object battery {\n');                    
                                    fprintf(write_file,'                  name es_batt_%s;\n',parent1);
                                    fprintf(write_file,'                  generator_mode SUPPLY_DRIVEN;\n');
                                    fprintf(write_file,'                  generator_status ONLINE;\n');
                                    fprintf(write_file,'                  use_internal_battery_model TRUE;\n');
                                    fprintf(write_file,'                  battery_type LI_ION;\n');
                                    fprintf(write_file,'                  round_trip_efficiency %.2f;\n', tech_data.es_battery_efficiency);
                                    fprintf(write_file,'                  battery_capacity %.2f kWh;\n', tech_data.es_battery_capacity_com);
                                    fprintf(write_file,'            };\n');
                                    fprintf(write_file,'      };\n');
                                    fprintf(write_file,'}\n');
                                end
                                stripmall_count = stripmall_count + 1;
                            end
                        end
                    end
                end                  
            end
        end
    end
    
    if (use_flags.use_energy_storage ~=0 || use_flags.use_energy_storage_res ~=0)
         if (exist('es_residential_array','var'))
            residential_penetration = rand(total_no_residential,1);
            off_cnt = 0;
            for off_ind=1:total_no_residential
                if (residential_penetration(off_ind) <= (total_es_batteries_res/(total_no_residential)))
                    off_cnt = off_cnt + 1;
                end
            end
            if (off_cnt < total_es_batteries_res)
                off_diff = total_es_batteries_res - off_cnt;
                for off_ind=1:total_no_residential
                    if (residential_penetration(off_ind) > (total_es_batteries_res/(total_no_residential)) && off_diff > 0)
                        residential_penetration(off_ind) = (total_es_batteries_res/(total_no_residential));
                        off_diff = off_diff - 1;
                    end
                end
            elseif (off_cnt > total_es_batteries_res)
                off_diff = off_cnt - total_es_batteries_res;
                for off_ind=1:total_no_residential
                    if (residential_penetration(off_ind) <= (total_es_batteries_res/(total_no_residential)) && off_diff > 0)
                        residential_penetration(off_ind) = (total_es_batteries_res/(total_no_residential)) + 0.1;
                        off_diff = off_diff - 1;
                    end
                end
            end
            residential_count=1;
            
            for jj=1:total_no_residential_length
                if (~isempty(es_residential_array{jj}))            
                    for jjj=1:length(es_residential_array{jj})
                        if (~isempty(es_residential_array{jj}{jjj}))
                            if (residential_penetration(residential_count) < (total_es_batteries_res/total_no_residential))
                                parent = es_residential_array_parent{jj}{jjj};  
                                parent1 = es_residential_array{jj}{jjj}; 
                                phase1 = es_residential_array_phase{jj}{jjj}; 
                                countES = countES + 1;   
                                fprintf(write_file,'object triplex_meter {\n');
                                fprintf(write_file,'      phases %s\n',phase1);
                                fprintf(write_file,'      name resES_tm_%s\n', parent1);
                                fprintf(write_file,'      parent %s\n',parent);
                                fprintf(write_file,'      nominal_voltage 120;\n');
                                fprintf(write_file,'      groupid Residental_tm_es;\n');
                                fprintf(write_file,'      object inverter {\n');
                                fprintf(write_file,'            name batt_inv_%s\n',parent1);
                                fprintf(write_file,'            phases %s\n',phase1);
                                fprintf(write_file,'            generator_mode CONSTANT_PQ;\n');
                                fprintf(write_file,'            generator_status ONLINE;\n');
                                fprintf(write_file,'            inverter_type FOUR_QUADRANT;\n');
                                fprintf(write_file,'            four_quadrant_control_mode GROUP_LOAD_FOLLOWING;\n');
                                fprintf(write_file,'            sense_object substation_transformer;\n');
                                fprintf(write_file,'            max_charge_rate %.0f kW;\n', tech_data.es_res_unit_rated_power);
                                fprintf(write_file,'            max_discharge_rate %.0f kW;\n', tech_data.es_res_unit_rated_power);
                                fprintf(write_file,'            rated_power %.0f kW;\n', tech_data.es_res_unit_rated_power);
                                fprintf(write_file,'            group_max_charge_rate %.0f kW;\n', total_es_power);
                                fprintf(write_file,'            group_max_discharge_rate %.0f kW;\n', total_es_power);
                                fprintf(write_file,'            group_rated_power %.0f kW;\n', total_es_power);
                                fprintf(write_file,'            charge_threshold %.0f kW;\n', (taxonomy_data.emissions_peak*tech_data.es_charge_setting));
                                fprintf(write_file,'            discharge_threshold %.0f kW;\n', (taxonomy_data.emissions_peak*tech_data.es_discharge_setting));
                                fprintf(write_file,'            inverter_efficiency %.1f;\n', (tech_data.es_inv_efficiency));
                                fprintf(write_file,'            charge_lockout_time 60;\n');
                                fprintf(write_file,'            discharge_lockout_time 60;\n');
                                fprintf(write_file,'            object battery {\n');                    
                                fprintf(write_file,'                  name es_batt_%s\n',parent1);
                                fprintf(write_file,'                  generator_mode SUPPLY_DRIVEN;\n');
                                fprintf(write_file,'                  generator_status ONLINE;\n');
                                fprintf(write_file,'                  use_internal_battery_model TRUE;\n');
                                fprintf(write_file,'                  battery_type LI_ION;\n');
                                fprintf(write_file,'                  round_trip_efficiency %.2f;\n', tech_data.es_battery_efficiency);
                                fprintf(write_file,'                  battery_capacity %.2f kWh;\n', tech_data.es_battery_capacity_res);
                                fprintf(write_file,'            };\n');
                                fprintf(write_file,'      };\n');
                                fprintf(write_file,'}\n');
                            end
                            residential_count = residential_count + 1;
                        end
                    end             
                end
            end
        end
    end
    
    % if you want to create and emissions object - THIS WILL BE REMOVED AND
    % EMISSIONS WILL BE PERFORMED IN POST PROCESSING
%     if (use_flags.use_emissions ~= 0)
%         % Add emissions object
%         fprintf(write_file,'object emissions {\n');
%         fprintf(write_file,'     name emissionsobject1;\n');
%         fprintf(write_file,'     parent network_node;\n');
%         fprintf(write_file,'     Naturalgas_Max_Out NG_Max_Out_R%d*%.1f ;\n',region,taxonomy_data.emissions_peak);
%         fprintf(write_file,'     Coal_Max_Out Coal_Max_Out_R%d*%.1f ;\n',region,taxonomy_data.emissions_peak);
%         fprintf(write_file,'     Biomass_Max_Out Bio_Max_Out_R%d*%.1f ;\n',region,taxonomy_data.emissions_peak);
%         fprintf(write_file,'     Geothermal_Max_Out Geo_Max_Out_R%d*%.1f ;\n',region,taxonomy_data.emissions_peak);
%         fprintf(write_file,'     Hydroelectric_Max_Out Hydro_Max_Out_R%d*%.1f ;\n',region,taxonomy_data.emissions_peak);
%         fprintf(write_file,'     Nuclear_Max_Out Nuclear_Max_Out_R%d*%.1f ;\n',region,taxonomy_data.emissions_peak);
%         fprintf(write_file,'     Wind_Max_Out Wind_Max_Out_R%d*%.1f ;\n',region,taxonomy_data.emissions_peak);
%         fprintf(write_file,'     Petroleum_Max_Out Petroleum_Max_Out_R%d*%.1f ;\n',region,taxonomy_data.emissions_peak);
%         fprintf(write_file,'     Solarthermal_Max_Out Solar_Max_Out_R%d*%.1f ;\n\n',region,taxonomy_data.emissions_peak);
% 
%         fprintf(write_file,'     Naturalgas_Conv_Eff %.2f MBtu/MWh;\n',tech_data.Naturalgas_Conv_Eff);
%         fprintf(write_file,'     Coal_Conv_Eff %.2f MBtu/MWh;\n',tech_data.Coal_Conv_Eff);
%         fprintf(write_file,'     Biomass_Conv_Eff %.2f MBtu/MWh;\n',tech_data.Biomass_Conv_Eff);
%         fprintf(write_file,'     Geothermal_Conv_Eff %.2f MBtu/MWh;\n',tech_data.Geothermal_Conv_Eff);
%         fprintf(write_file,'     Hydroelectric_Conv_Eff %.2f MBtu/MWh;\n',tech_data.Hydroelectric_Conv_Eff);
%         fprintf(write_file,'     Nuclear_Conv_Eff %.2f MBtu/MWh;\n',tech_data.Nuclear_Conv_Eff);
%         fprintf(write_file,'     Wind_Conv_Eff %.2f MBtu/MWh;\n',tech_data.Wind_Conv_Eff);
%         fprintf(write_file,'     Petroleum_Conv_Eff %.2f MBtu/MWh;\n',tech_data.Petroleum_Conv_Eff);
%         fprintf(write_file,'     Solarthermal_Conv_Eff %.2f MBtu/MWh;\n\n',tech_data.Solarthermal_Conv_Eff);
% 
%         fprintf(write_file,'     Naturalgas_CO2 %.2f lb/MBtu;\n',tech_data.Naturalgas_CO2);
%         fprintf(write_file,'     Coal_CO2 %.2f lb/MBtu;\n',tech_data.Coal_CO2);	
%         fprintf(write_file,'     Biomass_CO2 %.2f lb/MBtu;\n',tech_data.Biomass_CO2);
%         fprintf(write_file,'     Geothermal_CO2 %.2f lb/MBtu;\n',tech_data.Geothermal_CO2);
%         fprintf(write_file,'     Hydroelectric_CO2 %.2f lb/MBtu;\n',tech_data.Hydroelectric_CO2);
%         fprintf(write_file,'     Nuclear_CO2 %.2f lb/MBtu;\n',tech_data.Nuclear_CO2);
%         fprintf(write_file,'     Wind_CO2 %.2f lb/MBtu;\n',tech_data.Wind_CO2);
%         fprintf(write_file,'     Petroleum_CO2 %.2f lb/MBtu;\n',tech_data.Petroleum_CO2);
%         fprintf(write_file,'     Solarthermal_CO2 %.2f lb/MBtu;\n\n',tech_data.Solarthermal_CO2);
% 
%         fprintf(write_file,'     Naturalgas_SO2 %.2f lb/MBtu;\n',tech_data.Naturalgas_SO2);
%         fprintf(write_file,'     Coal_SO2 %.2f lb/MBtu;\n',tech_data.Coal_SO2);	
%         fprintf(write_file,'     Biomass_SO2 %.2f lb/MBtu;\n',tech_data.Biomass_SO2);
%         fprintf(write_file,'     Geothermal_SO2 %.2f lb/MBtu;\n',tech_data.Geothermal_SO2);
%         fprintf(write_file,'     Hydroelectric_SO2 %.2f lb/MBtu;\n',tech_data.Hydroelectric_SO2);
%         fprintf(write_file,'     Nuclear_SO2 %.2f lb/MBtu;\n',tech_data.Nuclear_SO2);
%         fprintf(write_file,'     Wind_SO2 %.2f lb/MBtu;\n',tech_data.Wind_SO2);
%         fprintf(write_file,'     Petroleum_SO2 %.2f lb/MBtu;\n',tech_data.Petroleum_SO2);
%         fprintf(write_file,'     Solarthermal_SO2 %.2f lb/MBtu;\n\n',tech_data.Solarthermal_SO2);
% 
%         fprintf(write_file,'     Naturalgas_NOx %.2f lb/MBtu;\n',tech_data.Naturalgas_NOx);
%         fprintf(write_file,'     Coal_NOx %.2f lb/MBtu;\n',tech_data.Coal_NOx);	
%         fprintf(write_file,'     Biomass_NOx %.2f lb/MBtu;\n',tech_data.Biomass_NOx);
%         fprintf(write_file,'     Geothermal_NOx %.2f lb/MBtu;\n',tech_data.Geothermal_NOx);
%         fprintf(write_file,'     Hydroelectric_NOx %.2f lb/MBtu;\n',tech_data.Hydroelectric_NOx);
%         fprintf(write_file,'     Nuclear_NOx %.2f lb/MBtu;\n',tech_data.Nuclear_NOx);
%         fprintf(write_file,'     Wind_NOx %.2f lb/MBtu;\n',tech_data.Wind_NOx);
%         fprintf(write_file,'     Petroleum_NOx %.2f lb/MBtu;\n',tech_data.Petroleum_NOx);
%         fprintf(write_file,'     Solarthermal_NOx %.2f lb/MBtu;\n\n',tech_data.Solarthermal_NOx);
%         
%         fprintf(write_file,'     Nuclear_Order %.0f;\n',regional_data.dispatch_order(1));
% 		fprintf(write_file,'     Hydroelectric_Order %.0f;\n',regional_data.dispatch_order(2));
% 		fprintf(write_file,'     Solarthermal_Order %.0f;\n',regional_data.dispatch_order(3));
% 		fprintf(write_file,'     Biomass_Order %.0f;\n',regional_data.dispatch_order(4));
% 		fprintf(write_file,'     Wind_Order %.0f;\n',regional_data.dispatch_order(5));
% 		fprintf(write_file,'     Coal_Order %.0f;\n',regional_data.dispatch_order(6));
% 		fprintf(write_file,'     Naturalgas_Order %.0f;\n',regional_data.dispatch_order(7));
% 		fprintf(write_file,'     Geothermal_Order %.0f;\n',regional_data.dispatch_order(8));
% 		fprintf(write_file,'     Petroleum_Order %.0f;\n\n',regional_data.dispatch_order(9));
% 
%         fprintf(write_file,'     cycle_interval %.0f min;\n',tech_data.cycle_interval);
%         fprintf(write_file,'}\n\n');
%         
%         fprintf(write_file,'object recorder {\n');
%         fprintf(write_file,'     file %s_emissions.csv;\n',tech_file);
%         fprintf(write_file,'     parent emissionsobject1;\n');
%         fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
%         fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
%         fprintf(write_file,'     property Total_emissions_CO2,Total_emissions_SO2,Total_energy_out,Total_emissions_NOx,Naturalgas_Out,Coal_Out,Biomass_Out,Geothermal_Out,Hydroelectric_Out,Nuclear_Out,Wind_Out,Petroleum_Out,Solarthermal_Out;\n');
%         fprintf(write_file,'}\n\n');
% 
%     end
    
    % Add players to capacitor for outtages
    if (use_flags.use_capacitor_outtages == 1)
        [cap_out_a,cap_out_b] = size(taxonomy_data.capacitor_outtage);
        for cap_ind=1:cap_out_a
            fprintf(write_file,'object player {\n');
            fprintf(write_file,'     parent %s;\n',taxonomy_data.capacitor_outtage{cap_ind,1});
            fprintf(write_file,'     file %s;\n',taxonomy_data.capacitor_outtage{cap_ind,2});
            fprintf(write_file,'     property service_status;\n');
            fprintf(write_file,'     loop 1;\n');
            fprintf(write_file,'};\n');
        end
    end
                
    %% Recorders, collectors, etc.
    fprintf(write_file,'object recorder {\n');
    fprintf(write_file,'     file %s_transformer_power.csv;\n',tech_file);
    fprintf(write_file,'     parent substation_transformer;\n');
    fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
    fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
    fprintf(write_file,'     property power_out_A.real,power_out_A.imag,power_out_B.real,power_out_B.imag,power_out_C.real,power_out_C.imag,power_out.real,power_out.imag,power_losses_A.real,power_losses_A.imag,power_losses_B.real,power_losses_B.imag,power_losses_C.real,power_losses_C.imag;\n');
    fprintf(write_file,'}\n\n');
            
    if (countSOLAR > 0)
        % Solar collector for residential
        fprintf(write_file,'object collector {\n');
        fprintf(write_file,'     file %s_Solar.csv;\n',tech_file);
        fprintf(write_file,'     group "class=triplex_meter AND groupid=Residential_tm_solar";\n');
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        fprintf(write_file,'     property sum(measured_real_energy),sum(measured_power.real);\n');
        fprintf(write_file,'}\n\n');
    end
    % end of Solar residential collector

    % Solar collector for Commercial (stripmall)
    if (countSOLAR_stripmall > 0)
        fprintf(write_file,'object collector {\n');
        fprintf(write_file,'     file %s_Solar_stripmall.csv;\n',tech_file);
        fprintf(write_file,'     group "class=triplex_meter AND groupid=Commercial_tm_solar_stripmall";\n');
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        fprintf(write_file,'     property sum(power_1_real),sum(power_2_real);\n');
        fprintf(write_file,'}\n\n');
    end
    % end of Solar Commercial collector (stripmall) 
         
    if (countSOLAR_office > 0)
        % Solar collector for Commercial (office)
        fprintf(write_file,'object collector {\n');
        fprintf(write_file,'     file %s_ES_office.csv;\n',tech_file);
        fprintf(write_file,'     group "class=triplex_meter AND groupid=Commercial_tm_solar_office";\n');
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        fprintf(write_file,'     property sum(measured_real_energy),sum(measured_power.real);\n');
        fprintf(write_file,'}\n\n');
    end
    % end of Solar commercial collector (office) 
         
    if (countSOLAR_bigbox > 0)
        % Solar collector for Commercial (bigbox)
        fprintf(write_file,'object collector {\n');
        fprintf(write_file,'     file %s_Solar_bigbox.csv;\n',tech_file);
        fprintf(write_file,'     group "class=triplex_meter AND groupid=Commercial_tm_solar_bigbox";\n');
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        fprintf(write_file,'     property sum(measured_real_energy),sum(measured_power.real);\n');
        fprintf(write_file,'}\n\n');
    end
    % end of Solar Commercial collector (bigbox) 
    if (countES > 0)
        % energy storage collector for residential
        fprintf(write_file,'object collector {\n');
        fprintf(write_file,'     file %s_ES.csv;\n',tech_file);
        fprintf(write_file,'     group "class=triplex_meter AND groupid=Residential_tm_es";\n');
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        fprintf(write_file,'     property sum(measured_real_energy),sum(measured_power.real);\n');
        fprintf(write_file,'}\n\n');
    end
    % end of energy storage residential collector

    % energy storage collector for Commercial (stripmall)
    if (countES_stripmall > 0)
        fprintf(write_file,'object collector {\n');
        fprintf(write_file,'     file %s_ES_stripmall.csv;\n',tech_file);
        fprintf(write_file,'     group "class=triplex_meter AND groupid=Commercial_tm_es_stripmall";\n');
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        fprintf(write_file,'     property sum(power_1_real),sum(power_2_real);\n');
        fprintf(write_file,'}\n\n');
    end
    % end of energy storage Commercial collector (stripmall) 
         
    if (countES_office > 0)
        % energy storage collector for Commercial (office)
        fprintf(write_file,'object collector {\n');
        fprintf(write_file,'     file %s_ES_office.csv;\n',tech_file);
        fprintf(write_file,'     group "class=triplex_meter AND groupid=Commercial_tm_es_office";\n');
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        fprintf(write_file,'     property sum(measured_real_energy),sum(measured_power.real);\n');
        fprintf(write_file,'}\n\n');
    end
    % end of energy storage commercial collector (office) 
         
    if (countES_bigbox > 0)
        % energy storage collector for Commercial (bigbox)
        fprintf(write_file,'object collector {\n');
        fprintf(write_file,'     file %s_ES_bigbox.csv;\n',tech_file);
        fprintf(write_file,'     group "class=triplex_meter AND groupid=Commercial_tm_es_bigbox";\n');
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        fprintf(write_file,'     property sum(measured_real_energy),sum(measured_power.real);\n');
        fprintf(write_file,'}\n\n');
    end
    % end of energy storage Commercial collector (bigbox)
    if (tech_data.measure_market == 1 && use_flags.use_market ~= 0)
        fprintf(write_file,'object recorder {\n');
        fprintf(write_file,'     parent %s;\n',tech_data.market_info{1});
        fprintf(write_file,'     property past_market.clearing_price,%s,%s;\n','my_avg','my_std');
        fprintf(write_file,'     limit %.0f;\n',tech_data.meas_limit);
        fprintf(write_file,'     interval %.0f;\n',tech_data.meas_interval);
        fprintf(write_file,'     file %s_markets.csv;\n',tech_file);
        fprintf(write_file,'}\n\n');
    end
    
    %Thermal storage collector - for storage-specific metric
    if (tech_data.tech_flag==9)    %Thermal storage
        fprintf(write_file,'object collector {\n');
        fprintf(write_file,'     group "class=thermal_storage";\n');
        fprintf(write_file,'     property sum(stored_capacity),sum(total_capacity);\n');
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        fprintf(write_file,'     file %s_StorageValues.csv;\n',tech_file);
        fprintf(write_file,'}\n\n');
    end

    if (tech_data.measure_losses == 1)
        if (no_ohls > 0)
            fprintf(write_file,'object collector {\n');
            fprintf(write_file,'     group "class=overhead_line";\n');
            fprintf(write_file,'     property sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag);\n');
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
            fprintf(write_file,'     file %s_OHL_losses.csv;\n',tech_file);
            fprintf(write_file,'}\n\n');
        end
        if (no_ugls > 0)
            fprintf(write_file,'object collector {\n');
            fprintf(write_file,'     group "class=underground_line";\n');
            fprintf(write_file,'     property sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag);\n');
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
            fprintf(write_file,'     file %s_UGL_losses.csv;\n',tech_file);
            fprintf(write_file,'}\n\n');
        end
        if (no_triplines > 0)
            fprintf(write_file,'object collector {\n');
            fprintf(write_file,'     group "class=triplex_line";\n');
            fprintf(write_file,'     property sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag);\n');
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
            fprintf(write_file,'     file %s_TPL_losses.csv;\n',tech_file);
            fprintf(write_file,'}\n\n');
        end

        % There's always a transformer (substation)
        fprintf(write_file,'object collector {\n');
        fprintf(write_file,'     group "class=transformer";\n');
        fprintf(write_file,'     property sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag);\n');
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        fprintf(write_file,'     file %s_TFR_losses.csv;\n',tech_file);
        fprintf(write_file,'}\n\n');

    end

    if (tech_data.collect_setpoints == 1)
        if (total_houses > 0)
            fprintf(write_file,'object collector {\n');
            fprintf(write_file,'     group "class=house AND groupid=Residential";\n');
            fprintf(write_file,'     property avg(cooling_setpoint),avg(heating_setpoint,avg(air_temperature),sum(is_AUX_on),sum(is_HEAT_on),sum(is_COOL_on));\n');
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
            fprintf(write_file,'     file %s_res_setpoints.csv;\n',tech_file);
            fprintf(write_file,'}\n\n');
        end
        
        if (ph3_meter + ph1_meter > 0)
            fprintf(write_file,'object collector {\n');
            fprintf(write_file,'     group "class=house AND groupid=Commercial";\n');
            fprintf(write_file,'     property avg(cooling_setpoint),avg(heating_setpoint,avg(air_temperature),sum(is_AUX_on),sum(is_HEAT_on),sum(is_COOL_on));\n');
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
            fprintf(write_file,'     file %s_comm_setpoints.csv;\n',tech_file);
            fprintf(write_file,'}\n\n');
        end
    end

    if (tech_data.measure_loads ~= 0)
        
        if (total_houses > 0)
            fprintf(write_file,'object collector {\n');
            fprintf(write_file,'     group "class=triplex_meter AND groupid=Residential_Meter";\n');
            fprintf(write_file,'     property sum(measured_real_power),sum(indiv_measured_power_1.real),sum(indiv_measured_power_2.real);\n');
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
            fprintf(write_file,'     file %s_res_load.csv;\n',tech_file);
            fprintf(write_file,'}\n\n');
        end

        if (ph3_meter > 0)
            fprintf(write_file,'object collector {\n');
            fprintf(write_file,'     group "class=meter AND groupid=Commercial_Meter";\n');
            fprintf(write_file,'     property sum(measured_power_A.real),sum(measured_power_B.real),sum(measured_power_C.real);\n');
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
            fprintf(write_file,'     file %s_comm_load1.csv;\n',tech_file);
            fprintf(write_file,'}\n\n');
        end
        
        if (ph1_meter > 0)
            fprintf(write_file,'object collector {\n');
            fprintf(write_file,'     group "class=triplex_meter AND groupid=Commercial_Meter";\n');
            fprintf(write_file,'     property sum(measured_real_power),sum(indiv_measured_power_1.real),sum(indiv_measured_power_2.real);\n');
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
            fprintf(write_file,'     file %s_comm_load2.csv;\n',tech_file);
            fprintf(write_file,'}\n\n');
        end
    end

    if (tech_data.measure_capacitors == 1 && cap_n > 0)
        for jindex = 1:cap_n
            fprintf(write_file,'object recorder {\n');
            fprintf(write_file,'     parent %s;\n',capacitor_list{jindex});
            fprintf(write_file,'     file %s_cap%.0f.csv;\n',tech_file,jindex);
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
            fprintf(write_file,'     property service_status,switchA,switchB,switchC,voltage_A.real,voltage_A.imag,voltage_B.real,voltage_B.imag,voltage_C.real,voltage_C.imag;\n');
            fprintf(write_file,'};\n\n');
        end
    end

    if (tech_data.measure_regulators == 1 && reg_n > 0)
        for jindex = 1:reg_n
            fprintf(write_file,'object recorder {\n');
            fprintf(write_file,'     parent %s;\n',regulator_list{jindex});
            fprintf(write_file,'     file %s_reg%.0f.csv;\n',tech_file,jindex);
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
            fprintf(write_file,'     property tap_A,tap_B,tap_C,power_in_A.real,power_in_A.imag,power_in_B.real,power_in_B.imag,power_in_C.real,power_in_C.imag,power_in.real,power_in.imag;\n');
            fprintf(write_file,'};\n\n');
        end
    end

    if (tech_data.measure_EOL_voltage ~= 0)
        
        [no_nodes,junk] = size(taxonomy_data.EOL_points);
        
        % If too many measurements, buffer gets angry so break it up
        if (no_nodes > 3)
            no_nodes1 = 3;
            no_nodes2 = no_nodes;
        else
            no_nodes1 = no_nodes;
            no_nodes2 = 0;
        end
        fprintf(write_file,'object multi_recorder {\n');
        fprintf(write_file,'     parent %s;\n',taxonomy_data.EOL_points{1,1});
        fprintf(write_file,'     file %s_EOLVolt1.csv;\n',tech_file);
        fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
        fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);
        
        fprintf(write_file,'     property ');
        
        for jind=1:no_nodes1
            if (length(strfind(taxonomy_data.EOL_points{jind,2},'A')) ~= 0)
                fprintf(write_file,'%s:voltage_A.real,%s:voltage_A.imag,',taxonomy_data.EOL_points{jind,1},taxonomy_data.EOL_points{jind,1});
            end
            if (length(strfind(taxonomy_data.EOL_points{jind,2},'B')) ~= 0)
                fprintf(write_file,'%s:voltage_B.real,%s:voltage_B.imag,',taxonomy_data.EOL_points{jind,1},taxonomy_data.EOL_points{jind,1});
            end
            if (length(strfind(taxonomy_data.EOL_points{jind,2},'C')) ~= 0)
                fprintf(write_file,'%s:voltage_C.real,%s:voltage_C.imag,',taxonomy_data.EOL_points{jind,1},taxonomy_data.EOL_points{jind,1});
            end            
        end
        fprintf(write_file,';\n');
        
        fprintf(write_file,'};\n\n');
        
        if (no_nodes2 > 0)
            fprintf(write_file,'object multi_recorder {\n');
            fprintf(write_file,'     parent %s;\n',taxonomy_data.EOL_points{1,1});
            fprintf(write_file,'     file %s_EOLVolt2.csv;\n',tech_file);
            fprintf(write_file,'     interval %d;\n',tech_data.meas_interval);
            fprintf(write_file,'     limit %d;\n',tech_data.meas_limit);

            fprintf(write_file,'     property ');

            for jind=4:no_nodes2
                if (length(strfind(taxonomy_data.EOL_points{jind,2},'A')) ~= 0)
                    fprintf(write_file,'%s:voltage_A.real,%s:voltage_A.imag,',taxonomy_data.EOL_points{jind,1},taxonomy_data.EOL_points{jind,1});
                end
                if (length(strfind(taxonomy_data.EOL_points{jind,2},'B')) ~= 0)
                    fprintf(write_file,'%s:voltage_B.real,%s:voltage_B.imag,',taxonomy_data.EOL_points{jind,1},taxonomy_data.EOL_points{jind,1});
                end
                if (length(strfind(taxonomy_data.EOL_points{jind,2},'C')) ~= 0)
                    fprintf(write_file,'%s:voltage_C.real,%s:voltage_C.imag,',taxonomy_data.EOL_points{jind,1},taxonomy_data.EOL_points{jind,1});
                end            
            end
            fprintf(write_file,';\n');

            fprintf(write_file,'};\n\n');
        end

    end

    if (tech_data.dump_bills ~= 0)
        my_date_start = datevec(tech_data.start_date);
        my_date_end = datevec(tech_data.end_date);

        print_date = my_date_start;
        print_date(4) = 3;

        my_month = 1;
        while (datenum(print_date) <= datenum(my_date_end))
            print_date = print_date + [0 1 0 0 0 0];
            print_date2 = datestr(print_date,'yyyy-mm-dd HH:MM:SS');
            if (total_houses > 0)
                fprintf(write_file,'object billdump {\n');
                fprintf(write_file,'     runtime ''%s'';\n',print_date2);
                fprintf(write_file,'     filename %s_bill_res%.0f.csv;\n',tech_file,my_month);
                fprintf(write_file,'     group Residential_Meter;\n');
                fprintf(write_file,'     meter_type TRIPLEX_METER;\n');
                fprintf(write_file,'}\n\n');
            end
            if (ph1_meter > 0)
                fprintf(write_file,'object billdump {\n');
                fprintf(write_file,'     runtime ''%s'';\n',print_date2);
                fprintf(write_file,'     filename %s_bill_commSP%.0f.csv;\n',tech_file,my_month);
                fprintf(write_file,'     group Commercial_Meter;\n');
                fprintf(write_file,'     meter_type TRIPLEX_METER;\n');
                fprintf(write_file,'}\n\n');
            end
            if (ph3_meter > 0)
                fprintf(write_file,'object billdump {\n');
                fprintf(write_file,'     runtime ''%s'';\n',print_date2);
                fprintf(write_file,'     filename %s_bill_comm3p%.0f.csv;\n',tech_file,my_month);
                fprintf(write_file,'     group Commercial_Meter;\n');
                fprintf(write_file,'     meter_type METER;\n');
                fprintf(write_file,'}\n\n');
            end
            
            my_month = my_month + 1;
        end
    end

    if (tech_data.dump_voltage ~= 0)
        fprintf(write_file,'object voltdump {\n');
        fprintf(write_file,'     filename %s_voltdump.csv;\n',tech_file);
        fprintf(write_file,'     runtime ''%s'';\n',tech_data.end_date);
        fprintf(write_file,'}\n\n');
    end

    % print statistics of glm at bottom of glm
    if (tech_data.include_stats ~= 0)
        fprintf(write_file,'//This section will describe a number of the parameters');
        fprintf(write_file,'// that were used to create this particular GLM.\n');
        fprintf(write_file,'// Created: %s\n\n', datestr(now));
        fprintf(write_file,'//Technology Number %.0f\n',tech_data.tech_number);
        if (use_flags.use_homes == 1)
            fprintf(write_file,'\n//Average house %.3f\n',taxonomy_data.avg_house);
            fprintf(write_file,'//Impedance Fraction %.3f\n',tech_data.zfrac);
            fprintf(write_file,'//Current Fraction %.3f\n',tech_data.ifrac);
            fprintf(write_file,'//Power Fraction %.3f\n',tech_data.pfrac);
            fprintf(write_file,'//Impedance Power Factor %.3f\n',tech_data.z_pf);
            fprintf(write_file,'//Current Power Factor %.3f\n',tech_data.i_pf);
            fprintf(write_file,'//Power Power Factor %.3f\n',tech_data.p_pf);
            fprintf(write_file,'//Heat Gain Fraction %.3f\n',tech_data.heat_fraction);

        end
        if (use_flags.use_commercial == 0)
            fprintf(write_file,'\n//Impedance Fraction %.3f\n',tech_data.c_zfrac);
            fprintf(write_file,'//Current Fraction %.3f\n',tech_data.c_ifrac);
            fprintf(write_file,'//Power Fraction %.3f\n',tech_data.c_pfrac);
            fprintf(write_file,'//Impedance Power Factor %.3f\n',tech_data.c_z_pf);
            fprintf(write_file,'//Current Power Factor %.3f\n',tech_data.c_i_pf);
            fprintf(write_file,'//Power Power Factor %.3f\n',tech_data.c_p_pf);
        else
            fprintf(write_file,'\n//Average commercial %.3f\n',taxonomy_data.avg_commercial);
            fprintf(write_file,'//Average cooling COP %.3f\n',tech_data.cooling_COP);
            fprintf(write_file,'//Impedance Fraction %.3f\n',tech_data.c_zfrac);
            fprintf(write_file,'//Current Fraction %.3f\n',tech_data.c_ifrac);
            fprintf(write_file,'//Power Fraction %.3f\n',tech_data.c_pfrac);
            fprintf(write_file,'//Impedance Power Factor %.3f\n',tech_data.c_z_pf);
            fprintf(write_file,'//Current Power Factor %.3f\n',tech_data.c_i_pf);
            fprintf(write_file,'//Power Power Factor %.3f\n',tech_data.c_p_pf);
        end
        
        if (use_flags.use_ts ~= 0)
            fprintf(write_file,'\n//Thermal Storage Mode = %d\n',use_flags.use_ts);
            fprintf(write_file,'//Thermal Storage SOC = %0.2f\n',tech_data.ts_SOC);
            fprintf(write_file,'//Thermal Storage k value = %0.2f\n',tech_data.k_ts);
            if (isfield(taxonomy_data,'thermal_override'))
                fprintf(write_file,'//Thermal Storage Penetration = %.1f\n',taxonomy_data.thermal_override);
            else %No exist, use regional value
                fprintf(write_file,'//Thermal Storage Penetration = %.1f\n',regional_data.ts_penetration);
            end
        end
        
        %Write some solar information
        if ((use_flags.use_solar~=0) || (use_flags.use_solar_res~=0) || (use_flags.use_solar_com~=0))
            fprintf(write_file,'\n//Solar Size Information\n');
            if (use_flags.use_solar_res~=0)
                fprintf(write_file,'//Residential solar = %.1f ft^2\n',ResSolarArea);
            end
            
            if (use_flags.use_solar_com~=0)
                fprintf(write_file,'//Office solar    = %.1f ft^2\n',ComSolarAreaOffice);
                fprintf(write_file,'//Bigbox solar    = %.1f ft^2\n',ComSolarAreaBigBox);
                fprintf(write_file,'//Stripmall solar = %.1f ft^2\n',ComSolarAreaStripMall);
            end
            
            %Now convert to an ideal power rating - all were fixed at 0.2
            %efficiency and 92.902 W/Sf
            fprintf(write_file,'\n//Solar Output Information\n');

            if (use_flags.use_solar_res~=0)
                fprintf(write_file,'//Residential solar = %.2f kW\n',ResSolarArea*0.2*92.902/1000);
            end
            
            if (use_flags.use_solar_com~=0)
                fprintf(write_file,'//Office solar    = %.2f kW\n',ComSolarAreaOffice*0.2*92.902/1000);
                fprintf(write_file,'//Bigbox solar    = %.2f kW\n',ComSolarAreaBigBox*0.2*92.902/1000);
                fprintf(write_file,'//Stripmall solar = %.2f kW\n',ComSolarAreaStripMall*0.2*92.902/1000);
            end
        end
        
        %Write some phev information
        if(use_flags.use_phev ~= 0)
            fprintf(write_file, '\n//PHEV Output Information\n');
            fprintf(write_file, '//PHEV load = %.2f kW\n', (countPHEV * tech_data.phev_maximum_charge_rate / tech_data.phev_charging_efficiency));
        end
        
        %Write some energy storage information
        if ((use_flags.use_energy_storage~=0) || (use_flags.use_energy_storage_res~=0) || (use_flags.use_energy_storage_com~=0))
            fprintf(write_file,'\n//Energy Storage Capacity Information\n');
            if (use_flags.use_energy_storage_res~=0)
                fprintf(write_file,'//Residential = %.1f kWh\n',(total_es_batteries_res * tech_data.es_battery_capacity_res));
            end
            
            if (use_flags.use_energy_storage_com~=0)
                fprintf(write_file,'//Office    = %.1f kWh\n',(total_es_batteries_office * tech_data.es_battery_capacity_com));
                fprintf(write_file,'//Bigbox    = %.1f kWh\n',(total_es_batteries_bigbox * tech_data.es_battery_capacity_com));
                fprintf(write_file,'//Stripmall = %.1f kWh\n',(total_es_batteries_stripmall * tech_data.es_battery_capacity_com));
            end

            fprintf(write_file,'\n//Energy Storage Output Information\n');

            if (use_flags.use_energy_storage_res~=0)
                fprintf(write_file,'//Residential = %.2f kW\n',(total_es_batteries_res * tech_data.es_res_unit_rated_power));
            end
            
            if (use_flags.use_energy_storage_com~=0)
                fprintf(write_file,'//Office    = %.2f kW\n',(total_es_batteries_office * tech_data.es_com_unit_rated_power));
                fprintf(write_file,'//Bigbox    = %.2f kW\n',(total_es_batteries_bigbox * tech_data.es_com_unit_rated_power));
                fprintf(write_file,'//Stripmall = %.2f kW\n',(total_es_batteries_stripmall * tech_data.es_com_unit_rated_power));
            end
        end
        
        fprintf(write_file,'\n//Residential skews +/-%.3f, max:%f\n',tech_data.residential_skew_std,tech_data.residential_skew_max);
        fprintf(write_file,'//Commercial skews +/-%.3f, max:%f\n',tech_data.commercial_skew_std,tech_data.commercial_skew_max);

        if (use_flags.use_billing ~= 0) 
            fprintf(write_file,'\n//Monthly Fee %.3f\n',tech_data.monthly_fee); 
            fprintf(write_file,'//Flat Price %.3f\n',tech_data.flat_price);
            if (use_flags.use_billing == 2)
                fprintf(write_file,'//First Tier Energy %.3f\n',tech_data.tier_energy);
                fprintf(write_file,'//Second Tier Price %.3f\n',tech_data.second_tier_price);
            end
        end
    end
    disp(['Back off man, I am done with ',filename,' case ',num2str(tax_ind),' of ',num2str(no_of_tax)]);
    clear test;
    clear config;
    clear config_final;
    clear phase_S_houses;
    clear load_houses;
    
    if (use_flags.use_solar~=0 ||use_flags.use_solar_res~=0 ||use_flags.use_solar_com~=0)
        if (exist('solar_residential_array','var'))
            clear solar_residential_array;
            clear solar_residential_array_parent;
        end
        
        if (exist('solar_office_array','var'))
            clear solar_office_array;
            clear solar_office_array_parent;
        end
        
        if (exist('solar_bigbox_array','var'))
            clear solar_bigbox_array;
            clear solar_bigbox_array_parent;
        end
        
        if (exist('solar_stripmall_array','var'))
            clear solar_stripmall_array;
            clear solar_stripmall_array_parent;
        end
    end
    if(use_flags.use_energy_storage ~= 0 || use_flags.use_energy_storage_res ~= 0 || use_flags.use_energy_storage_com ~= 0)
        if(exist('es_residential_array', 'var'))
            clear es_residential_array;
            clear es_residential_array_parent;
        end
        if(exist('es_office_array', 'var'))
            clear es_office_array;
            clear es_office_array_parent;
        end
        if(exist('es_bigbox_array', 'var'))
            clear es_bigbox_array;
            clear es_bigbox_array_parent;
        end
        if(exist('es_stripmall_array', 'var'))
            clear es_stripmall_array;
            clear es_stripmall_array_parent;
        end
    end
    if (use_flags.use_phev~=0)
        if (exist('phev_residential_array','var'))
            clear phev_residential_array;
        end
    end
    if (use_flags.use_ts~=0)
        if (exist('ts_residential_array','var'))
            clear ts_residential_array;
        end
        
        if (exist('ts_office_array','var'))
            clear ts_office_array;
        end
        
        if (exist('ts_bigbox_array','var'))
            clear ts_bigbox_array;
        end
        
        if (exist('ts_stripmall_array','var'))
            clear ts_stripmall_array;
        end
    end
    fclose('all');
end

disp('So tired. All done.');
%clear;
