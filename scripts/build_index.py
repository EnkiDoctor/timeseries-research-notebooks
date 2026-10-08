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
    lines = ['# 模板场景索引', '', 'P / D 模板先运行对应 notebook 的初始化单元。V 模板只需 B 部分的 import，S 美观版先运行它自己的主题初始化格。B 回测模板先运行 03 的初始化格，每例先 display 输入 df，再运行回测和绘图。先看输入表和任务；没有自己的 df 时先运行该案例的示例建表格。无需先运行其他模板。',
             '在 GitHub notebook 中搜索编号即可定位。HTML 阅读版下载后可离线打开。', '']
    lines += ['M 机器学习模板运行 04 的初始化格；每例先 display 输入 df，再按时间切分、训练、展示预测与图形。M10 需要可选 XGBoost。', '']
    gallery = ['# 图表预览', '', '以下图片取自已执行的 02 基础版、02b 美观版、03 回测与04机器学习 notebook。先看输入表、场景与任务，再查看代码和图形结果；03/04 每个案例先 display 输入 df，并展示结果表。', '']
    for path in sorted((ROOT / 'notebooks').glob('0[1234]*_*.ipynb')):
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
                name = path.stem.split('_', 1)[0] + '-' + rid.lower() + '-' + str(i + 1) + '.png'
                (image_dir / name).write_bytes(base64.b64decode(data))
                gallery += ['## ' + current_title, '', '![' + rid + '](images/' + name + ')', '']
        lines += ['', '本册共 ' + str(len(seen)) + ' 个可独立执行的模板。', '']
    lines += ['[查看所有图表预览](GALLERY.md)', '']
    (ROOT / 'docs' / 'RECIPE_INDEX.md').write_text('\n'.join(lines), encoding='utf-8')
    (ROOT / 'docs' / 'GALLERY.md').write_text('\n'.join(gallery), encoding='utf-8')


if __name__ == '__main__':
    main()
