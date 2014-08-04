
# coding: utf-8

# In[2]:

#Basic module calls and function set-up to pop-out fig to zoom and etc.
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
get_ipython().magic(u'matplotlib inline')


# In[26]:

#This plots weather_climate data
jal=[x*0 for x in range(30)]
date5,jal[1],jal[2],jal[3],jal[4],jal[5],jal[6]= np.loadtxt('C:\Users\gour967\Documents\GitHub\omf\omf\weather_climate_data.csv',
                                      comments='#',delimiter=',',
                                      unpack=True,
                                      converters={0: lambda d5: mdates.strpdate2num('%Y-%m-%d %H:%M:%S')(d5[:-4])})
plt.subplot(6,1,1)
[plt.plot_date(date5,jal[1],fmt='-',color='green',label='Temperature')]
plt.legend(loc='best', numpoints=1)
plt.title('Temperature')
plt.xlabel('Time')
plt.ylabel('Temperature [degF]')

plt.subplot(6,1,2)
[plt.plot_date(date5,jal[2],fmt='-',color='brown',label='Wind Speed')]
plt.legend(loc='best', numpoints=1)
plt.title('Wind Speed')
plt.xlabel('Time')
plt.ylabel('Wind Speed [mph]')

plt.subplot(6,1,3)
[plt.plot_date(date5,jal[3],fmt='-',color='purple',label='Humidity')]
plt.legend(loc='best', numpoints=1)
plt.title('Humidity')
plt.xlabel('Time')
plt.ylabel('Humidity [%]')

plt.subplot(6,1,4)
[plt.plot_date(date5,jal[4],fmt='-',color='red',label='Solar Direct')]
plt.legend(loc='best', numpoints=1)
plt.title('Solar Direct')
plt.xlabel('Time')
plt.ylabel('Solar Direct [W/sf]')

plt.subplot(6,1,5)
[plt.plot_date(date5,jal[5],fmt='-',color='blue',label='Solar Diffuse')]
plt.legend(loc='best', numpoints=1)
plt.title('Solar Diffuse')
plt.xlabel('Time')
plt.ylabel('Solar Diffuse [W/sf]')

plt.subplot(6,1,6)
[plt.plot_date(date5,jal[6],fmt='-',color='black',label='Solar Global')]
plt.legend(loc='best', numpoints=1)
plt.title('Solar Global')
plt.xlabel('Time')
plt.ylabel('Solar Global [W/sf]')

plt.gcf().set_size_inches(18, 36)
plt.savefig('weather_climate_data.png')#,dpi=300
#plt.clf()


# In[25]:

#This plots weather_tripmeter_energy_consumed, max min avg voltage data
val=[x*0 for x in range(50)]
#file_name=raw_input('Enter the .csv file name:')
date,val[1],val[2],val[3],val[4],val[5],val[6],val[7],val[8]= np.loadtxt('C:\Users\gour967\Documents\GitHub\omf\omf\weather_triplex_meter_all.csv',
                                                                                        comments='#',
                                                                                        delimiter=',',
                                                                                        unpack=True,
                                                                                        converters={0:lambda d: mdates.strpdate2num('%Y-%m-%d %H:%M:%S')(d[:-4])})


plt.subplot(4,1,1)
[plt.plot_date(date,val[x],fmt='-',label='Voltage_'+str(x)) for x in range(1,3)]
plt.legend(loc='best', numpoints=1)
plt.title('Triplex meters Max Voltage')
plt.xlabel('Time')
plt.ylabel('Voltage (V)')

plt.subplot(4,1,2)
[plt.plot_date(date,val[x],fmt='-',label='Voltage_'+str(x-2)) for x in range(3,5)]
plt.legend(loc='best', numpoints=1)
plt.title('Triplex meters Avg Voltage')
plt.xlabel('Time')
plt.ylabel('Voltage (V)')

