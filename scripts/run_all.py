import subprocess
import sys
for module in ['src.model.train', 'scripts.benchmark', 'pytest']:
    subprocess.run([sys.executable,'-m',module],check=True)
