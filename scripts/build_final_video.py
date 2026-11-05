#!/usr/bin/env python3
"""
scripts/build_final_video.py
Produces SchemaCourt_Final_60s.mp4 (Locked 60.0s duration, 1080p60):
- 00-04s (4s): Opening card ("A field moved. Revenue disappeared...")
- 04-14s (10s): Dashboard goes directly from Green Baseline (4-9s) to Red Failure (9-14s) with ZERO black PowerShell gap
- 14-31s (17s): Tight zoom on @SchemaCourtBot diagnosis, COALESCE(...) SQL repair, and @maya_data prompt
- 31-43s (12s): Human approval via Wispr Flow voice dictation (cropped below browser tabs)
- 43-55s (12s): Dashboard turns green + $0.00 delta + dual-contract verification table & decision record
- 55-60s (5s): Final SchemaCourt thesis card
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
    background: rgba(15, 23, 42, 0.94); border: 2px solid #1e293b;
    box-shadow: 0 25px 70px rgba(0,0,0,0.8);
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
  .card-title { font-size: 19px; font-weight: 800; color: #38bdf8; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.6px; }
  .card-body { font-size: 20.5px; color: #e2e8f0; line-height: 1.4; }
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
  .part-pill.red { background: #dc2626; }
  .part-pill.purple { background: #7c3aed; }
  .part-pill.green { background: #059669; }
  .top-desc { color: #f8fafc; font-size: 18px; font-weight: 600; }
  .top-right { color: #94a3b8; font-size: 14px; font-family: Consolas, monospace; }
  .wispr-callout {
    position: absolute; left: 530px; top: 835px;
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
  <div class="wispr-callout" id="wispr-box">
    <div style="font-size: 26px;">👈 🎙️</div>
    <div>
      <div class="wispr-title">HUMAN APPROVAL VIA WISPR FLOW VOICE</div>
      <div class="wispr-sub">AI proposes evidence; @maya_data controls the decision by voice</div>
    </div>
  </div>
  <script>
    window.configureOverlay = function(partTitle, descText, pillColor, showWispr) {
      const pill = document.getElementById('pill');
      pill.textContent = partTitle;
      pill.className = 'part-pill ' + (pillColor || '');
      document.getElementById('desc').textContent = descText;
      document.getElementById('wispr-box').style.display = showWispr ? 'flex' : 'none';
    };
  </script>
</body>
</html>
"""

