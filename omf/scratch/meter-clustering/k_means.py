"""
https://stackoverflow.com/questions/32525718/assign-line-colors-in-pandas
https://matplotlib.org/3.1.0/api/colors_api.html#module-matplotlib.colors - acceptable color values
https://scikit-learn.org/stable/modules/preprocessing.html#scaling-features-to-a-range
"""

import os
import numpy as np  
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt  
from sklearn.cluster import KMeans
from sklearn.preprocessing import scale
from sklearn.preprocessing import MinMaxScaler

"""
matplotlib allows hex color strings to specify color, which seems to be the easiest way to specify a color and an alpha at the same time.
"""


def get_dataframe(filename):
    """ The pickled files are implicitly already pandas dataframes """
    filepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../ami_output", filename)
    return pd.read_pickle(filepath)


def standardize_data(ary):
    # type: (ndarray) -> ndarray
    """ Data arrives in row = meter and column = datetime """
    standardized_ndarray = scale(ary, axis=1)
    return standardized_ndarray


def normalize_data(ary):
    # type: (ndarray) -> ndarray
    """ Data arrives in row = meter and column = datetime """
    ary = ary.T # get data back into row = datetime and column = meter
    norm_ary = MinMaxScaler().fit_transform(ary)
    return norm_ary.T # get data back into row = meter and column = datetime


def average_data(ary):
    # type: (ndarray) -> ndarray
    """ Data arrives in row = meter and column = datetime """
    averaged_arrays = np.zeros((len(ary), 96))
    assert len(averaged_arrays) == 736
    assert len(averaged_arrays[0]) == 96
    for k in range(len(averaged_arrays)):
        for i in range(96): # 4 * 24 = 96 measurements per day, so 96 groups, indexed [0, 95]
            group_sum = ary[k][i]
            for j in range(1, 30): # 29 days other than the first day, so iterate 1 - 29
                matching_time_idx = i + 96 * j
                group_sum += ary[k][matching_time_idx]
            averaged_arrays[k][i] = group_sum / 30
    return averaged_arrays


def labels_to_floats(labels, cluster_num):
    # type: (ndarray, int) -> list
    """
    Convert a list of labels into a list of floats according to how many clusters there were:
    - [0, 1, 2, 3, 4, 0, 1, 0, 0] -> [0, 0.25, 0.5, 0.75, 1, 0, 0.25, 0, 0]
    """
    return [x/(cluster_num - 1) for x in labels]


def plot(times, rows, km, color_clusters=False, show_centroids=False):
    # type: (list, ndarray, KMeans, Boolean, Boolean) -> None
    cluster_count = len(km.cluster_centers_)
    if color_clusters is True:
        line_colors = labels_to_floats(km.labels_, cluster_count)
    cmap = matplotlib.cm.get_cmap('viridis')
    fig = plt.figure()
    idx = 0
    for ts in rows:
        ax = fig.add_subplot()
        if color_clusters is True:
            if show_centroids is True:
                ax.plot(times, ts, color=cmap(line_colors[idx]), alpha=0.05)
            else:
                ax.plot(times, ts, color=cmap(line_colors[idx]))
        else:
            ax.plot(times, ts, color="#d9d9d9") # good
        idx += 1
    if show_centroids is True:
        idx = 0
        for c in km.cluster_centers_:
            color = idx / (cluster_count - 1)
            ax.plot(times, c, color=cmap(color)) # good
            idx += 1
    plt.show()


def run_k_means(ary, clusters):
    # type: (ndarray, int) -> KMeans
    """
    - km.cluster_centers_: a numpy.ndarray whose length is equal to the number of specified clusters.
        - Each element in this outer ndarray is an inner 1D ndarray that contains the values for all the dimensions of a particular cluster center
            - If the element is a 1D ndarray of length 2, the 1st scalar is the x-coordinate and the 2nd scalar is the y-coordinate
            - If the element is a 1D ndarray of length 10, then the 1st scalar is the 1D value , the 2nd scalar is the 2D value, ..., the 10th scalar
              is the 10D value, etc.
            - If the element is a 1D ndarray of length 2880, then the 2880th scalar is the value for the 2880 dimension
    - km.labels_: a numpy.ndarray whose length is equal to the number of labels (i.e. the number of training data objects, since each object needs to
      be assigned to a centroid label)
      - labels start at 0, not 1
    """
    # df arrives as 736 * 2880, rows = meters and columns = datetimes
    km = KMeans(n_clusters=clusters)
    km.fit(ary)
    #print(len(km.labels_)) # 736
    #print(km.labels_) # very useful
    return km


def plot_all_data(clusters, normalize=False, standardize=False):
    # df starts as 2880 * 736
    df = get_dataframe("ALGIERS_kWh_2017-06-01 00:00:00-05:00_15min_sum.pkl.gz")
    #df = df.iloc[:, 0:20] # Get all rows for the first 20 columns
    ary = df.to_numpy()
    ary = ary.T # data is transposed to 736 * 2880, set rows = meters and columns = datetimes
    if standardize is True:
        ary = standardize_data(ary)
    if normalize is True:
        ary = normalize_data(ary)
    km = run_k_means(ary, clusters)
    #plot(df.index.tolist(), ary, km, color_clusters=False, show_centroids=True) # focus on centroids
    #plot(df.index.tolist(), ary, km, color_clusters=True, show_centroids=False) # focus on clusters
    plot(df.index.tolist(), ary, km, color_clusters=True, show_centroids=True) # show both


def plot_average_data(clusters, normalize=False, standardize=False):
    # df starts as 2880 * 736
    df = get_dataframe("ALGIERS_kWh_2017-06-01 00:00:00-05:00_15min_sum.pkl.gz")
    ary = df.to_numpy()
    ary = ary.T # data is transposed to 736 * 2880, set rows = meters and columns = datetimes
    ary = average_data(ary) # average the data from 2880 measurements into 96 measurements
    if standardize is True:
        ary = standardize_data(ary)
    if normalize is True:
        ary = normalize_data(ary) 
    km = run_k_means(ary, clusters)
    #plot(df.index.tolist()[:96], ary, km, color_clusters=False, show_centroids=True) # focus on centroids
    #plot(df.index.tolist()[:96], ary, km, color_clusters=True, show_centroids=False) # focus on clusters
    plot(df.index.tolist()[:96], ary, km, color_clusters=True, show_centroids=True) # show both


if __name__ == "__main__":
    plot_all_data(4, normalize=True)
    # 8, 6, 5 is too many look how a couple of centroids are very close. 4 clusters is a little more interesting.
    #plot_average_data(4, normalize=True)