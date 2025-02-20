import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

def transform_input_to_matrices(input_file, num_buses,v_base = 240):
    """
    Extracts P and V matrices from the input file based on bus names, 
    renaming buses to the old format while reading and providing mapping for reverting.

    Parameters:
    - input_file (str): Path to the formatted input file.
    - num_buses (int): Number of buses in the system.

    Returns:
    - P (numpy.ndarray): Power matrix (rows: time steps, columns: buses).
    - V (numpy.ndarray): Voltage matrix (rows: time steps, columns: buses).
    - bus (list): List of old-format bus names (e.g., "bus1", "bus2", etc.).
    - bus_name_mapping (dict): Mapping of old names to new names for reverting later.
    """
    data = pd.read_csv(input_file)
    data = data[~data['datetime'].str.contains('-01-01')]
    P, V, bus = [], [], []
    bus_name_mapping = {}

    # Get unique bus names in the file
    unique_bus_names = data['busname'].unique()

    # Rename to old format (bus1, bus2, etc.) during iteration
    for index, new_bus_name in enumerate(unique_bus_names, start=1):
        old_bus_name = f"bus{index}"
        bus_name_mapping[old_bus_name] = new_bus_name  # Store mapping for reverting later
        bus_data = data[data['busname'] == new_bus_name]
        P.append(bus_data['kw_reading'].values)
        V.append(bus_data['v_reading'].values / v_base)
        bus.append(old_bus_name)

    # Convert to numpy arrays and transpose
    return np.array(P).T, np.array(V).T, bus, bus_name_mapping





def data_load(test_system):
    """
    Load data for the specified test system (EC2, ST, or EC4).

    Parameters:
    test_system (str): The test system to load data for ('EC2', 'ST' or 'EC4').

    Returns:
    tuple: Contains loaded data including node_number, Trans_num, P_data, V_data, coordinates_file, coord, and distance_coord.
    """
    if test_system == 'EC2':
        node_number = 403
        Trans_num = 60
        input_file = "input data/EC2_Input.csv"  
        P, V, bus = transform_input_to_matrices(input_file, num_buses=node_number)        
        coordinates_file = "input data/EC2_XY.csv"
        coord = np.array(pd.read_csv('input data/EC2_coord_distance.csv', header=None))
        distance_coord = pd.read_csv('input data/EC2_cluster_distance.csv', header=None)

        Delta_P = np.diff(P, axis=0)[23:, :]
        Delta_V = np.diff(V, axis=0)[23:, :]
        
    elif test_system == 'ST':
        node_number = 46
        Trans_num = 12
        input_file = "input data/ST_Input.csv"  
        P, V, bus,bus_name_mapping = transform_input_to_matrices(input_file, num_buses=node_number)        
        coordinates_file = "input data/ST_XY.csv"
        coord = np.array(pd.read_csv('input data/ST_distance.csv', header=None))
        distance_coord = pd.read_csv('input data/ST_cluster_distance.csv', header=None)

        Delta_P = np.diff(P, axis=0)[23:, :]
        Delta_V = np.diff(V, axis=0)[23:, :]
        

    elif test_system == 'EC4':
        node_number = 110
        Trans_num = 61
        input_file = "input data/EC4_Input.csv"  
        P, V, bus = transform_input_to_matrices(input_file, num_buses=node_number)        
        coordinates_file = "input data/EC4_XY.csv"
        coord = np.array(pd.read_csv('input data/EC4_coord_distance.csv', header=None))
        distance_coord = pd.read_csv('input data/EC4_cluster_distance.csv', header=None)

        Delta_P = np.diff(P, axis=0)[23:, :]
        Delta_V = np.diff(V, axis=0)[23:, :]

    else:
        raise ValueError("Unsupported test system. Please choose 'EC2', 'ST', or 'EC4'.")

    V_data = Delta_V
    P_data = Delta_P

    #  print("Data loading finished for", test_system)
    return node_number, Trans_num, P_data, V_data, coordinates_file, coord, distance_coord, P, V, bus, bus_name_mapping

