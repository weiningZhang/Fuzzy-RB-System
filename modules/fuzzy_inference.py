import seaborn as sns
import numpy as np

from modules.fuzzy_load import *

sns.set(style='darkgrid', palette="Paired")


def map_variable_types(measurement_file, fuzzy_variables, var_names, x_ranges, fuzzy_dict):
    '''
    Creates a lookup mapping of the current fuzzy variables, which includes their range and type (anticedent or consequent).
    
        Args:
            measurement_file(str): the input knowledge base file name
            fuzzy_variables(dict): the processed fuzzy dictionary with memberships
            var_names(list): lookup list with variable names
            x_ranges(dict): membership ranges for each fuzzy variable
            fuzzy_dict(dict): the original parsed fuzzy variable dictionary

        Returns:
            var_type_list(list): list of dictionaries containing the variable name, type and range
            fuzzy_measurements(dict): parsed dictionary of measurements
            
    '''


    var_type_list = []
    fuzzy_measurements = read_measurements(measurement_file, fuzzy_variables)

    for var_name in var_names:
        var_type_dict = {}
        if var_name in fuzzy_measurements.keys():
            var_type_dict['name'] = var_name
            var_type_dict['type'] = 'Antecedent'
            var_type_dict['range'] = x_ranges[var_name]

            var_type_list.append(var_type_dict)
        else:
            var_type_dict['name'] = var_name
            var_type_dict['type'] = 'Consequent'
            var_type_dict['range'] = x_ranges[var_name]

            var_type_list.append(var_type_dict)

    for k, v in fuzzy_dict.items():
        if k in var_names:
            for k_j, v_j in v.items():
                for vmfx in var_type_list:
                    if vmfx['name'] == k:
                        vmfx['vmfx'] = v_j

    return var_type_list, fuzzy_measurements


def infer_rules(file, fuzzy_vars, fuzzy_dict, fuzzy_measurements, x_ranges):
    '''
    Creates activations for each fuzzy rule, based on the Mamdani inference principles.
    The areas of activation are then aggregated using max-min composition.
    Can handle simple rules with 1 (SIMPLE) or 2 (AND, OR) conditions.

        Args:
            file(str): the input knowledge base file name
            fuzzy_vars(dict): the processed fuzzy dictionary with memberships
            fuzzy_dict(dict): the original parsed fuzzy variable dictionary
            fuzzy_measurements(dict): the original parsed measurements dictionary
            x_ranges(dict): membership ranges for each fuzzy variable
            
        Returns:
            activation_dict(dict): resulting membership values throughout the range
            
    '''


    anticedent_keys = list(fuzzy_measurements.keys())
    for k, v in fuzzy_dict.items():
        if str(k) in anticedent_keys:
            for k_j, v_j in v.items():
                cur_interp = np.interp(fuzzy_measurements[k], x_ranges[k], v[k_j], left=0, right=0)
                v[k_j] = cur_interp

    fuzzy_rules = read_rulebase(file, fuzzy_vars)
    activation_dict = {}
    idx = 1
    for rule in fuzzy_rules:

        cur_condition = rule['precedents']
        cur_result = rule['result']
        result_membership = fuzzy_dict[list(cur_result.keys())[0]][list(cur_result.values())[0]]

        if rule['connector'] == 'SIMPLE':
            precedent_membership = fuzzy_dict[list(cur_condition.keys())[0]][list(cur_condition.values())[0]]
            activation = np.fmin(precedent_membership, result_membership)
            activation_dict['R' + str(idx)] = activation
            idx += 1

        else:
            # can handle rules with 2 conditions
            if len(cur_condition) == 2:
                precedent_membership_i = fuzzy_dict[list(cur_condition.keys())[0]][list(cur_condition.values())[0]]
                precedent_membership_j = fuzzy_dict[list(cur_condition.keys())[1]][list(cur_condition.values())[1]]
                if rule['connector'] == 'AND':
                    rule_activation = np.fmin(precedent_membership_i, precedent_membership_j)
                elif rule['connector'] == 'OR':
                    rule_activation = np.fmax(precedent_membership_i, precedent_membership_j)

                activation = np.fmin(rule_activation, result_membership)
                activation_dict['R' + str(idx)] = activation
                idx += 1
            else:
                print('Invalid condition count')
                return

    return activation_dict
