# TDC Jitter Simulator

## Overview
This software provides a Monte Carlo (MC) simulation of a coarse-fine Time-to-Digital Converter (TDC) driven by a jittered clock, equipped with an interactive Graphical User Interface (GUI) to easily configure parameters and analyze results.

By simulating hundreds of thousands of measurements, the tool compares each measured timestamp against its known true value, characterizing the magnitude and statistical dispersion of the resulting measurement errors. To validate the simulation framework, empirical results are systematically compared against an analytical prediction model.

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

For every simulated event, the software calculates the difference between the reported time and the true time, yielding the measurement error. Any constant systematic offset common to all events is removed, as it represents a quantity that can be calibrated rather than an intrinsic uncertainty. The remaining random scatter is quantified by a single parameter, $$\sigma$$, representing the typical magnitude of the measurement error (in picoseconds).

This simulator allows users to analyze how the overall TDC timing resolution is degraded depending on the specific type of clock jitter introduced and the presence of TAC calibration errors.

## Experimental Motivation
The development of this simulator was motivated by the design requirements of the dual-radiator RICH (dRICH) detector for the ePIC experiment at the future Electron-Ion Collider (EIC), located at Brookhaven National Laboratory (BNL).

The dRICH will be the first detector in a collider experiment to employ Silicon Photomultipliers (SiPMs) as photosensors. SiPMs were selected to guarantee reliable operation within the $\sim 1\text{ T}$ magnetic field at the dRICH location, achieving single-photon resolution while covering an area of nearly $3\text{ m}^2$ in the ePIC hadron endcap.

However, the primary challenge of using SiPM technology is its inherently high Dark Count Rate (DCR), which increases with radiation exposure. Without mitigation, this noise background would mask the Cherenkov photon signals (fewer than 20 photons expected per ring).

Effective DCR discrimination can only be achieved with excellent front-end timing resolution (less than 200 ps for the entire front-end module integrating the SiPMs and the electronics) to perform precise time cuts around Cherenkov signals during offline analysis. Evaluating the quality of the clock signal distributed to the front-end electronics is critical, and this simulator serves as a tool to estimate the direct impact of clock jitter on the overall TDC timing resolution.

## Repository Contents
This repository contains the following files:

* **`tdc_jitter_sim_def.py`**  
  The core MC simulation engine. It generates the jittered clock signal, simulates the TDC conversion process, computes error statistics, compares results against the analytical RSS prediction model, and generates five output diagnostic plots. It includes a editable parameter block at the top and can be executed independently as a standalone script.

* **`tdc_jitter_gui_def.py`**  
  The PyQt5-based Graphical User Interface (GUI) that drives the simulation engine. It provides an interactive window equipped with text boxes, checkboxes, and sliders to adjust simulation inputs. Upon clicking `Run`, the application automatically generates a `Data_TDC/` output folder to store log files (`.txt`) for each run, recording the configuration parameters alongside the resulting numerical report.

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
3. Six independent windows will open: one containing the **numerical report** and five displaying **diagnostic plots**, each accompanied by a descriptive caption on the bottom.
4. Modify any parameters and click **Run** again to observe their immediate effect on the output.

**Note:** The MC pseudo-random number generator uses a fixed seed (`SEED = 12345`). Executing the simulation multiple times with identical settings will yield identical numerical results. To simulate a different random realization, change the `SEED` variable inside `tdc_jitter_sim_def.py`.

### Standalone Engine
The core simulation script (`tdc_jitter_sim_def.py`) can also be executed independently without the graphical interface:

1. Open `tdc_jitter_sim_def.py` in a text editor and modify the configuration variables within the `PARAMETERS` block at the top of the file. Clock frequencies must be specified in **Hertz**.
2. Run the script from the terminal:
```bash
python3 tdc_jitter_sim_def.py
```
3. The numerical summary report will be printed directly to the terminal console, and five PNG plot files will be saved in the same directory as the script.

**Note:** When executed directly from the command line, the script does **not** create log files inside the `Data_TDC/` folder; output file logging is handled exclusively by the GUI.

## Simulation Parameters
Below is a detailed breakdown of the configurable simulation parameters and their physical meaning within the TDC model.

### Clock Frequency (`F_CLK`)
The number of clock ticks per second ($f_{\text{CLK}}$). The clock period ($T_{\text{CLK}} = 1 / f_{\text{CLK}}$) defines the interval between two consecutive ticks. The coarse stage counts these clock cycles to establish the main timestamp.

### Random Clock Jitter (`SIGMA_RJ`)
The RMS ($\sigma_{\text{RJ}}$) magnitude of the random temporal displacement of clock edges from their ideal arrival times, expressed in picoseconds ($\text{ps}$). 