def correlation_calculation(V_data, P_data, node_number, weight_power=0, weight_voltage=1, plot=False):
    """
    Perform correlation calculations, plot heatmap, and calculate connections.

    Parameters:
    - V_data (numpy.ndarray): Voltage time-series data.
    - P_data (numpy.ndarray): Power time-series data.
    - node_number (int): Number of customers (nodes).
    - weight_power (float): Weight for power correlation. 
    - weight_voltage (float): Weight for voltage correlation.

    Returns:
    - average_pc (numpy.ndarray): Weighted correlation matrix.
    - all_set (list): Bi-directional reachability for each customer.
    """

    cor_collect_V_V = []
    V_V_daily = np.reshape(V_data, (363, 24, node_number))
    for i in range(363):
        daily_V_V = pd.DataFrame(V_V_daily[i, :]).corr()
        cor_collect_V_V.append(daily_V_V)
    average_pc_VV = abs(np.array(cor_collect_V_V)).mean(axis=0)

    cor_collect_P_P = []
    P_P_daily = np.reshape(P_data, (363, 24, node_number))
    for i in range(363):
        daily_P_P = pd.DataFrame(P_P_daily[i, :]).corr()
        cor_collect_P_P.append(daily_P_P)
    average_pc_PP = abs(np.array(cor_collect_P_P)).mean(axis=0)

    weighted_correlation_matrix = (weight_power * average_pc_PP) + (weight_voltage * average_pc_VV)
    average_pc = weighted_correlation_matrix

    if plot:
        # Heatmap Plot for Customer Correlation
        indices_to_show = np.arange(0, weighted_correlation_matrix.shape[0], 20)
        labels_to_show = [str(i) for i in indices_to_show]

        plt.figure(figsize=(30, 25))
        sns.heatmap(
            weighted_correlation_matrix,
            annot=False,
            cmap='Greens',
            cbar_kws={'label': 'Correlation'},
            linewidths=0.3,
        )
        plt.title("Customer Correlation Matrix", fontsize=40)
        plt.xlabel("Customer Index", fontsize=40)
        plt.ylabel("Customer Index", fontsize=40)

        colorbar = plt.gca().collections[0].colorbar
        colorbar.ax.tick_params(labelsize=20)
        colorbar.set_label('Correlation', fontsize=40)

        plt.xticks(indices_to_show + 0.5, labels_to_show, fontsize=40)
        plt.yticks(indices_to_show + 0.5, labels_to_show, fontsize=40)

        plt.show()

    # Calculate Connection
    Index_potential_cust = []
    for selected_num in range(node_number):
        selected_cust = average_pc[selected_num, :]
        index_potential_cust = np.argsort(selected_cust)[-3:]
        Index_potential_cust.append(index_potential_cust)

    # Calculate Bi-directional Reachability for each customer
    all_set = []
    for selected_num in range(node_number):
        bi_c_set = []
        for item in Index_potential_cust[selected_num]:
            if selected_num in Index_potential_cust[item]:
                bi_c_set.append(item)
        all_set.append(bi_c_set)

    #  print("Correlation calculation and reachability analysis completed.")
    return average_pc, all_set


def generate_connection_results_exact(
    node_number, Trans_num, all_set, average_pc, coord, num_iterations=10):
    """
    Generate transformer-customer connection results through clustering and adjustment.

    Parameters:
    - node_number (int): Number of customers (nodes).
    - Trans_num (int): ASSERT Exact number of transformers.  !!!
    - all_set (list): Bi-directional reachability for each customer.
    - average_pc (numpy.ndarray): Weighted correlation matrix.
    - coord (numpy.ndarray): Customer physical distance matrix.
    - num_iterations (int): Number of iterations for connection adjustment.

    Returns:
    - sorted_result (list): Final sorted transformer-customer connection clusters.
    """
    import random

    Connection_score = []
    Connection_result = []

    for i in range(num_iterations):
        #  print(f"|=====================|\n| Iteration {i + 1} |\n|=====================|")
        original_set = random.sample(range(node_number), node_number)
        Connection_result_temp, _, _, _, _, _, _ = Connection_adjustment(
            original_set, all_set, node_number, average_pc, Trans_num, coord
        )
        Connection_score_temp = Score_Cal(Connection_result_temp, average_pc)
        Connection_score.append(Connection_score_temp)
        Connection_result.append(Connection_result_temp)
        #  print(f"Iteration {i + 1} completed.")

    Final_result = Connection_result[Connection_score.index(max(Connection_score))]
    sorted_result = sort_customer_clusters(Final_result)

    #  print("Final customer-transformer connection results generated!")
    return sorted_result


