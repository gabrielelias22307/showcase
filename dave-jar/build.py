"""Embed model/jar.glb into index.html as a data URI.

Canvas serves uploaded HTML over ~450 KB from a host that does not run
JavaScript, so the finished page must stay under that ceiling.
"""
import base64, pathlib, re, sys

here = pathlib.Path(__file__).parent
page = here / "index.html"
glb = base64.b64encode((here / "model" / "jar.glb").read_bytes()).decode()
html = re.sub(r'(data:model/gltf-binary;base64,)[^"]*', lambda m: m.group(1) + glb, page.read_text())
page.write_text(html)
kb = len(html.encode()) / 1024
print(f"index.html: {kb:.0f} KB")
sys.exit(1 if kb > 440 else 0)
