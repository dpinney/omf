import argparse
import cProfile
import matplotlib.pyplot as plt
import numpy as np
import time
from numpy import *

class VirtualBattery(object):
    """ Base class for abstraction. """
    def __init__(self, ambient_temp, capacitance, resistance, rated_power, COP, deadband, setpoint, tcl_number):
        # C :thermal capacitance
        # R : thermal resistance
        # P: rated power (kW) of each TCL
        # eta: COP
        # delta: temperature deadband
        # theta_s: temperature setpoint
        # N: number of TCL
        # ambient: ambient temperature
        self.ambient = ambient_temp
        self.C = capacitance
        self.R = resistance
        self.P = rated_power
        self.eta = COP
        self.delta = deadband
        self.theta_s = setpoint
        self.N = tcl_number

    def generate(self, participation_number, P0_number):

        """ Main calculation happens here. """
        #heuristic function of participation
        atan = np.arctan
        participation = participation_number
        P0 = P0_number

        P0[P0 < 0] = 0.0 # set negative power consumption to 0
        p_lower = self.N*participation*P0 # aggregated baseline power consumption considering participation

        p_upper = self.N*participation*(self.P - P0)
        p_upper[p_upper < 0] = 0.0 # set negative power upper bound to 0
        e_ul = self.N*participation*self.C*self.delta/2/self.eta
        return p_lower, p_upper, e_ul


class AC(VirtualBattery):
    """ Derived Class for specifically AC Virtual Battery. """
    def __init__(self, theta_a, capacitance, resistance, rated_power, COP, deadband, setpoint, tcl_number):
        super(AC, self).__init__(theta_a, capacitance, resistance, rated_power, COP, deadband, setpoint, tcl_number)

    # self.tcl_idx = tcl_idx
        self.theta_a = self.ambient  # theta_a == ambient temperature

    def generate(self):
        #heuristic function of participation
        atan = np.arctan
        # participation for AC
        Ta = np.linspace(20, 45, num=51)
        participation = (atan(self.theta_a-27) - atan(Ta[0]-27))/((atan(Ta[-1]-27) - atan(Ta[0]-27)))

        participation = np.clip(participation, 0, 1)

        #P0 for AC
        P0 = (self.theta_a - self.theta_s)/self.R/self.eta # average baseline power consumption for the given temperature setpoint

        return super(AC, self).generate(participation, P0)

class HP(VirtualBattery):
    """ Derived Class for specifically HP Virtual Battery. """
    def __init__(self, theta_a, capacitance, resistance, rated_power, COP, deadband, setpoint, tcl_number):
        super(HP, self).__init__(theta_a, capacitance, resistance, rated_power, COP, deadband, setpoint, tcl_number)

    #  self.tcl_idx = tcl_idx
        self.theta_a = self.ambient  # theta_a == ambient temperature

    def generate(self):
        #heuristic function of participation
        atan = np.arctan
        # participation for HP
        Ta = np.linspace(0, 25, num=51)
        participation = 1-(atan(self.theta_a-10) - atan(Ta[0]-10))/((atan(Ta[-1]-10) - atan(Ta[0]-10)))

        participation = np.clip(participation, 0, 1)

        #P0 for HP
        P0 = (self.theta_s - self.theta_a)/self.R/self.eta

        return super(HP, self).generate(participation, P0)

class RG(VirtualBattery):
    """ Derived Class for specifically RG Virtual Battery. """
    def __init__(self, theta_a, capacitance, resistance, rated_power, COP, deadband, setpoint, tcl_number):
        super(RG, self).__init__(theta_a, capacitance, resistance, rated_power, COP, deadband, setpoint, tcl_number)
    # self.tcl_idx = tcl_idx
        self.theta_a = self.ambient  # theta_a == ambient temperature
    def generate(self):
        #heuristic function of participation
        atan = np.arctan
        # participation for RG
        participation = np.ones(self.theta_a.shape)

        participation = np.clip(participation, 0, 1)

        #P0 for RG
        P0 = (self.theta_a - self.theta_s)/self.R/self.eta # average baseline power consumption for the given temperature setpoint

        return super(RG, self).generate(participation, P0)



