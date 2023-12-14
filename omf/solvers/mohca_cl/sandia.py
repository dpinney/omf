import numpy as np
import pandas as pd
from datetime import datetime
from sklearn import linear_model


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

    # Create mask for missing indices.  A missing value any any field in df_modified will cause that whole index to be eliminated
    mask = np.squeeze(np.ones((1,df_modified.shape[0]),dtype=bool))
    keyList = list(df_modified.keys())
    for colCtr in range(0,len(keyList)):
        currKey = keyList[colCtr]
        currValues = np.array(df_modified[currKey],dtype=float)
        mask = mask & ~np.isnan(currValues)
    
    # Mask off any indices with missing values from the df_modified dataframe
    df_modMissFiltered = pd.DataFrame()
    for colCtr in range(0,len(keyList)):
        currKey = keyList[colCtr]
        df_modMissFiltered[currKey] = df_modified[currKey][mask]
        
    # mask of any indices with missing values from the df_filtered dataframe
    keyList2 = list(df_filtered.keys())
    df_missFiltered = pd.DataFrame()
    for colCtr in range(0,len(keyList2)):
        currKey = keyList2[colCtr]
        df_missFiltered[currKey] = df_filtered[currKey][mask]
    
    #Check if a large number of datapoints were elminated
    # It might be best to move this check to a pre-processing step
    numDatapoints = df_missFiltered.shape[0]
    if numDatapoints < 200:
        print('Warning!  A large number of datapoints were eliminated due to missing data.  ' + str(numDatapoints) + ' datapoints remain.')

    ##Fit based on P and Q
    ##only fit to time points with large load and voltage changes
    filter_1= (df_modMissFiltered.Pdiff>abs(df_modMissFiltered.Pdiff).quantile(.25)) | (df_modMissFiltered.Pdiff<-abs(df_modMissFiltered.Pdiff).quantile(.25)) #only large changes in P
    filter_2= (df_modMissFiltered.PFdiff>abs(df_modMissFiltered.PFdiff).quantile(.10)) | (df_modMissFiltered.PFdiff<-abs(df_modMissFiltered.PFdiff).quantile(.10)) & (filter_1) #only large changes in PF
    filter_3= (df_modMissFiltered.Vdiff<abs(df_modMissFiltered.Vdiff).quantile(.99)) & (df_modMissFiltered.Vdiff>-abs(df_modMissFiltered.Vdiff).quantile(.99)) & (filter_2); #remove large dV outliers

    ##linear fit (bias term included)

    PQ_combined=pd.concat([df_modMissFiltered.Pdiff[filter_3],df_modMissFiltered.Qdiff[filter_3]],axis=1)

    fPQ=linear_model.LinearRegression(fit_intercept=True)
    fPQ.fit(PQ_combined,df_modMissFiltered.Vdiff[filter_3]) ###linear fit (V = p00 + p10*P + p01*Q)

    sigma_P = fPQ.coef_[0]

    ##Fit only based on S kva
    ##only fit to time points with large load and voltage changes
    filter_4 = (df_modMissFiltered.Sdiff>abs(df_modMissFiltered.Sdiff).quantile(.50)) | (df_modMissFiltered.Sdiff<-abs(df_modMissFiltered.Sdiff).quantile(.50)) ##only large changes in P
    filter_5 = (df_modMissFiltered.Vdiff<abs(df_modMissFiltered.Vdiff).quantile(.95)) & (df_modMissFiltered.Vdiff>-abs(df_modMissFiltered.Vdiff).quantile(.95)) & filter_4; ##remove large dV outliers

    fS = np.polyfit(df_modMissFiltered.Sdiff[filter_5], df_modMissFiltered.Vdiff[filter_5], deg=1) #creates a linear fit (V = p0 + p1*S)
    sigma_S = fS[0]

    ##Select Sensitivity Coefficient
    badFit = (abs(sigma_P-sigma_S)/abs(sigma_S))*100 > 30 #difference between estimates is more than X percent

    if badFit==True:
        sigma_Final = sigma_S
    else:
        sigma_Final = sigma_P

    ##Calculate kW_max
    df_modMissFiltered['kW_max'] = (1.05*df_modMissFiltered['Vbase'] - df_missFiltered['v_reading'])/sigma_Final

    ##Calculate HC
    HC_Scenario2 = min(df_modMissFiltered.kW_max[isDaylight]); 
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
