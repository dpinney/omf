import uscrn_data_validation
from uscrn_data_validation import stations


#"AK_Gustavus_2_NE":
#"AK_King_Salmon_42_SE":
#"AK_Cordova_14_ESE":
#"AK_Deadhorse_3_S":
#"AK_Port_Alsworth_1_SW":
#"AK_Red_Dog_Mine_3_SSW":
#"AK_Fairbanks_11_NE":
#"AK_Metlakatla_6_S":
#"AK_Ruby_44_ESE":
#"AK_Denali_27_N":
#"AK_Kenai_29_ENE":
#"AK_Bethel_87_WNW":
#"AK_Glennallen_64_N":
#"AK_Ivotuk_1_NNE":


hourly = {
    "AK_Gustavus_2_NE": ["hourly", 2018, "AK_Gustavus_2_NE", 8760, 8755, 5],
    "AK_King_Salmon_42_SE": ["hourly", 2018, "AK_King_Salmon_42_SE",8760, 8753,7],
    "AK_Cordova_14_ESE": ["hourly", 2018, "AK_Cordova_14_ESE", 8760, 7593,1167],
    "AK_Deadhorse_3_S": ["hourly", 2018, "AK_Deadhorse_3_S", 8760, 8751,9],
    "AK_Port_Alsworth_1_SW": ["hourly", 2018, "AK_Port_Alsworth_1_SW", 8760,8755,5],
    "AK_Red_Dog_Mine_3_SSW": ["hourly", 2018, "AK_Red_Dog_Mine_3_SSW", 8760,8757,3],
    "AK_Fairbanks_11_NE": ["hourly", 2018, "AK_Fairbanks_11_NE", 8760,8754,6],
    "AK_Metlakatla_6_S": ["hourly", 2018, "AK_Metlakatla_6_S", 8760,8753,7],
    "AK_Ruby_44_ESE": ["hourly", 2018, "AK_Ruby_44_ESE", 8760,8755,5],
    "AK_Denali_27_N": ["hourly", 2018, "AK_Denali_27_N", 8760,8624,136],
    "AK_Kenai_29_ENE": ["hourly", 2018, "AK_Kenai_29_ENE", 8760,8757,3],
    "AK_Bethel_87_WNW": ["hourly", 2018, "AK_Bethel_87_WNW", 3287,2923,364],
    "AK_Glennallen_64_N": ["hourly", 2018, "AK_Glennallen_64_N", 8760,6576,2184],
    "AK_Ivotuk_1_NNE": ["hourly", 2018, "AK_Ivotuk_1_NNE", 8760,8573,187]
}


subhourly = {
    "AK_Gustavus_2_NE": ["subhourly", 2018, "AK_Gustavus_2_NE", 105120, 105060, 60],
    "AK_King_Salmon_42_SE": ["subhourly", 2018, "AK_King_Salmon_42_SE", 105120, 105036, 84],
    "AK_Cordova_14_ESE": ["subhourly", 2018, "AK_Cordova_14_ESE", 105120, 94308, 10812],
    "AK_Deadhorse_3_S": ["subhourly", 2018, "AK_Deadhorse_3_S", 105120, 96072, 9048],
    "AK_Port_Alsworth_1_SW": ["subhourly", 2018, "AK_Port_Alsworth_1_SW", 105120, 105060, 60],
    "AK_Red_Dog_Mine_3_SSW": ["subhourly", 2018, "AK_Red_Dog_Mine_3_SSW", 105120, 105084, 36],
    "AK_Fairbanks_11_NE": ["subhourly", 2018, "AK_Fairbanks_11_NE", 105120, 105048, 72],
    "AK_Metlakatla_6_S": ["subhourly", 2018, "AK_Metlakatla_6_S", 105120, 105060, 60],
    "AK_Ruby_44_ESE": ["subhourly", 2018, "AK_Ruby_44_ESE", 105120, 75192, 29928],
    "AK_Denali_27_N": ["subhourly", 2018, "AK_Denali_27_N", 105120, 103308, 1812],
    "AK_Kenai_29_ENE": ["subhourly", 2018, "AK_Kenai_29_ENE", 105120, 105084, 36],
    "AK_Bethel_87_WNW": ["subhourly", 2018, "AK_Bethel_87_WNW", 39444, 38676, 768],
    "AK_Glennallen_64_N": ["subhourly", 2018, "AK_Glennallen_64_N", 105120, 78908, 26212],
    "AK_Ivotuk_1_NNE": ["subhourly", 2018, "AK_Ivotuk_1_NNE", 105120, 102784, 2336]
}


class Test_MergeDictionaries(object):


    def test_hourlySubhourlyOrder_returnsMergedDictionary(self):
        h = hourly.copy()
        del h["AK_Fairbanks_11_NE"]
        del h["AK_Glennallen_64_N"]
        s = subhourly.copy()
        merged = uscrn_data_validation.merge_dictionaries(h, s)
        assert len(merged.keys()) == len(hourly.keys()) - 2
        assert len(merged[merged.keys()[0]]) == 12


    def test_subhourlyHourlyOrder_returnsMergedDictionary(self):
        h = hourly.copy()
        del h["AK_Fairbanks_11_NE"]
        del h["AK_Glennallen_64_N"]
        s = subhourly.copy()
        merged = uscrn_data_validation.merge_dictionaries(s, h)
        assert len(merged.keys()) == len(hourly.keys()) - 2
        assert len(merged[merged.keys()[0]]) == 12


class Test_SortMetaData(object):


    def test_sortedByHourlyYearAndValidCountAndName(self):
        h = hourly.copy()
        s = subhourly.copy()
        m = uscrn_data_validation.merge_dictionaries(h, s)
        #print(m)
        sorted_data = uscrn_data_validation.sort_metadata(m.values())
        for l in sorted_data:
            print(l)


if __name__ == "__main__":
    #obj = Test_MergeDictionaries()
    #obj.test_hourlySubhourlyOrder_returnsMergedDictionary()
    obj = Test_SortMetaData()
    obj.test_sortedByHourlyYearAndValidCountAndName()