class WH(VirtualBattery):
    """ Derived class for specifically Water Heater Virtual Battery. """
    N_wh = 50

    def __init__(self, theta_a, capacitance, resistance, rated_power, COP, deadband, setpoint, tcl_number,Tout, water):
        super(WH, self).__init__(theta_a, capacitance, resistance, rated_power, COP, deadband, setpoint, tcl_number)

        self.C_wh = self.C*np.ones((self.N_wh, 1))  # thermal capacitance, set in parent class
        self.R_wh = self.R*np.ones((self.N_wh, 1))  # thermal resistance
        self.P_wh = self.P*np.ones((self.N_wh, 1))   # rated power (kW) of each TCL
        self.delta_wh = self.delta*np.ones((self.N_wh, 1)) # temperature deadband
        self.theta_s_wh = self.theta_s*np.ones((self.N_wh, 1)) # temperature setpoint
        self.Tout=Tout
        self.water = water
        # self.N = self.para[6] # number of TCL

    def calculate_twat(self,tout_avg,tout_madif):
        tout_avg=tout_avg/5*9+32

        tout_madif=tout_madif/5*9

        ratio = 0.4 + 0.01 * (tout_avg - 44)

        lag = 35 - 1.0 * (tout_avg - 44)

        twat = 1*np.ones((365*24*60,1))

        for i in range(365):
              for j in range(60*24):
                    twat[i*24*60+j]= (tout_avg+6)+ratio*(tout_madif/ 2) * sin((0.986 * (i - 15 - lag) - 90)/180*3.14)

        twat=(twat-32.)/9.*5.

        return twat

    def prepare_pare_for_calculate_twat(self,tou_raw):
    
        tout_avg = sum(tou_raw)/len(tou_raw)
        
        mon=[31,28,31,30,31,30,31,31,30,31,30,31]
        
        mon_ave=1*np.ones((12,1))

        mon_ave[1]=sum(tou_raw[0:mon[1]*24])/mon[1]/24
        
        stop=mon[1]*24
        
        for idx in range(1,len(mon)):
             mon_ave[idx]=sum(tou_raw[stop:stop+mon[idx]*24])/mon[idx]/24;

        tou_madif=max(mon_ave)- min(mon_ave) 

        return tout_avg, tou_madif
    
    
    def generate(self):
        # theta_a is the ambient temperature
        # theta_a = (72-32)*5.0/9*np.ones((365, 24*60))   # This is a hard-coded 72degF, converted to degCel
        theta_a = self.ambient#*np.ones((365, 24*60))  # theta_a == ambient temperature
        #nRow, nCol = theta_a.shape
        nRow, nCol = 365, 24*60
        theta_a = np.reshape(theta_a, [nRow*nCol, 1])
                        
        Tout1min= np.zeros((size(theta_a)));
        for i in range(len(self.Tout)):
            theta_a[i]= (self.Tout[i]+self.ambient[i])/2; # CHANGED THIS

        # h is the model time discretization step in seconds
        h = 60
        #T is the number of time step considered, i.e., T = 365*24*60 means a year
        # with 1 minute time discretization
        T = len(theta_a)
        tou_avg,maxdiff=self.prepare_pare_for_calculate_twat(self.Tout)
        twat=self.calculate_twat(tou_avg,maxdiff);
        # print twat
        
        # theta_lower is the temperature lower bound
        theta_lower_wh = self.theta_s_wh - self.delta_wh/2.0
        # theta_upper is the temperature upper bound
        theta_upper_wh = self.theta_s_wh + self.delta_wh/2.0

        # m_water is the water draw in unit of gallon per minute
        m_water = self.water#np.genfromtxt("Flow_raw_1minute_BPA.csv", delimiter=',')[1:, 1:]
        where_are_NaNs = isnan(m_water)
        m_water[where_are_NaNs] = 0	

        m_water = m_water *0.00378541178*1000/h

        m_water_row, m_water_col = m_water.shape
        water_draw = np.zeros((m_water_row, int(self.N_wh)))

        for i in range(int(self.N_wh)):
            k = np.random.randint(m_water_col)
            water_draw[:, i] = np.roll(m_water[:, k], (1, np.random.randint(-14, 1))) + m_water[:, k] * 0.1 * (np.random.random() - 0.5)
#            k = m_water_col - 1
            # print(k)
            # raise(ArgumentError, "Stop here")
