"""
https://stackoverflow.com/questions/32525718/assign-line-colors-in-pandas
https://matplotlib.org/3.1.0/api/colors_api.html#module-matplotlib.colors - acceptable color values
https://scikit-learn.org/stable/modules/preprocessing.html#scaling-features-to-a-range
"""


import os, datetime, csv
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


#############################
### Calculation functions ###
#############################


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
    # df arrives as 736 * 2880 or 736 * 96 or 736 * 192. rows = meters and columns = datetimes
    assert len(ary) == 736 and (len(ary[0]) == 2880 or len(ary[0]) == 96 or len(ary[0]) == 192)
    km = KMeans(n_clusters=clusters)
    km.fit(ary)
    #print(len(km.labels_)) # 736
    #print(km.labels_) # very useful
    return km


def calculate_absolute_deviation(t_series, cluster):
    # Data arrives in row = meter and column = datetime
    """
    Calculate the absolute deviation of a time series from its cluster.

    :param t_series: a sequence of y values from a time series
    :type t_series: ndarray
    :param cluster: a sequence of y values from a time series cluster
    :type cluster: ndarray
    :return: the absolute deviation of the time series from the cluster
    :rtype: float
    """
    assert isinstance(t_series, np.ndarray) and isinstance(cluster, np.ndarray)
    assert len(t_series) == len(cluster)
    return np.sum(np.absolute(t_series - cluster))


# Need to test this
def calculate_absolute_deviations(meter_ids, meters, cluster_centers, labels):
    """
    :type meter_ids: list
    :type meters: ndarray
    :type cluster_centers: ndarray
    :type labels: ndarray
    :rtype: list
    """
    # Also calclate within-cluster z-score?
    assert len(meter_ids) == 736 and len(meters) == 736 and len(labels) == 736
    assert len(meters[0]) == 2880 or len(meters[0]) == 96
    csv_data = []
    abs_dev_by_cluster = {key:[] for key in range(len(cluster_centers))}
    for m_idx in range(len(meters)):
        cluster_idx = labels[m_idx]
        abs_dev = calculate_absolute_deviation(meters[m_idx], cluster_centers[cluster_idx])
        abs_dev_by_cluster[cluster_idx].append(abs_dev)
        csv_data.append([meter_ids[m_idx], cluster_idx, abs_dev])
    # Iterate over each list that contains the absolute deviation of each time series from its cluster, and calculate the standard deviation
    std_by_cluster = {key: np.std(abs_dev_by_cluster[key]) for key in abs_dev_by_cluster }
    # Iterate over each list that contains the absolute deviation of each time series from its cluster, and calculate the mean
    mean_by_cluster = {key: np.mean(abs_dev_by_cluster[key]) for key in abs_dev_by_cluster}
    for row in csv_data:
        z_score = (row[2] - mean_by_cluster[row[1]]) / std_by_cluster[row[1]]
        row.append(z_score)
    return csv_data


#def calculate_standard_score()


def get_daily_averaged_dataframe(df):
    """Data arrives in row = meter and column = Timestamp format."""
    def grouping_function(dt):
        dt = dt.to_pydatetime().replace(tzinfo=None)
        return str(dt.hour) + ":" + str(dt.minute)
    gb = df.groupby(grouping_function, axis=1, sort=False)
    return gb.mean()


def get_weekday_weekend_averaged_dataframe(df):
    """
    Data arrives in row = meter and column = Timestamp format. If you look at a calendar for June 2017, you will see that the weekends fall on days
    3-4, 10-11, 17-18, and 24-25 and weekdays fall on the other days.
    """
    def grouping_function(dt):
        dt = dt.to_pydatetime().replace(tzinfo=None)
        weekdays = [1, 2]
        weekdays.extend(range(5, 10))
        weekdays.extend(range(12, 17))
        weekdays.extend(range(19, 24))
        weekdays.extend(range(26, 31))
        if dt.day in weekdays:
            group_name = "weekday"
        else:
            group_name = "weekend"
        group_name += "-" + str(dt.hour) + ":" + str(dt.minute)
        return group_name
    gb = df.groupby(grouping_function, axis=1, sort=False)
    #print(len(gb)) # 96 * 2 = 192
    #print(gb.groups[list(gb.groups)[0]]) # DatetimeIndex of Timestamps for 22 different days at 12 am
    #print()
    #print(df.loc[gb.groups[list(gb.groups)[0]], df.columns.tolist()[0]]) # Weekdays at 12 am for first meter
    #print()
    #print(gb.mean().iloc[:, 0].to_string()) # All averaged values for first meter. They are NOT sorted correctly.
    # This DataFrame no longer has datetime index labels. Instead each index label is a group name.
    #print(gb.mean().index.tolist()[0]) # weekday-0:0
    #print(gb.mean().columns.tolist()[0]) # <meter header>
    return gb.mean()


