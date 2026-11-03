#!/usr/bin/env bash
# 列出各子模块目录的实际内容

SRC="$HOME/openems-src"

for d in CSXCAD AppCSXCAD QCSXCAD CTB fparser hyp2mat openEMS; do
    printf '==== %s ====\n' "$d"
    if [ ! -d "$SRC/$d" ]; then
        echo "  目录不存在"
        continue
    fi
    n=$(ls -A "$SRC/$d" 2>/dev/null | wc -l)
    echo "  条目数: $n"
    ls -A "$SRC/$d" 2>/dev/null | head -6 | sed 's/^/    /'

    # 若只有 .git，说明工作区没检出
    if [ "$n" -le 1 ]; then
        if [ -d "$SRC/.git/modules/$d" ]; then
            echo "    -> git 目录存在（.git/modules/$d），但工作区未检出"
        else
            echo "    -> 连 git 目录都没有，是真的没初始化"
        fi
    fi
    echo
done

echo "==== .git/modules 下的子模块 git 目录 ===="
ls -A "$SRC/.git/modules" 2>/dev/null | sed 's/^/  /' || echo "  无"

echo
echo "==== 磁盘占用 ===="
du -sh "$SRC" 2>/dev/null
