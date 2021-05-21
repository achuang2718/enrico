import json
import time
from json import JSONDecodeError
import numpy as np
import matplotlib.pyplot as plt


def fancy_plot(x, y, fmt='', ax = None, **kwargs):
    """Wraps around matplotlib.pyplot (aliased to plt) with last-point highlighting and statistics

    Plots x and y as in plt.plot, but a) averages together y-values with the same x-value and calculates and plots 
    an error bar, and b) plots the final (x,y) point in a different color than the previous ones. 

    Args:
        x: The x-data to be plotted. Assumed to be an iterable with contents of
            numeric type, including possibly np.nan
        y: The y-data to be plotted. Same assumptions on type.
        fmt: The format string. In contrast to ax.plot, it is a kwarg.
        ax: The axes object on which to plot. If None, plt.gca() is called. 
        kwargs: Any kwarg that can be passed to ax.errorbar.

    Returns:
        ErrorbarContainer, as detailed in the docs for plt.errorbar

    Raises:
        ValueError if x and y are not of the same length
    """
    if(ax == None):
        ax = plt.gca()
    if(len(x) != len(y)):
        raise ValueError(
            "The input x and y arrays must be of the same length.")
    # Filter out the NaNs in either x or y while preserving order
    zipped_list = list(zip(x, y))
    nan_filter = filter(lambda v: (
        (not np.isnan(v[0])) and (not np.isnan(v[1]))), zipped_list)
    nan_stripped_list = list(nan_filter)
    # Pull off the last point so that it can be plotted in a different color
    if(len(nan_stripped_list) != 0):
        most_recent_xy_pair = nan_stripped_list[-1]
        nan_stripped_list = nan_stripped_list[:len(nan_stripped_list) - 1]
    else:
        most_recent_xy_pair = None
    # Sort the NaN-stripped list to make getting statistics faster for large data
    sorted_list = sorted(nan_stripped_list, key=(lambda v: v[0]))
    # Reconstitute to x- and y- lists
    if(len(sorted_list) > 0):
        x_sorted, y_sorted = zip(*sorted_list)
        sorted_x_list = list(x_sorted)
        sorted_y_list = list(y_sorted)
    else:
        sorted_x_list = []
        sorted_y_list = []
    # Perform statistics and condense repeated measurements
    index = 0
    final_x_list = []
    final_y_list = []
    final_error_list = []
    while(index < len(sorted_x_list)):
        current_x_value = sorted_x_list[index]
        final_x_list.append(current_x_value)
        y_list_for_current_x = []
        while(index < len(sorted_x_list) and sorted_x_list[index] == current_x_value):
            y_list_for_current_x.append(sorted_y_list[index])
            index += 1
        y_array_for_current_x = np.array(y_list_for_current_x)
        y_mean = sum(y_array_for_current_x) / float(len(y_array_for_current_x))
        final_y_list.append(y_mean)
        # Calculate the standard error of mean if possible
        if(len(y_list_for_current_x) == 1):
            final_error_list.append(np.nan)
        else:
            variance_estimate = sum(np.square(
                y_mean - y_array_for_current_x)) / float(len(y_array_for_current_x) - 1)
            standard_error_of_mean = np.sqrt(
                variance_estimate / len(y_array_for_current_x))
            final_error_list.append(standard_error_of_mean)
    # Convert all lists to np arrays
    final_x_values = np.array(final_x_list)
    final_y_values = np.array(final_y_list)
    final_error_values = np.array(final_error_list)
    # Plot the most recent point with a hardcoded but distinctive black diamond symbol
    if(most_recent_xy_pair != None):
        ax.plot(most_recent_xy_pair[0], most_recent_xy_pair[1], 'dr')
    # Plot and return the errorbar graph with the input kwargs
    return ax.errorbar(final_x_values, final_y_values, final_error_values, fmt=fmt, **kwargs)