def generate_connection_results_estimate(
    node_number,
    Trans_num,
    all_set,
    average_pc,
    coord,
    V,
    num_iterations=50,
):
    """
    Generate transformer-customer connection results through clustering and adjustment.

    Parameters:
    - node_number (int): Number of customers (nodes).
    - Trans_num (int): Number of transformers.  !!! minimum... 4 as default...
    - all_set (list): Bi-directional reachability for each customer.
    - average_pc (numpy.ndarray): Weighted correlation matrix.
    - coord (numpy.ndarray): Customer physical distance matrix.
    - num_iterations (int): Number of iterations for connection adjustment.

    Returns:
    - sorted_result (list): Final sorted transformer-customer connection clusters.
    """
    import random
    from collections import Counter

    #print(coord)

    optimal_cluster_numbers = []  # To store optimal cluster numbers from each iteration
    cluster_results = {}  # To store cluster results for each cluster number

    for i in range(num_iterations):
        #print(f"|=====================|\n| Iteration {i + 1} |\n|=====================|")
        original_set = random.sample(range(node_number), node_number)
        optimal_cluster_set, cluster_set, _, _, _, _, _, _ = Connection_adjustment_est(
            original_set, all_set, node_number, average_pc, Trans_num, coord, V
        )
        
        # Determine the number of clusters in the optimal cluster set
        optimal_cluster_num = len(optimal_cluster_set)
        optimal_cluster_numbers.append(optimal_cluster_num)

        # Store the cluster result for this cluster number
        cluster_results[optimal_cluster_num] = optimal_cluster_set
        #print(f"Iteration {i + 1} completed. Optimal cluster number: {optimal_cluster_num}")

    # Filter and prioritize cluster numbers >= Trans_num
    filtered_cluster_numbers = [num for num in optimal_cluster_numbers if num > Trans_num]

    if not filtered_cluster_numbers:
        raise ValueError("No valid cluster numbers found that are > Trans_num.")

    # Count the frequency of each cluster number in the filtered list
    frequency_counter = Counter(filtered_cluster_numbers)

    # Select the cluster number closest to Trans_num, breaking ties using frequency
    most_common_cluster_num = min(
        frequency_counter.keys(),
        key=lambda k: (abs(k - Trans_num), -frequency_counter[k])  # Prioritize proximity, then frequency
    )
    #print(f"Selected optimal cluster number: {most_common_cluster_num}")

    # Retrieve the cluster set for the selected cluster number
    final_cluster_set = cluster_results[most_common_cluster_num]

    # Sort the final result
    sorted_result = sort_customer_clusters(final_cluster_set)

    # print("generate_connection_results_estimate")
    return sorted_result



