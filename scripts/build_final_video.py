#!/usr/bin/env python3
"""
scripts/build_final_video.py (60-Second Submission Master • 15 Mbps CBR)
Implements all final pre-submission edits:
1. ~60-second total runtime; reaches the live app at 0:04.5 and failing dashboard by 0:13.
2. Crops out Microsoft Edge tabs, URL bar, and the "Browse right away..." startup banner in Clip 1 & Clip 3.
3. Minimalist opening slide: "A field moved. Revenue disappeared. SchemaCourt catches breaking data-contract changes—with human approval."
4. Precise, honest framing: "A $17.2M simulated baseline metric evaluates to NULL after a schema change" + "Why alerts alone aren't enough".
5. True 15 Mbps High-Bitrate CBR/ABR encoding (-b:v 15M -minrate 12M -maxrate 18M, nal-hrd=cbr) so YouTube/Devpost compression stays razor-sharp.
"""
import shutil
import subprocess
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "build_video"


def get_ffmpeg_bin() -> str:
    """Finds imageio_ffmpeg or system ffmpeg."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys_ffmpeg = shutil.which("ffmpeg")
        if sys_ffmpeg:
            return sys_ffmpeg
        return "ffmpeg"


def find_clip(candidates: list[str]) -> Path:
    search_folders = [
        BASE_DIR,
        BASE_DIR / "videos",
        Path("C:/Users/mihee/Videos/Screen Recordings"),
        Path.cwd(),
    ]
    for folder in search_folders:
        for name in candidates:
            p = folder / name
            if p.exists():
                return p
    raise FileNotFoundError(
        f"Could not find {candidates[0]} in {search_folders}."
    )


SLIDES_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; }
  body {
    width: 1920px; height: 1080px; overflow: hidden;
    background: radial-gradient(circle at 20% 20%, #111827 0%, #090d16 65%, #05070c 100%);
    color: #f8fafc; display: flex; align-items: center; justify-content: center;
  }
  .slide {
    width: 1540px; padding: 76px 84px; border-radius: 24px;
    background: rgba(15, 23, 42, 0.92); border: 2px solid #1e293b;
    box-shadow: 0 25px 70px rgba(0,0,0,0.75);
  }
  .eyebrow {
    display: inline-block; padding: 8px 18px; border-radius: 999px;
    font-size: 17px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase;
    margin-bottom: 28px; background: #064e3b; color: #6ee7b7; border: 1px solid #10b981;
  }
  h1 { font-size: 76px; font-weight: 900; line-height: 1.08; margin-bottom: 28px; letter-spacing: -1.5px; color: #ffffff; }
  p.promise { font-size: 38px; font-weight: 600; color: #e2e8f0; line-height: 1.38; margin-bottom: 40px; }
  .sub-pill {
    display: inline-block; background: #090d16; border: 1px solid #334155;
    padding: 14px 24px; border-radius: 12px; font-size: 22px; color: #38bdf8; font-weight: 600;
  }
  .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; margin-top: 32px; }
  .card { background: #090d16; border: 1px solid #334155; border-radius: 16px; padding: 24px 26px; }
  .card-title { font-size: 20px; font-weight: 800; color: #38bdf8; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.6px; }
  .card-body { font-size: 21px; color: #e2e8f0; line-height: 1.4; }
  .code-pill {
    font-family: Consolas, monospace; background: #1e293b; color: #38bdf8;
    padding: 3px 10px; border-radius: 6px; font-size: 0.9em;
  }
</style>
</head>
<body>
  <div id="stage"></div>
  <script>
    window.showSlide = function(htmlContent) {
      document.getElementById('stage').innerHTML = `<div class="slide">${htmlContent}</div>`;
    };
  </script>
</body>
</html>
"""

