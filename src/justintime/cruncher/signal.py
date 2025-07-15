from typing import Tuple
from scipy import signal
import pandas as pd
import numpy as np

# Signal filtering
def butter_highpass(cutoff, fs, order=7):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def butter_highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = signal.lfilter(b, a, data)
    return pd.DataFrame(y, columns=data.columns)


def calc_fft_fft_sq(df: pd.DataFrame) -> Tuple[pd.DataFrame]:
    """
    Calculates the Fast Fourier Transform on the fragment waveforms
    
    Args:
        df (pd.DataFrame): Fragment dataframe
    
    Returns:
        list[pd.DataFrame]: Description
    
    """
    df_fft = df.apply(np.fft.fft)
    df_fft_sq = np.abs(df_fft) ** 2
    freq = np.fft.fftfreq(df.index.size, 0.512e-6)
    df_fft['Freq'] = freq
    df_fft_sq['Freq'] = freq
    # Cleanup fft2 for plotting
    df_fft_sq = df_fft_sq[df_fft_sq['Freq']>0]
    df_fft_sq = df_fft_sq.set_index('Freq')
    return df_fft, df_fft_sq


def calc_fft(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the Fast Fourier Transform on the fragment waveforms
    
    Args:
        df (pd.DataFrame): Fragment dataframe
    
    Returns:
        list[pd.DataFrame]: Description
    
    """
    df_fft = df.apply(np.fft.fft)
    freq = np.fft.fftfreq(df.index.size, 0.512e-6)
    df_fft['Freq'] = freq
    return df_fft
    

def calc_fft_sum_by_plane(df: pd.DataFrame, planes: dict) -> pd.DataFrame:
    """Calculates the sum by plane of the FFT 
    
    Args:
        df (pd.DataFrame): Fragment dataframe
        planes (dict): plane/offline channel map
    
    Returns:
        TYPE: Description
    """
    p = {i:[] for i in range(3)}
    p.update({k:list(set(v) & set(df.columns)) for k,v in planes.items()})

    df_sum_U = df[p[0]].sum(axis=1).to_frame()
    df_sum_U = df_sum_U.rename(columns= {0: 'U-plane'})
    df_sum_V = df[p[1]].sum(axis=1).to_frame()
    df_sum_V = df_sum_V.rename(columns= {0: 'V-plane'})
    df_sum_Z = df[p[2]].sum(axis=1).to_frame()
    df_sum_Z = df_sum_Z.rename(columns= {0: 'Z-plane'})
    df_sums = pd.concat([df_sum_U, df_sum_V, df_sum_Z], axis=1)


    df_fft = df_sums.apply(np.fft.fft)
    df_fft2 = np.abs(df_fft) ** 2
    freq = np.fft.fftfreq(df_sums.index.size, 0.512e-6)
    df_fft2['Freq'] = freq
    df_fft2 = df_fft2[df_fft2['Freq']>0]
    df_fft2 = df_fft2.set_index('Freq')

    return df_fft2.sort_index()


def calc_diffs(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:
    """Subtract two dataframes
    
    Args:
        df_a (TYPE): TR A dataframe
        df_b (TYPE): TR B dataframe
    
    Returns:
        TYPE: A-B dataframe
    """
    # value_offset=4096
    dt_a_rst = df_a.reset_index().drop('ts', axis=1)
    dt_b_rst = df_b.reset_index().drop('ts', axis=1)
    dt_ab_diff = (dt_a_rst.astype('int')-dt_b_rst.astype('int'))

    return dt_ab_diff

def calc_fft_phase(df_fft: pd.DataFrame, fmin: float=0., fmax: float=2e6) -> pd.DataFrame:
    df_phase = df_fft[(df_fft['Freq'] > fmin) & (df_fft['Freq'] < fmax)].drop('Freq', axis=1).apply(np.angle).mean().to_frame('phase')
    #print(df_phase)
    return df_phase
