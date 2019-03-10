### Description

This software generates load shapes for a given device type. Types include gas heat pump heater, resistance heater, gas heat (with fan), waterheater, electric AC, heat pump AC, electric vehicle, non defferable loads Refrigerators and freezers, a defferable loads like dryers clotheswashers. 

### Usage

Install by download (insert URL).

You need some prerequirements. Install these from (insert list of software).

Then run the simulation: `python LoadsimGLD <load_type>` where load_type is one of the following: "GasHeat", "HeatPump", "Resistance", "AC_electric", "AC_HeatPump", "Waterheater", "EV", "Refrigerator",  "Clotheswasher", "Dryer", "Freezer".

Output should look like:

![](out_power_chart1.png)
![](out_temp_chart.png)

### Advanced Usage

Change the climate data by replacing inc_climate.tmy2 with a TYM2 or TYM3 file (add link to where these are on the internet, probably NREL). 

You will need to edit the titles of some charts in LoadSimGLD.py in order for the chart titles to match exactly the climate's location. 

You can change the house energy efficiency metrics (square footage, insulation, glazing, etc.) by editing them in LoadSimGLD.py.

To change attributes of loads, you will need to open the in_super_house.glm file to change the attributes of the loads. Only the house load is defined in LoadSimGLD.py. 

There is also a inc_super_schedules.glm file where all of the load shapes are defined, if you want to change how much power a load uses and when, you will have to change this file. 

For more information on this schedule file, and to see where the default power draws were obtained from, you can check out this link https://github.com/gridlab-d/gridlab-d/blob/develop/residential/elcap2010.h

For more information on the gridlabd schedule object, check out this link http://gridlab-d.shoutwiki.com/wiki/Schedule.

For more information on gridlabd powerflow, check out this link http://gridlab-d.shoutwiki.com/wiki/Power_Flow_User_Guide.