#########################
### Utility functions ###
#########################


def get_dataframe(filename):
    """ The pickled files are implicitly already pandas dataframes """
    filepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../ami_output", filename)
    return pd.read_pickle(filepath)


def standardize_data(ary):
    """ Data arrives in row = meter and column = datetime """
    assert isinstance(ary, np.ndarray) and len(ary) == 736
    standardized_ndarray = scale(ary, axis=1)
    return standardized_ndarray


def normalize_data(ary):
    """ Data arrives in row = meter and column = datetime """
    assert isinstance(ary, np.ndarray) and len(ary) == 736
    ary = ary.T # get data back into row = datetime and column = meter
    norm_ary = MinMaxScaler().fit_transform(ary)
    return norm_ary.T # get data back into row = meter and column = datetime


def write_tseries_to_cluster_fit_csv(rows, filename, cluster_num, standardize=False, normalize=False, daily_avg=False):
    if standardize:
        filename += "-standardized"
    if normalize:
        filename += "-normalized"
    if daily_avg:
        filename += "-dailyaveraged"
    filename += "-{}cluster-fit.csv".format(cluster_num)
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def plot_specific_meters(times, rows, km, meter_indexes, title=None, x_label=None, y_label=None):
    """
    Get rows of all meter data and highlight specific meters.
    """
    color_floats = get_colormap_line_color_floats(km)
    cmap = matplotlib.cm.get_cmap('viridis')
    fig = plt.figure()
    ax = fig.add_subplot()
    clusters_to_show = []
    idx = 0
    for ts in rows:
        if idx in meter_indexes:
            # We want to examine particular meters, so emphasize them in the graph
            ax.plot(times, ts, color=cmap(color_floats[idx]), alpha=0.35)
            cluster_id = km.labels_[idx]
            if cluster_id not in clusters_to_show:
                clusters_to_show.append(cluster_id)
        else:
            # We aren't interested in this meter
            #ax.plot(times, ts, color="#d9d9d9", alpha=0.05)
            pass
        idx += 1
    for cluster_id in clusters_to_show:
        color_float = cluster_id / (len(km.cluster_centers_) - 1)
        cluster_centroid = km.cluster_centers_[cluster_id]
        ax.plot(times, cluster_centroid, color=cmap(color_float))
    set_axes_labels_and_show_graph(times, ax, title, x_label, y_label)


def plot_all_meters(times, rows, km, color_clusters=False, show_centroids=False, title=None, x_label=None, y_label=None):
    # type: (list, ndarray, KMeans, Boolean, Boolean, str) -> None
    color_floats = get_colormap_line_color_floats(km)
    cmap = matplotlib.cm.get_cmap('viridis')
    fig = plt.figure()
    ax = fig.add_subplot()
    idx = 0
    for ts in rows:
        if color_clusters is True:
            if show_centroids is True:
                ax.plot(times, ts, color=cmap(color_floats[idx]), alpha=0.05)
            else:
                ax.plot(times, ts, color=cmap(color_floats[idx]))
        else:
            ax.plot(times, ts, color="#d9d9d9")
        idx += 1
    if show_centroids is True:
        idx = 0
        for c in km.cluster_centers_:
            color = idx / (len(km.cluster_centers_) - 1)
            ax.plot(times, c, color=cmap(color))
            idx += 1
    set_axes_labels_and_show_graph(times, ax, title, x_label, y_label)


def get_colormap_line_color_floats(km):
    # type: (ndarray, int) -> list
    """
    Convert a list of labels into a list of floats according to how many clusters there were:
    - [0, 1, 2, 3, 4, 0, 1, 0, 0] -> [0, 0.25, 0.5, 0.75, 1, 0, 0.25, 0, 0]
    """
    cluster_count = len(km.cluster_centers_)
    return [cluster_id / (cluster_count - 1) for cluster_id in km.labels_]


def set_axes_labels_and_show_graph(times, ax, title=None, x_label=None, y_label=None):
    # type: (list, Axes, str, str, str) -> None
    if len(times) <= 192:
        locator = matplotlib.dates.HourLocator()
        #fmt = matplotlib.dates.DateFormatter("%H:%M")
        fmt = matplotlib.dates.DateFormatter("%H")
    else:
        locator = matplotlib.dates.DayLocator()
        fmt = matplotlib.dates.DateFormatter("%a")
    ax.get_xaxis().set_major_locator(locator)
    ax.get_xaxis().set_major_formatter(fmt)
    if title is not None:
        ax.set_title(title)
    if x_label is not None:
        ax.set_xlabel(x_label, fontsize=14)
    if y_label is not None:
        ax.set_ylabel(y_label, fontsize=14)
    datemin = times[0]
    datemax = times[-1]
    ax.set_xlim(datemin, datemax)
    plt.show()


