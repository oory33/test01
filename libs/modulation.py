import numpy as np


def SinMod(**kwargs):
    """
    Sinosoidal Amplitude Modulation.
    Requires:
        numpy

    Parameters
    ----------
    signal : ndarray()
        shape: (n,2)
        input signal(stereo)
    srate : int
        sampling rate
    freq : float
        modulation frequency(Hz)
    depth : float
        modulation depth(0-1)

    Returns
    -------
    Output signal in ndarray() .
    """
    signal = kwargs["signal"]
    duration = int(len(signal) / kwargs["srate"])

    alpha = 1
    beta = kwargs["depth"] * alpha

    # 正弦波生成
    phi = kwargs["freq"] / kwargs["srate"]
    index = np.array(range(kwargs["srate"]*duration))
    sin_sig = np.zeros(len(index))

    for i in range(len(index)):
        sin_sig[i] = np.sin(2 * np.pi * phi * index[i] + (3/2)*np.pi)

    # 正規化、最大値が1になる様に
    mod = (alpha + (beta * sin_sig)) / (1 + kwargs["depth"])

    # AM変調
    mod_sig_l = mod * signal.T[0]
    mod_sig_r = mod * signal.T[1]

    mod_sig_n = np.vstack([mod_sig_l, mod_sig_r]).T

    return mod_sig_n


# raised-cosのOnset/Offset
def RaisedCos(**kwargs):
    """
    Raised-cosine window modulation. Cuttoff would be half of the Nyquist frequency.

    Requires:
        numpy

    Parameters
    ----------
    signal : ndarray()
        shape: (n,2)
        input signal(stereo)
    srate : int
        sampling rate in Hz.
    beta : float
        window parameter.
    length : float
        window length in miliseconds.

    Returns
    -------
    Output signal in ndarray().
    """

    signal = kwargs["signal"]
    window_length = int(kwargs["srate"] * kwargs["length"] / 1000)  # in bins
    T = 1 / window_length

    a_1 = int((1-kwargs["beta"])/(2 * T))
    a_2 = int((1+kwargs["beta"])/(2 * T))

    H_f = np.zeros(window_length, dtype=float)

    for i in range(a_1):
        H_f[i] = 1

    for i in range(a_1, a_2):
        H_f[i] = 0.5 * (1 + np.cos((np.pi*T/kwargs["beta"]) * (i - a_1)))

    H_on = np.conj(np.flip(H_f))

    sig_l = signal.T[0]
    sig_r = signal.T[1]

    sig_l_raise = sig_l[0:window_length] * H_on
    sig_l_mid = sig_l[window_length:len(sig_l)-window_length]
    sig_l_release = sig_l[len(sig_l)-window_length:len(sig_l)] * H_f

    sig_r_raise = sig_r[0:window_length] * H_on
    sig_r_mid = sig_r[window_length:len(sig_r)-window_length]
    sig_r_release = sig_r[len(sig_r)-window_length:len(sig_r)] * H_f

    sig_l = np.hstack([sig_l_raise, sig_l_mid, sig_l_release])
    sig_r = np.hstack([sig_r_raise, sig_r_mid, sig_r_release])

    out = np.vstack([sig_l, sig_r]).T

    return out


def HalfSinMod(**kwargs):
    """
    Half-sin modulation.

    Requires:
        numpy

    Parameters
    ----------
    signal : ndarray()
        shape: (n,2)
        input signal(stereo)
    srate : int
        sampling rate in Hz.
    freq : float
        modulation frequency in Hz.
    depth : float
        modulation depth(0-1).

    Returns
    -------
    Output signal in ndarray().
    """

    signal = kwargs["signal"]
    duration = int(len(signal) / kwargs["srate"])

    alpha = 1
    beta = kwargs["depth"] * alpha

    # 正弦波生成
    phi = kwargs["freq"] / kwargs["srate"]
    index = np.array(range(kwargs["srate"]*duration))
    sin_sig = np.zeros(len(index))

    for i in range(len(index)):
        # 偶数回目の回転なら
        if (index[i] // (1 / phi)) % 2 == 0:
            sin_sig[i] = np.sin(2 * np.pi * phi * index[i] + ((3/2)*np.pi))
        else:
            sin_sig[i] = -1

    # 正規化、最大値が1になる様に
    mod = (alpha + (beta * sin_sig)) / (1 + kwargs["depth"])

    # AM変調
    mod_sig_l = mod * signal.T[0]
    mod_sig_r = mod * signal.T[1]

    mod_sig_n = np.vstack([mod_sig_l, mod_sig_r]).T

    return mod_sig_n