plt.subplot(4,1,3)
[plt.plot_date(date,val[x],fmt='-',label='Voltage_'+str(x-4)) for x in range(5,7)]
plt.legend(loc='best', numpoints=1)
plt.title('Triplex meters Min Voltage')
plt.xlabel('Time')
plt.ylabel('Voltage (V)')

plt.subplot(4,1,4)
[plt.plot_date(date,val[7]/1000,fmt='-',label='Real Energy')]
[plt.plot_date(date,val[8]/1000,fmt='-',label='Reactive Energy')]
plt.legend(loc='best', numpoints=1)
plt.title('Energy Consumed by Loads')
plt.xlabel('Time')
plt.ylabel('Energy (kWh)')

plt.gcf().set_size_inches(18, 24)
plt.savefig('weather_max_min_avg_volt.png')#,dpi=300
#plt.clf()


# In[27]:

#This plots regulator power related data-power into feeder, powerfactor, power losses
bal=[x*0 for x in range(50)]
#file_name=raw_input('Enter the .csv file name:')
date1,bal[1],bal[2],bal[3],bal[4]= np.loadtxt('C:\Users\gour967\Documents\GitHub\omf\omf\weather_regulator_power_data.csv',
                                                                                        comments='#',
                                                                                        delimiter=',',
                                                                                        unpack=True,
                                                                                        converters={0:lambda d1: mdates.strpdate2num('%Y-%m-%d %H:%M:%S')(d1[:-4])})
 
plt.subplot(2,1,1)
[plt.plot_date(date1,bal[1]/1000,fmt='-',color='brown',label='Power Flow into Feeder')]
plt.legend(loc='best', numpoints=1)
plt.title('Power Flow into Feeder')
plt.xlabel('Time')
plt.ylabel('Power (kW)')

plt.subplot(2,1,2)
[plt.plot_date(date1,bal[4],fmt='-',color='green',label='Substation Power Factor')]
plt.legend(loc='best', numpoints=1)
plt.title('Substation Power Factor')
plt.xlabel('Time')
plt.ylabel('Substation Power Factor')

plt.gcf().set_size_inches(18, 12)
plt.savefig('weather_@regulator_power_data.png')#,dpi=300
#plt.clf()


# In[22]:

#This plots focuses on net energy losses
hal=[x*0 for x in range(20)]
#file_name=raw_input('Enter the .csv file name:')
date2,hal[1],hal[2],hal[3]= np.loadtxt('C:\Users\gour967\Documents\GitHub\omf\omf\weather_regulator_meter_energy.csv',
                                                                                        comments='#',
                                                                                        delimiter=',',
                                                                                        unpack=True,
                                                                                        converters={0:lambda d2: mdates.strpdate2num('%Y-%m-%d %H:%M:%S')(d2[:-4])})
plt.subplot(3,1,1)
[plt.plot_date(date2,hal[1]/1000,fmt='-',color='red',label='Energy at Substation')]
plt.legend(loc='best', numpoints=1)
plt.title('Energy at Substation')
plt.xlabel('Time')
plt.ylabel('Energy (kWh)')

plt.subplot(3,1,2)
[plt.plot_date(date2,hal[2]/1000,fmt='-',color='green',label='Energy consumed by loads')]
plt.legend(loc='best', numpoints=1)
plt.title('Energy Consumed by Loads')
plt.xlabel('Time')
plt.ylabel('Energy (kWh)')

plt.subplot(3,1,3)
[plt.plot_date(date2,hal[3]/1000,fmt='-',color='blue',label='Energy consumed by Losses')]
plt.legend(loc='best', numpoints=1)
plt.title('Energy Consumed by Losses')
plt.xlabel('Time')
plt.ylabel('Energy (kWh)')#,fontsize=16

#plt.tight_layout()
plt.gcf().set_size_inches(18, 18)
plt.savefig('weather_energy_losses_net.png')#,dpi=300
#plt.clf()


# In[ ]:



