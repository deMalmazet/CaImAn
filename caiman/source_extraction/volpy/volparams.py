import logging
import numpy as np

class volparams(object):

    def __init__(self, fnames=None, fr=None, index=None, ROIs=None, weights=None,
                 context_size=35, censor_size=12, flip_signal=True, hp_freq_pb=1/3, nPC_bg=8, ridge_bg=0.01,  
                 hp_freq=1, threshold_method='simple', min_spikes=10, threshold=4, 
                 sigmas=np.array([1, 1.5, 2]), n_iter=2, weight_update='ridge', do_plot=True,  
                 do_cross_val=False, sub_freq=75, method='spikepursuit', superfactor=10, params_dict={}):
        """Class for setting parameters for voltage imaging. Including parameters for the data, motion correction and
        spike detection. The prefered way to set parameters is by using the set function, where a subclass is determined
        and a dictionary is passed. The whole dictionary can also be initialized at once by passing a dictionary
        params_dict when initializing the CNMFParams object.
        """
        self.data = {
            'fnames': fnames, # name of the movie, only memory map file for spike detection
            'fr': fr, # sample rate of the movie
            'index': index, # a list of cell numbers for processing
            'ROIs': ROIs, # a 3-d matrix contains all region of interests
            'weights': weights  # spatial weights generated by previous blocks as initialization  
        }

        self.volspike = {
            'context_size': context_size, #number of pixels surrounding the ROI to use as context
            'censor_size': censor_size, # number of pixels surrounding the ROI to censor from the background PCA;
            # roughly the spatial scale of scattered/dendritic neural signals, in pixels.
            'flip_signal': flip_signal, # whether to flip signal to find spikes
            'hp_freq_pb': hp_freq_pb, # high-pass frequency for removing photobleaching    
            'nPC_bg': nPC_bg, # number of principle components used for background subtraction
            'ridge_bg':ridge_bg, # regularization strength for Ridge to remove bg
            'hp_freq': hp_freq, #high-pass cutoff frequency to filter the signal after computing the trace
            'threshold_method':threshold_method, # 'simple' or 'adaptive_threshold' method for thresholding signals
            'min_spikes': min_spikes, # minimal spikes to be detected
            'threshold': threshold, # threshold for finding spikes
            'sigmas': sigmas, # spatial smoothing radius imposed on high-pass filtered movie
            'n_iter': n_iter, # number of iterations alternating between estimating temporal and spatial filters
            'weight_update': weight_update, # method for updating spatial weights 'NMF' or 'ridge'
            'do_plot': do_plot, # plot in the last iteration
            'do_cross_val': do_cross_val, # cross-validate to optimize regression regularization parameters
            'sub_freq': sub_freq, # frequency for extracting subthreshold osciilation
            'method': method, # 'spikepursuit' or 'atm' (adaptive template matching)
            'superfactor': superfactor, # factor for temporal super-resolution of spike times, e.g. 10 for 1/(10*framerate)
        }

        self.motion = {
            'border_nan': 'copy',  # flag for allowing NaN in the boundaries
            'gSig_filt': None,  # size of kernel for high pass spatial filtering in 1p data
            'max_deviation_rigid': 3,  # maximum deviation between rigid and non-rigid
            'max_shifts': (6, 6),  # maximum shifts per dimension (in pixels)
            'min_mov': None,  # minimum value of movie
            'niter_rig': 1,  # number of iterations rigid motion correction
            'nonneg_movie': True,  # flag for producing a non-negative movie
            'num_frames_split': 80,  # split across time every x frames
            'num_splits_to_process_els': None,
            'num_splits_to_process_rig': None,
            'overlaps': (32, 32),  # overlap between patches in pw-rigid motion correction
            'pw_rigid': False,  # flag for performing pw-rigid motion correction
            'shifts_opencv': True,  # flag for applying shifts using cubic interpolation (otherwise FFT)
            'splits_els': 14,  # number of splits across time for pw-rigid registration
            'splits_rig': 14,  # number of splits across time for rigid registration
            'strides': (96, 96),  # how often to start a new patch in pw-rigid registration
            'upsample_factor_grid': 4,  # motion field upsampling factor during FFT shifts
            'use_cuda': False  # flag for using a GPU
        }

        self.change_params(params_dict)
#%%
    def set(self, group, val_dict, set_if_not_exists=False, verbose=False):
        """ Add key-value pairs to a group. Existing key-value pairs will be overwritten
            if specified in val_dict, but not deleted.

        Args:
            group: The name of the group.
            val_dict: A dictionary with key-value pairs to be set for the group.
            set_if_not_exists: Whether to set a key-value pair in a group if the key does not currently exist in the group.
        """

        if not hasattr(self, group):
            raise KeyError('No group in CNMFParams named {0}'.format(group))

        d = getattr(self, group)
        for k, v in val_dict.items():
            if k not in d and not set_if_not_exists:
                if verbose:
                    logging.warning(
                        "NOT setting value of key {0} in group {1}, because no prior key existed...".format(k, group))
            else:
                if np.any(d[k] != v):
                    logging.warning(
                        "Changing key {0} in group {1} from {2} to {3}".format(k, group, d[k], v))
                d[k] = v

#%%
    def get(self, group, key):
        """ Get a value for a given group and key. Raises an exception if no such group/key combination exists.

        Args:
            group: The name of the group.
            key: The key for the property in the group of interest.

        Returns: The value for the group/key combination.
        """

        if not hasattr(self, group):
            raise KeyError('No group in CNMFParams named {0}'.format(group))

        d = getattr(self, group)
        if key not in d:
            raise KeyError('No key {0} in group {1}'.format(key, group))

        return d[key]

    def get_group(self, group):
        """ Get the dictionary of key-value pairs for a group.

        Args:
            group: The name of the group.
        """

        if not hasattr(self, group):
            raise KeyError('No group in CNMFParams named {0}'.format(group))

        return getattr(self, group)

    def change_params(self, params_dict, verbose=False):
        for gr in list(self.__dict__.keys()):
            self.set(gr, params_dict, verbose=verbose)
        for k, v in params_dict.items():
            flag = True
            for gr in list(self.__dict__.keys()):
                d = getattr(self, gr)
                if k in d:
                    flag = False
            if flag:
                logging.warning('No parameter {0} found!'.format(k))
        return self