#            water_draw[:, i] = m_water[:, k]

        first = -(
            np.matmul(theta_a, np.ones((1, self.N_wh)))
            - np.matmul(np.ones((T, 1)), self.theta_s_wh.transpose())
        )
    #    print(np.argwhere(np.isnan(first)))
        second = np.matmul(np.ones((T, 1)), self.R_wh.transpose())
    #    print(np.argwhere(np.isnan(second)))
        Po = (
            first
            / second
            - 4.2
            * np.multiply(water_draw, (55-32) * 5/9.0 - np.matmul(np.ones((T, 1)), self.theta_s_wh.transpose()))
        )
    #    print(water_draw.shape)
    #    print(len(water_draw[:1]))
        # Po_total is the analytically predicted aggregate baseline power
        Po_total = np.sum(Po, axis=1)
        upper_limit = np.sum(self.P_wh, axis=0)

    #    print(np.argwhere(np.isnan(water_draw)))
        Po_total[Po_total > upper_limit[0]] = upper_limit


        # theta is the temperature of TCLs
        theta = np.zeros((self.N_wh, T))
        theta[:, 0] = self.theta_s_wh.reshape(-1)

        # m is the indicator of on-off state: 1 is on, 0 is off
        m = np.ones((self.N_wh, T))
        m[:int(self.N_wh*0.8), 0] = 0

        for t in range(T - 1):
            theta[:, t+1] = (
                (1 - h/(self.C_wh * 3600) / self.R_wh).reshape(-1)
                * theta[:, t]
                + (h / (self.C_wh * 3600) / self.R_wh).reshape(-1)
                * theta_a[t]
                + ((h/(self.C_wh * 3600))*self.P_wh).reshape(-1)*m[:, t]
            )

            m[theta[:, t+1] > (theta_upper_wh).reshape(-1), t+1] = 0
            m[theta[:, t+1] < (theta_lower_wh).reshape(-1), t+1] = 1

            m[(theta[:, t+1] >= (theta_lower_wh).reshape(-1)) & (theta[:, t+1] <= (theta_upper_wh).reshape(-1)), t+1] = m[(theta[:, t+1] >= (theta_lower_wh).reshape(-1)) & (theta[:, t+1] <= (theta_upper_wh).reshape(-1)), t]


        theta[:, 0] = theta[:, -1]
        m[:, 0] = m[:, -1]

        # Po_total_sim is the predicted aggregate baseline power using simulations
        Po_total_sim = np.zeros((T, 1))
        Po_total_sim[0] = np.sum(m[:, 0]*(self.P_wh.reshape(-1)))

        for t in range(T - 1):
            # print t
            theta[:, t+1] = (1 - h/(self.C_wh * 3600)/self.R_wh).reshape(-1) * theta[:, t] + (h/(self.C_wh * 3600)/self.R_wh).reshape(-1)*theta_a[t] + (h/(self.C_wh*3600)).reshape(-1)*m[:, t]*self.P_wh.reshape(-1) + h*4.2*water_draw[t, :].transpose() * (twat[t] -theta[:, t]) / ((self.C_wh*3600).reshape(-1))
            m[theta[:, t+1] > (theta_upper_wh).reshape(-1), t+1] = 0
            m[theta[:, t+1] < (theta_lower_wh).reshape(-1), t+1] = 1
            m[(theta[:, t+1] >= (theta_lower_wh).reshape(-1)) & (theta[:, t+1] <= (theta_upper_wh).reshape(-1)), t+1] = m[(theta[:, t+1] >= (theta_lower_wh).reshape(-1)) & (theta[:, t+1] <= (theta_upper_wh).reshape(-1)), t]
            Po_total_sim[t+1] = np.sum(m[:, t+1] * self.P_wh.reshape(-1))

        index_available = np.ones((self.N_wh, T))

        for t in range(T - 1):
            index_available[(theta[:, t] < (theta_lower_wh-0.5).reshape(-1)) | (theta[:, t] > (theta_upper_wh+0.5).reshape(-1)), t] = 0

        # Virtual battery parameters
        p_upper_wh1 = np.sum(self.P_wh) - Po_total_sim
        p_lower_wh1 = Po_total_sim
        e_ul_wh1 = np.sum((np.matmul(self.C_wh, np.ones((1, T))) * np.matmul(self.delta_wh, np.ones((1, T))) / 2 * index_available).transpose(), axis=1)

        # calculate hourly average data from minute output for power
        p_upper_wh1 = np.reshape(p_upper_wh1, [8760,60])			
        p_upper_wh = np.mean(p_upper_wh1, axis=1)*float(self.N)/float(self.N_wh)       
        p_lower_wh1 = np.reshape(p_lower_wh1, [8760,60])
        p_lower_wh = np.mean(p_lower_wh1, axis=1)*float(self.N)/float(self.N_wh)
        # extract hourly data from minute output for energy
        e_ul_wh = e_ul_wh1[59:len(e_ul_wh1):60]*float(self.N)/float(self.N_wh)
        return p_lower_wh, p_upper_wh, e_ul_wh