######################
### Main functions ###
######################


def create_tseries_to_cluster_fit_csv(filename, cluster_num, standardize=False, normalize=False, daily_avg=False):
    #assert not (daily_avg and weekday_weekend_avg)
    assert not (normalize and standardize)
    df = get_dataframe(filename)
    df = df.transpose()
    if daily_avg:
        df = get_daily_averaged_dataframe(df)
    ary = df.to_numpy()
    if standardize is True:
        ary = standardize_data(ary)
    if normalize is True:
        ary = normalize_data(ary)
    km = run_k_means(ary, cluster_num)
    rows = calculate_absolute_deviations(df.index.tolist(), ary, km.cluster_centers_, km.labels_)
    rows = sorted(rows, key=lambda e: e[2], reverse=True) # Sort by absolute deviation
    rows.insert(0, ["Meter ID", "Cluster", "Absolute deviation", "Within-Cluster z-score"])
    write_tseries_to_cluster_fit_csv(rows, filename, cluster_num, standardize, normalize, daily_avg)


def view_meters_time_series(filename, cluster_num, meter_ids=None, normalize=False, standardize=False, daily_avg=False, weekday_weekend_avg=False):
    assert not (daily_avg and weekday_weekend_avg)
    assert not (normalize and standardize)
    # df starts as 2880 * 736
    original_df = get_dataframe(filename)
    # df is now 736 * 2880
    df = original_df.transpose()
    all_meter_ids = [tup[2] for tup in df.index.tolist()]

    #print(df_T.iloc[0:3, 0:10])
    # meter_ids are in the same order as the rows in df_T
    #meter_ids = [tup[2] for tup in df_T.index.tolist()]
    #print(meter_ids)

    if daily_avg:
        times = [dt.to_pydatetime().replace(tzinfo=None) for dt in df.columns.tolist()[:96]] # Get 1 days worth of datetimes
        # df is now 736 * 96
        df = get_daily_averaged_dataframe(df)
        title = "Daily Averaged kWh Consumption Over Time"
        x_label = "Hours in 1 Day"
    elif weekday_weekend_avg:
        times = [dt.to_pydatetime().replace(tzinfo=None) for dt in df.columns.tolist()[:192]] # Get 2 days worth of datetimes
        # df is now 736 * 192
        df = get_weekday_weekend_averaged_dataframe(df)
        title = "Weekday-Weekend Averaged kWh Consumption Over Time"
        x_label = "Hours in 2 Pseudodays"
    else:
        title = "Daily kWh Consumption over time"
        x_label = "Days in the Month of June 2017"
        times = [dt.to_pydatetime().replace(tzinfo=None) for dt in df.columns.tolist()]
    ary = df.to_numpy()
    y_label = "Absolute kWh Consumption"
    if standardize:
        ary = standardize_data(ary)
        y_label = "Standardized kWh Consumption"
    if normalize:
        ary = normalize_data(ary)
        y_label = "Normalized kWh Consumption"
    km = run_k_means(ary, cluster_num)
    if meter_ids is not None:
        meter_indexes = []
        for m_id in meter_ids:
            meter_indexes.append(all_meter_ids.index(m_id))
        plot_specific_meters(times, ary, km, meter_indexes, title=title, x_label=x_label, y_label=y_label)
    else:
        plot_all_meters(times, ary, km, color_clusters=True, show_centroids=True, title=title, x_label=x_label, y_label=y_label)


if __name__ == "__main__":
    """
    8, 6, 5 is too many look how a couple of centroids are very close. 4 clusters is a little more interesting.
    """
    filename = "ALGIERS_kVARhDel_2017-06-01 00:00:00-05:00_15min_sum.pkl.gz"
    #filename = "ALGIERS_kWh_2017-06-01 00:00:00-05:00_15min_sum.pkl.gz"
    cluster_num = 4
    normalize = True

    #daily_avg = False
    #meter_ids = ["14-3H-22", "14-1A-110.10B"]

    daily_avg = True
    #meter_ids = ["14-2-87.1A", "14-2C2-47.3"]
    #meter_ids = ["14-2C2-47.3"]

    view_meters_time_series(filename, cluster_num, normalize=normalize, daily_avg=daily_avg)
    #view_meters_time_series(filename, cluster_num, meter_ids=meter_ids, normalize=normalize, daily_avg=daily_avg)
    #create_tseries_to_cluster_fit_csv(filename, cluster_num, normalize=normalize, daily_avg=daily_avg)
    #view_meters_time_series(filename, cluster_num, normalize=True, weekday_weekend_avg=True)