"""Initializes a live-plot figure

    Creates and returns a new figure on which data can be live-plotted, which 
    displays as a new window.

    Parameters:

    num: int or str, optional. If passed, piped to matplotlib.pyplot.figure as num. Default None 
    can_make_interactive: bool. If true, the initialization function is allowed to turn on interactive mode 
        (which could interfere with other plotting). Default True. 

    Returns:
    (fig, ax)
    figure: A matplotlib.pyplot.Figure instance created by the method 
    ax: A matplotlib.pyplot.Axes instance attached to figure; this is what does the actual plotting
"""

def initialize_live_plot(num = None, can_make_interactive = True):
    if(can_make_interactive and not plt.isinteractive()):
        plt.ion() 
    fig = plt.figure(num = num) 
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
    return (fig, ax)


"""Updates a live_plot figure 

    Plots new data to a live-plotting figure object (or to the currently active one).
    Optionally does this in fancy_plot format.

    Parameters:

    x, y, fmt, **kwargs: Identical to those for ax.plot() 
    fancy: If true, applies fancy_plot to the input data, instead of plot
    ax: The Axes object on which the data should be live-plotted. If None, plt.gca() is called. 
    pause_length: The amount of time passed to plt.pause() to allow drawing. Default 0.001.
    clear_previous: Whether to clear the previous curves off of the live plot when a new one is plotted. Default True. 
    keep_settings: Whether axis settings (e.g. log scale, labels, etc.) are kept when the data is cleared. Default True.
"""
def update_live_plot(x, y, fmt = '', ax = None, fancy = False, clear_previous = True, keep_settings = True, pause_length = 0.001, **kwargs):
    if(ax == None):
        ax = plt.gca() 
    if(clear_previous):
        if(keep_settings):
            for artist in ax.lines + ax.collections:
                artist.remove() 
        else:
            ax.clear()
    if(fancy):
        fancy_plot(x, y, fmt = fmt, ax = ax, **kwargs)
    else:
        ax.plot(x, y, fmt, **kwargs) 
    plt.draw()
    plt.pause(pause_length)
    
    

    







def load_breadboard_client():
    """Wraps the breadboard import process

    Uses a system-specific .json config file, stored in the working directory, to import breadboard
    without hard-coded paths.

    Returns:
        BreadboardClient object; see breadboard documentation

    Raises:
        FileNotFoundError if no .json file exists
        KeyError if a .json file exists but does not contain the right keys
        ValueError if the breadboard_repo_path variable in the .json does not lead to a breadboard install
    """

    import json
    import sys
    import os
    with open(os.path.join(os.path.dirname(__file__), "breadboard_path_config.json")) as my_file:
        breadboard_dict = json.load(my_file)
        breadboard_repo_path = breadboard_dict.get("breadboard_repo_path")
        if(breadboard_repo_path is None):
            raise KeyError(
                "The .json config does not contain variable breadboard_repo_path")
        breadboard_API_config_path = breadboard_dict.get(
            "breadboard_API_config_path")
        if(breadboard_API_config_path is None):
            raise KeyError(
                "The .json config does not contain variable breadboard_API_config_path")
        sys.path.insert(0, breadboard_repo_path)
        try:
            from breadboard import BreadboardClient
        except ModuleNotFoundError:
            raise ValueError(
                "Unable to import breadboard using specified value of breadboard_repo_path")
        bc = BreadboardClient(breadboard_API_config_path)
    return bc


def get_newest_run_dict(bc, max_retries=10):
    """Gets newest run dictionary containing runtime, run_id, and parameters via breadboard client bc
    """
    retries = 0
    while retries < max_retries:
        try:
            resp = bc._send_message(
                'get', '/runs/', params={'lab': 'fermi1', 'limit': 1})
            if resp.status_code != 200:
                retries += 1
                time.sleep(0.3)
                continue
            new_run_dict = resp.json()['results'][0]
            break
        except JSONDecodeError:
            time.sleep(0.3)
            retries += 1

    new_run_dict_clean = {'runtime': new_run_dict['runtime'],
                          'run_id': new_run_dict['id'],
                          **new_run_dict['parameters']}
    return new_run_dict_clean

