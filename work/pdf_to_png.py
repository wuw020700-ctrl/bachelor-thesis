# -*- coding: utf-8 -*-
"""把 PDF 每页渲染成 PNG，供视觉检查。"""

import sys
from pathlib import Path

from pdf2image import convert_from_path

POPPLER = r"C:\Users\ww\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin"


def main():
    pdf = Path(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)

    pages = convert_from_path(str(pdf), dpi=110, poppler_path=POPPLER)
    for i, img in enumerate(pages, start=1):
        p = out / f"page-{i}.png"
        img.save(p)
        print(f"  {p.name}  {img.width}x{img.height}")
    print(f"共 {len(pages)} 页")


if __name__ == "__main__":
    main()