In a physical system, jitter originates from the reference oscillator and distribution tree electronics. Because the TDC assumes an ideal, perfectly timed clock, a tick arriving $5\text{ ps}$ late introduces a direct $5\text{ ps}$ error to every measurement referencing that edge. This is typically the dominant parameter in timing performance.

The total expected error is calculated using the **Root-Sum-of-Squares (RSS)** model combining jitter and quantization noise:

$$\sigma_{\text{total}} = \sqrt{\sigma_{\text{RJ}}^2 + \left(\frac{\text{LSB}}{\sqrt{12}}\right)^2}$$

* For ($\sigma_{\text{RJ}} \ll \text{LSB}$), the total error is dominated by the quantization noise floor.
* For ($\sigma_{\text{RJ}} > \text{LSB}$), the error scales linearly with jitter, and the error distribution converges to a Gaussian curve.
* For ($\sigma_{\text{RJ}} \approx 7.11\text{ ps}$ default), jitter and quantization contribute roughly equally to the variance ($\sigma^2$), meaning that reducing only one of the two yields minimal improvement in overall resolution.

### Random-Walk Share of Jitter (`ALPHA_RW`)
Real-world oscillator jitter is rarely purely uncorrelated from tick to tick. A portion of the phase noise accumulates over time (a *random walk*-like behavior). This parameter defines how the total jitter power is partitioned:
* **`0`:** Every clock tick is displaced **independently** of the others (pure white phase noise).
* **`1`:** Displacements **accumulate** from tick to tick, modeling a free-running oscillator.
* **Intermediate values ($0 < \alpha < 1$):** Represents a mixed phase-noise profile.

### TAC Resolution / LSB (`LSB`)
The ($\text{LSB}$), expressed in $\text{ps}$, represents the finest step size resolved by the TAC during the fine measurement stage. A smaller LSB corresponds to a higher-resolution digital scale.

The fine time interval is rounded to the nearest integer multiple of the LSB. This process introduces quantization noise distributed uniformly over one LSB step, with a characteristic RMS value of:

$$\sigma_q = \frac{\text{LSB}}{\sqrt{12}} \quad (\approx 7.22\text{ ps for } \text{LSB} = 25\text{ ps})$$

For small LSB, quantization noise becomes negligible and the resolution is limited solely by the clock jitter($\sigma \rightarrow \sigma_{\text{RJ}}$). On the other hand, for large LSB, quantization dominates ($\sigma \rightarrow \text{LSB}/\sqrt{12}$), giving the error distribution a rectangular shape of width equal to $1\text{ LSB}$. 

### TAC Non-Linearity (`INL_AMP`)
Models physical defects in the TAC conversion circuit. Inside the TAC, the time interval is converted into a voltage ramp. If the ramp exhibits non-linearities, the measured interval will be slightly overestimated or underestimated depending on where the event falls within the clock cycle. 

This Integral Non-Linearity (INL) is modeled as a sinusoidal distortion with a peak amplitude $\text{INL}_{\text{amp}}$ in picoseconds. It contributes an independent RMS error component of $\text{INL}/\sqrt{2}$, expanding the theoretical RSS model to:

$$\sigma_{\text{total}} = \sqrt{\sigma_{\text{RJ}}^2 + \sigma_q^2 + \frac{\text{INL}^2}{2}}$$

**Note:** The standard analytical formula displayed in the report assumes ideal linearity and does not include INL. When INL is enabled, the simulated resolution $\sigma_{\text{sim}}$ will naturally exceed the basic RSS prediction ($\sigma_{\text{sim}} > \sigma_{\text{RSS}}$). This deviation is expected and highlighted as a note within the graphical user interface.

### Clock Edges Used (`USE_NEAREST_EDGE`)
Defines which clock edges (transitions) are utilized by the fine stage for time measurements:

* **Rising Edge Only (`False`, default):** the fine stage measures the sub-clock interval from the event timestamp to the next rising edge. The maximum measurable interval corresponds to one full clock period.
* **Nearest Edge (`True`):** the fine stage measures the time to the **nearest clock edge**, whether rising or falling. This halves the maximum interval to at most $T_{\text{CLK}} / 2$, but introduces sensitivity to **Duty Cycle Distortion (DCD)**.

### Duty Cycle Distortion / DCD (`DCD_PP`)
Expresses the peak-to-peak distortion of the clock signal's duty cycle in picoseconds ($\text{ps}$).