def get_newest_value(bc, key, max_tries_this_level = 6, delay_seconds = 5):
    tries = 0
    while (tries < max_tries_this_level):
        newest_run_dict = get_newest_run_dict(bc)
        if(key in newest_run_dict):
            return newest_run_dict[key] 
        else:
            time.sleep(delay_seconds) 
            tries += 1
    return None
        


def time_diff_in_sec(runtime_str, trigger_time):
    """Returns time difference in seconds between trigger time and runtime.
    Args:
        runtime_str: The string value from run_dict['runtime'], e.g. from get_newest_run_dict.
        trigger_time: a datetime object.
    """
    import datetime
    runtime = datetime.datetime.strptime(runtime_str, "%Y-%m-%dT%H:%M:%SZ")
    time_diff = (runtime - trigger_time)
    return time_diff.total_seconds()


def load_bec1serverpath():
    import json
    import os
    with open(os.path.join(os.path.dirname(__file__), "bec1server_config.json")) as my_file:
        breadboard_dict = json.load(my_file)
        bec1_server_path = breadboard_dict.get("BEC1server_path")
    return bec1_server_path


def load_analysis_path():
    """
    Returns a dictionary of folder paths containing .m files for analysis and basepath for where data is stored (locally or on a server).
    Requires a analysis_config.json file in the same folder as utility_functions.py.
    """
    import json
    import os
    with open(os.path.join(os.path.dirname(__file__), "analysis_config.json")) as my_file:
        analysis_paths = json.load(my_file)
    return analysis_paths

def get_newest_df(watchfolder, optional_column_names=[], existing_df=None):
    """Returns a dataframe constructed by getting data from breadboard for run_ids parsed from watchfolder directory.

    Args:
        watchfolder: path string.
        optional_column_names: a list of non-default columns to get from breadboard (e.g. non list-bound variables.)
        existing_df: previously created dataframe generated by calling get_newest_df. This prevents overloading breadboard with unnecessary get requests.
    """
    from measurement_directory import run_ids_from_txt, run_ids_from_filenames
    import os
    bc = load_breadboard_client()
    run_ids = []
    files = [filename for filename in os.listdir(watchfolder)]
    files_spe = []
    for file in files:
        if '.spe' in file:
            files_spe.append(file)
        elif 'run_ids.txt' in file:
            run_ids += run_ids_from_txt(
                os.path.abspath(os.path.join(watchfolder, file)))
    if existing_df is None:
        run_ids += run_ids_from_filenames(files_spe)
        df = bc.get_runs_df_from_ids(
            run_ids, optional_column_names=optional_column_names)
    else:
        run_ids = list(set(run_ids_from_filenames(files_spe)).union(set(run_ids)).difference(
            set(list(existing_df['run_id']))))
        if len(run_ids) > 0:
            df = existing_df.append(bc.get_runs_df_from_ids(run_ids,
                                                            optional_column_names=optional_column_names),
                                    sort=False,
                                    ignore_index=True)
        else:
            df = existing_df

    def custom_sort(df):
        # takes in df and returns same df with user-interaction columns first
        #['run_id','badshot','manual_foo1','manual_foo2', 'listboundvar1', etc.]
        cols = list(df.columns)
        manual_cols = []
        for col in cols:
            if 'manual' in col:
                manual_cols += [col]
        manual_cols = sorted(manual_cols)
        user_interact_cols = ['run_id'] + ['badshot'] + manual_cols
        for col in user_interact_cols:
            cols.remove(col)
        return df[user_interact_cols + cols]

    df = custom_sort(df)
    df.sort_values(by='run_id', ascending=False, inplace=True)
    return df