def Connection_adjustment_est(original_set, all_set, node_number, average_pc, Trans_num,coord,V):

    cluster_set = []  # pre-result
    saved_cluster_sets = {}  # Store cluster_set for each cluster count
    while original_set:
        # print(len(original_set))
        new_item = set([item for item in original_set]).intersection(set(all_set[original_set[0]]))
        original_set = [i for i in original_set if i not in list(new_item)]
        cluster_set.append(list(new_item)) 
        # print(len(original_set))
        # print(len(cluster_set))

    # Cluster adjustment based on bi-connect degree  
    for i in range(10):
        #print("|*********{0}*********|".format(i+1))
        # target_item = 0
        for target_item in range(node_number):
            Bi_connect_degree = []
            subset_index = 0
            for subset in cluster_set:
                
                average_pc[target_item,subset]
                
                bi_connect_degree =len(set(all_set[target_item]).intersection(set(subset)))/ (len(subset) + 1)
                
                if target_item in subset:
                    target_item_subset = subset_index
                    # print(target_item_subset)
                    bi_connect_degree -= 1/(len(subset) + 1)     
                Bi_connect_degree.append(bi_connect_degree)
                subset_index += 1
                
         
            potential_position = [item for item in Bi_connect_degree if item > Bi_connect_degree[target_item_subset]] 
            
            if potential_position and len(cluster_set[target_item_subset]) > 1:
                # print("Target {0} moved to {1} from {2}".format(target_item, Bi_connect_degree.index(potential_position[0]), target_item_subset))
                cluster_set[target_item_subset].remove(target_item)
                cluster_set[Bi_connect_degree.index(potential_position[0])].append(target_item)


    cluster_set_nonempty = [ele for ele in cluster_set if ele != []]
    # if len(cluster_set_nonempty)<Trans_num:
    if len(cluster_set_nonempty)<1:
        cluster_set = []
        # print(cluster_set_nonempty)
        return cluster_set # if rough clustering result is smaller than it
    
    cluster_set = cluster_set_nonempty
    dist_result = []
    for i in cluster_set:
        for j in cluster_set:
            temp_result = []
            output = [[a, b] for a in i for b in j]
            for k in output:
                temp_result.append( average_pc[ k[0], k[1] ] )
            dist_result.append(np.mean(temp_result))
    dist_matrix = np.reshape(np.array(dist_result), (len(cluster_set),len(cluster_set)))  ## distance within cluster
    
    cluster_inter_record = []
    cluster_ext_record = []
    result_DBI_clusternum = []
    save_corr = []
    collect_cluster_set = []
    max_physic_distance_current_cluster =[]


    while len(cluster_set)>Trans_num:
        # print("The cluster number now:", len(cluster_set))

        Row    = np.where(np.triu(dist_matrix, 1) == np.max(np.triu(dist_matrix, 1)))[0][0]
        Column = np.where(np.triu(dist_matrix, 1) == np.max(np.triu(dist_matrix, 1)))[1][0]

    
        dist_coord = []
        for i in cluster_set:
            for j in cluster_set:
                temp_coord = []
                output1 = [[a, b] for a in i for b in j]
                for k in output1:
                    #temp_coord.append( coord[ k[0], k[1] ] )
                    temp_coord.append(0.0)  # NOTE: was changed 2025027
                dist_coord.append(np.mean(temp_coord))
        dist_matrix_coord = np.reshape(np.array(dist_coord), (len(cluster_set),len(cluster_set)))  ## distance within cluster with coordinates
        
        if dist_matrix_coord[Row,Column] < 100:
            delete1 = cluster_set[Row]
            delete2 = cluster_set[Column]
            merge_set = list(set(delete1 + delete2))
            
            cluster_set.remove(delete1)
            cluster_set.remove(delete2)
            cluster_set.append(merge_set)
            dist_result = []
            for i in cluster_set:
                for j in cluster_set:
                    temp_result = []
                    output = [[a, b] for a in i for b in j]
                    for k in output:
                        temp_result.append( average_pc[ k[0], k[1] ] )
                    dist_result.append(np.mean(temp_result))
            dist_matrix = np.reshape(np.array(dist_result), (len(cluster_set),len(cluster_set))) 
        else:
            dist_matrix[Row,Column] = 0
            new_Row    = np.where(np.triu(dist_matrix, 1) == np.max(np.triu(dist_matrix, 1)))[0][0]
            new_Column = np.where(np.triu(dist_matrix, 1) == np.max(np.triu(dist_matrix, 1)))[1][0]
            delete1 = cluster_set[new_Row]
            delete2 = cluster_set[new_Column]
            merge_set = list(set(delete1 + delete2))
            
            cluster_set.remove(delete1)
            cluster_set.remove(delete2)
            cluster_set.append(merge_set)
            dist_result = []
            for i in cluster_set:
                for j in cluster_set:
                    temp_result = []
                    output = [[a, b] for a in i for b in j]
                    for k in output:
                        temp_result.append( average_pc[ k[0], k[1] ] )
                    dist_result.append(np.mean(temp_result))
            dist_matrix = np.reshape(np.array(dist_result), (len(cluster_set),len(cluster_set)))        
            
        # import itertools
        
        # physic_distance_current_cluster = []
    #     for item in cluster_set:
    #         if len(item) > 1:
    #             for i, j in itertools.combinations(item, 2):
    #                 if i == j:
    #                     physic_distance_current_cluster.append(0)
    #                 physic_distance_current_cluster.append(coord[i, j])
    #         elif len(item) == 1:
    #             physic_distance_current_cluster.append(0)  
    #     max_physic_distance_current_cluster.append(max(physic_distance_current_cluster))
    # # comment out...?
            
            
    ## calculate DBI
           
        # average_dist_item=[]
        # corr_for_this_cluster=[]
        # index = 0
        # for item in cluster_set:
        #     corr_dist = []
        #     for i in item:
        #         for j in item:
        #             if i==j:
        #                 corr_dist.append(0)
        #                 continue
        #             corr_dist.append(1 - average_pc[i,j])
        #     corr_dist_reshape = np.reshape(corr_dist, (len(cluster_set[index]), len(cluster_set[index])))
        #     # corr_dist_reshape[corr_dist_reshape == 0] = 1
        #     # corr_for_this_cluster.append(sum(np.min(corr_dist_reshape, axis=1))/len(cluster_set[index]))
        #     corr_for_this_cluster.append(np.max(np.triu(corr_dist_reshape)))
        #     # corr_for_this_cluster.append((sum(corr_dist_reshape.reshape(-1))/(np.count_nonzero(corr_dist_reshape)+1)) )
        #     # print((sum(corr_dist_reshape.reshape(-1))/(np.count_nonzero(corr_dist_reshape)+1)))
            
        #     # corr_for_this_cluster = [0 if x == 1 else x for x in corr_for_this_cluster]
        #     index +=1
        # save_corr.append(corr_for_this_cluster)
        
       # -------------------- Metrics Calculation and Saving --------------------
        cluster_labels = np.zeros(node_number)
        for idx, cluster in enumerate(cluster_set):
            for item in cluster:
                cluster_labels[item] = idx
                
        cluster_indices = [item for subset in cluster_set for item in subset]
        X = V[:, cluster_indices].T
        
        if len(set(cluster_labels)) > 1:  # Ensure valid metrics calculation
            silhouette = silhouette_score(X, cluster_labels)
            davies_bouldin = davies_bouldin_score(X, cluster_labels)
            calinski_harabasz = calinski_harabasz_score(X, cluster_labels)
            saved_cluster_sets[len(cluster_set)] = {
                "cluster_set": cluster_set.copy(),
                "silhouette": silhouette,
                "davies_bouldin": davies_bouldin,
                "calinski_harabasz": calinski_harabasz
            }
            # print(f"Clusters: {len(cluster_set)}, Silhouette: {silhouette:.4f}, DBI: {davies_bouldin:.4f}, CH: {calinski_harabasz:.4f}")
        # -------------------------------------------------------------------------


    # -------------------- Select the Optimal Cluster Number --------------------
    # Select the best cluster number based on weighted scores
    best_cluster_num, optimal_cluster_set = select_best_cluster(saved_cluster_sets)
    #print(f"Optimal cluster number: {best_cluster_num}")

    # -------------------------------------------------------------------------

    return optimal_cluster_set, cluster_set, cluster_inter_record, cluster_ext_record, np.array(result_DBI_clusternum), save_corr, collect_cluster_set, max_physic_distance_current_cluster


