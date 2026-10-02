#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MONTE CARLO SIMULATION OF A COARSE-FINE TDC DRIVEN BY A JITTERED CLOCK
----------------------------------------------------------------------

Glossary
---------
Clock
    Electronic signal strictly alternating between LOW (0) and HIGH (1) logic
    states, used for system synchronization. In HEP collider experiments, a
    clock synchronized with the accelerator RF is forwarded from back-end to
    front-end electronics (including TDCs). TDCs determine the timing of a 
    physics event by counting elapsed clock ticks relative to the Bunch Cros-
    sing (BX) ID within a specific orbit.

Rising Edge
    0 to 1 voltage transition in the clock signal. Each rising edge represents
    a clock "tick" (a 1-to-0 transition is termed "falling edge").

Coarse-Fine Time Measurement
    A two-step measurement procedure used by TDCs:
      - COARSE step: counts the total number of clock ticks elapsed from the
        start of an orbit.
      - FINE step: measures the sub-period fractional remainder between the
        event arrival and the next clock tick.

TAC (Time-to-Amplitude/Analog Converter)
    Analog circuit responsible for performing the fine step measurement.

LSB (Least Significant Bit)
    The minimum time interval resolved by the TDC, defining its nominal 
    time resolution.

DCD (Duty Cycle Distortion) 
    Systematic deviation of the clock duty cycle from its nominal 50% value.
    This causes the time duration of HIGH states to differ from that of LOW 
    states, shifting the relative position of falling edges. Critical when 
    TDC architectures use both clock edges for fine time measurements.   

Clock Jitter
    Random temporal fluctuations of the actual clock tick relative to its ideal
    period. Since the TDC assumes an ideal clock, any injected jitter directly
    propagates into measurement uncertainty.

USAGE
-----
    python3 tdc_jitter_sim.py
    (edit the PARAMETERS block below to explore other configurations)
    
    This program prints a report on screen and saves 5 PNG images in the
    same folder as this file.

Dependencies: 
------------
numpy, matplotlib

