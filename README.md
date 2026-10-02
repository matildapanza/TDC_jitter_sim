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

Effective DCR discrimination can only be achieved with excellent front-end timing resolution (less than 200 ps for the entire front-end module integrating the SiPMs and the electronics) to perform precise time cuts around Cherenkov signals during offline analysis. Evaluating the quality of the clock signal distributed to the front-end electronics is critical, and this simulator serves as a tool to estimate the direct impact of clock jitter on the overall TDC timing resolution.

## Repository Contents
This repository contains the following files:

* **`tdc_jitter_sim_def.py`**  
  The core Monte Carlo (MC) simulation engine. It generates the jittered clock signal, simulates the TDC conversion process, computes error statistics, compares results against the analytical RSS prediction model, and generates five output diagnostic plots. It includes a editable parameter block at the top and can be executed independently as a standalone script.

* **`tdc_jitter_gui_def.py`**  
  The PyQt5-based Graphical User Interface (GUI) that drives the simulation engine. It provides an innteractive window equipped with text boxes, checkboxes, and sliders to adjust simulation inputs. Upon clicking `Run`, the application automatically generates a `Data_TDC/` output folder to store log files (`.txt`) for each run, recording the configuration parameters alongside the resulting numerical report.

* **`README.md`**  
  This documentation file, providing an overview of the TDC architecture, theoretical error model, experimental motivation (ePIC/dRICH), and scripts usage.

## Execution Requirements
To run the simulation and interactive GUI, Python 3 is required, along with the following packages:
* **NumPy**: for optimized array manipulation and MC random number generation.
* **Matplotlib**: for displaying and saving the diagnostic plots.
* **PyQt5**: required exclusively for the graphical interface (`tdc_jitter_gui_def.py`).

Additional OS-specific details and installation commands can be found in the header comments of the scripts.

## Running the Program

### GUI (Recommended)

To launch the interactive GUI, navigate to the repository directory and run:

```bash
cd path/to/the/repository      
python3 tdc_jitter_gui_def.py

```

The GUI provides text boxes, drop-down menus, and sliders to adjust simulation parameters, change numeric values, and activate optional features or non-idealities.

1. The main window opens with pre-filled default parameters.
2. Click **Run** to launch the simulation (execution takes only a few seconds).
3. Six independent windows will open: one containing the **numerical report** and five displaying **diagnostic plots**, each accompanied by an explanatory caption on the bottom.
4. Modify any parameters and click **Run** again to observe their immediate effect on the output.

**Note:** The MC pseudo-random number generator uses a fixed seed (`SEED = 12345`). Executing the simulation multiple times with identical settings will yield identical numerical results. To simulate a different random realization, change the `SEED` variable inside `tdc_jitter_sim_def.py`.

### Standalone Engine

The core simulation script (`tdc_jitter_sim_def.py`) can also be executed independently without the graphical interface:

1. Open `tdc_jitter_sim_def.py` in a text editor and modify the configuration variables within the `PARAMETERS` block at the top of the file. Clock frequencies must be specified in **Hertz** (e.g., `F_CLK = 400e6` for $400\text{ MHz}$).
2. Run the script from the terminal:
```bash
python3 tdc_jitter_sim_def.py
```
3. The numerical summary report will be printed directly to the terminal console, and five PNG plot files will be saved in the same directory as the script.

**Note:** When executed directly from the command line, the script does **not** create log files inside the `Data_TDC/` folder; output file logging is handled exclusively by the GUI.















