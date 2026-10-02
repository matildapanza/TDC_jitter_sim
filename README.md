# TDC Jitter Simulator

## Overview
This software provides a Monte Carlo simulation of a coarse-fine Time-to-Digital Converter (TDC) driven by a jittered clock, equipped with an interactive Graphical User Interface (GUI) to easily configure parameters and analyze results.

By simulating hundreds of thousands of measurements, the tool compares each measured timestamp against its known true value, characterizing the magnitude and statistical dispersion of the resulting measurement errors. To validate the simulation framework, empirical results are systematically compared against an analytical pen-and-paper prediction model.

## TDC Architecture and Measurement Mechanism
A TDC is an electronic device designed to register an event (such as a particle hitting a sensor connected to the TDC) and output a digital number representing the exact time at which it occurred.

To synchronize the system and establish a temporal reference, the TDC relies on a clock signal—an electronic digital sequence alternating between high (1) and low (0) logic states. The conversion mechanism operates in a two-stage coarse-fine architecture:

1. Coarse Stage: counts the integer number of whole clock ticks that elapse
2. Fine Stage  : uses a Time-to-Analog/Amplitude Converter (TAC)—an analog block that translates the remaining sub-clock-cycle time interval into a proportional voltage or charge level for quantization. The fine stage operates with a fixed minimum step size called the Least Significant Bit (LSB), set by default to $25\text{ ps}$.

## Error Sources
The overall timing resolution of the TDC system is fundamentally limited by two primary effects:
1. Clock Jitter: physical clock ticks do not arrive at perfect intervals; each edge is displaced by a small random amount. Because the TDC assumes an ideal, perfectly timed clock, any edge displacement translates directly into a measurement error.
2. Quantization: Because the fine stage can only output integer multiples of the LSB, the true sub-cycle time is rounded to the nearest step. This rounding introduces an intrinsic error with a characteristic RMS value of:

$$\text{Quantization Noise Floor} = \frac{\text{LSB}}{\sqrt{12}} \quad (\approx 7.22\text{ ps for } \text{LSB} = 25\text{ ps})$$

For every simulated event, the software calculates the difference between the reported time and the true time, yielding the measurement error. Any constant systematic offset common to all events is removed, as it represents a calibratable quantity rather than an intrinsic uncertainty. The remaining random scatter is quantified by a single parameter, $$\sigma$$, representing the typical magnitude of the measurement error (in picoseconds).

This simulator allows users to analyze how the overall TDC timing resolution is degraded depending on the specific type of clock jitter introduced and the presence of TAC calibration errors.

## Experimental Motivation
The development of this simulator was motivated by the design requirements of the dual-radiator RICH (dRICH) detector for the ePIC experiment at the future Electron-Ion Collider (EIC), located at Brookhaven National Laboratory (BNL).

The dRICH will be the first detector in a collider experiment to employ Silicon Photomultipliers (SiPMs) as photosensors. SiPMs were selected to guarantee reliable operation within the $\sim 1\text{ T}$ magnetic field at the dRICH location, achieving single-photon resolution while covering an area of nearly $3\text{ m}^2$ in the ePIC hadron endcap.

However, the primary challenge of using SiPM technology is its inherently high Dark Count Rate (DCR), which increases with radiation exposure. Without mitigation, this noise background would mask the Cherenkov photon signals (fewer than 20 photons expected per ring).

Effective DCR discrimination can only be achieved with excellent front-end timing resolution 
(less than 200 ps for the entire front-end module integrating the SiPMs and the electronics) to perform precise time cuts around Cherenkov signals during offline analysis. Evaluating the quality of the clock signal 
distributed to the front-end electronics is critical, and this simulator serves as a tool to estimate the direct impact of clock jitter on the overall TDC timing resolution.
