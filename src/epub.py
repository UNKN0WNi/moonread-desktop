"""EPUB 解析核心。

与 moonread 项目（https://github.com/UNKN0WNi/moonread）的 tools/render_html.py
共用同一套解析规则：EPUB 即 ZIP，读 OPF 拿书目与 spine 顺序，读 NCX 还原目录，
再按 spine 顺序从 XHTML 提取正文段落。只依赖 Python 标准库。
"""

from __future__ import annotations

import html
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

OPF_NS = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
NCX_NS = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}


class EpubError(Exception):
    """EPUB 解析失败。"""


def _clean_text(frag: str) -> str:
    frag = re.sub(r"(?is)<br\s*/?>", "", frag)
    frag = re.sub(r"(?s)<[^>]+>", "", frag)
    frag = html.unescape(frag).replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", frag).strip()


def _extract(xhtml: str):
    """返回 (章节标题, 段落列表)。"""
    s = re.sub(r"(?is)<head.*?</head>", "", xhtml)
    s = re.sub(r"(?is)<script.*?</script>", "", s)
    s = re.sub(r"(?is)<style.*?</style>", "", s)
    m = re.search(r"(?is)<body[^>]*>(.*)</body>", s)
    body = m.group(1) if m else s
    title = ""
    hm = re.search(r"(?is)<h[1-3][^>]*>(.*?)</h[1-3]>", body)
    if hm:
        title = _clean_text(hm.group(1))
        body = body[: hm.start()] + body[hm.end() :]
    paras = []
    for pm in re.finditer(r"(?is)<p[^>]*>(.*?)</p>", body):
        t = _clean_text(pm.group(1))
        if t:
            paras.append(t)
    if not paras:
        paras = [p for p in re.split(r"\n{2,}", _clean_text(body)) if p]
    return title, paras


def parse_epub(path: str | Path) -> dict:
    """解析 EPUB，返回可直接交给前端渲染的结构：

    {
      "title": str, "author": str, "chapters": [{"title", "paras"}],
      "toc": [{"level", "title", "idx"}], "chars": int,
    }
    """
    path = Path(path)
    if not path.is_file():
        raise EpubError(f"找不到文件：{path}")

    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())

        opf_name = next((n for n in z.namelist() if n.endswith(".opf")), None)
        if opf_name is None:
            raise EpubError("这不是有效的 EPUB：缺少 .opf 文件")

        base = opf_name.rsplit("/", 1)[0] if "/" in opf_name else ""

        def resolve(href: str) -> str:
            if not href:
                return href
            return (base + "/" + href.split("#")[0]) if base else href.split("#")[0]

        root = ET.fromstring(z.read(opf_name).decode("utf-8", errors="replace"))
        manifest = {
            it.get("id"): it.get("href")
            for it in root.findall(".//opf:manifest/opf:item", OPF_NS)
        }
        spine = [it.get("idref") for it in root.findall(".//opf:spine/opf:itemref", OPF_NS)]
        spine_hrefs = [resolve(manifest[i]) for i in spine if i in manifest]
        title = root.findtext(".//dc:title", default="（无标题）", namespaces=OPF_NS).strip()
        author = root.findtext(".//dc:creator", default="", namespaces=OPF_NS).strip()

        toc = []
        ncx_name = next((n for n in z.namelist() if n.endswith(".ncx")), None)
        if ncx_name:
            nbase = ncx_name.rsplit("/", 1)[0] if "/" in ncx_name else ""

            def nresolve(src: str) -> str:
                return (nbase + "/" + src.split("#")[0]) if nbase else src.split("#")[0]

            nroot = ET.fromstring(z.read(ncx_name).decode("utf-8", errors="replace"))
            navmap = nroot.find("ncx:navMap", NCX_NS)

            def walk(np, level):
                lbl = np.findtext("ncx:navLabel/ncx:text", default="", namespaces=NCX_NS).strip()
                c = np.find("ncx:content", NCX_NS)
                src = c.get("src") if c is not None else ""
                toc.append({"level": level, "title": lbl, "href": nresolve(src)})
                for ch in np.findall("ncx:navPoint", NCX_NS):
                    walk(ch, level + 1)

            if navmap is not None:
                for np in navmap.findall("ncx:navPoint", NCX_NS):
                    walk(np, 0)

        href_to_idx = {h: i for i, h in enumerate(spine_hrefs)}
        for t in toc:
            t["idx"] = href_to_idx.get(t["href"])

        chapters = []
        for i, h in enumerate(spine_hrefs):
            if h not in names:
                chapters.append({"title": f"第 {i + 1} 章", "paras": []})
                continue
            ch_title, paras = _extract(z.read(h).decode("utf-8", errors="replace"))
            if not ch_title:
                ch_title = next(
                    (t["title"] for t in toc if t["href"] == h and t["title"]),
                    f"第 {i + 1} 章",
                )
            chapters.append({"title": ch_title, "paras": paras})

    # 目录标题补齐空/泛化的章节标题
    by_idx = {}
    for t in toc:
        if t.get("idx") is not None and t["title"]:
            by_idx.setdefault(t["idx"], t["title"])
    for i, c in enumerate(chapters):
        if (not c["title"] or re.match(r"^第 \d+ 章$", c["title"])) and i in by_idx:
            c["title"] = by_idx[i]

    for t in toc:
        t.pop("href", None)

    return {
        "title": title,
        "author": author,
        "chapters": chapters,
        "toc": toc,
        "chars": sum(len(p) for c in chapters for p in c["paras"]),
    }