An ideal clock maintains a $50\%$ duty cycle, where high and low states last for exactly half a clock period ($T_{\text{CLK}} / 2$). In physical systems, asymmetries shift the falling edges from their ideal value. In the simulation, falling edges are displaced by $\pm \text{DCD}_{\text{PP}} / 2$.

This effect is active **only** when *Nearest Edge* mode is enabled. Because the TDC assumes falling edges are located exactly at the half-period mark, any duty cycle imbalance introduces a systematic measurement offset for events referenced to a falling edge.
**Note:** Ignored when operating in *Rising Edge Only* mode.

### Periodic Jitter Amplitude (`PJ_AMP`)
Models a deterministic, repeating timing disturbance affecting clock edges—equivalent to a sinusoidal phase modulation of the clock arrival times. A typical physical source is cross-talk or supply noise coupled from adjacent circuits operating at a fixed frequency. Unlike random jitter, periodic jitter is deterministic.

The parameter specifies the peak amplitude ($\text{PJ}_{\text{amp}}$) in picoseconds ($\text{ps}$). Its RMS contribution ($\text{PJ}_{\text{amp}} / \sqrt{2}$) combines in quadrature with the other uncertainty sources:

$$\sigma_{\text{total}} = \sqrt{\sigma_{\text{RJ}}^2 + \sigma_q^2 + \frac{\text{PJ}_{\text{amp}}^2}{2}}$$

**Note:** The default analytical RSS formula displayed in the report assumes purely random noise and does not include periodic jitter. Enabling periodic jitter will cause the simulated result to exceed the basic RSS prediction ($\sigma_{\text{sim}} > \sigma_{\text{RSS}}$), as indicated in the summary report.

### Periodic Jitter Frequency (`PJ_FREQ`)
Specifies the repetition rate of the periodic timing disturbance in $\text{MHz}$.

### Number of Events (`N_EVENTS`)
Sets the total number of MC measurements simulated during a single run. Simulated events arrive at uniformly distributed random instants, completely uncorrelated with clock edges.

Adjusting $N_{\text{events}}$ does not alter the *true* underlying standard deviation ($\sigma$), but improves the precision of its estimate. The relative statistical uncertainty on $\sigma$ scales as:

$$\frac{\delta\sigma}{\sigma} \approx \frac{1}{\sqrt{2 N_{\text{events}}}}$$

Computation time scales linearly with the number of simulated events (a default run of hundreds of thousands of events executes in a few seconds).

### Script-Only Parameters

Two global parameters can only be modified directly within the `PARAMETERS` configuration block at the top of `tdc_jitter_sim_def.py`:

* **`N_CLK_EDGES`** *(default: 400000)*: Sets the total number of generated clock cycles. Simulated event timestamps are distributed randomly across the time span covered by these edges.
* **`SEED`** *(default: 12345)*: The initialization seed for the pseudo-random number generator. Modifying this value generates a statistically independent MC realization.

## Simulation Outputs
Each simulation run generates status messages in the terminal console, a comprehensive numerical report (displayed in a dedicated GUI window and printed to the terminal), and five diagnostic plots.

When running via the GUI, every execution automatically generates a time-stamped text log file inside the `Data_TDC/` directory (created automatically in the root folder of the scripts if it does not exist). This folder stores the complete numerical report alongside the full list of input parameters used for that specific run.

**Note:** Diagnostic plots are not saved automatically in GUI mode. To save individual figures, click the **Save image...** button in each plot window.

### The Five Diagnostic Plots

#### Plot 1 – Error Distribution
Displays a normalized probability density histogram of all simulated measurement errors ($\text{ps}$).

The **red dashed curve** represents the theoretical Gaussian distribution with a standard deviation ($\sigma_{\text{TOT}}$) predicted by the analytical RSS formula: close agreement between the histogram bars and the red dashed curve confirms that measurement errors are normally distributed and align with analytical predictions.

#### Plot 2 – Dither Effect
Presents four side-by-side histograms comparing error distributions across four distinct clock jitter levels ($0.5$, $2.0$, $7.11$, and $20.0\text{ ps}$), keeping all other parameters fixed to user indication. Panel titles indicate the specific jitter level and resulting total resolution ($\sigma$).

At negligible jitter, the error is dominated by quantization, producing a flat-topped, box-like histogram. As jitter increases, phase noise smooths out the quantization steps, causing the distribution to converge to a more Gaussian-like curve. This beneficial smoothing effect of random noise on digital quantization is known as **dither effect**.

#### Plot 3 – Error vs. Jitter
Maps the evolution of total timing resolution ($\sigma$) as random clock jitter increases continuously from $0.5\text{ ps}$ to $30.0\text{ ps}$.