def normalize_metrics(saved_cluster_sets):
    """
    Normalize clustering metrics for comparison.
    """
    silhouettes = [saved_cluster_sets[k]["silhouette"] for k in saved_cluster_sets]
    dbis = [saved_cluster_sets[k]["davies_bouldin"] for k in saved_cluster_sets]
    chs = [saved_cluster_sets[k]["calinski_harabasz"] for k in saved_cluster_sets]

    # Compute min and max for normalization
    min_silhouette, max_silhouette = min(silhouettes), max(silhouettes)
    min_dbi, max_dbi = min(dbis), max(dbis)
    min_ch, max_ch = min(chs), max(chs)

    normalized_scores = {}
    for k, metrics in saved_cluster_sets.items():
        normalized_silhouette = (metrics["silhouette"] - min_silhouette) / (max_silhouette - min_silhouette)
        normalized_dbi = 1 - (metrics["davies_bouldin"] - min_dbi) / (max_dbi - min_dbi)
        normalized_ch = (metrics["calinski_harabasz"] - min_ch) / (max_ch - min_ch)

        normalized_scores[k] = {
            "normalized_silhouette": normalized_silhouette,
            "normalized_dbi": normalized_dbi,
            "normalized_ch": normalized_ch,
        }
    return normalized_scores

def select_best_cluster(saved_cluster_sets, weights=(0.2, 0.2, 0.6)):
    """
    Select the best cluster number based on weighted normalized metrics.
    """
    normalized_scores = normalize_metrics(saved_cluster_sets)

    # Compute weighted scores
    weighted_scores = {}
    for k, metrics in normalized_scores.items():
        weighted_score = (
            weights[0] * metrics["normalized_silhouette"] +
            weights[1] * metrics["normalized_dbi"] +
            weights[2] * metrics["normalized_ch"]
        )
        weighted_scores[k] = weighted_score

    # Select the best cluster number
    best_cluster_num = max(weighted_scores, key=weighted_scores.get)
    return best_cluster_num, saved_cluster_sets[best_cluster_num]["cluster_set"]

