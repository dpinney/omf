import pandas as pd
from scipy.stats import zscore
import pickle
import time
import numpy as np
from sklearn.linear_model import LinearRegression
import os
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import loadForecast as lf

def dispatch_strategy(df, epochs):
    # date, max_load
    df['date'] = df.dates.dt.date
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

    p1, a1 = lf.neural_net_predictions(all_X_1, all_y, EPOCHS=epochs)
    p2, a2 = lf.neural_net_predictions(all_X_2, all_y, EPOCHS=epochs)
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
    this_year = max(list(d_df.year.unique()))
    df_dispatch['load'] = d_df[d_df['year'] == this_year]['max_load']
    df_dispatch['should_dispatch'] = d_df[d_df['year'] == this_year]['should_dispatch']
    df_dispatch['1-day'] = p1_max
    df_dispatch['2-day'] = p2_max
    df_dispatch['month'] = d_df['month']
    df_dispatch['threshold'] = df_dispatch['month'].apply(lambda x: thresholds[x-1])
    df_dispatch['above_threshold'] = df_dispatch['1-day'] >= df_dispatch['threshold']
    df_dispatch['2-day_lower'] = df_dispatch['2-day'] <= df_dispatch['1-day']

    highest = [-1*float('inf')]*12
    dispatch_highest = [False]*365
    for i, (l, m) in enumerate(zip(df_dispatch['1-day'], df_dispatch['month'])):
        if l >= highest[m-1]:
            dispatch_highest[i] = True
            highest[m-1] = l

    df_dispatch['highest_so_far'] = dispatch_highest
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
        '2-day_accuracy': a2
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

def main():
    df = pd.read_csv('hourly/NCENT.csv', parse_dates=['dates'])
    df['year'] = df['dates'].dt.year
    df['month'] = df['dates'].dt.month
    df['day'] = df['dates'].dt.day
    df['hour'] = df['dates'].dt.hour
    d_dict = dispatch_strategy(df, epochs=1)
    a_dict = analyze_predictions(d_dict['dispatch'], d_dict['should_dispatch'])
    print(a_dict)

if __name__ == '__main__':
    main()