import numpy as np
import pyloudnorm as pyln
from scipy.io.wavfile import write


def Generate(**kwargs):
    """
    Generate a Akeroyd signal.
    Requires:
        pyloudnorm
        numpy
        scipy

    Parameters
    ----------
    srate : int
        Sampling rate.
    shift : int
        Shift frequency in Hz.
    duration : int
        Total duration in seconds.
    bwd : int
        Bandwidth in Hz.
    centre : int
        Centre frequency of bandpass filter in Hz.
    init_direction : str
        Initial direction of shift. Either "left" or "right".

    Returns
    -------
    Output signal in 32-bit float wav format at current directory.
    """
    if kwargs["init_direction"] == "left":
        ud = -1
    elif kwargs["init_direction"] == "right":
        ud = 1

    lufs_targ = -14
    meter = pyln.Meter(kwargs["srate"])

    # 周波数をbin数に直す
    total_bin = kwargs["srate"] * kwargs["duration"]
    nq_bin = int(total_bin / 2)
    shift_bin = kwargs["shift"] * kwargs["duration"]
    bwd_bin = kwargs["bwd"] * kwargs["duration"]

    # 通過帯域の上限下限のbin番号
    bwdlow_bin = (kwargs["centre"] - int(kwargs["bwd"]/2)) * kwargs["duration"]
    bwdhigh_bin = (kwargs["centre"] + int(kwargs["bwd"]/2)
                   ) * kwargs["duration"]

    # 通過帯域内の信号生成
    fsig_inbwd = np.random.normal(size=bwd_bin) + 1j * \
        np.random.normal(size=bwd_bin)

    # ゼロ詰
    dc = 0
    btm_zero = np.zeros(bwdlow_bin, dtype=complex)
    top_zero = np.zeros(nq_bin - bwdhigh_bin, dtype=complex)
    fsig_left = np.hstack([dc, btm_zero, fsig_inbwd, top_zero])
    # 複素共役
    fsig_right = np.conj(np.flipud(fsig_left[1:nq_bin]))
    fsig = np.hstack([fsig_left, fsig_right])

    # shfit
    shft_bwdlow_bin = bwdlow_bin + int(ud * shift_bin)
    shft_bwdhigh_bin = bwdhigh_bin + int(ud * shift_bin)

    # ゼロ詰
    btm_zero = np.zeros(shft_bwdlow_bin, dtype=complex)
    top_zero = np.zeros(int(total_bin/2) - shft_bwdhigh_bin, dtype=complex)
    fshift_left = np.hstack([dc, btm_zero, fsig_inbwd, top_zero])
    fshift_right = np.conj(np.flipud(fshift_left[1:nq_bin]))
    # 複素共役
    fshift = np.hstack([fshift_left, fshift_right])

    # IFFT
    tsig = np.real(np.fft.ifft(fsig))*100
    tshift = np.real(np.fft.ifft(fshift))*100

    # cast
    tsig = tsig.astype(np.float32)
    tshift = tshift.astype(np.float32)

    # normalize
    lufs_sorc_l = meter.integrated_loudness(tsig)
    lufs_sorc_r = meter.integrated_loudness(tshift)

    tsig_n = pyln.normalize.loudness(tsig, lufs_sorc_l, lufs_targ)
    tshift_n = pyln.normalize.loudness(tshift, lufs_sorc_r, lufs_targ)

    sig = np.vstack([tsig_n, tshift_n])

    write('akeroyd.wav', kwargs["srate"], sig.T)


def GenrateInitIpd(**kwargs):
    """
    Generate a Akeroyd signal with initial IPD.
    Requires:
        pyloudnorm
        numpy
        scipy

    Parameters
    ----------
    srate : int
        Sampling rate.
    shift : int
        Shift frequency in Hz.
    duration : int
        Total duration in seconds.
    bwd : int
        Bandwidth in Hz.
    centre : int
        Centre frequency of bandpass filter in Hz.
    init_direction : str
        Initial direction of shift. Either "left" or "right".
    init_ipd : float
        Initial IPD in degree.
    file_name : str
        Output file name.(optional)
    wav : bool
        Output wav file or not. If True, output wavfile.(optional)

    Returns
    -------
    Output signal in 32-bit float wav format at current directory.
    """

    if kwargs["init_direction"] == "left":
        ud = -1
    elif kwargs["init_direction"] == "right":
        ud = 1

    if "file_name" in kwargs:
        file_name = kwargs["file_name"]
    else:
        file_name = "akeroyd_%s.wav" % kwargs["init_ipd"]

    lufs_targ = -14
    meter = pyln.Meter(kwargs["srate"])

    # 周波数をbin数に直す
    false_dur = kwargs["duration"] * 2
    total_bin = kwargs["srate"] * false_dur
    nq_bin = int(total_bin / 2)
    shift_bin = kwargs["shift"] * false_dur
    bwd_bin = kwargs["bwd"] * false_dur

    # 通過帯域の上限下限のbin番号
    bwdlow_bin = (kwargs["centre"] - int(kwargs["bwd"]/2)) * false_dur
    bwdhigh_bin = (kwargs["centre"] + int(kwargs["bwd"]/2)) * false_dur

    ## ---信号生成--- ##

    # 通過帯域内の信号生成
    fsig_inbwd = np.random.normal(size=bwd_bin) + 1j * \
        np.random.normal(size=bwd_bin)

    # ゼロ詰
    dc = 0
    btm_zero = np.zeros(bwdlow_bin, dtype=complex)
    top_zero = np.zeros(nq_bin - bwdhigh_bin, dtype=complex)
    fsig_left = np.hstack([dc, btm_zero, fsig_inbwd, top_zero])

    # 複素共役
    fsig_right = np.conj(np.flipud(fsig_left[1:nq_bin]))
    fsig = np.hstack([fsig_left, fsig_right])

    ## shfitの生成 ##
    shft_bwdlow_bin = bwdlow_bin + int(ud * shift_bin)
    shft_bwdhigh_bin = bwdhigh_bin + int(ud * shift_bin)

    # ゼロ詰
    btm_zero = np.zeros(shft_bwdlow_bin, dtype=complex)
    top_zero = np.zeros(nq_bin - shft_bwdhigh_bin, dtype=complex)

    fshift_left = np.hstack([dc, btm_zero, fsig_inbwd, top_zero])
    fshift_right = np.conj(np.flipud(fshift_left[1:nq_bin]))
    fshift = np.hstack([fshift_left, fshift_right])

    # IFFT
    tsig = np.real(np.fft.ifft(fsig))*100
    tshift = np.real(np.fft.ifft(fshift))*100

    # cast
    tsig = tsig.astype(np.float32)
    tshift = tshift.astype(np.float32)

    # 刺激の切り取り
    onset = int((kwargs["init_ipd"] / 360) *
                (1/kwargs["shift"]) * kwargs["srate"])
    offset = onset + (kwargs["duration"] * kwargs["srate"])
    tsig_out = tsig[onset:offset]
    tshift_out = tshift[onset:offset]

    # normalize
    lufs_sorc_l = meter.integrated_loudness(tsig_out)
    lufs_sorc_r = meter.integrated_loudness(tshift_out)

    tsig_n = pyln.normalize.loudness(tsig_out, lufs_sorc_l, lufs_targ)
    tshift_n = pyln.normalize.loudness(tshift_out, lufs_sorc_r, lufs_targ)

    sig = np.vstack([tsig_n, tshift_n])

    if "wav" in kwargs:
        write(file_name, kwargs["srate"], sig.T)
    else:
        return sig.T
