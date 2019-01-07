USAGE
1. Directly open regulator_meter_plots.html to see plots and script [deprecated].
2. weather.py, weather.pyc used to generate weatheryearDCA.csv and called in IEEE_quickhouse.glm
3. python script used to generate these plots is regulator_meter_plots.py.
	NOTE: to enable X Server and pop out image, comment %matplotlib inline
4. Separate plots are saved a .png

TODO
XXX Move scapeAsos.py in to weather.py.
OOO Get aGosedWeather.py running its tests.
OOO Pull the weather data from weatherNoaaHourly.py instead of weather.py.
OOO Update climateChange function in web.py
OOO Factor weather.py out of all other models.