"""Build a searchable Markdown catalog and export notebook figures for easy GitHub browsing."""
import base64
import re
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parents[1]


def recipe_id(cell):
    value = cell.metadata.get('recipe_id')
    if value:
        return value
    for tag in cell.metadata.get('tags', []):
        if tag.startswith('recipe:'):
            return tag.split(':', 1)[1]
    return None


def main():
    image_dir = ROOT / 'docs' / 'images'
    image_dir.mkdir(parents=True, exist_ok=True)
    lines = ['# 模板场景索引', '', 'P / D 模板先运行对应 notebook 的初始化单元。V 模板只需 B 部分的 import：先看输入表和任务，再复制绘图格；没有自己的 df 时先运行该案例的示例建表格。无需先运行其他模板。',
             '在 GitHub notebook 中搜索编号即可定位。HTML 阅读版下载后可离线打开。', '']
    gallery = ['# 图表预览', '', '以下图片直接取自已执行的 02 notebook。每个 V 案例按「输入表 → 要做什么 → 示例建表 / 绘图代码 → 图形结果」排列，复制时用自己的 df 替换示例表即可。', '']
    for path in sorted((ROOT / 'notebooks').glob('0[12]_*.ipynb')):
        nb = nbformat.read(str(path), 4)
        lines += ['## ' + path.stem, '', '[打开 Notebook](../notebooks/' + path.name + ')', '',
                  '| 编号 | 场景 / 模板 |', '|---|---|']
        current_title = ''
        seen = set()
        for cell in nb.cells:
            if cell.cell_type == 'markdown':
                headings = re.findall(r'^#{1,4}\s+(.+)', cell.source, re.M)
                if headings:
                    current_title = headings[-1]
            if cell.cell_type != 'code':
                continue
            rid = recipe_id(cell)
            if not rid:
                continue
            if rid not in seen:
                clean_title = re.sub(r'<[^>]+>', '', current_title).strip().replace('|', '／')
                lines.append('| `' + rid + '` | ' + clean_title + ' |')
                seen.add(rid)
            images = [o['data']['image/png'] for o in cell.get('outputs', []) if 'image/png' in o.get('data', {})]
            for i, data in enumerate(images):
                name = path.name[:2] + '-' + rid.lower() + '-' + str(i + 1) + '.png'
                (image_dir / name).write_bytes(base64.b64decode(data))
                gallery += ['## ' + current_title, '', '![' + rid + '](images/' + name + ')', '']
        lines += ['', '本册共 ' + str(len(seen)) + ' 个可独立执行的模板。', '']
    lines += ['[查看所有图表预览](GALLERY.md)', '']
    (ROOT / 'docs' / 'RECIPE_INDEX.md').write_text('\n'.join(lines), encoding='utf-8')
    (ROOT / 'docs' / 'GALLERY.md').write_text('\n'.join(gallery), encoding='utf-8')


if __name__ == '__main__':
    main()
