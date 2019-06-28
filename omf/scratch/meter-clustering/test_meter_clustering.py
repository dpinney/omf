import datetime, random, os, pytest
import numpy as np
import pandas as pd
import meter_clustering


@pytest.fixture(scope="module")
def toy_dataframe():
    df = pd.DataFrame()
    values = [0.54, 0.32, 0.11, 0.0, 0.90, 0.88, 0.27, 0.31, 0.82, 0.01]
    for i in range(13):
        # <list>.insert() returns nothing, so can't combine these next two lines
        values.insert(0, values.pop())
        s = pd.Series(values[:2])
        df = df.append(s, ignore_index=True)
    #df = df.append(pd.Series([0.55, 1.23, 0.0, 130.91, 3.40, 7.26, 0.45, 0.11, 1.32, 1.88]), ignore_index=True)
    df = df.append(pd.Series([0.55, 1.23]), ignore_index=True)
    # 2 meters
    column_labels = [
        ('FLAVORTOWN', '4', '19-3H-24', 20.2, 25.3),
        ('FLAVORTOWN', '4', '19-1D1-9B', 20.2, 25.3)
        #('FLAVORTOWN', '4', '19-1A-180.10A', 20.2, 25.3),
        #('FLAVORTOWN', '5', '19-1D1-93', 20.2, 25.3),
        #('FLAVORTOWN', '5', '19-3J-1A1', 20.2, 25.3),
        #('FLAVORTOWN', '4', '19-3-142.1.1B', 20.2, 25.3),
        #('FLAVORTOWN', '4', '19-3H-2A', 20.2, 25.3),
        #('FLAVORTOWN', '2', '19-2C2-07.3', 20.2, 25.3),
        #('FLAVORTOWN', '5', '19-2D-16', 20.2, 25.3),
        #('FLAVORTOWN', '5', '19-2D-82.3B', 20.2, 25.3)
    ]
    df.columns = column_labels
    # 7 days, 2 measures per day
    row_labels = []
    start_date = datetime.datetime(2017, 6, 1)
    time_step = datetime.timedelta(hours=12)
    for i in range(14):
        row_labels.append(start_date + time_step * i)
    df.index = row_labels
    return df


@pytest.fixture(scope="module")
def k_means():
    """Mock KMeans"""
    km = Test_CalculateAbsoluteDeviationAndZscore()
    km.cluster_centers_ = [[0.75, 0.44, 1.23, 0.49, 0.71, 0.85, 0.34, 1.99, 0.81, 0.12, 0.91, 0.55, 0.83, 0.53]]
    km.labels_ = [0, 0] 
    return km


class Test_CalculateAbsoluteDeviationAndZscore(object):


    # Test passes. Need to update pandas package with David's approval before this will run in OMF
    def test_returnsCorrectValues(self, toy_dataframe, k_means):
        df = toy_dataframe.transpose()
        ary = df.to_numpy()
        rows = meter_clustering.calculate_absolute_deviation_and_zscore(df.index.tolist(), ary, k_means)
        # Test 2 out of the 10 meters of the DataFrame. Good enough
        assert round(rows[0][2], 2) == 7.32 # absolute deviation
        assert round(rows[0][3], 1) == 1.0 # zscore
        assert round(rows[1][2], 2) == 6.77 # absolute deviation
        assert round(rows[1][3], 1) == -1.0 # zscore


if __name__ == "__main__":
    df = toy_dataframe()
    #df.to_csv(os.path.join(os.path.dirname(__file__), "dataframe.csv"))