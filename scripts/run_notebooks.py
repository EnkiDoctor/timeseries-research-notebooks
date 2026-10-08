"""Execute notebooks in clean kernels, optionally validate recipe independence and export HTML.

Examples:
    python scripts/run_notebooks.py --check-recipes --html
    python scripts/run_notebooks.py --check-recipes --html --write
Without --write, executed notebooks go to ignored artifacts/ instead of replacing source.
"""
import argparse
import ast
import contextlib
import io
import json
import platform
import re
import sys
import warnings
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

ROOT = Path(__file__).resolve().parents[1]


def check_recipes(nb):
    """Use fresh namespaces: only setup + the selected recipe are available."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    setup_cells = [c for c in nb.cells if c.cell_type == 'code' and 'setup' in c.metadata.get('tags', [])]
    setups = [c.source for c in setup_cells if 'visualization_setup' not in c.metadata.get('tags', [])]
    visual_setups = [c.source for c in setup_cells if 'visualization_setup' in c.metadata.get('tags', [])]
    recipes = {}
    for c in nb.cells:
        if c.cell_type != 'code':
            continue
        ast.parse(c.source, feature_version=(3, 8))
        recipe_id = c.metadata.get('recipe_id')
        if not recipe_id:
            for tag in c.metadata.get('tags', []):
                if tag.startswith('recipe:'):
                    recipe_id = tag.split(':', 1)[1]
        if recipe_id:
            recipes.setdefault(recipe_id, []).append(c.source)
    if not setups or not recipes:
        raise AssertionError('Notebook must tag setup cells and identify each independent recipe.')
    for recipe_id, blocks in recipes.items():
        namespace = {'__name__': '__main__'}
        try:
            with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
                # Only the headless independent-recipe check lacks an interactive canvas.
                warnings.filterwarnings('ignore', message='Matplotlib is currently using agg.*', category=UserWarning)
                selected_setups = visual_setups if recipe_id.startswith('V') and visual_setups else setups
                for source in selected_setups + blocks:
                    exec(compile(source, '<recipe ' + recipe_id + '>', 'exec'), namespace)
        except Exception as exc:
            raise RuntimeError('Independent recipe failed: ' + recipe_id) from exc
        finally:
            plt.close('all')
    return sorted(recipes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--html', action='store_true')
    parser.add_argument('--check-recipes', action='store_true')
    parser.add_argument('--notebook', action='append', help='Optional notebook filename to run.')
    args = parser.parse_args()
    artifacts = ROOT / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    files = sorted((ROOT / 'notebooks').glob('0[123]*_*.ipynb'))
    if args.notebook:
        files = [p for p in files if p.name in args.notebook]
    if not files:
        raise ValueError('No completed notebooks found.')
    results = []
    for path in files:
        nb = nbformat.read(str(path), as_version=4)
        print('Executing ' + path.name, flush=True)
        km = KernelManager(kernel_name='python3')
        km.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
        client = NotebookClient(nb, km=km, timeout=240, resources={'metadata': {'path': str(ROOT)}})
        client.execute(cleanup_kc=True)
        nbformat.validate(nb)
        code_cells = [c for c in nb.cells if c.cell_type == 'code']
        assert all(c.execution_count is not None for c in code_cells)
        assert not [o for c in code_cells for o in c.outputs if o.output_type == 'error']
        recipes = check_recipes(nb) if args.check_recipes else []
        # Execution metadata must not leak local paths. Setup outputs print versions, not cwd.
        text = nbformat.writes(nb)
        for marker in ('/Users/', '/home/', 'access_token', 'ghp_'):
            if marker in text:
                raise AssertionError('Unexpected local path or sensitive marker: ' + marker)
        destination = path if args.write else artifacts / path.name
        nbformat.write(nb, str(destination))
        if args.html:
            from nbconvert import HTMLExporter
            body, _ = HTMLExporter(template_name='lab').from_notebook_node(nb)
            html_dir = ROOT / 'docs' if args.write else artifacts
            html_dir.mkdir(exist_ok=True)
            (html_dir / (path.stem + '.html')).write_text(body, encoding='utf-8')
        images = sum('image/png' in o.get('data', {}) for c in code_cells for o in c.outputs)
        result = {'notebook': path.name, 'cells': len(nb.cells), 'code_cells': len(code_cells),
                  'independently_checked_recipes': recipes, 'embedded_figures': images, 'errors': 0}
        results.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    import numpy, pandas, matplotlib
    report = {'python': platform.python_version(), 'numpy': numpy.__version__,
              'pandas': pandas.__version__, 'matplotlib': matplotlib.__version__, 'results': results}
    report_path = (ROOT / 'docs' if args.write else artifacts) / 'validation.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