#### Plot 4 – Duty Cycle Effect
Displays two comparative histograms evaluating the two clock transition modes:

* **Left Panel (Rising Edge Only):** Duty Cycle Distortion (DCD) has no impact on timing accuracy.
* **Right Panel (Nearest Edge):** DCD displaces falling edges, causing the error distribution to split into two distinct peaks.

* **Note:** This diagnostic plot **always displays both edge modes side by side** using your active DCD, jitter, and LSB settings, regardless of which mode is currently selected for the main simulation run.

#### Plot 5 – Error Spectrum (FFT Analysis)
Plots the frequency spectrum derived from a Fast Fourier Transform (FFT) analysis of the measurement error sequence, ordered chronologically.

The horizontal axis indicates normalized frequency (cycles per measurement, spanning $0$ to $0.5$), while the logarithmic vertical axis represents spectral amplitude ($\text{ps}$).

This analysis allows to identify periodic oscillations or deterministic noise patterns embedded within the measurement error sequence.

## Analytical Prediction Model
The simulation report compares empirical MC results against a theoretical **analytical error budget**:

$$\sigma_{\text{TOT}} = \sqrt{\sigma_{\text{RJ}}^2 + \sigma_{\text{DCD}}^2 + \sigma_q^2}$$

The individual variance components are summed in quadrature because the underlying error mechanisms are statistically independent (RSS model).

### Step-by-Step Simulation Workflow
1. **Jittered Clock Generation:** Rising clock edges arrive at timestamps $t_k = k \cdot T_{\text{CLK}} + \varphi(k)$, where $\varphi(k)$ represents edge displacement composed of white phase noise, random-walk noise, and an optional sinusoidal periodic component. White and random-walk variances are scaled so that their combined standard deviation equals the set jitter parameter ($\sigma_{\text{RJ}}$).
2. **Event Timestamp Generation:** $N_{\text{events}}$ arrival times are sampled randomly from a uniform distribution across the simulated time window, completely uncorrelated with clock edges.
3. **Coarse Timestamping:** For each event, the TDC identifies the first subsequent rising edge index $k$.
4. **Fine Interval Measurement:** The residual interval between the event and edge $k$ is subjected to optional INL distortion, then rounded to the midpoint of its corresponding LSB bin.
5. **Reported Time Calculation:** $t_{\text{reported}} = k \cdot T_{\text{CLK}} - t_{\text{fine, rounded}}$. Because the TDC assumes an **ideal** clock tick location ($k \cdot T_{\text{CLK}}$) rather than the physical displaced arrival time, clock edge displacements translate directly into measurement errors.
6. **Error Extraction:** $e_i = t_{\text{reported}} - t_{\text{true}}$, with the global mean offset subtracted to eliminate systematic calibration bias.

**Note:** When *Nearest Edge* mode is active, falling edges are inserted at $t = k \cdot T_{\text{CLK}} + T_{\text{CLK}}/2 + \text{DCD}_{\text{PP}}/2$. The TDC uses the first arriving edge of either transition type while maintaining the assumption of ideal, symmetric half-period intervals.

## Suggested Test Cases
 
For each guided example, only the specified parameters need to be adjusted (all other settings remain at their default values). Each scenario details the plot expected features alongside their underlying physical interpretation.

### Example 1 – Only rounding
* **Input:** RJ jitter = 0.
* **Output:** `sigma_sim ≈ 7.23 ps`; peak-to-peak exactly 25 ps (= LSB), `|err| < 2 sig = 100 %`, a **flat-topped box** in plot 1 that does not follow the theoretical prediction.
* **Explanation:** with a perfect clock the only error is the rounding to the nearest 25 ps step, uniformly spread over one step.

### Example 2 – Dither effect
* **Input:** defaults; look at the **Dither effect** plot.
* **Output:** the first panel (jitter = 0.5 ps) is a box, the last (jitter = 20 ps) a Gaussian.
* **Explanation:** random noise smooths the steps of the rounding. If you raise the LSB to 100 ps and run again: the box persists up to larger jitters, because more random noise is needed to smooth a bigger step.

### Example 2 – Duty cycle distortion, two peaks
* **Input:** edge mode *Nearest edge*, jitter = 2, LSB = 5, DCD = 40.
* **Output:** `sigma_sim ≈ 10.3 ps` and `dev. vs RSS ≈ −49 %`; the histogram and the right panel of the *Duty cycle effect* plot show two separate peaks about 20 ps apart.
* **Explanation:** events measured against a rising edge and against a falling edge are read with a relative shift of `DCD/2`.
