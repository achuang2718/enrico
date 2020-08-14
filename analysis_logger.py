breadboard_repo_path = r'D:\Fermidata1\enrico\breadboard-python-client\\'
import ipywidgets as widgets
from ipywidgets import interact
from measurement_directory import *
import sys
sys.path.insert(0, breadboard_repo_path)
from breadboard import BreadboardClient
# enter your path to the API_config
bc = BreadboardClient(config_path='API_CONFIG_fermi1.json')
import os
import time
import datetime
import shutil
import warnings
import enrico_bot
from image_watchdog import getFileList
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('analysis_debugging.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)


# loading takes a while, don't run this if testing
def load_matlab_engine():
    print('loading matlab engine...')
    import matlab.engine
    eng = matlab.engine.start_matlab()
    print('matlab engine loaded')
    return eng


warnings.filterwarnings(
    "ignore", "Your application has authenticated using end user credentials")
warnings.filterwarnings(
    "ignore", "Could not find appropriate MS Visual C Runtime")
bc = BreadboardClient(config_path='API_CONFIG_fermi1.json')


def main(analysis_type, watchfolder, load_matlab=True):
    refresh_time = 1  # seconds
    print("\n\n Watching this folder for changes: " + watchfolder + "\n\n")

    # loading matlab takes a while, disable if testing
    if load_matlab:
        eng = load_matlab_engine()

    # define subfunction analysis_function which outputs analysis and settings dictionaries
    # define analyzed_var_names list manually, these are the scalar values most easily parsed from Carsten's analysis MATLAB structs.
    # TODO: parse all of Carsten's MATLAB struct, not just scalar values.
    if analysis_type == 'fake analysis':
        import matlab_wrapper.fake_analysis1 as analysis_function
        import matlab_wrapper.fake_analysis1_var_names as analyzed_var_names
    elif analysis_type == 'fake analysis 2':
        import matlab_wrapper.fake_analysis2 as analysis_function
        import matlab_wrapper.fake_analysis2_var_names as analyzed_var_names
    elif analysis_type == 'ycam':
        from matlab_wrapper import getYcamAnalysis
        import matlab_wrapper.ycam_analyzed_var_names as analyzed_var_names

        def analysis_function(filepath, previous_settings=None):
            if previous_settings is None:
                matlab_dict = getMATLABanalysis(eng, filepath)
            else:
                matlab_dict = getMATLABanalysis(eng, filepath, marqueeBox=previous_settings['marqueeBox'],
                                                normBox=previous_settings['normBox'])
            analysis_dict, settings = matlab_dict['analysis'], matlab_dict['settings']
            return analysis_dict, settings
    elif analysis_type == 'zcam_dual_imaging':
        from matlab_wrapper import getDualImagingAnalysis
        import matlab_wrapper.dual_imaging_analyzed_var_names as analyzed_var_names

        def analysis_function(filepath, previous_settings=None):
            if previous_settings is None:
                matlab_dict = getDualImagingAnalysis(eng, filepath)
    #         else:
    #             matlab_dict = getMATLABanalysis(eng, filepath, marqueeBox = previous_settings['marqueeBox'],
    #                                            normBox = previous_settings['normBox'])
            analysis_dict = matlab_dict['analysis']
            settings = None
            return analysis_dict, settings

    # wrap analysis_function
    def analyze_image(image_filename, previous_settings=None, output_previous_settings=True):
        # TODO adapt for triple imaging later
        abs_image_path = os.path.join(os.path.join(
            os.getcwd(), watchfolder), image_filename)
        logger.debug('{file} analyzing: '.format(file=image_filename))
        analysis_dict, settings = analysis_function(
            abs_image_path, previous_settings)
        if not output_previous_settings:
            settings = None  # forces user to select new marquee box for each shot
        for key in analyzed_var_names:
            logger.debug(key, analysis_dict[key])
        return analysis_dict, settings

    previous_settings = None
    unanalyzed_files = []
    done_files = []
    append_mode = True

    # Main Loop
    while True:
        if not os.path.exists(watchfolder):
            time.sleep(refresh_time)
            continue
        else:
            files, _ = getFileList(watchfolder)
            fresh_files = sorted(list(set(files).difference(
                set(done_files)).difference(set(unanalyzed_files))))
            unanalyzed_files += fresh_files  # push newest files to top of stack

        for file in reversed(unanalyzed_files):  # start from top of stack
            run_id = run_id_from_filename(file)
            if append_mode:
                run_dict = bc._send_message(
                    'get', '/runs/' + str(run_id) + '/').json()
                if set(analyzed_var_names).issubset(set(run_dict.keys())):
                    popped_file = [unanalyzed_files.pop()]
                    done_files += popped_file
                    continue
            try:
                analysis_dict, previous_settings = analyze_image(
                    file, previous_settings)
                popped_file = [unanalyzed_files.pop()]
                done_files += popped_file
            except:
                analysis_dict = {}
                warning_message = str(
                    run_id) + 'could not be analyzed. Skipping for now.'
                warnings.warn(warning_message)
                logger.warn(warning_message)
            resp = bc.append_analysis_to_run(run_id, analysis_dict)
            print('\n')

        time.sleep(refresh_time)