def Connection_adjustment(original_set, all_set, node_number, average_pc, Trans_num, coord):
    # 
    cluster_set = []  # pre-result
    while original_set:
        # print(len(original_set))
        new_item = set([item for item in original_set]).intersection(set(all_set[original_set[0]]))
        original_set = [i for i in original_set if i not in list(new_item)]
        cluster_set.append(list(new_item)) 
        #  print(len(original_set))
        #  print(len(cluster_set))

    # Cluster adjustment based on bi-connect degree  
    for i in range(10):
        #  print("|*********{0}*********|".format(i+1))
        # target_item = 0
        for target_item in range(node_number):
            Bi_connect_degree = []
            subset_index = 0
            for subset in cluster_set:
                
                average_pc[target_item,subset]
                
                bi_connect_degree =len(set(all_set[target_item]).intersection(set(subset)))/ (len(subset) + 1)
                
                if target_item in subset:
                    target_item_subset = subset_index
                    # print(target_item_subset)
                    bi_connect_degree -= 1/(len(subset) + 1)     
                Bi_connect_degree.append(bi_connect_degree)
                subset_index += 1
                
         
            potential_position = [item for item in Bi_connect_degree if item > Bi_connect_degree[target_item_subset]] 
            
            if potential_position and len(cluster_set[target_item_subset]) > 1:
                #  print("Target {0} moved to {1} from {2}".format(target_item, Bi_connect_degree.index(potential_position[0]), target_item_subset))
                cluster_set[target_item_subset].remove(target_item)
                cluster_set[Bi_connect_degree.index(potential_position[0])].append(target_item)


    cluster_set_nonempty = [ele for ele in cluster_set if ele != []]
    # if len(cluster_set_nonempty)<Trans_num:
    if len(cluster_set_nonempty)<1:
        cluster_set = []
        #  print(cluster_set_nonempty)
        return cluster_set # if rough clustering result is smaller than it
    
    
    cluster_set = cluster_set_nonempty
    dist_result = []
    for i in cluster_set:
        for j in cluster_set:
            temp_result = []
            output = [[a, b] for a in i for b in j]
            for k in output:
                temp_result.append( average_pc[ k[0], k[1] ] )
            dist_result.append(np.mean(temp_result))
    dist_matrix = np.reshape(np.array(dist_result), (len(cluster_set),len(cluster_set)))  ## distance within cluster
    
    cluster_inter_record = []
    cluster_ext_record = []
    result_DBI_clusternum =[]   
    save_corr = []
    collect_cluster_set = []
    max_physic_distance_current_cluster =[]
    while len(cluster_set)>Trans_num:
        #  print(len(cluster_set))

        Row    = np.where(np.triu(dist_matrix, 1) == np.max(np.triu(dist_matrix, 1)))[0][0]
        Column = np.where(np.triu(dist_matrix, 1) == np.max(np.triu(dist_matrix, 1)))[1][0]

    
        dist_coord = []
        for i in cluster_set:
            for j in cluster_set:
                temp_coord = []
                output1 = [[a, b] for a in i for b in j]
                for k in output1:
                    temp_coord.append( coord[ k[0], k[1] ] )
                dist_coord.append(np.mean(temp_coord))
        dist_matrix_coord = np.reshape(np.array(dist_coord), (len(cluster_set),len(cluster_set)))  ## distance within cluster with coordinates
        
        if dist_matrix_coord[Row,Column] < 10000:
            delete1 = cluster_set[Row]
            delete2 = cluster_set[Column]
            merge_set = list(set(delete1 + delete2))
            
            cluster_set.remove(delete1)
            cluster_set.remove(delete2)
            cluster_set.append(merge_set)
            dist_result = []
            for i in cluster_set:
                for j in cluster_set:
                    temp_result = []
                    output = [[a, b] for a in i for b in j]
                    for k in output:
                        temp_result.append( average_pc[ k[0], k[1] ] )
                    dist_result.append(np.mean(temp_result))
            dist_matrix = np.reshape(np.array(dist_result), (len(cluster_set),len(cluster_set))) 
        else:
            dist_matrix[Row,Column] = 0
            new_Row    = np.where(np.triu(dist_matrix, 1) == np.max(np.triu(dist_matrix, 1)))[0][0]
            new_Column = np.where(np.triu(dist_matrix, 1) == np.max(np.triu(dist_matrix, 1)))[1][0]
            delete1 = cluster_set[new_Row]
            delete2 = cluster_set[new_Column]
            merge_set = list(set(delete1 + delete2))
            
            cluster_set.remove(delete1)
            cluster_set.remove(delete2)
            cluster_set.append(merge_set)
            dist_result = []
            for i in cluster_set:
                for j in cluster_set:
                    temp_result = []
                    output = [[a, b] for a in i for b in j]
                    for k in output:
                        temp_result.append( average_pc[ k[0], k[1] ] )
                    dist_result.append(np.mean(temp_result))
            dist_matrix = np.reshape(np.array(dist_result), (len(cluster_set),len(cluster_set)))        
            
    #     import itertools
        
    #     # TODO: can be removed
    #     physic_distance_current_cluster = []
    #     for item in cluster_set:
    #         if len(item) > 1:
    #             for i, j in itertools.combinations(item, 2):
    #                 if i == j:
    #                     physic_distance_current_cluster.append(0)
    #                 physic_distance_current_cluster.append(coord[i, j])
    #         elif len(item) == 1:
    #             physic_distance_current_cluster.append(0)  
    #     max_physic_distance_current_cluster.append(max(physic_distance_current_cluster))
            
            
    # ## calculate DBI
           
    #     average_dist_item=[]
    #     corr_for_this_cluster=[]
    #     index = 0
    #     for item in cluster_set:
    #         corr_dist = []
    #         for i in item:
    #             for j in item:
    #                 if i==j:
    #                     corr_dist.append(0)
    #                     continue
    #                 corr_dist.append(1 - average_pc[i,j])
    #         corr_dist_reshape = np.reshape(corr_dist, (len(cluster_set[index]), len(cluster_set[index])))
    #         # corr_dist_reshape[corr_dist_reshape == 0] = 1
    #         # corr_for_this_cluster.append(sum(np.min(corr_dist_reshape, axis=1))/len(cluster_set[index]))
    #         corr_for_this_cluster.append(np.max(np.triu(corr_dist_reshape)))
    #         # corr_for_this_cluster.append((sum(corr_dist_reshape.reshape(-1))/(np.count_nonzero(corr_dist_reshape)+1)) )
    #         # print((sum(corr_dist_reshape.reshape(-1))/(np.count_nonzero(corr_dist_reshape)+1)))
            
    #         # corr_for_this_cluster = [0 if x == 1 else x for x in corr_for_this_cluster]
    #         index +=1
    #     save_corr.append(corr_for_this_cluster)


    return cluster_set,cluster_inter_record,cluster_ext_record, np.array(result_DBI_clusternum),save_corr,collect_cluster_set,max_physic_distance_current_cluster