"""

import numpy as np
import matplotlib
matplotlib.use("Agg")          
import matplotlib.pyplot as plt
import os

# INPUT PARAMETERS  --  EDIT HERE ONLY
#-------------------------------------
# Units are given in square brackets: ps = picoseconds, Hz = ticks per second

F_CLK        = 400e6           # [Hz]  reference clock frequency            (Baseline: 400 million ticks per second)
T_CLK        = 1e12 / F_CLK    # [ps]  time between two ticks = 1 / F_CLK   (Baseline: 2500 ps)

LSB          = 25.0            # [ps]  TAC resolution                       (Baseline: 25 ps)
SIGMA_RJ     = 7.11            # [ps]  RMS of the random jitter (RJ) of the clock ticks     (Baseline: 7.11 ps)
DCD_PP       = 4.3             # [ps]  DCD, peak-to-peak (total displacement range)         (Baseline: 4.3 ps)

# Split of the RJ power between white phase noise and random walk:
#----------------------------------------------------------------
# "White"       = every tick is displaced by a random amount, unrelated to previous ticks
# "Random walk" = each tick inherits the displacement of the previous one plus a small new random push (errors build up slowly)
# Variance (sigma squared) = adds up between independent noise sources

ALPHA_RW     = 0.3             # fraction of variance in random-walk term (= 0 fully white; = 1 fully random walk)

# Periodic jitter: 
#-----------------
# sinusoidal disturbance at a fixed frequency, pushes ticks back and forth repeatedly

PJ_AMP       = 0.0             # [ps]  periodic jitter peak amplitude (= 0 to disable)
PJ_FREQ      = 10e6            # [Hz]  disturbance frequency

# TAC Integral Non-Linearity (INL): 
#----------------------------------
# oversizing/undersizing of the fine time interval due to non-uniform TAC resolution; sinusoidal distortion over fine range

INL_AMP      = 0.0             # [ps]  peak INL amplitude (= 0 for ideal, undistorted TAC)

# Clock edges used for fine measurement:
#---------------------------------------
# False = fine on RISING edge only (Baseline)
# True  = nearest edge (RISING or FALLING), range halved, DCD activated
USE_NEAREST_EDGE = False       

#Number of simulated events:
#---------------------------
# More events --> smoother statistics, slower run
N_EVENTS = 200_000         

# Number of generated clock ticks:
#---------------------------------
# time span over which events are spread

N_CLK_EDGES = 400_000 

# Random Number Generator seed:
#------------------------------
# same seed = same results st every run

SEED = 12345            

# Output folder:
#---------------
# where PNG images are saved

OUTDIR = os.path.dirname(os.path.abspath(__file__))   


# 1) JITTERED CLOCK GENERATION
# -----------------------------  

def generate_clock_edges(n_edges, t_clk, sigma_rj, alpha_rw,
                         pj_amp, pj_freq, rng):
    """
    Clock RISING edges tick slightly early or late each time relative to the ideal clock; individual tick displacement ("phase jitter")
    given by the sum of a white + a random-walk component.

    Inputs (all times in ps):
        n_edges  : ticks to generate
        t_clk    : ideal time between two ticks
        sigma_rj : wanted RJ typical size
        alpha_rw : fraction of RJ
        pj_amp, pj_freq : periodic jitter amplitude and frequency
        rng      : random number generator

    Returns:
        t_edges : array [ps] rising-edge instants (with jitter)
        phi     : array [ps] individual edge phase deviation 
    """
    # White component:
    #-----------------
    # individual tick displacement drawn from a Gaussian distribution; variances add up, so a fraction (1 - alpha_rw) of total variance
    # is assigned (if fraction is zero, no noise is generated)

    var_white = (1.0 - alpha_rw) * sigma_rj**2
    phi_white = rng.normal(0.0, np.sqrt(var_white), n_edges) if var_white > 0 \
                else np.zeros(n_edges)

    # Random-walk component:
    #-----------------------
    # generates a random-walk profile and simulates stabilizing effect of Phase-Locked Loop(PLL)/calibration circuits by removing mean offset.
    # (A PLL keeps an oscillator synchronised to a reference, preventing it from wandering indefinitely)
    var_rw = alpha_rw * sigma_rj**2
    if var_rw > 0:
        rw = np.cumsum(rng.normal(0.0, 1.0, n_edges))   # generates cumulative random steps
        rw = rw - np.mean(rw)                           # removes mean offset (shift the curve to average zero) 
        rw = rw / np.std(rw) * np.sqrt(var_rw)          # rescales to wanted typical size
    else:
        rw = np.zeros(n_edges)

    # Periodic jitter component:
    #--------------------------
    # sine wave added to tick instants

    k = np.arange(n_edges)     # tick numbers
    if pj_amp > 0:
        phi_pj = pj_amp * np.sin(2 * np.pi * pj_freq * (k * t_clk * 1e-12)) # ideal tick time k = k * t_clk (ps to s conversion with factor 1e-12)
    else:
        phi_pj = np.zeros(n_edges)

    # Total displacement of each tick:
    #---------------------------------
    # sum of the three contributions.
    
    phi = phi_white + rw + phi_pj

    # Ideal instants plus jitter: list of REAL tick times.
    t_edges = k * t_clk + phi
    return t_edges, phi


# 2) TDC MODEL
# -------------
# TDC simulation: given a list of real clock ticks and events, works out the TDC time reported for each event

def quantize_tac(dt, lsb, inl_amp, fine_range):
    """
    TAC quantization with a fixed LSB and optional sinusoidal INL.

    Note: fine measurement can only report multiples of the LSB; difference between true and TDC output value is "quantization error".
    INL modelled as a systematic error depending on position within fine range. 
    Inside the TAC, interval is turned into a voltage ramp: if the ramp is not perfectly straight, reading is slightly distorted.

    Inputs:
        dt         : interval(s) to be measured [ps]
        lsb        : step size [ps]
        inl_amp    : ramp distortion size [ps] (0 = none)
        fine_range : full range covered by fine measurement [ps]
    """
    if inl_amp > 0:
        dt = dt + inl_amp * np.sin(2 * np.pi * dt / fine_range)
    
    return np.floor(dt / lsb) * lsb + lsb / 2.0     # floor(dt / lsb) = how many whole steps fit in dt (rounding down);
                                                    # adding lsb / 2 places reported value in the MIDDLE of the step
                                                    # (so that rounding error averages to zero instead of being always in same direction)


def simulate_tdc(n_events, t_edges, t_clk, lsb, dcd_pp,
                 use_nearest_edge, inl_amp, rng):
    """
    Simulate measurement of n_events asynchronous events.

    For every event, TDC:
      1. finds first clock tick that comes AFTER the event;
      2. coarse stage knows the number of that tick and assumes it happened at (number * ideal period);
      3. fine stage measures short time between the event and that tick, rounded to LSB;
      4. reported time is (tick time) - (fine interval).
    Error arises from quantization error + TDC assuming tick to be ideal (wile it is jittered)

    Returns:
        t_true  : [ps] true arrival time of the event
        t_meas  : [ps] timestamp reconstructed by the TDC
        err     : [ps] measurement error (t_meas - t_true)
    """
    # Events with uniform phase:
    #---------------------------
    # spread uniformly over span covered by the clock, leaving margin at both ends; events are asynchronous
    #to clock ticks. A margin of 10 ticks avoids events too close to the start/end of the list

    t_min = t_edges[10]
    t_max = t_edges[-10]
    t_true = rng.uniform(t_min, t_max, n_events)
    t_true = np.sort(t_true)     # sorted in time, just for convenience

    if not use_nearest_edge:
        # ---------------------------------------------------------------------
        # CASE A: standard fine measurement (Event -> NEXT Rising Edge)
        # CDC has no effect: only rising edges used for timing reconstruction.
        # ---------------------------------------------------------------------
        
        # Find index of the first rising edge occurring immediately after the event
        idx = np.searchsorted(t_edges, t_true, side="right")
        t_edge_next = t_edges[idx]

        # Calculate unquantized fine interval [0, T_clk) and coarse tick count
        dt_fine = t_edge_next - t_true
        coarse = idx
        fine_range = t_clk

        # Apply TAC quantization (LSB resolution + INL distortion)
        dt_q = quantize_tac(dt_fine, lsb, inl_amp, fine_range)

        # Time reconstruction: TDC assumes an ideal clock (coarse * T_clk) and subtracts
        # measured fine interval to reconstruct event arrival time

        t_meas = coarse * t_clk - dt_q

    else:
        # -------------------------------------------------------------------
        # CASE B: Nearest Edge Measurement (Rising OR Falling Edge)
        # Fine measurement range halved to T_clk / 2.
        # Falling edges shifted from ideal half-periods by delta = DCD_pp / 2 
        # due to DCD != 50%
        # -------------------------------------------------------------------

        # Calculate falling edges positions with DCD displacement
        delta = dcd_pp / 2.0
        t_fall = t_edges + t_clk / 2.0 + delta          

        # Merge rising and falling edges into one sorted array
        t_all = np.sort(np.concatenate([t_edges, t_fall]))

        # Find next edge (rising or falling) occurring after the event
        idx = np.searchsorted(t_all, t_true, side="right")
        idx = np.clip(idx, 1, len(t_all) - 1)    # keeps index inside valid range
        t_edge_next = t_all[idx]

        # Calculate fine interval [0, t_clk / 2) and apply TAC quantization
        dt_fine = t_edge_next - t_true
        fine_range = t_clk / 2.0
        dt_q = quantize_tac(dt_fine, lsb, inl_amp, fine_range)

        # Time reconstruction:
        # TDC logic assumes perfectly symmetric half-periods (unaware of DCD).
        # This discrepancy introduces a deterministic (i.e. always the same) time error if
        # a displaced falling edge is used as timing reference.
        
        t_meas = idx * (t_clk / 2.0) - dt_q

    # Measurement Error: Difference between reported time and true time
    err = t_meas - t_true

    # Remove mean offset (constant calibration error) so that only the random scatter 
    #around the average remains
    
    err = err - np.mean(err)

    return t_true, t_meas, err


# 3) ANALYSIS AND COMPARISON WITH ANALYTICAL BUDGET
# -------------------------------------------------
# compare simulation with result predicted by theoretical model

def analytical_budget(sigma_rj, lsb, dcd_pp, use_nearest_edge):
    """
    Computes analytical resolution budget via Root-Sum-Square (RSS) combination.

    Calculates expected total time resolution (without running MC simulation) 
    assuming independent and uncorrelated error sources.
    
    Returns:
            s_q (float)   : [ps] quantization noise standard deviation (LSB / sqrt(12))
            s_dcd (float) : [ps] RMS contribution from DCD
            s_tot (float) : [ps] combined total resolution (RSS of jitter, DCD, and quantization)

    """
    s_q = lsb / np.sqrt(12.0)
    s_dcd = (dcd_pp / 2.0) if use_nearest_edge else 0.0
    s_tot = np.sqrt(sigma_rj**2 + s_dcd**2 + s_q**2)
    return s_q, s_dcd, s_tot


def print_report(err, sigma_rj, lsb, dcd_pp, use_nearest_edge):
    """
    Print the numerical results on screen and return (sigma_sim, sigma_RSS).

    Report is structured into 4 blocks: 
        Input Parameters 
        Analytical Budget (RSS) Results
        MC Simulation Results
        Single Measurement Confidence Intervals

    """
    s_q, s_dcd, s_tot = analytical_budget(sigma_rj, lsb, dcd_pp, use_nearest_edge)
    s_sim = np.std(err)                      # typical size of the simulated errors

    print("=" * 70)
    print(" COARSE-FINE TDC SIMULATION RESULTS")
    print("=" * 70)
    print(f"  Clock            : {F_CLK/1e6:.0f} MHz   (T = {T_CLK:.0f} ps)")
    print(f"  TAC LSB          : {lsb:.1f} ps")
    print(f"  Fine mode        : {'nearest edge' if use_nearest_edge else 'rising edge only'}")
    print(f"  Events simulated : {len(err):,}")
    print("-" * 70)

    #Iindividual error contributions and their relative share of total variance (total sum = 100%).
    print("  ANALYTICAL BUDGET (RSS)")
    print(f"    sigma_RJ       = {sigma_rj:6.2f} ps   ({100*sigma_rj**2/s_tot**2:5.1f} % of variance)")
    print(f"    sigma_DCD      = {s_dcd:6.2f} ps   ({100*s_dcd**2/s_tot**2:5.1f} % of variance)")
    print(f"    sigma_quant    = {s_q:6.2f} ps   ({100*s_q**2/s_tot**2:5.1f} % of variance)")
    print(f"    --------------------------------")
    print(f"    sigma_TOT      = {s_tot:6.2f} ps")
    print("-" * 70)
    print("  MONTE CARLO SIMULATION")
    print(f"    sigma_sim      = {s_sim:6.2f} ps")

    # Discrepancy between simulated RMS and analytical RSS
    print(f"    dev. vs RSS    = {100*(s_sim - s_tot)/s_tot:+6.2f} %") 

    # Peak-to-Peak Error (maximum span of observed measurement errors) 
    print(f"    peak-to-peak   = {np.ptp(err):6.2f} ps")               

    #Empirical Coverage: Fractions of errors bounded by 2*sigma and 3*sigma, compared to ideal Gaussian values (95.45% and 99.73%).
    print(f"    |err| < 2 sig  = {100*np.mean(np.abs(err) < 2*s_sim):5.2f} %  (gaussian: 95.45 %)")
    print(f"    |err| < 3 sig  = {100*np.mean(np.abs(err) < 3*s_sim):5.2f} %  (gaussian: 99.73 %)")
    print("-" * 70)

    print("  CONFIDENCE INTERVALS ON A SINGLE MEASUREMENT")
    print(f"    68 % (1 sigma) : +/- {1*s_sim:5.2f} ps")
    print(f"    95 % (2 sigma) : +/- {2*s_sim:5.2f} ps")
    print(f"    99.7% (3 sigma): +/- {3*s_sim:5.2f} ps")
    print("=" * 70)
    return s_sim, s_tot


# 4) PLOTS
# ---------
# Each function below generates a distinct plot and saves it as a PNG image

def plot_histogram(err, s_tot, fname):
    """
    Plots normalized histogram of simulated measurement errors and superimposes a theoretical 
    Gaussian distribution curve from the analytical RSS error budget 

    """
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(err, bins=120, density=True, color="#4C72B0",
            alpha=0.75, edgecolor="none", label="simulated error")

    # Gaussian
    x = np.linspace(err.min(), err.max(), 500)
    g = np.exp(-x**2 / (2 * s_tot**2)) / (s_tot * np.sqrt(2 * np.pi))
    ax.plot(x, g, "r--", lw=2, label=f"RSS gaussian ($\\sigma$={s_tot:.2f} ps)")

    ax.set_xlabel("timestamp error [ps]")
    ax.set_ylabel("probability density")
    ax.set_title("TDC error distribution (single-shot)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(fname, dpi=130)
    plt.close(fig)


def plot_dither_comparison(fname, rng_seed=999):
    """
    Demonstrates the Dither effect: how clock jitter alters error distribution.

    When RJ is added to a quantized measurement, it acts as a "dither" signal, smoothing 
    quantization noise:
      - Low Jitter case (RJ << LSB) : quantization dominates and error distribution is 
                                      rectangular (pure uniform quantization).
      - High Jitter case (RJ ~ LSB) : jitter smooths out quantization steps, transforming 
                                      overall distribution into a smooth Gaussian 

    This function generates 4-panels comparing error histograms across four 
    jitter levels (0.5 ps, 2.0 ps, 7.11 ps, and 20.0 ps)

    """
    rng = np.random.default_rng(rng_seed)
    sigmas = [0.5, 2.0, 7.11, 20.0]
    fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)

    # For each jitter value generate a clock, simulate TDC, plot errors.
    for ax, s in zip(axes, sigmas):
        t_edges, _ = generate_clock_edges(120_000, T_CLK, s, ALPHA_RW,
                                          0.0, PJ_FREQ, rng)
        _, _, err = simulate_tdc(60_000, t_edges, T_CLK, LSB, DCD_PP,
                                 USE_NEAREST_EDGE, INL_AMP, rng)
        ax.hist(err, bins=80, density=True, color="#55A868", alpha=0.8)
        ax.set_title(f"$\\sigma_{{RJ}}$ = {s:.2f} ps\n$\\sigma_{{tot}}$ = {np.std(err):.2f} ps",
                     fontsize=10)
        ax.set_xlabel("error [ps]")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("density")
    fig.suptitle(f"Dither effect: quantization (LSB = {LSB:.0f} ps) vs random jitter",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(fname, dpi=130)
    plt.close(fig)


def plot_sweep(fname):
    """
    Plots resolution response over a parameter sweep of clock jitter (sigma_RJ).

    Evaluates overall TDC time resolution across a range of jitter values (0.5 to 30 ps) 
    to identify transition between quantization-dominated and jitter-dominated regimes.

    PLot Elements:
      - Blue dots          : simulation results
      - Red dashed line    : analytical RSS model curve
      - Grey dotted line   : LSB quantization noise floor (sigma_q = LSB / sqrt(12)).
      - Green vertical line: jitter value used in the primary simulation

    """
    rng = np.random.default_rng(2024)
    rj_vals = np.linspace(0.5, 30, 18)       # 18 jitter values from 0.5 to 30 ps
    sim, ana = [], []                        # results: simulated and from the formula

    for s in rj_vals:
        t_edges, _ = generate_clock_edges(120_000, T_CLK, s, ALPHA_RW,
                                          0.0, PJ_FREQ, rng)
        _, _, err = simulate_tdc(60_000, t_edges, T_CLK, LSB, DCD_PP,
                                 USE_NEAREST_EDGE, INL_AMP, rng)
        sim.append(np.std(err))
        ana.append(analytical_budget(s, LSB, DCD_PP, USE_NEAREST_EDGE)[2])

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(rj_vals, ana, "r--", lw=2, label="analytical RSS budget")
    ax.plot(rj_vals, sim, "o-", color="#4C72B0", lw=1.8, ms=5,
            label="Monte Carlo")
    ax.axhline(LSB / np.sqrt(12), color="gray", ls=":",
               label=f"quantization floor = {LSB/np.sqrt(12):.2f} ps")
    ax.axvline(SIGMA_RJ, color="green", ls="-.", alpha=0.7,
               label=f"operating point ($\\sigma_{{RJ}}$ = {SIGMA_RJ} ps)")

    ax.set_xlabel("clock $\\sigma_{RJ}$ [ps]")
    ax.set_ylabel("total $\\sigma$ of the timestamp error [ps]")
    ax.set_title("TDC uncertainty versus clock jitter")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(fname, dpi=130)
    plt.close(fig)


def plot_dcd_comparison(fname):
    """
    Direct comparison: fine stage on RISING edge only vs. NEAREST EDGE.

    This plot shows the impact of DCD on time reconstruction:
        - Rising Edge Only (Left): immune to DCD since only 0-to-1 clock transitions are used
          (unimodal, single-peak) error distribution);
        - Nearest Edge (Right): utilizes both rising and falling edges; displaced falling edges 
          split measurement errors (bimodal, two-peak) distribution).

    """
    rng = np.random.default_rng(777)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    #Same simulation twice, changing clocking scheme only (False / True).
    for ax, nearest, title in zip(
            axes, [False, True],
            ["RISING edge only\n(DCD does not enter)",
             "NEAREST EDGE\n(DCD active -> bimodality)"]):
        dcd = DCD_PP
        t_edges, _ = generate_clock_edges(200_000, T_CLK, SIGMA_RJ, ALPHA_RW,
                                          0.0, PJ_FREQ, rng)
        _, _, err = simulate_tdc(100_000, t_edges, T_CLK, LSB, dcd,
                                 nearest, INL_AMP, rng)
        ax.hist(err, bins=100, density=True, color="#C44E52", alpha=0.8)
        ax.set_title(f"{title}\n$\\sigma$ = {np.std(err):.2f} ps", fontsize=10)
        ax.set_xlabel("error [ps]")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("density")
    fig.suptitle(f"Effect of DCD ({DCD_PP} ps pp) depending on the clocking scheme",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(fname, dpi=130)
    plt.close(fig)


def plot_spectrum(err, fname):
    """
    Frequency-domain analysis via Fast Fourier Transform (FFT) on measurement errors, 
    to detect deterministic periodic disturbances (spurs):
        - Flat Noise Floor (PJ_AMP = 0): purely stochastic errors (RJ and quantization) 
          produce flat, broadband white-noise spectrum.
        - Spectral Spurs (PJ_AMP > 0): periodic jitter appears as narrow peaks above noise floor.

    """
    # Use a number of samples that is a power of two (what the FFT handles
    # best): n is the largest power of two not exceeding the number of data.
    n = 2 ** int(np.floor(np.log2(len(err))))
    e = err[:n] - np.mean(err[:n])           # subtract the average so that the zero-frequency peak does not dominate
    # The Hanning window gently fades the data to zero at both ends, which
    # prevents artificial peaks caused by cutting the data abruptly.
    E = np.abs(np.fft.rfft(e * np.hanning(n))) / n

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.semilogy(np.linspace(0, 0.5, len(E)), E + 1e-12, lw=0.7, color="#8172B2")
    ax.set_xlabel("normalised frequency (cycles / sample)")
    ax.set_ylabel("amplitude [ps]")
    ax.set_title("Timestamp error spectrum (looking for spurs / Pj)")
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(fname, dpi=130)
    plt.close(fig)


# MAIN
# -------

def main():
# random number generator, initialised with the chosen seed
    rng = np.random.default_rng(SEED)       

    # 1) jittered clock generation
    t_edges, phi = generate_clock_edges(N_CLK_EDGES, T_CLK, SIGMA_RJ,
                                        ALPHA_RW, PJ_AMP, PJ_FREQ, rng)
    print(f"[clock] sigma of the generated phase = {np.std(phi):.3f} ps "
          f"(target {SIGMA_RJ} ps)")

    # 2) TDC simulation
    t_true, t_meas, err = simulate_tdc(N_EVENTS, t_edges, T_CLK, LSB, DCD_PP,
                                       USE_NEAREST_EDGE, INL_AMP, rng)

    # 3) numerical report
    s_sim, s_tot = print_report(err, SIGMA_RJ, LSB, DCD_PP, USE_NEAREST_EDGE)

    # 4) plots
    plot_histogram(err, s_tot, os.path.join(OUTDIR, "tdc_error_histogram.png"))
    plot_dither_comparison(os.path.join(OUTDIR, "tdc_dither_effect.png"))
    plot_sweep(os.path.join(OUTDIR, "tdc_jitter_sweep.png"))
    plot_dcd_comparison(os.path.join(OUTDIR, "tdc_dcd_effect.png"))
    plot_spectrum(err, os.path.join(OUTDIR, "tdc_error_spectrum.png"))

    print("\nPlots saved in:", OUTDIR)


# Note: run main() only when the file is launched directly (python3 tdc_jitter_sim.py),
# not when it is imported from another program
if __name__ == "__main__":
    main()
