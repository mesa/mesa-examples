# Example Validation Script

## Summary

This tool provides a prototype for validating whether examples in the Mesa Examples repository execute successfully.

As the Mesa framework evolves, example models may stop working due to API changes, missing dependencies, or outdated documentation. Manually verifying each example can be time-consuming, especially as the repository grows.

This script automates part of that process by discovering runnable examples and attempting to execute them. The goal is to quickly identify examples that run successfully and those that require maintenance.

This prototype is intended as an early step toward **automated validation of examples**, which could later be integrated into a Continuous Integration (CI) workflow.

---

## Requirements

The script only uses Python's **standard library**, so no additional dependencies are required for the script itself.

However, the repository dependencies should be installed before running the validation.

Requirements:

- Python **3.10 or newer**
- Repository dependencies installed

Install dependencies from the repository root:


pip install -r requirements.txt


Note that some examples may require additional packages (for example `networkx`, `solara`, or `matplotlib`). If these dependencies are missing, the validation script may report those examples as failed. Detecting such cases is part of the intended behavior.

---

## Usage

Run the script from the **root of the repository**:

python scripts/run_examples.py

The script will automatically:

1. Search the `examples/` directory for runnable examples.
2. Attempt to execute each example.
3. Record whether the example passes, fails, or times out.

After execution:

- A summary is printed in the terminal.
- A detailed report is written to:

validation_report.txt


Example output:


Running examples/forest_fire
PASS

Running examples/rumor_mill
PASS

Running examples/termites
FAIL

SUMMARY
PASS: 7
FAIL: 8
TIMEOUT: 2


---

## How It Works

The validation process consists of several steps.

### 1. Example Discovery

The script scans the `examples/` directory recursively and identifies folders containing an `app.py` file. These directories are treated as runnable examples.

### 2. Example Execution

Each discovered example is executed using:

python app.py

The example is executed within its own directory using a subprocess call.

A timeout is applied to prevent examples from running indefinitely.

### 3. Result Classification

Each example is categorized based on execution outcome:

- **PASS** – The example executed successfully.
- **FAIL** – The example raised an error during execution.
- **TIMEOUT** – The example exceeded the allowed execution time.

### 4. Report Generation

At the end of the validation run, the script:

- prints a summary of results to the terminal
- writes detailed results to `validation_report.txt`

This report allows maintainers to quickly identify examples that require updates or further investigation.

---

## Limitations

This prototype currently assumes examples can be executed using:


python app.py


Some examples may require alternative commands such as:


solara run app.py


Handling multiple execution modes could be added in future iterations.

---

## Future Improvements

This prototype could be extended in several ways:

- Integration with **GitHub Actions** for automated CI validation
- Support for multiple example execution commands (`solara`, notebooks, etc.)
- Automatic dependency installation using structured example metadata
- Generation of structured reports for maintainers
- Version compatibility tracking for examples

---

## Purpose

The long-term goal of this tool is to help ensure that examples remain functional as Mesa evolves, improving the reliability and maintainability of the examples repository.