SLIDE_CONTENTS = {
    "intro_hook": (
        4.0,
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
        5.0,
        """
        <span class="eyebrow">✅ VERIFIED ACROSS 100,000 LEGACY &amp; DRIFTED FIXTURE ROWS</span>
        <h1 style="font-size: 62px;">AI Investigates &amp; Proposes.<br>Humans Control the Decision.</h1>
        <p class="promise" style="font-size: 27px; margin-bottom: 24px;">
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

# Crisp 1080p60 High-Profile Encoding Flags (QP 12 near-lossless for crystal-clear UI/code text)
VIDEO_ENCODE_FLAGS = [
    "-c:v", "libx264",
    "-profile:v", "high",
    "-level:v", "4.2",
    "-preset", "slow",
    "-qp", "12",
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

        # 1. Render transparent PNG top headers
        ov_page = browser.new_page(viewport={"width": 1920, "height": 1080})
        ov_page.goto(overlay_html.as_uri())

        overlays = [
            (
                "ov_1a_baseline.png",
                "1. SIMULATED BASELINE PASSING",
                "checkout-service v2.8 matches contract -> $17.2M simulated baseline verified across 100,000 rows",
                "green", False
            ),
            (
                "ov_1b_failing.png",
                "1. SCHEMA CHANGE -> CONTRACT FAILING",
                "checkout-service v3.0 moves discount_cents into promo_struct -> $17.2M metric evaluates to NULL",
                "red", False
            ),
            (
                "ov_2_diagnosis.png",
                "2. EVIDENCE & PROPOSED REPAIR",
                "@SchemaCourtBot isolates schema impact, proposes COALESCE(...) SQL diff & waits for @maya_data",
                "", False
            ),
            (
                "ov_3_approval_wispr.png",
                "3. HUMAN APPROVAL (WISPR FLOW)",
                "@maya_data approves the proposed repair by voice before any SQL model change is applied",
                "purple", True
            ),
            (
                "ov_3_approval_sent.png",
                "3. HUMAN APPROVAL (WISPR FLOW)",
                "@maya_data approval received -> @SchemaCourtBot applies patch & runs dual-fixture check",
                "purple", False
            ),
            (
                "ov_4_verified.png",
                "4. DUAL-CONTRACT PROOF ($0.00 DELTA)",
                "Verified across 100,000 Legacy + 100,000 Drifted rows -> Dashboard returns to GREEN & decision logged",
                "green", False
            ),
        ]
        for fname, title, desc, color, show_wispr in overlays:
            ov_page.evaluate(
                "(args) => window.configureOverlay(args.t, args.d, args.c, args.w)",
                {"t": title, "d": desc, "c": color, "w": show_wispr},
            )
            ov_page.screenshot(path=str(OUT_DIR / fname), omit_background=True)
        ov_page.close()

        # 2. Render lossless PNG slides and encode to exact duration at 60fps
        slide_page = browser.new_page(viewport={"width": 1920, "height": 1080})
        slide_page.goto(slides_html.as_uri())

        for key, (dur, html_body) in SLIDE_CONTENTS.items():
            slide_png = OUT_DIR / f"slide_{key}.png"
            out_mp4 = OUT_DIR / f"seg_{key}.mp4"
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
                + VIDEO_ENCODE_FLAGS
                + ["-an", str(out_mp4)],
            )

        slide_page.close()
        browser.close()


def build_locked_segment(
    ffmpeg_bin: str,
    src_mp4: Path,
    overlay_png: Path,
    out_mp4: Path,
    crop_filter: str,
    start_sec: float,
    clip_play_sec: float,
    total_segment_sec: float,
) -> None:
    """
    Extracts exactly `clip_play_sec` starting at `start_sec`, crops tightly around the active UI,
    freezes the final frame to reach `total_segment_sec` (if needed), and locks duration with `-t`.
    """
    freeze_sec = max(0.0, round(total_segment_sec - clip_play_sec, 3))
    tpad = f",tpad=stop_mode=clone:stop_duration={freeze_sec + 0.5}" if freeze_sec > 0 else ""

    filter_complex = (
        f"[0:v]trim=start={start_sec}:duration={clip_play_sec},setpts=PTS-STARTPTS,"
        f"{crop_filter},"
        f"scale=1920:1024:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad=1920:1080:(ow-iw)/2:56+(1024-ih)/2:black,fps=60{tpad}[vid];"
        f"[vid][1:v]overlay=0:0,format=yuv420p[out]"
    )

    run_ffmpeg(
        ffmpeg_bin,
        [
            "-i", str(src_mp4),
            "-i", str(overlay_png),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-t", str(total_segment_sec),
        ]
        + VIDEO_ENCODE_FLAGS
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

    print("[1/8] Rendering opening (4.0s) and closing (5.0s) cards...")
    render_slides_and_overlays(ffmpeg_bin, slides_html, overlay_html)

    # 04-09s (5.0s): Passing Baseline Dashboard (Clip 1, 2.2s..7.2s, cropped below Edge banner)
    print("[2/8] 04-09s (5.0s): Green Baseline Dashboard (no browser chrome)...")
    seg_1a = OUT_DIR / "seg_1a_baseline.mp4"
    build_locked_segment(
        ffmpeg_bin, clip1_src, OUT_DIR / "ov_1a_baseline.png", seg_1a,
        crop_filter="crop=1776:904:72:138",
        start_sec=2.2, clip_play_sec=5.0, total_segment_sec=5.0,
    )

    # 09-14s (5.0s): Failing Red Dashboard in-place (Clip 1, 13.8s..15.0s + 3.8s hold -> ZERO black screen!)
    print("[3/8] 09-14s (5.0s): In-place flip to Red Failing Dashboard (zero black gap)...")
    seg_1b = OUT_DIR / "seg_1b_failing.mp4"
    build_locked_segment(
        ffmpeg_bin, clip1_src, OUT_DIR / "ov_1b_failing.png", seg_1b,
        crop_filter="crop=1776:904:72:138",
        start_sec=13.8, clip_play_sec=1.2, total_segment_sec=5.0,
    )

    # 14-18s (4.0s): Tight zoom on user prompt & @SchemaCourtBot starting diagnosis
    print("[4/8] 14-18s (4.0s): Tight zoom on Telegram prompt & @SchemaCourtBot trigger...")
    seg_2a = OUT_DIR / "seg_2a_prompt.mp4"
    build_locked_segment(
        ffmpeg_bin, clip2_src, OUT_DIR / "ov_2_diagnosis.png", seg_2a,
        crop_filter="crop=1200:640:265:415",
        start_sec=2.2, clip_play_sec=4.0, total_segment_sec=4.0,
    )

    # 18-31s (13.0s): Tight zoom on Bot Diagnosis, COALESCE(...) SQL Diff & @maya_data approval request
    print("[5/8] 18-31s (13.0s): Tight zoom on Bot Diagnosis, COALESCE(...) repair & @maya_data prompt...")
    seg_2b = OUT_DIR / "seg_2b_diagnosis.mp4"
    build_locked_segment(
        ffmpeg_bin, clip2_src, OUT_DIR / "ov_2_diagnosis.png", seg_2b,
        crop_filter="crop=1160:815:265:225",
        start_sec=12.0, clip_play_sec=6.0, total_segment_sec=13.0,
    )

    # 31-39s (8.0s): Human approval via Wispr Flow voice dictation (cropped below browser tabs, y=135..1040)
    print("[6/8] 31-39s (8.0s): @maya_data voice approval via Wispr Flow...")
    seg_3a = OUT_DIR / "seg_3a_wispr.mp4"
    build_locked_segment(
        ffmpeg_bin, clip3_src, OUT_DIR / "ov_3_approval_wispr.png", seg_3a,
        crop_filter="crop=1710:905:140:135",
        start_sec=3.8, clip_play_sec=8.0, total_segment_sec=8.0,
    )

    # 39-43s (4.0s): Approval sent in chat & @SchemaCourtBot running dual-contract check
    print("[7/8] 39-43s (4.0s): Approval message sent & agent executing patch...")
    seg_3b = OUT_DIR / "seg_3b_apply.mp4"
    build_locked_segment(
        ffmpeg_bin, clip3_src, OUT_DIR / "ov_3_approval_sent.png", seg_3b,
        crop_filter="crop=1710:905:140:135",
        start_sec=18.8, clip_play_sec=4.0, total_segment_sec=4.0,
    )

    # 43-55s (12.0s): Dashboard turns GREEN + $0.00 delta + Dual-Contract PASS table & Decision Record
    print("[8/8] 43-55s (12.0s): Dashboard flips GREEN + $0.00 delta + logged decision...")
    seg_4 = OUT_DIR / "seg_4_verified.mp4"
    build_locked_segment(
        ffmpeg_bin, clip3_src, OUT_DIR / "ov_4_verified.png", seg_4,
        crop_filter="crop=1710:905:140:135",
        start_sec=23.5, clip_play_sec=5.5, total_segment_sec=12.0,
    )

    ordered_files = [
        OUT_DIR / "seg_intro_hook.mp4",    # 00-04s (4.0s)
        seg_1a,                            # 04-09s (5.0s)
        seg_1b,                            # 09-14s (5.0s)
        seg_2a,                            # 14-18s (4.0s)
        seg_2b,                            # 18-31s (13.0s)
        seg_3a,                            # 31-39s (8.0s)
        seg_3b,                            # 39-43s (4.0s)
        seg_4,                             # 43-55s (12.0s)
        OUT_DIR / "seg_outro_summary.mp4", # 55-60s (5.0s)
    ]

    concat_list = OUT_DIR / "concat_list.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in ordered_files),
        encoding="utf-8"
    )

    final_output = BASE_DIR / "SchemaCourt_Final_60s.mp4"
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
    print(f"\n🎉 EXACT 60.0-SECOND SUBMISSION VIDEO READY ({size_mb} MB):\n   {final_output}")

    videos_dest = Path("C:/Users/mihee/Videos/Screen Recordings") / "SchemaCourt_Final_60s.mp4"
    try:
        shutil.copy2(final_output, videos_dest)
        print(f"   Mirrored to: {videos_dest}")
    except Exception as e:
        print(f"   Note: Could not mirror to Screen Recordings: {e}")


if __name__ == "__main__":
    main()
