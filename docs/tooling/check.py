"""Validate publication sources without executing article content."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
import markdown

ROOT = Path(__file__).resolve().parents[2]
PUBLICATIONS = ROOT / "docs/publications"


def local(path):
    value = ROOT / path
    guide = path in {"docs/CONTRIBUTING.md", "docs/CONTRIBUTING.zh-CN.md"}
    if value.is_symlink() or (not guide and not value.resolve().is_relative_to(PUBLICATIONS.resolve())):
        raise ValueError("Publication path escapes its directory: " + path)
    return value


def inspect_html(text):
    soup = BeautifulSoup(markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"]), "html.parser")
    for n in soup.find_all():
        if n.name in {"script", "style", "object", "embed", "form", "input", "button", "base", "link", "meta"}:
            raise ValueError("Executable document element: " + n.name)
        for key, value in n.attrs.items():
            if key.lower().startswith("on") or key in {"srcdoc", "formaction"}:
                raise ValueError("Executable document attribute")
            if key in {"href", "src", "poster", "xlink:href"}:
                value = re.sub(r"[\x00-\x20]+", "", str(value))
                scheme = urlsplit(value).scheme.lower()
                if scheme not in {"", "https", "http", "mailto", "tel", "data"}:
                    raise ValueError("Unsafe URL")
                if scheme == "data" and not (n.name == "img" and value.startswith(("data:image/png;", "data:image/jpeg;", "data:image/webp;"))):
                    raise ValueError("Only bitmap data URLs are accepted")
            if key == "style" and re.search(r"url\s*\(|expression\s*\(|@import", str(value), re.I):
                raise ValueError("Active CSS")
        if n.name == "iframe" and urlsplit(n.get("src", "")).hostname not in {"www.youtube.com", "www.youtube-nocookie.com", "player.bilibili.com"}:
            raise ValueError("Unapproved video host")
    return soup


def main():
    cat = json.loads((PUBLICATIONS / "catalogue.json").read_text())
    urls = {r["url"] for r in cat["documents"]}
    if len(urls) != len(cat["documents"]):
        raise ValueError("Duplicate page")
    for row in cat["documents"]:
        if not re.fullmatch(r"/(?:[a-z0-9-]+/)+", row["url"]):
            raise ValueError("Invalid route")
        src = local(row["path"])
        text = src.read_text()
        if re.search(r"(?:/Users/|/home/|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9]{20}|sb_secret_)", text):
            raise ValueError("Private path or credential pattern: " + row["path"])
        soup = inspect_html(text)
        if len(soup.select("h1")) != 1:
            raise ValueError("Expected exactly one title: " + row["path"])
        pair = row["url"][3:] if row["language"] == "zh" else "/zh" + row["url"]
        if pair not in urls and row["url"] not in cat.get("translation_pending", []):
            raise ValueError("Missing translation: " + row["url"])
        for a in soup.select("a[href],img[src]"):
            value = a.get("href", a.get("src"))
            target = urlsplit(value)
            if not target.scheme and target.path:
                file = src.parent / target.path
                if not file.resolve().is_relative_to(ROOT.resolve()) or not file.exists():
                    raise ValueError("Broken relative link: " + row["path"] + ": " + value)
    for asset in cat["assets"]:
        file = local(asset["path"])
        if not file.is_file() or file.stat().st_size > 20 * 1024 * 1024:
            raise ValueError("Missing or oversized figure")
        if file.suffix == ".svg":
            svg = ET.fromstring(file.read_text())
            for element in svg.iter():
                if element.tag.rsplit("}", 1)[-1].lower() in {"script", "object", "embed", "iframe", "form", "input", "button", "link", "meta"}:
                    raise ValueError("Executable SVG element")
                for key, value in element.attrib.items():
                    key = key.rsplit("}", 1)[-1].lower()
                    if key.startswith("on") or (key in {"href", "src"} and urlsplit(value).scheme.lower() not in {"", "http", "https"}):
                        raise ValueError("Executable SVG attribute")
    for lang in ("zh", "en"):
        for module in ("perception", "memory", "reasoning", "action", "reflection", "collaboration", "governance"):
            prefix = "/zh" if lang == "zh" else ""
            if prefix + "/patterns/" + module + "/" not in urls:
                raise ValueError("Missing module overview")
    if len([r for r in cat["documents"] if r["id"].startswith("workshops/")]) < 14:
        raise ValueError("The initial seven bilingual workshops must remain available")
    print(f"Publication checks passed: {len(urls)} articles, {len(cat['assets'])} figures")


if __name__ == "__main__":
    main()
