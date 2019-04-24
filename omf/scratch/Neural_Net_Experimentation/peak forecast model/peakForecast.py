import pandas as pd
import numpy as np
import loadForecast as lf
from datetime import datetime as dt

def dispatch_strategy(df, EPOCHS=10):
    if 'dates' not in df.columns:
        df['dates'] = df.apply(
            lambda x: dt(
                int(x['year']), 
                int(x['month']), 
                int(x['day']), 
                int(x['hour'])), 
            axis=1
        ) 
    df['date'] = df.dates.dt.date
    
    # find max load for each day in d_df (day dataframe)
    d_df = pd.DataFrame()
    d_df['max_load'] = df.groupby('date')['load'].max()
    d_df['date'] = df['date'].unique().astype('datetime64')
    d_df['year'] = d_df['date'].dt.year
    d_df['month'] = d_df['date'].dt.month
    d_df['day'] = d_df['date'].dt.day

    # get the correct answers for every month
    l = []
    for y in d_df['year'].unique():
        d = d_df[d_df['year'] == y]
        l.extend(d.groupby('month')['max_load'].idxmax())
    d_df['should_dispatch'] = [(i in l) for i in d_df.index]

    # forecast
    all_X_1 = lf.makeUsefulDf(df, noise=2.5, hours_prior=24)
    all_X_2 = lf.makeUsefulDf(df, noise=4, hours_prior=48)
    all_y = df['load']

    p1, a1 = lf.neural_net_predictions(all_X_1, all_y, EPOCHS=EPOCHS)
    p2, a2 = lf.neural_net_predictions(all_X_2, all_y, EPOCHS=EPOCHS)
    p1_max = [max(p1[i:i+24]) for i in range(0, len(p1), 24)]
    p2_max = [max(p2[i:i+24]) for i in range(0, len(p2), 24)]

    # create threshold
    max_vals = {}
    for y in d_df['year'].unique()[:-1]:
        d = d_df[d_df['year'] == y]
        max_vals[y] = list(d.groupby('month')['max_load'].max())

    df_thresh = pd.DataFrame(max_vals).T
    thresholds = [None]*12
    for i in range(12):
        thresholds[i] = df_thresh[i].min()

    # make dispatch decisions
    df_dispatch = pd.DataFrame()
    this_year = d_df['year'].unique()[-1]
    df_dispatch['load'] = d_df[d_df['year'] == this_year]['max_load']
    df_dispatch['should_dispatch'] = d_df[d_df['year'] == this_year]['should_dispatch']
    df_dispatch['1-day'] = p1_max
    df_dispatch['2-day'] = p2_max
    df_dispatch['month'] = d_df['month']
    df_dispatch['threshold'] = df_dispatch['month'].apply(lambda x: thresholds[x-1])
    
    # is tomorrow above the monthly threshold?
    df_dispatch['above_threshold'] = df_dispatch['1-day'] >= df_dispatch['threshold']
    # is tomorrow higher than the prediction in two days?
    df_dispatch['2-day_lower'] = df_dispatch['2-day'] <= df_dispatch['1-day']
    # is tomorrow the highest of the month?
    highest = [-1*float('inf')]*12
    dispatch_highest = [False]*365
    zipped = zip(df_dispatch['1-day'], df_dispatch['month'], df_dispatch['load'])
    for i, (predicted_load, m, load) in enumerate(zipped):
        if predicted_load >= highest[m-1]:
            dispatch_highest[i] = True
        if load >= highest[m-1]:
            highest[m-1] = load
    df_dispatch['highest_so_far'] = dispatch_highest
    
    # dispatch if all three conditions are met
    df_dispatch['dispatch'] = (df_dispatch['highest_so_far'] & 
                               df_dispatch['2-day_lower'] & df_dispatch['above_threshold'])

    # compare correct answers
    pre = np.array(df_dispatch['dispatch'])
    ans = np.array(df_dispatch['should_dispatch'])

    return {
        'dispatch': pre,
        'should_dispatch': ans,
        'df_dispatch': df_dispatch,
        '1-day_accuracy': a1,
        '2-day_accuracy': a2,
    }

def analyze_predictions(ans, pre):
    def recall(ans, pre):
        true_positive = sum(ans & pre)
        false_negative = sum(ans & (~ pre))
        return true_positive / (true_positive + false_negative + 1e-7)
    def precision(ans, pre):
        true_positive = sum(ans & pre)
        false_positive = sum((~ ans) & pre)
        return (true_positive)/(true_positive + false_positive + 1e-7)
    def peaks_missed(ans, pre):
        return sum(ans & (~ pre))
    def unnecessary_dispatches(ans, pre):
        return sum((~ ans) & pre)

    return {
        'recall': recall(ans, pre), 
        'precision': precision(ans, pre), 
        'peaks_missed': peaks_missed(ans, pre), 
        'unnecessary_dispatches': unnecessary_dispatches(ans, pre)
    }

def confidence_dispatch(df_d, max_c=.1):
# return dispatch for given df and confidence
    confidence_dict = {}
    for c in np.linspace(0, max_c, 100):
        # we want to increase the likelihood of dispatching tomorrow
        df = df_d.copy()
        df['1-day'] *= (1+c)
        df['2-day'] *=(1-c)
        df['threshold'] *= (1-c)

        df['above_threshold'] = df['1-day'] >= df['threshold']
        df['2-day_lower'] = df['2-day'] <= df['1-day']

        highest = [-1*float('inf')]*12
        dispatch_highest = [False]*365
        zipped = zip(df['1-day'], df['month'], df['load'])
        for i, (predicted_load, m, load) in enumerate(zipped):
            if predicted_load >= highest[m-1]:
                dispatch_highest[i] = True
            if load >= highest[m-1]:
                highest[m-1] = predicted_load

        df['highest_so_far'] = dispatch_highest
        df['dispatch'] = (df['highest_so_far'] & 
                                   df['2-day_lower'] & df['above_threshold'])

        m = np.array(df['dispatch'])
        confidence_dict[c] = analyze_predictions(df_d['should_dispatch'], m)
    df_conf = pd.DataFrame(confidence_dict).T

    return df_conf

def find_lowest_confidence(df_conf):
    # what is the lowest amount of confidence that captures all peaks?
    df = df_conf.copy()
    df = df[df['peaks_missed'] == 0]
    if df.shape[0] != 0:
        return {
            'confidence': df['unnecessary_dispatches'].idxmin(), 
            'unnecessary_dispatches': df['unnecessary_dispatches'].min()
        }
    else:
        return {
            'confidence': "larger than given max interval",
            'unnecessary_dispatches': "greater than {}".format(
                df_conf['unnecessary_dispatches'].min())
        }

def main():
    df = pd.read_csv('static/testFiles/d_Texas_17yr_TempAndLoad.csv')
    d_dict = dispatch_strategy(df, EPOCHS=1)
    a_dict = analyze_predictions(d_dict['dispatch'], d_dict['should_dispatch'])
    print a_dict

if __name__ == '__main__':
    main()