OVERLAY_GEN_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, sans-serif; }
  body { background: transparent; width: 1920px; height: 1080px; overflow: hidden; position: relative; }
  .top-bar {
    position: absolute; top: 0; left: 0; width: 1920px; height: 56px;
    background: #090d16; border-bottom: 2px solid #0284c7;
    display: flex; align-items: center; justify-content: space-between; padding: 0 28px;
  }
  .top-left { display: flex; align-items: center; gap: 14px; }
  .part-pill {
    background: #0284c7; color: #ffffff; font-weight: 800; font-size: 15px;
    padding: 5px 12px; border-radius: 6px; letter-spacing: 0.8px; text-transform: uppercase;
  }
  .part-pill.purple { background: #7c3aed; }
  .top-desc { color: #f8fafc; font-size: 18px; font-weight: 600; }
  .top-right { color: #94a3b8; font-size: 14px; font-family: Consolas, monospace; }
  /* Masks out the right-pane Edge browser tabs + localhost URL bar in Clip 3 */
  .chrome-mask {
    position: absolute; left: 690px; top: 56px; width: 1230px; height: 56px;
    background: #0e1117; border-bottom: 1px solid #1e293b;
    display: none; align-items: center; justify-content: space-between; padding: 0 24px;
  }
  .mask-title { color: #94a3b8; font-size: 14px; font-weight: 600; font-family: Consolas, monospace; }
  .mask-badge { background: #1e293b; color: #38bdf8; font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 6px; }
  .wispr-callout {
    position: absolute; left: 520px; top: 840px;
    background: linear-gradient(90deg, #5b21b6 0%, #7c3aed 100%);
    border: 2px solid #c4b5fd; border-radius: 12px;
    padding: 12px 20px; color: #ffffff;
    box-shadow: 0 12px 32px rgba(0,0,0,0.75);
    display: none; align-items: center; gap: 12px;
  }
  .wispr-title { font-size: 17px; font-weight: 800; letter-spacing: 0.4px; }
  .wispr-sub { font-size: 13.5px; color: #ede9fe; margin-top: 2px; }
</style>
</head>
<body>
  <div class="top-bar">
    <div class="top-left">
      <span class="part-pill" id="pill">STEP 1</span>
      <span class="top-desc" id="desc">Description</span>
    </div>
    <div class="top-right">SchemaCourt • Simulated 100k-Row Baseline</div>
  </div>
  <div class="chrome-mask" id="chrome-mask">
    <span class="mask-title">⚖️ SchemaCourt Live Contract Monitor (100,000 Fixture Rows)</span>
    <span class="mask-badge">Auto-Refresh: 1s</span>
  </div>
  <div class="wispr-callout" id="wispr-box">
    <div style="font-size: 26px;">👈 🎙️</div>
    <div>
      <div class="wispr-title">HUMAN APPROVAL VIA WISPR FLOW VOICE</div>
      <div class="wispr-sub">AI proposes evidence; @maya_data controls the decision by voice</div>
    </div>
  </div>
  <script>
    window.configureOverlay = function(partTitle, descText, isPurple, showWispr, maskRightChrome) {
      const pill = document.getElementById('pill');
      pill.textContent = partTitle;
      pill.className = isPurple ? 'part-pill purple' : 'part-pill';
      document.getElementById('desc').textContent = descText;
      document.getElementById('wispr-box').style.display = showWispr ? 'flex' : 'none';
      document.getElementById('chrome-mask').style.display = maskRightChrome ? 'flex' : 'none';
    };
  </script>
</body>
</html>
"""

SLIDE_CONTENTS = {
    "intro_hook": (
        4.5,
        """
        <span class="eyebrow">⚖️ SCHEMACOURT • DATA CONTRACT CHANGE REVIEW</span>
        <h1>A field moved.<br>Revenue disappeared.</h1>
        <p class="promise">
          SchemaCourt catches breaking data-contract changes—with human approval.
        </p>
        <div class="sub-pill">
          Evidence, approval, and verification—not just alerts.
        </div>
        """
    ),
    "outro_summary": (
        4.5,
        """
        <span class="eyebrow">✅ VERIFIED across 100,000 LEGACY &amp; DRIFTED FIXTURE ROWS</span>
        <h1 style="font-size: 62px;">AI Investigates &amp; Proposes.<br>Humans Control the Decision.</h1>
        <p class="promise" style="font-size: 28px; margin-bottom: 24px;">
          A <b>$17.2M simulated baseline metric</b> evaluated to <span class="code-pill">NULL</span> after a schema change—caught,
          approved by voice, and verified with <b>$0.00 delta</b>.
        </p>
        <div class="grid-3">
          <div class="card">
            <div class="card-title">Why Alerts Aren't Enough</div>
            <div class="card-body">Evidence, approval, and dual-contract verification in one shared Switch Room.</div>
          </div>
          <div class="card">
            <div class="card-title">Accountable Sign-Off</div>
            <div class="card-body"><b>@SchemaCourtBot</b> proposes the SQL repair; <b>@maya_data</b> approves via <b>Wispr Flow</b>.</div>
          </div>
          <div class="card">
            <div class="card-title" style="color:#34d399;">Dual-Fixture Proof</div>
            <div class="card-body">100,000 Legacy + 100,000 Drifted Parquet rows verified in DuckDB (<b>$0.00 delta</b>).</div>
          </div>
        </div>
        """
    ),
}

# True 15 Mbps CBR/ABR High-Profile H.264 Master Flags (No -crf override!)
TRUE_15MBPS_VIDEO_FLAGS = [
    "-c:v", "libx264",
    "-profile:v", "high",
    "-level:v", "4.2",
    "-preset", "medium",
    "-b:v", "15M",
    "-minrate", "12M",
    "-maxrate", "18M",
    "-bufsize", "30M",
    "-x264-params", "nal-hrd=cbr:force-cfr=1",
    "-g", "60",
    "-pix_fmt", "yuv420p",
]


def run_ffmpeg(ffmpeg_bin: str, args: list[str]) -> None:
    cmd = [ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "error"] + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{res.stderr}")


def render_slides_and_overlays(ffmpeg_bin: str, slides_html: Path, overlay_html: Path) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        # 1. Render transparent PNG overlays
        ov_page = browser.new_page(viewport={"width": 1920, "height": 1080})
        ov_page.goto(overlay_html.as_uri())

        overlays = [
            (
                "ov_part1.png",
                "1. SCHEMA CHANGE DETECTED",
                "A $17.2M simulated baseline metric evaluates to NULL after discount_cents moves",
                False, False, False
            ),
            (
                "ov_part2.png",
                "2. EVIDENCE & PROPOSAL",
                "@SchemaCourtBot reports verified impact, proposes COALESCE repair & waits for @maya_data",
                False, False, False
            ),
            (
                "ov_part3_base.png",
                "3. HUMAN APPROVAL & PROOF",
                "@maya_data approves via Wispr Flow -> Verified across 100k legacy & drifted rows ($0.00 delta)",
                True, False, True
            ),
            (
                "ov_part3_wispr.png",
                "3. HUMAN APPROVAL & PROOF",
                "@maya_data approves via Wispr Flow -> Verified across 100k legacy & drifted rows ($0.00 delta)",
                True, True, True
            ),
        ]
        for fname, title, desc, is_purple, show_wispr, mask_chrome in overlays:
            ov_page.evaluate(
                "(args) => window.configureOverlay(args.t, args.d, args.p, args.w, args.m)",
                {"t": title, "d": desc, "p": is_purple, "w": show_wispr, "m": mask_chrome},
            )
            ov_page.screenshot(path=str(OUT_DIR / fname), omit_background=True)
        ov_page.close()

        # 2. Render lossless PNG slides and encode at True 15 Mbps 60fps
        slide_page = browser.new_page(viewport={"width": 1920, "height": 1080})
        slide_page.goto(slides_html.as_uri())

        for key, (dur, html_body) in SLIDE_CONTENTS.items():
            slide_png = OUT_DIR / f"slide_{key}.png"
            out_mp4 = OUT_DIR / f"slide_{key}.mp4"
            slide_page.evaluate("(html) => window.showSlide(html)", html_body)
            slide_page.wait_for_timeout(100)
            slide_page.screenshot(path=str(slide_png))

            run_ffmpeg(
                ffmpeg_bin,
                [
                    "-loop", "1",
                    "-framerate", "60",
                    "-i", str(slide_png),
                    "-t", str(dur),
                    "-vf", "scale=1920:1080:flags=lanczos,fps=60",
                ]
                + TRUE_15MBPS_VIDEO_FLAGS
                + ["-an", str(out_mp4)],
            )

        slide_page.close()
        browser.close()


def process_clip(
    ffmpeg_bin: str,
    src_mp4: Path,
    overlay_png: Path,
    out_mp4: Path,
    crop_filter: str,
    start_sec: float = 0.0,
    freeze_end_sec: float = 0.0,
    wispr_overlay_png: Path | None = None,
) -> None:
    """
    Trims dead start time, crops out browser chrome/banners, scales cleanly into 1920x1024 at y=56,
    and encodes at a true 15 Mbps CBR/ABR so text remains ultra-sharp after upload.
    """
    tpad = f",tpad=stop_mode=clone:stop_duration={freeze_end_sec}" if freeze_end_sec > 0 else ""
    base_chain = (
        f"[0:v]{crop_filter},"
        f"scale=1920:1024:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad=1920:1080:(ow-iw)/2:56+(1024-ih)/2:black,fps=60{tpad}[vid];"
    )

    ss_args = ["-ss", str(start_sec)] if start_sec > 0 else []

    if wispr_overlay_png is None:
        filter_complex = f"{base_chain}[vid][1:v]overlay=0:0,format=yuv420p[out]"
        inputs = ss_args + ["-i", str(src_mp4), "-i", str(overlay_png)]
    else:
        filter_complex = (
            f"{base_chain}"
            f"[vid][1:v]overlay=0:0[tmp];"
            f"[tmp][2:v]overlay=0:0:enable='between(t,1.0,11.0)',format=yuv420p[out]"
        )
        inputs = ss_args + ["-i", str(src_mp4), "-i", str(overlay_png), "-i", str(wispr_overlay_png)]

    run_ffmpeg(
        ffmpeg_bin,
        inputs
        + ["-filter_complex", filter_complex, "-map", "[out]"]
        + TRUE_15MBPS_VIDEO_FLAGS
        + ["-an", str(out_mp4)],
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg_bin = get_ffmpeg_bin()

    clip1_src = find_clip(["clip1(final).mp4", "clip1.mp4"])
    clip2_src = find_clip(["clip2(final).mp4", "clip2.mp4"])
    clip3_src = find_clip(["clip3.mp4", "clip3(final).mp4"])

    slides_html = OUT_DIR / "slides.html"
    slides_html.write_text(SLIDES_HTML, encoding="utf-8")
    overlay_html = OUT_DIR / "overlays.html"
    overlay_html.write_text(OVERLAY_GEN_HTML, encoding="utf-8")

    print("[1/4] Rendering simplified opening/closing slides & chrome-masking overlays...")
    render_slides_and_overlays(ffmpeg_bin, slides_html, overlay_html)

    c1_out = OUT_DIR / "demo_clip1.mp4"
    c2_out = OUT_DIR / "demo_clip2.mp4"
    c3_out = OUT_DIR / "demo_clip3.mp4"

    # Clip 1: Skip first 2.3s (half-loaded state) & crop y=138..1042 to remove Edge tabs, URL bar & "Browse right away..." banner
    print("[2/4] Encoding Clip 1 (Cropping out Edge banner/tabs + 2.5s freeze on Red Dashboard @ 15 Mbps)...")
    process_clip(
        ffmpeg_bin,
        clip1_src,
        OUT_DIR / "ov_part1.png",
        c1_out,
        crop_filter="crop=1776:904:72:138",
        start_sec=2.3,
        freeze_end_sec=2.5,
    )

    # Clip 2: Skip first 2.0s ("You created a group" empty box) & crop tight around Telegram window
    print("[3/4] Encoding Clip 2 (Tight Telegram viewport @ 15 Mbps)...")
    process_clip(
        ffmpeg_bin,
        clip2_src,
        OUT_DIR / "ov_part2.png",
        c2_out,
        crop_filter="crop=1404:1036:258:20",
        start_sec=2.0,
        freeze_end_sec=1.5,
    )

    # Clip 3: Skip first 2.2s idle wait, crop desktop margins, mask right-pane Edge tabs/URL bar, keep Wispr bar 100% visible
    print("[4/4] Encoding Clip 3 (Masked Edge tabs + Wispr Flow approval + Green recovery @ 15 Mbps)...")
    process_clip(
        ffmpeg_bin,
        clip3_src,
        OUT_DIR / "ov_part3_base.png",
        c3_out,
        crop_filter="crop=1780:1016:70:44",
        start_sec=2.2,
        freeze_end_sec=3.0,
        wispr_overlay_png=OUT_DIR / "ov_part3_wispr.png",
    )

    ordered_files = [
        OUT_DIR / "slide_intro_hook.mp4",
        c1_out,
        c2_out,
        c3_out,
        OUT_DIR / "slide_outro_summary.mp4",
    ]

    concat_list = OUT_DIR / "concat_list.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in ordered_files),
        encoding="utf-8"
    )

    final_output = BASE_DIR / "SchemaCourt_Submission_60s_15Mbps.mp4"
    run_ffmpeg(
        ffmpeg_bin,
        [
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(final_output),
        ],
    )
    size_mb = round(final_output.stat().st_size / (1024 * 1024), 1)
    print(f"\n🎉 60s HIGH-BITRATE MASTER READY ({size_mb} MB @ ~15 Mbps):\n   {final_output}")

    # Also mirror to Videos / Screen Recordings for user accessibility
    videos_dest = Path("C:/Users/mihee/Videos/Screen Recordings") / "SchemaCourt_Submission_60s_15Mbps.mp4"
    try:
        shutil.copy2(final_output, videos_dest)
        print(f"   Mirrored to: {videos_dest}")
    except Exception as e:
        print(f"   Note: Could not mirror to Screen Recordings: {e}")


if __name__ == "__main__":
    main()
