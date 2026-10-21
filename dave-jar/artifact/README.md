Source for the Claude artifact version of this activity.

- `template.html` is the page. `__QUESTIONS__` is filled with the question
  markup from `../index.html`, and `src="jar.glb"` is swapped for
  `jar-hq.glb` embedded as a data URI (the artifact host does not serve .glb).
- `jar-hq.glb` is the sharper model (about 37k triangles, 2048px texture,
  quantized, no meshopt), since the artifact has no 450 KB ceiling.