def Score_Cal(cluster_set, average_pc):
    '''

    Parameters
    ----------
    cluster_set : list
       rough clustering.
    average_pc : numpy.ndarray
        average of customer correlation matrix over 365 days.

    Returns
    -------
    Result_score : double
        score of obtained result.

    '''
    if len(cluster_set)==0:# exculde cluster_set with transformer number less than actual value
        Result_score = 1
        
    Bi_connect_degree = []  
    for subset in cluster_set:
        output = [[a, b] for a in subset for b in subset]
        temp_result = []
        for k in output:
            temp_result.append( average_pc[ k[0], k[1] ] )        
        Bi_connect_degree.append(np.mean(temp_result))
    Result_score = np.mean(Bi_connect_degree)
    return Result_score


def sort_customer_clusters(customer_clusters):
    """
    Sorts a list of customer clusters (list of lists) by the smallest customer index in each cluster
    and increments every customer index by 1.

    Parameters:
    customer_clusters (list of list of int): List of customer clusters.

    Returns:
    list of list of int: Sorted and shifted list of customer clusters.
    """
    # Increment every index by 1
    shifted_clusters = [[index + 1 for index in cluster] for cluster in customer_clusters]
    # Sort clusters by the smallest customer index
    sorted_clusters = sorted(shifted_clusters, key=lambda cluster: cluster[0])
    return sorted_clusters



