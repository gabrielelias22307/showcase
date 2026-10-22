# Handover: put "Jar Made by Dave" into Canvas

**For:** a Claude Cowork session on the teacher's computer, with Chrome signed in to Canvas.
**Skill to load first:** `canvas-unit-build`. It covers the connection and the Control Chrome traps. This file covers only this one item.

## What to build

One 3D-object activity, delivered as:

1. **A file** in Course Files: `Jar Made by Dave - 3D Activity.html` (390,356 bytes).
2. **An assignment** whose description holds an iframe to that file.
3. **A module item** in the module and position the teacher chooses.

Everything lands **unpublished**.

| Field | Value |
|---|---|
| Name | `🟥 L#: 3D Object — Jar Made by Dave` (teacher gives the L number) |
| Points | 1 |
| Submission types | `online_text_entry`, `online_upload` |
| Published | false |
| Assignment group | same as the module's other lessons |

The submission types come from the file's own buttons. It has **Copy My Answers** (text entry) and **Download (.txt)** (file upload). Checked with:

```bash
grep -o '<button[^>]*>[^<]\{2,60\}</button>' "Jar Made by Dave - 3D Activity.html" | sed 's/<[^>]*>//g' | sort -u
```

## Ask the teacher once, before the first write

- Which course? (Get the ID from the URL `/courses/<id>`.)
- Which module, and at what position?
- What L number goes in the title?

Show them the plan in the table above, get one yes, then go.

## Authentication: there is no API key

Don't ask for, create or paste a Canvas access token. Every call runs inside the teacher's signed-in Chrome tab and uses the session's CSRF cookie. `examples/worker-helpers.js` has the helper. If a call returns 401 or 403, stop and tell the teacher. Don't look for another way in.

## Steps

All URLs are relative to the teacher's Canvas domain. Run the calls from a worker tab open on `/api/v1/users/self`, as the skill says.

### 1. Upload the file (Canvas's three-step file upload)

1. `POST /api/v1/courses/:cid/files` with the body in `examples/1-file-upload-request.json`. The `size` must be the exact byte count. The reply holds `upload_url` and `upload_params`.
2. Send the bytes from the teacher's computer (the same pattern the skill uses for QTI zips). Put every `upload_params` key first, then the file:
   ```bash
   curl -sS -X POST "<upload_url>" \
     -F "<each upload_params key>=<value>" \
     -F "file=@Jar Made by Dave - 3D Activity.html;type=text/html"
   ```
3. If the reply is a redirect or has a `location`, `GET` or `POST` that URL to confirm. The final JSON has the file `id`. That is **FILE_ID**.

**Check:** `GET /api/v1/files/FILE_ID` shows `size: 390356`. Canvas display names can be misleading, so match files by byte size, not by name.

### 2. Create the assignment

`POST /api/v1/courses/:cid/assignments` with `examples/2-assignment.json`, after swapping `COURSE_ID`, `FILE_ID`, `L#` and `GROUP_ID`. The description is `examples/canvas-embed.html` with the same two numbers swapped in. Pass it as a template literal (backticks) and write the emoji as `\u{1F7E5}`.

### 3. Add it to the module

`POST /api/v1/courses/:cid/modules/:mid/items` with `examples/3-module-item.json`. Set `position` to the slot the teacher chose. Each insert shifts the items below it.

### 4. Verify before reporting

Read everything back from the API:

- The assignment has `published: false`, `points_possible: 1` and both submission types.
- The description still contains the `<iframe` with `/files/FILE_ID/preview`. Canvas keeps iframes, plus `allow`, `allowfullscreen` and `loading`.
- The module item sits at the right position and is unpublished.

Then open the assignment in **Student View** and confirm:

- The page loads inside the iframe (not blank). A blank page usually means the file is over about 450 KB. This one is 390 KB.
- The 3D jar appears in the **Quick viewer** tab. It loads `model-viewer` from `cdn.jsdelivr.net`. If a school filter blocks that, the page switches to the **Smithsonian viewer** tab after about 12 seconds.
- **Check My Answers** marks a wrong answer red.

## Report back to the teacher

- The module listing with positions and published flags.
- What you checked, and how.
- That everything is **unpublished**.
- Anything you couldn't confirm. In particular, whether the jar loaded in Student View.

## Files in this folder

| File | What it is |
|---|---|
| `Jar Made by Dave - 3D Activity.html` | The activity to upload (390 KB, self-contained, 3D model built in) |
| `examples/1-file-upload-request.json` | Step 1 request body |
| `examples/2-assignment.json` | Step 2 request body, with placeholders |
| `examples/3-module-item.json` | Step 3 request body, with placeholders |
| `examples/canvas-embed.html` | The iframe that becomes the assignment description |
| `examples/worker-helpers.js` | CSRF helper plus a call-by-call example sequence |

Source and history: `github.com/gabrielelias22307/showcase`, branch `claude/amazing-lamport-invmx6`, folder `dave-jar/`.
