"""Optional Graphviz rendering without shell-dependent binary output redirection."""
from pathlib import Path
import subprocess

Path('generated').mkdir(exist_ok=True)
graph = subprocess.check_output(['terraform', 'graph'])
subprocess.run(['dot', '-Tpng', '-o', 'generated/terraform-graph.png'], input=graph, check=True)
print('Created generated/terraform-graph.png')
