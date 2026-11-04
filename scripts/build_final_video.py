#!/usr/bin/env python3
"""
scripts/build_final_video.py (Master High-Bitrate Edition)
Implements all 5 judging upgrades:
1. Explicit 2-second product promise at 0:00 ("SchemaCourt catches and repairs breaking data-contract changes—with human approval.")
2. Concrete financial consequence ("Dashboards silently under-report revenue and ship incorrect financial reporting.")
3. Owns the SchemaCourt Agent (@SchemaCourtBot / @drift-sentry) identity instead of generic @claude wrapper framing.
4. Combines the 11s Product Teaser + Real Live Screen Recording (Clip 1 + Clip 2 + Clip 3) with non-overlapping top headers.
5. Exports a High-Bitrate 1080p60 Master (-crf 14, -b:v 12M, -maxrate 16M, -bufsize 32M) to preserve fine SQL/code text.
"""
import shutil
import subprocess
import sys
import time
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
        Path.cwd()
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
    width: 1580px; padding: 60px 72px; border-radius: 24px;
    background: rgba(15, 23, 42, 0.92); border: 2px solid #1e293b;
    box-shadow: 0 25px 70px rgba(0,0,0,0.75);
  }
  .promise-bar {
    background: linear-gradient(90deg, #064e3b 0%, #0f172a 100%);
    border: 1px solid #10b981; color: #ecfdf5;
    padding: 12px 22px; border-radius: 12px; font-size: 23px; font-weight: 700;
    margin-bottom: 28px; display: flex; align-items: center; justify-content: space-between;
  }
  .promise-tag {
    background: #10b981; color: #052e16; font-size: 14px; font-weight: 900;
    padding: 4px 10px; border-radius: 6px; text-transform: uppercase; letter-spacing: 1px;
  }
  .eyebrow {
    display: inline-block; padding: 8px 18px; border-radius: 999px;
    font-size: 17px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase;
    margin-bottom: 22px; background: #1e3a8a; color: #93c5fd; border: 1px solid #3b82f6;
  }
  .eyebrow.red { background: #7f1d1d; color: #fca5a5; border-color: #ef4444; }
  .eyebrow.green { background: #064e3b; color: #6ee7b7; border-color: #10b981; }
  .eyebrow.purple { background: #4c1d95; color: #ddd6fe; border-color: #8b5cf6; }
  h1 { font-size: 62px; font-weight: 900; line-height: 1.12; margin-bottom: 22px; letter-spacing: -1px; }
  p.lead { font-size: 29px; color: #cbd5e1; line-height: 1.45; margin-bottom: 32px; }
  .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-top: 18px; }
  .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 24px; }
  .card { background: #090d16; border: 1px solid #334155; border-radius: 16px; padding: 24px 26px; }
  .card-title { font-size: 22px; font-weight: 800; color: #38bdf8; margin-bottom: 10px; }
  .card-body { font-size: 20px; color: #e2e8f0; line-height: 1.42; }
  .stat-num { font-size: 44px; font-weight: 900; color: #10b981; margin-bottom: 6px; font-family: Consolas, monospace; }
  .code-pill {
    font-family: Consolas, monospace; background: #1e293b; color: #38bdf8;
    padding: 4px 12px; border-radius: 8px; font-size: 0.9em;
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
  .wispr-callout {
    position: absolute; left: 515px; top: 845px;
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
      <span class="part-pill" id="pill">PART 1</span>
      <span class="top-desc" id="desc">Description</span>
    </div>
    <div class="top-right">SchemaCourt Agent (@SchemaCourtBot &amp; @drift-sentry) • Switch AI</div>
  </div>
  <div class="wispr-callout" id="wispr-box">
    <div style="font-size: 26px;">👈 🎙️</div>
    <div>
      <div class="wispr-title">HUMAN APPROVAL VIA WISPR FLOW VOICE</div>
      <div class="wispr-sub">AI proposes evidence; @maya_data controls the decision by voice</div>
    </div>
  </div>
  <script>
    window.configureOverlay = function(partTitle, descText, isPurple, showWispr) {
      const pill = document.getElementById('pill');
      pill.textContent = partTitle;
      pill.className = isPurple ? 'part-pill purple' : 'part-pill';
      document.getElementById('desc').textContent = descText;
      document.getElementById('wispr-box').style.display = showWispr ? 'flex' : 'none';
    };
  </script>
</body>
</html>
"""

SLIDE_CONTENTS = {
    "intro_1_problem": (
        5.0,
        """
        <div class="promise-bar">
          <span>⚖️ <b>SchemaCourt</b> catches and repairs breaking data-contract changes—with human approval.</span>
          <span class="promise-tag">LIVE DEMO</span>
        </div>
        <h1>A Field Moved. Revenue Disappeared.</h1>
        <p class="lead">
          Backend ships <span class="code-pill">checkout-service v3.0</span> and moves <span class="code-pill">discount_cents</span>
          into <span class="code-pill">promo_struct</span>. Without a contract check, downstream models ship
          <b style="color:#f87171;">corrupted financial reporting</b> and silently under-report <b style="color:#f87171;">$17.2M</b> as <span class="code-pill">NULL</span>.
        </p>
        <div class="grid">
          <div class="card">
            <div class="card-title" style="color:#f87171;">❌ Why Unchecked AI &amp; CI Alerts Fail</div>
            <div class="card-body">CI alerts dump red logs without a fix. Auto-deploying AI patches without data-owner sign-off risks silent financial drift.</div>
          </div>
          <div class="card">
            <div class="card-title" style="color:#34d399;">✅ The SchemaCourt Evidence Workflow</div>
            <div class="card-body"><b>@SchemaCourtBot</b> &amp; <b>@drift-sentry</b> surface impact, propose a compatible repair, and wait for accountable human approval.</div>
          </div>
        </div>
        """
    ),
    "intro_2_brag": (
        4.8,
        """
        <div class="promise-bar">
          <span>⚖️ <b>SchemaCourt</b> — Evidence-Backed Change Review Room for Data Contracts</span>
          <span class="promise-tag">ARCHITECTURE</span>
        </div>
        <h1>AI Investigates &amp; Proposes.<br>Humans Control the Decision.</h1>
        <p class="lead">
          Powered by <b>Switch AI</b> in Telegram: uniting the Backend Producer, Data Owner (<span class="code-pill">@maya_data</span>),
          <span class="code-pill">@SchemaCourtBot</span>, and <span class="code-pill">@drift-sentry</span> in one shared room.
        </p>
        <div class="grid-4">
          <div class="card">
            <div class="stat-num">100,000</div>
            <div class="card-body">Parquet Rows Audited (Legacy + Drifted)</div>
          </div>
          <div class="card">
            <div class="stat-num">$17.2M</div>
            <div class="card-body">Financial Reporting Baseline Protected</div>
          </div>
          <div class="card">
            <div class="stat-num">$0.00</div>
            <div class="card-body">Measured Revenue Delta Across Tiers</div>
          </div>
          <div class="card">
            <div class="stat-num" style="color:#a78bfa;">Wispr</div>
            <div class="card-body">Voice-Driven Data Owner Sign-Off</div>
          </div>
        </div>
        """
    ),
    "card_step1": (
        2.2,
        """
        <span class="eyebrow red">LIVE DEMO • STEP 1 OF 3</span>
        <h1>A Field Moves ➔ Financial Reporting Breaks</h1>
        <p class="lead">
          Watch the live contract monitor flip from <b style="color:#34d399;">$17.2M Passing</b> to <b style="color:#f87171;">NULL (Failing)</b>
          when <span class="code-pill">checkout-service@v3.0.0-stripe</span> moves <span class="code-pill">discount_cents</span>.
        </p>
        """
    ),
    "card_step2": (
        2.4,
        """
        <span class="eyebrow">LIVE DEMO • STEP 2 OF 3</span>
        <h1><span class="code-pill">@SchemaCourtBot</span> Diagnoses &amp; Waits for <span class="code-pill">@maya_data</span></h1>
        <p class="lead">
          The SchemaCourt Agent separates verified schema evidence from its proposed <span class="code-pill">COALESCE</span> repair—and
          halts until the human Data Owner approves.
        </p>
        """
    ),
    "card_step3": (
        2.4,
        """
        <span class="eyebrow purple">LIVE DEMO • STEP 3 OF 3</span>
        <h1>Human Voice Approval ➔ Dual-Contract Proof ($0.00 Delta)</h1>
        <p class="lead">
          <span class="code-pill">@maya_data</span> approves via <b>Wispr Flow</b> voice dictation. <span class="code-pill">@drift-sentry</span>
          verifies all 100,000 Legacy &amp; Drifted rows before logging the decision.
        </p>
        """
    ),
    "outro_brag": (
        4.5,
        """
        <div class="promise-bar">
          <span>✅ <b>SchemaCourt</b> — Catching &amp; Repairing Breaking Data Changes with Human Approval</span>
          <span class="promise-tag">VERIFIED</span>
        </div>
        <h1>Evidence First. Human Approved. Zero Drift.</h1>
        <p class="lead">
          <b>Break Detected ➔ Evidence Surface ➔ Repair Proposed ➔ @maya_data Voice Approval ➔ Dual-Fixture Proof</b>
        </p>
        <div class="grid">
          <div class="card">
            <div class="card-title">🛠️ SchemaCourt Stack</div>
            <div class="card-body">@SchemaCourtBot • @drift-sentry • Switch AI • Telegram • Wispr Flow • DuckDB • Parquet • Streamlit</div>
          </div>
          <div class="card">
            <div class="card-title" style="color:#34d399;">📊 Dual-Contract Verification Proof</div>
            <div class="card-body">100,000 Legacy Rows + 100,000 Drifted Rows = <b>$17,200,000.00 Net Revenue ($0.00 Delta)</b></div>
          </div>
        </div>
        """
    ),
}

# High-Bitrate 1080p60 Master Encoding Flags (~12-16 Mbps, CRF 14, High Profile)
HIGH_QUALITY_VIDEO_FLAGS = [
    "-c:v", "libx264",
    "-profile:v", "high",
    "-level:v", "4.2",
    "-preset", "fast",
    "-crf", "14",
    "-b:v", "12M",
    "-maxrate", "16M",
    "-bufsize", "32M",
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

        # 1. Render transparent PNG overlays (Top header bars + Wispr callout)
        ov_page = browser.new_page(viewport={"width": 1920, "height": 1080})
        ov_page.goto(overlay_html.as_uri())

        overlays = [
            ("ov_part1.png", "STEP 1: BREAKING CHANGE", "A field moved (discount_cents -> promo_struct) -> $17.2M financial model evaluates to NULL", False, False),
            ("ov_part2.png", "STEP 2: SCHEMACOURT AGENT", "@SchemaCourtBot surfaces verified impact, proposes COALESCE repair & waits for @maya_data", False, False),
            ("ov_part3_base.png", "STEP 3: HUMAN VOICE APPROVAL & PROOF", "@maya_data approves via Wispr Flow -> @drift-sentry verifies 100,000 rows ($0.00 delta)", True, False),
            ("ov_part3_wispr.png", "STEP 3: HUMAN VOICE APPROVAL & PROOF", "@maya_data approves via Wispr Flow -> @drift-sentry verifies 100,000 rows ($0.00 delta)", True, True),
        ]
        for fname, title, desc, is_purple, show_wispr in overlays:
            ov_page.evaluate(
                "(args) => window.configureOverlay(args.t, args.d, args.p, args.w)",
                {"t": title, "d": desc, "p": is_purple, "w": show_wispr},
            )
            ov_page.screenshot(path=str(OUT_DIR / fname), omit_background=True)
        ov_page.close()

        # 2. Render crisp PNG snapshots of each slide and encode directly to 60fps High-Bitrate MP4
        #    (Using direct 1920x1080 PNG-to-MP4 encoding gives 10x sharper text!)
        slide_page = browser.new_page(viewport={"width": 1920, "height": 1080})
        slide_page.goto(slides_html.as_uri())

        for key, (dur, html_body) in SLIDE_CONTENTS.items():
            slide_png = OUT_DIR / f"slide_{key}.png"
            out_mp4 = OUT_DIR / f"slide_{key}.mp4"
            slide_page.evaluate("(html) => window.showSlide(html)", html_body)
            slide_page.wait_for_timeout(120)
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
                + HIGH_QUALITY_VIDEO_FLAGS
                + ["-an", str(out_mp4)],
            )

        slide_page.close()
        browser.close()


def process_clip_with_top_header(
    ffmpeg_bin: str,
    src_mp4: Path,
    overlay_png: Path,
    out_mp4: Path,
    freeze_end_sec: float = 0.0,
    wispr_overlay_png: Path | None = None,
) -> None:
    """
    Uses Lanczos scaling into 1920x1024 at y=56 (leaving the bottom 100% uncovered)
    and encodes at 60fps High-Bitrate CRF 14 so fine SQL/code text stays crystal clear.
    """
    tpad = f",tpad=stop_mode=clone:stop_duration={freeze_end_sec}" if freeze_end_sec > 0 else ""
    base_chain = (
        f"[0:v]scale=1920:1024:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad=1920:1080:(ow-iw)/2:56+(1024-ih)/2:black,fps=60{tpad}[vid];"
    )

    if wispr_overlay_png is None:
        filter_complex = f"{base_chain}[vid][1:v]overlay=0:0,format=yuv420p[out]"
        inputs = ["-i", str(src_mp4), "-i", str(overlay_png)]
    else:
        filter_complex = (
            f"{base_chain}"
            f"[vid][1:v]overlay=0:0[tmp];"
            f"[tmp][2:v]overlay=0:0:enable='between(t,2.5,13.5)',format=yuv420p[out]"
        )
        inputs = ["-i", str(src_mp4), "-i", str(overlay_png), "-i", str(wispr_overlay_png)]

    run_ffmpeg(
        ffmpeg_bin,
        inputs
        + ["-filter_complex", filter_complex, "-map", "[out]"]
        + HIGH_QUALITY_VIDEO_FLAGS
        + ["-an", str(out_mp4)],
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg_bin = get_ffmpeg_bin()
    print(f"Using FFmpeg at: {ffmpeg_bin}", flush=True)

    clip1_src = find_clip(["clip1(final).mp4", "clip1.mp4"])
    clip2_src = find_clip(["clip2(final).mp4", "clip2.mp4"])
    clip3_src = find_clip(["clip3.mp4", "clip3(final).mp4"])

    slides_html = OUT_DIR / "slides.html"
    slides_html.write_text(SLIDES_HTML, encoding="utf-8")
    overlay_html = OUT_DIR / "overlays.html"
    overlay_html.write_text(OVERLAY_GEN_HTML, encoding="utf-8")

    print("[1/4] Rendering lossless PNG slides -> 60fps High-Bitrate Master slides...", flush=True)
    render_slides_and_overlays(ffmpeg_bin, slides_html, overlay_html)

    c1_out = OUT_DIR / "demo_clip1.mp4"
    c2_out = OUT_DIR / "demo_clip2.mp4"
    c3_out = OUT_DIR / "demo_clip3.mp4"

    print("[2/4] Encoding Clip 1 (Lanczos 1080p60 CRF 14 + 3s freeze on Red Dashboard)...", flush=True)
    process_clip_with_top_header(
        ffmpeg_bin, clip1_src, OUT_DIR / "ov_part1.png", c1_out, freeze_end_sec=3.0
    )

    print("[3/4] Encoding Clip 2 (Lanczos 1080p60 CRF 14 + @SchemaCourtBot diagnosis)...", flush=True)
    process_clip_with_top_header(
        ffmpeg_bin, clip2_src, OUT_DIR / "ov_part2.png", c2_out, freeze_end_sec=2.0
    )

    print("[4/4] Encoding Clip 3 (Lanczos 1080p60 CRF 14 + Wispr Flow approval + 4s Green freeze)...", flush=True)
    process_clip_with_top_header(
        ffmpeg_bin,
        clip3_src,
        OUT_DIR / "ov_part3_base.png",
        c3_out,
        freeze_end_sec=4.0,
        wispr_overlay_png=OUT_DIR / "ov_part3_wispr.png",
    )

    ordered_files = [
        OUT_DIR / "slide_intro_1_problem.mp4",
        OUT_DIR / "slide_intro_2_brag.mp4",
        OUT_DIR / "slide_card_step1.mp4",
        c1_out,
        OUT_DIR / "slide_card_step2.mp4",
        c2_out,
        OUT_DIR / "slide_card_step3.mp4",
        c3_out,
        OUT_DIR / "slide_outro_brag.mp4",
    ]

    concat_list = OUT_DIR / "concat_list.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in ordered_files),
        encoding="utf-8"
    )

    final_output = BASE_DIR / "SchemaCourt_Master_1080p60.mp4"
    final_output_videos = Path("C:/Users/mihee/Videos/Screen Recordings/SchemaCourt_Master_1080p60.mp4")

    print("Stitching final 1080p60 High-Bitrate Master MP4...", flush=True)
    run_ffmpeg(
        ffmpeg_bin,
        [
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(final_output),
        ],
    )
    shutil.copy2(final_output, final_output_videos)
    print(f"\nSUCCESS! High-Bitrate 1080p60 Master is ready:\n   1. {final_output}\n   2. {final_output_videos}", flush=True)


if __name__ == "__main__":
    main()