def generate_transformer_customer_mapping(
    sorted_result, coordinates_data, output_file, bus, bus_name_mapping
):
    """
    Generates a mapping of customer indices, transformer indices, and coordinates,
    replaces old bus names with new bus names, and exports the results to a CSV file.

    Parameters:
    - sorted_result: list of list of int
        Sorted and shifted list of customer groups assigned to transformers.
    - coordinates_data: dataframe of coordinates per busname x y
    - output_file: str
        Path to save the resulting CSV file.
    - bus: list
        List of old bus names (e.g., "bus1", "bus2").
    - bus_name_mapping: dict
        Mapping of old bus names to new bus names.

    Returns:
    - Final_results (pd.DataFrame): DataFrame containing the final mapping with new bus names.
    """
    # NOTE coordinates data now ASSERTS busname
    # generate bus name to int map
    bus_to_int_map = {val: int(str(key).replace('bus', '')) for key, val in bus_name_mapping.items()}
    coordinates_data["Customer Index"] = [bus_to_int_map[b] for b in bus_to_int_map.keys()]

    # Prepare a DataFrame for exporting
    rows = []
    for transformer_idx, customer_group in enumerate(sorted_result, start=1):
        for customer_idx in customer_group:
            # Fetch X and Y coordinates for the current customer
            x_coord = coordinates_data.loc[coordinates_data['Customer Index'] == customer_idx, 'X'].values[0]
            y_coord = coordinates_data.loc[coordinates_data['Customer Index'] == customer_idx, 'Y'].values[0]
            rows.append([customer_idx, transformer_idx, x_coord, y_coord])

    # Convert rows to DataFrame
    export_data = pd.DataFrame(rows, columns=["Customer Index", "Transformer Index", "X", "Y"])
    # Sort the data by "Customer Index"
    export_data = export_data.sort_values(by="Customer Index", ascending=True)

    # Replace old bus names with new bus names
    export_data["busname"] = [bus_name_mapping[b] for b in bus]

    # drop customer index here
    Final_results = export_data[['busname', 'Transformer Index', 'X', 'Y']]

    # Export to CSV
    Final_results.to_csv(output_file, index=False)
    #  print(f"CSV file has been saved as {output_file}.")

    return Final_results.reset_index(drop=True)


def get_groupings(
        input_meter_data_fp,
        grouping_output_fp,
        minimum_xfmr_n=None,
        xfmr_n_is_exact=False,
        bus_coords_fp=None,
):
    """
    perform customer transformer grouping, return grouping results
    """

    input_data = pd.read_csv(input_meter_data_fp)
    bus_names = input_data['busname'].unique()
    node_number = len(bus_names)

    # NOTE: this num_buses input is not used.
    P, V, bus, bus_name_mapping = transform_input_to_matrices(
        input_meter_data_fp,
        num_buses='not used...')

    # make distance matrix from bus coords
    if bus_coords_fp is None:
        # handle optional bus coordinates..
        #print('zeroing bus coords')
        coords = pd.DataFrame(index=list(range(0, len(bus_names))))
        coords['busname'] = bus_names
        no_coord_val = 0.0  # NOTE: used to fill coordinates if none.
        coords['X'] = no_coord_val
        coords['Y'] = no_coord_val
    else:
        coords = pd.read_csv(bus_coords_fp)

    # create distance matrix
    z = np.array([complex(row['X'], row['Y']) for _, row in coords.iterrows()])
    m, n = np.meshgrid(z, z)
    dist_matrix = abs(m-n)

    # NOTE: ask about this 23... should it be optional?
    Delta_P = np.diff(P, axis=0)[23:, :]
    Delta_V = np.diff(V, axis=0)[23:, :]
    V_data = Delta_V
    P_data = Delta_P

    average_pc, all_set = correlation_calculation(
        V_data,
        P_data,
        node_number)

    # Generate Connection Results
    # TODO: account for 2 cases: exact xfmr number given
    if xfmr_n_is_exact:
        #print('performing exact')
        sorted_result = generate_connection_results_exact(
            node_number,
            minimum_xfmr_n,
            all_set,
            average_pc,
            dist_matrix,
            )
    else:
        #print('performing estimate')
        if minimum_xfmr_n is None:
            minimum_xfmr_n = int(node_number / 4)
        sorted_result = generate_connection_results_estimate(
            node_number,
            minimum_xfmr_n,
            all_set,
            average_pc,
            coords,
            V
            )
    # Export Results
    grouping_results = generate_transformer_customer_mapping(
        sorted_result,
        coords,
        grouping_output_fp,
        bus,
        bus_name_mapping)

    return grouping_results
