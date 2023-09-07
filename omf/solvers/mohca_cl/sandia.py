import numpy as np
import pandas as pd
from datetime import datetime


# insert algo here.

def hosting_cap(input_csv_path, output_csv_path):
  
  
  df_input=pd.read_csv(input_csv_path) #reading the data file
##Organize Data
##reading timestamps which works offline. There is a bug in pandas that provides error in the CI test for using astype
  #timestamp = df_input.datetime.astype(np.datetime64)
  #hourOfDay = timestamp.dt.hour
  
 ##alternative method to read timestamp
  hours=[]
  for iii in range(len(df_input)):
      ind_hours=int(datetime.strptime(df_input.datetime[iii],'%Y-%m-%dT%H:%Mz').strftime('%H'))
      hours.append(ind_hours)
  hourOfDay=pd.Series(hours)
  isDaylight = (hourOfDay>=9) & (hourOfDay<15) ##Only considering the hours between 9 AM - 3 PM

  
  ##reading customer ids and number of customers
  bus_list=df_input['busname'].unique() ##list of buses/customers
  no_of_buses=len(bus_list)
  data_all=[] ##storing data for all buses
  for ii in range(no_of_buses):
    df_filtered=df_input[df_input['busname']==bus_list[ii]]


    df_modified=pd.DataFrame() #making a new dataframe to make adjustments and include other necessary variables to run the algorithm
    #sign convention: negative for load, positive for PV injections
    df_modified['P'] = -1*df_filtered['kw_reading']
    df_modified['Q'] = -1*df_filtered['kvar_reading']
    df_modified['V'] = df_filtered['v_reading']
    df_modified['S'] = -1*np.sqrt(df_modified['P']**2+df_modified['Q']**2)
    df_modified['PF'] = df_modified['P']/df_modified['S']


    ##code to select a vbase
    vbase_options = pd.DataFrame({'Option_1':[120]*len(df_modified),'Option_2':[240]*len(df_modified)})
    vbase_diff=pd.DataFrame({'Option_1_diff':abs(df_filtered['v_reading']-vbase_options['Option_1'].values),'Option_2_diff':abs(df_filtered['v_reading']-vbase_options['Option_2'].values)})
    index_val=vbase_diff.idxmin(axis=1)

    Vfinal=[]
    for i in range(df_modified.index[0],df_modified.index[-1]+1):
        if index_val[i]=='Option_1_diff':
            Vbase=120
        else:
            Vbase=240
        Vfinal.append(Vbase)
    df_modified['Vbase']=Vfinal


    #Calcualte deltas
    df_modified['Pdiff'] = df_modified['P'].diff()
    df_modified['Qdiff'] = df_modified['Q'].diff()
    df_modified['Vdiff'] = df_modified['V'].diff()
    df_modified['Sdiff'] = df_modified['S'].diff()
    df_modified['PFdiff'] =abs(df_modified['PF'].diff())


  ##Fit based on P and Q
  ##only fit to time points with large load and voltage changes
    filter_1= (df_modified.Pdiff>abs(df_modified.Pdiff).quantile(.25)) | (df_modified.Pdiff<-abs(df_modified.Pdiff).quantile(.25)) #only large changes in P
    filter_2= (df_modified.PFdiff>abs(df_modified.PFdiff).quantile(.10)) | (df_modified.PFdiff<-abs(df_modified.PFdiff).quantile(.10)) & (filter_1) #only large changes in PF
    filter_3= (df_modified.Vdiff<abs(df_modified.Vdiff).quantile(.99)) & (df_modified.Vdiff>-abs(df_modified.Vdiff).quantile(.99)) & (filter_2); #remove large dV outliers



  ##linear fit (bias term included)

    PQ_combined=pd.concat([df_modified.Pdiff[filter_3],df_modified.Qdiff[filter_3]],axis=1)

    from sklearn import linear_model
    fPQ=linear_model.LinearRegression(fit_intercept=True)
    fPQ.fit(PQ_combined,df_modified.Vdiff[filter_3]) ###linear fit (V = p00 + p10*P + p01*Q)

    sigma_P = fPQ.coef_[0]


  ##Fit only based on S kva
  ##only fit to time points with large load and voltage changes
    filter_4 = (df_modified.Sdiff>abs(df_modified.Sdiff).quantile(.50)) | (df_modified.Sdiff<-abs(df_modified.Sdiff).quantile(.50)) ##only large changes in P
    filter_5 = (df_modified.Vdiff<abs(df_modified.Vdiff).quantile(.95)) & (df_modified.Vdiff>-abs(df_modified.Vdiff).quantile(.95)) & filter_4; ##remove large dV outliers



    fS = np.polyfit(df_modified.Sdiff[filter_5], df_modified.Vdiff[filter_5], deg=1) #creates a linear fit (V = p0 + p1*S)
    sigma_S = fS[0]

  ##Select Sensitivity Coefficient
    badFit = (abs(sigma_P-sigma_S)/abs(sigma_S))*100 > 30 #difference between estimates is more than X percent

    if badFit==True:
        sigma_Final = sigma_S
    else:
        sigma_Final = sigma_P


  ##Calculate kW_max
    df_modified['kW_max'] = (1.05*df_modified['Vbase'] - df_filtered['v_reading'])/sigma_Final


  ##Calculate HC
    HC_Scenario2 = min(df_modified.kW_max[isDaylight]); 
    if HC_Scenario2<0:
        HC_Scenario2=0  ##set any negative HCs to 0


  ##Output CSV File of Results
  ##rename variables for readability
    HC_kW = HC_Scenario2 
    MeterID = bus_list[ii]

    data = [MeterID, HC_kW]
    data_all.append(data)
  HC_Results=pd.DataFrame(data_all,index=range(no_of_buses),columns=['busname','kW_hostable'])




  return(HC_Results,HC_Results.to_csv(output_csv_path))  # showing results and file transferring to CSV format


def sanity_check(model_based_result,model_free_result):
    df_model_based=pd.read_csv(model_based_result)
    df_model_free=pd.read_csv(model_free_result)
    Error_percentage=((abs(df_model_based['kW_hostable']-df_model_free['kW_hostable']))/df_model_based['kW_hostable'])*100

    if (Error_percentage.any() <= 50):
        x= ('The model free result is correct')
    else:
        x= ('The model free result is incorrect')
    return (print(x))
