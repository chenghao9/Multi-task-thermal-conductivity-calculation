# Multi-task-thermal-conductivity-calculation
A Python script for batch processing temperature and heat-flux files from multiple molecular dynamics case folders and automatically calculating thermal conductivity.

## Overview

`TC_rc.py` is designed for non-equilibrium molecular dynamics (NEMD) post-processing workflows where multiple simulation case folders need to be analyzed in a consistent and automated way.

The script can:

- read temperature distribution data from each case folder
- calculate the averaged temperature profile
- fit heat-flux exchange data to obtain the average heat power
- fit the temperature profile in a user-defined range to obtain the temperature gradient
- calculate thermal conductivity from the heat-flux density and temperature gradient
- save case-level results in each folder
- generate a batch summary file in the root directory

This workflow is especially useful when handling a series of simulation folders such as `0`, `10`, `20`, and `30`, where each folder contains one temperature file and one heat-flux file.

## Features

- Batch processing of multiple case folders
- Configurable input through a single parameter file
- Automatic averaging of temperature data
- Linear fitting of heat-flux exchange data
- Linear fitting of temperature gradients in a specified range
- Automatic calculation of thermal conductivity
- Per-case output files and batch summary export

## Requirements

- Python 3.9 or later

Required Python packages:

```bash
pip install numpy pandas matplotlib scipy
```

## Installation

Clone or copy the script and place it in your working directory together with the input file template.

Example files:

- `TC_rc.py`
- `rc_k.in`

No additional installation is required beyond the Python dependencies listed above.

## Project Structure

A typical directory structure is shown below:

```text
project_root/
├── TC_rc.py
├── rc_k.in
├── 0/
│   ├── temperature_file
│   └── heat_flux_file
├── 10/
│   ├── temperature_file
│   └── heat_flux_file
├── 20/
│   ├── temperature_file
│   └── heat_flux_file
└── ...
```

## Configuration

All runtime settings are controlled through the input file `rc_k.in`.

### Top-Level Parameters

#### `root_dir`
Root directory containing all case subfolders.

- You can use an absolute path
- You can also use `.` to indicate the current directory

#### `scan_mode`
Controls how case folders are discovered.

- `list`: process only the folders specified in `case_dirs`
- `auto`: automatically process all subfolders under `root_dir`

#### `case_dirs`
A comma-separated list of case folder names to process when `scan_mode = list`.

Example:

```ini
case_dirs = 0, 10, 20
```

For a single folder:

```ini
case_dirs = 0,
```

#### `batch_summary_name`
File name of the batch summary output.

### Parameters in `[defaults]`

#### Input and Output File Names

- `temp_input_name`: temperature input file name
- `heat_flux_input_name`: heat-flux input file name
- `extracted_temp_name`: extracted temperature detail file name
- `mean_temp_name`: averaged temperature profile file name
- `mean_temp_figure_name`: averaged temperature profile figure name
- `heat_flux_figure_name`: heat-flux fitting figure name
- `temp_fit_figure_name`: temperature fitting figure name
- `summary_name`: summary file name for a single case

#### Temperature Processing Parameters

- `num_blocks`: number of blocks used for averaging
- `num_chunks`: number of spatial chunks read in each block
- `position_factor`: scaling factor applied to the position values

#### Heat-Flux Processing Parameters

- `time_ps_factor`: conversion factor used to convert the first column of the heat-flux file into ps

#### Thermal Conductivity Parameters

- `contact_area`: contact area in `m^2`
- `fit_range`: fitting range for the temperature gradient, for example `34, 160`

### Case-Specific Overrides

If one case needs different settings from the defaults, add a dedicated override section.

Example:

```ini
[case:10]
fit_range = 40, 150
time_ps_factor = 0.001
contact_area = 2.2e-18
```

This means only folder `10` uses these values, while all other folders continue to use the settings in `[defaults]`.

## Usage

Run the script from the command line:

```bash
python TC_rc.py rc_k.in
```

## Workflow

For each case folder, the script performs the following steps.

### 1. Temperature Data Processing

- Read the first `num_blocks` blocks
- Read `num_chunks` spatial points from each block
- Multiply the position values by `position_factor`
- Export the extracted temperature data
- Compute and export the averaged temperature profile

Generated files:

- `extracted_temperature_data.txt`
- `mean_temperature_data.txt`
- `mean_temperature_vs_position_no_zero.png`

### 2. Heat-Flux Fitting

- Perform linear fitting for the energy exchange at the hot side
- Perform linear fitting for the energy exchange at the cold side
- Estimate the average heat power

Generated file:

- `energy_flux_fit.png`

### 3. Temperature Gradient Fitting and Thermal Conductivity Calculation

- Perform linear fitting on the averaged temperature profile within `fit_range`
- Obtain the temperature gradient
- Calculate heat-flux density
- Calculate thermal conductivity

Generated files:

- `temperature_fit_single_range.png`
- `result_summary.csv`

## Output Files

### Files Generated in Each Case Folder

- `extracted_temperature_data.txt`: extracted temperature detail data
- `mean_temperature_data.txt`: averaged temperature profile data
- `mean_temperature_vs_position_no_zero.png`: averaged temperature profile figure
- `energy_flux_fit.png`: heat-flux fitting figure
- `temperature_fit_single_range.png`: temperature fitting figure
- `result_summary.csv`: summary file for the current case

### File Generated in the Root Directory

- `batch_results_summary.csv`: summary file for all processed cases

## `result_summary.csv` Columns

- `case`: case name (folder name)
- `status`: processing status; `ok` means success and `failed` means failure
- `P_avg_W`: average heat power in W
- `heat_flux_W_m2`: heat-flux density in W/m²
- `gradT_K_m`: temperature gradient in K/m
- `k_W_mK`: thermal conductivity in W/(m·K)
- `slope_hot_eV_ps`: fitted slope of hot-side energy exchange in eV/ps
- `slope_cold_eV_ps`: fitted slope of cold-side energy exchange in eV/ps
- `intercept_hot`: intercept of the hot-side fitting
- `intercept_cold`: intercept of the cold-side fitting
- `temp_slope_K_per_A`: raw fitted temperature slope in K/Å
- `temp_intercept`: intercept of the temperature fitting
- `fit_range_start`: start point of the fitting range
- `fit_range_end`: end point of the fitting range
- `contact_area_m2`: contact area in m²
- `position_factor`: position scaling factor
- `time_ps_factor`: conversion factor from time step to ps
- `num_blocks`: number of blocks used for averaging
- `num_chunks`: number of chunks read in each block

## Notes

- Make sure the input file names in `rc_k.in` match the actual file names in each case folder.
- When using `scan_mode = auto`, all valid subfolders under `root_dir` will be processed automatically.
- For reliable thermal conductivity fitting, choose `fit_range` carefully to avoid non-linear temperature regions.

## File Mapping

- Main script: `TC_rc.py`
- Parameter template: `rc_k.in`
- Per-case summary: `result_summary.csv`
- Batch summary: `batch_results_summary.csv`

## License

- Author：cheng hao
- Email: chenghao8425@163.com;chenghao8425@gmail.com
- 微信公众号：材料计算学习笔记
