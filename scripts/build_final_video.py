#!/usr/bin/env python3
"""
scripts/build_final_video.py
Fixes the bottom-banner overlap issue:
1. Places the PART 1 / 2 / 3 status bar in a dedicated 56px TOP header strip
   above the video canvas so 0 pixels of the bottom typing area or Wispr Flow pill are covered.
2. Adds a non-overlapping Wispr Flow spotlight callout in the empty dark space
   under the Streamlit table during Part 3 (t=2.5s to t=13.5s).
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
    width: 1560px; padding: 64px 72px; border-radius: 24px;
    background: rgba(15, 23, 42, 0.88); border: 2px solid #1e293b;
    box-shadow: 0 25px 70px rgba(0,0,0,0.65);
  }
  .eyebrow {
    display: inline-block; padding: 8px 18px; border-radius: 999px;
    font-size: 18px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;
    margin-bottom: 26px; background: #1e3a8a; color: #93c5fd; border: 1px solid #3b82f6;
  }
  .eyebrow.red { background: #7f1d1d; color: #fca5a5; border-color: #ef4444; }
  .eyebrow.green { background: #064e3b; color: #6ee7b7; border-color: #10b981; }
  .eyebrow.purple { background: #4c1d95; color: #ddd6fe; border-color: #8b5cf6; }
  h1 { font-size: 64px; font-weight: 900; line-height: 1.12; margin-bottom: 24px; letter-spacing: -1px; }
  p.lead { font-size: 30px; color: #cbd5e1; line-height: 1.45; margin-bottom: 36px; }
  .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-top: 20px; }
  .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 28px; }
  .card { background: #090d16; border: 1px solid #334155; border-radius: 16px; padding: 26px 28px; }
  .card-title { font-size: 22px; font-weight: 800; color: #38bdf8; margin-bottom: 10px; }
  .card-body { font-size: 21px; color: #e2e8f0; line-height: 1.4; }
  .stat-num { font-size: 46px; font-weight: 900; color: #10b981; margin-bottom: 6px; font-family: Consolas, monospace; }
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
    <div class="top-right">SchemaCourt • Switch AI + Claude Code + DuckDB + Wispr Flow</div>
  </div>
  <div class="wispr-callout" id="wispr-box">
    <div style="font-size: 26px;">👈 🎙️</div>
    <div>
      <div class="wispr-title">LIVE WISPR FLOW VOICE DICTATION</div>
      <div class="wispr-sub">Watch the bottom-center waveform &amp; bottom-left Telegram input bar</div>
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
        4.5,
        """
        <span class="eyebrow red">⚠️ THE SILENT PRODUCTION KILLER</span>
        <h1>Backend Ships <span class="code-pill">v3.0</span>. Tests Pass.<br>Downstream Revenue Quietly Breaks.</h1>
        <p class="lead">
          When <span class="code-pill">checkout-service</span> moves top-level <span class="code-pill">discount_cents</span>
          into <span class="code-pill">promo_struct.discount_cents</span>, the microservice build succeeds—while the
          Gold SQL model (<span class="code-pill">fct_revenue.sql</span>) evaluates to <b style="color:#f87171;">NULL</b> across 100,000 rows.
        </p>
        <div class="grid">
          <div class="card">
            <div class="card-title" style="color:#f87171;">❌ Why Standard Chatbots & CI Fail</div>
            <div class="card-body">CI alerts dump noisy red logs without a fix. Solo terminal agents only see one repo and cannot coordinate human sign-off.</div>
          </div>
          <div class="card">
            <div class="card-title" style="color:#34d399;">✅ What Teams Actually Need</div>
            <div class="card-body">An evidence-backed review room where Backend, Data Owner, and AI inspect impact, verify a compatible patch, and log approval.</div>
          </div>
        </div>
        """
    ),
    "intro_2_brag": (
        5.0,
        """
        <span class="eyebrow">⚖️ FLIP THE SWITCH HACKATHON</span>
        <h1>SchemaCourt — Change Review Room for Data Contracts</h1>
        <p class="lead">
          Bridging <span class="code-pill">@Claude Code</span> into Telegram via <b>Switch AI</b> to investigate schema drift,
          propose backward-compatible SQL, and verify parity before merge.
        </p>
        <div class="grid-4">
          <div class="card">
            <div class="stat-num">100,000</div>
            <div class="card-body">Parquet Fixture Rows Checked (Legacy + Drifted)</div>
          </div>
          <div class="card">
            <div class="stat-num">$17.2M</div>
            <div class="card-body">Baseline Contract Net Revenue Protected</div>
          </div>
          <div class="card">
            <div class="stat-num">&lt; 20ms</div>
            <div class="card-body">In-Memory DuckDB Dual-Contract Audit</div>
          </div>
          <div class="card">
            <div class="stat-num" style="color:#a78bfa;">Wispr</div>
            <div class="card-body">Live Voice Approval in Shared Chat</div>
          </div>
        </div>
        """
    ),
    "card_step1": (
        2.5,
        """
        <span class="eyebrow">PART 1 OF 3 • THE BREAKING PRODUCER CHANGE</span>
        <h1>Baseline Contract Passing ($17.2M) ➔ Schema Drift Simulated</h1>
        <p class="lead">
          Watch the live Streamlit Contract Monitor as <span class="code-pill">checkout-service@v3.0.0-stripe</span>
          deprecates <span class="code-pill">discount_cents</span> and breaks <span class="code-pill">models/fct_revenue.sql</span>.
        </p>
        """
    ),
    "card_step2": (
        2.5,
        """
        <span class="eyebrow">PART 2 OF 3 • EVIDENCE-BACKED INVESTIGATION IN SWITCH</span>
        <h1><span class="code-pill">@SchemaCourtBot</span> Separates Verified Facts from Proposals</h1>
        <p class="lead">
          Inside the Telegram Switch Room, Claude Code inspects the 100k-row Parquet stream, reports exact NULL counts,
          proposes a <span class="code-pill">COALESCE</span> patch, and pauses for <span class="code-pill">@maya_data</span> approval.
        </p>
        """
    ),
    "card_step3": (
        2.5,
        """
        <span class="eyebrow purple">PART 3 OF 3 • WISPR FLOW VOICE SIGN-OFF & DUAL VERIFICATION</span>
        <h1>Voice Approval ➔ Live SQL Patch ➔ $0.00 Delta Verified</h1>
        <p class="lead">
          Watch the bottom-center <b>Wispr Flow</b> dictation bar and bottom-left Telegram input as the Data Owner
          approves by voice—triggering dual-fixture DuckDB verification and flipping the dashboard <b style="color:#34d399;">GREEN</b>.
        </p>
        """
    ),
    "outro_brag": (
        4.5,
        """
        <span class="eyebrow green">✅ CONTRACT VERIFIED & RECORDED IN SWITCH</span>
        <h1>SchemaCourt: Zero Silent Data Outages.</h1>
        <p class="lead">
          <b>Detect ➔ Investigate ➔ Propose ➔ Human Voice Approval (Wispr Flow) ➔ Dual-Fixture Verify ➔ Record</b>
        </p>
        <div class="grid">
          <div class="card">
            <div class="card-title">🛠️ Built With</div>
            <div class="card-body">Switch AI • Claude Code • Telegram • Wispr Flow • DuckDB • PyArrow Parquet • Streamlit</div>
          </div>
          <div class="card">
            <div class="card-title" style="color:#34d399;">📊 Final Verification Result</div>
            <div class="card-body">100,000 Legacy Rows + 100,000 Drifted Rows = <b>$17,200,000.00 Net Revenue ($0.00 Variance)</b></div>
          </div>
        </div>
        """
    ),
}


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
            ("ov_part1.png", "PART 1: BREAKING CHANGE", "checkout-service v3.0 drops discount_cents -> $17.2M revenue evaluates to NULL", False, False),
            ("ov_part2.png", "PART 2: SWITCH AI INVESTIGATION", "@SchemaCourtBot (Claude Code) isolates drift, proposes COALESCE diff & awaits @maya_data", False, False),
            ("ov_part3_base.png", "PART 3: WISPR FLOW VOICE SIGN-OFF", "Data Owner approves via Wispr Flow voice dictation -> Dual-contract check -> GREEN", True, False),
            ("ov_part3_wispr.png", "PART 3: WISPR FLOW VOICE SIGN-OFF", "Data Owner approves via Wispr Flow voice dictation -> Dual-contract check -> GREEN", True, True),
        ]
        for fname, title, desc, is_purple, show_wispr in overlays:
            ov_page.evaluate(
                "(args) => window.configureOverlay(args.t, args.d, args.p, args.w)",
                {"t": title, "d": desc, "p": is_purple, "w": show_wispr},
            )
            ov_page.screenshot(path=str(OUT_DIR / fname), omit_background=True)
        ov_page.close()

        # 2. Render full-screen title slides
        for key, (dur, html_body) in SLIDE_CONTENTS.items():
            tmp_dir = OUT_DIR / f"_tmp_{key}"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=str(tmp_dir),
                record_video_size={"width": 1920, "height": 1080},
            )
            page = context.new_page()
            page.goto(slides_html.as_uri())
            page.evaluate("(html) => window.showSlide(html)", html_body)
            time.sleep(dur + 0.3)
            video = page.video
            context.close()
            raw_webm = Path(video.path())

            out_mp4 = OUT_DIR / f"slide_{key}.mp4"
            run_ffmpeg(
                ffmpeg_bin,
                [
                    "-i", str(raw_webm),
                    "-t", str(dur),
                    "-vf", "scale=1920:1080,fps=30,format=yuv420p",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                    "-an", str(out_mp4),
                ],
            )
            shutil.rmtree(tmp_dir, ignore_errors=True)

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
    Scales the source video into 1920x1024 positioned at y=56 (leaving the bottom 100% uncovered!)
    and composites the 56px top header PNG (plus the non-overlapping Wispr spotlight in Part 3).
    """
    tpad = f",tpad=stop_mode=clone:stop_duration={freeze_end_sec}" if freeze_end_sec > 0 else ""
    base_chain = (
        f"[0:v]scale=1920:1024:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:56+(1024-ih)/2:black,fps=30{tpad}[vid];"
    )

    if wispr_overlay_png is None:
        filter_complex = f"{base_chain}[vid][1:v]overlay=0:0,format=yuv420p[out]"
        inputs = ["-i", str(src_mp4), "-i", str(overlay_png)]
    else:
        # Show the Wispr spotlight callout in the empty space under the Streamlit table from t=2.5s to t=13.5s
        filter_complex = (
            f"{base_chain}"
            f"[vid][1:v]overlay=0:0[tmp];"
            f"[tmp][2:v]overlay=0:0:enable='between(t,2.5,13.5)',format=yuv420p[out]"
        )
        inputs = ["-i", str(src_mp4), "-i", str(overlay_png), "-i", str(wispr_overlay_png)]

    run_ffmpeg(
        ffmpeg_bin,
        inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an", str(out_mp4),
        ],
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

    print("[1/4] Rendering slides and non-overlapping top header overlays...", flush=True)
    render_slides_and_overlays(ffmpeg_bin, slides_html, overlay_html)

    c1_out = OUT_DIR / "demo_clip1.mp4"
    c2_out = OUT_DIR / "demo_clip2.mp4"
    c3_out = OUT_DIR / "demo_clip3.mp4"

    print("[2/4] Processing Clip 1 (Top header bar + 3s freeze on Red Dashboard)...", flush=True)
    process_clip_with_top_header(
        ffmpeg_bin, clip1_src, OUT_DIR / "ov_part1.png", c1_out, freeze_end_sec=3.0
    )

    print("[3/4] Processing Clip 2 (Top header bar + bottom typing bar 100% uncovered)...", flush=True)
    process_clip_with_top_header(
        ffmpeg_bin, clip2_src, OUT_DIR / "ov_part2.png", c2_out, freeze_end_sec=2.0
    )

    print("[4/4] Processing Clip 3 (Top header + Wispr Flow spotlight + 4s freeze on Green Dashboard)...", flush=True)
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

    final_output = BASE_DIR / "SchemaCourt_Final_Submission.mp4"
    final_output_videos = Path("C:/Users/mihee/Videos/Screen Recordings/SchemaCourt_Final_Submission.mp4")

    print("Stitching final 1080p MP4...", flush=True)
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
    print(f"\n🎉 FIXED! Bottom typing bar & Wispr Flow are now 100% visible:\n   1. {final_output}\n   2. {final_output_videos}", flush=True)


if __name__ == "__main__":
    main()
