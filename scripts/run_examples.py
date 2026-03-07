import os
import subprocess

# Root directory containing all Mesa examples
EXAMPLES_DIR = "examples"


def find_examples():
    """
    Recursively search the examples directory and return
    a list of folders that contain an 'app.py' file.
    """
    Local_EXAMPLE_DIR = EXAMPLES_DIR

    example_paths = []

    # os.walk traverses the directory tree:
    # root -> current directory path
    # dirs -> subdirectories inside root
    # files -> files inside root
    for root, dirs, files in os.walk(Local_EXAMPLE_DIR):
        if "app.py" in files:
            # If an app.py exists in this directory,
            # it is considered a runnable Mesa example
            example_paths.append(root)

    return example_paths


# Find all runnable examples
examples = find_examples()

print(f"Found {len(examples)} runnable examples\n")


# Store results of execution
results = {"PASS": [], "FAIL": [], "TIMEOUT": []}


for example in examples:
    print(f"Running {example}")

    try:
        # Run the example using subprocess
        subprocess.run(
            ["python", "app.py"],  # command to execute
            cwd=example,  # run the command inside the example folder
            timeout=15,  # stop execution if it runs longer than 15 seconds
            check=True,  # raise an exception if the program exits with an error
            stdout=subprocess.DEVNULL,  # suppress normal output from the example
            stderr=subprocess.DEVNULL,  # suppress error output
        )

        # If execution finishes successfully
        results["PASS"].append(example)
        print("PASS\n")

    except subprocess.TimeoutExpired:
        # If the example runs longer than 15 seconds
        # (many Mesa apps run continuously due to GUI loops)
        results["TIMEOUT"].append(example)
        print("TIMEOUT\n")

    except Exception:
        # Any other exception means the example crashed
        results["FAIL"].append(example)
        print("FAIL\n")


# Print final summary of results
print("\nSUMMARY")
print("PASS:", len(results["PASS"]))
print("FAIL:", len(results["FAIL"]))
print("TIMEOUT:", len(results["TIMEOUT"]))


# Saves the results in a text file (i.e  validation_report.txt)
with open("validation_report.txt", "w") as f:
    for status, items in results.items():
        f.write(f"{status}:\n")
        for i in items:
            f.write(f"  {i}\n")
