import subprocess
import sys
from pathlib import Path

app_path = Path(__file__).parent / "app.py"
subprocess.run([sys.executable, "-m", "solara", "run", str(app_path)], check=False)
