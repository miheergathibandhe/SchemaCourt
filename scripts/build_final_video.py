#!/usr/bin/env python3
"""
scripts/build_final_video.py (Final Polished 60.00s Master)
Applies all 4 final polish items while keeping duration locked to 60.00 seconds:
1. Replaces the 4 truncated split-screen metric columns in Clip 3 with 2 full-width
   cards (Active Stream Model Output + Switch Room Approval), followed by a dedicated
   Full-Width Green Verification Dashboard shot (49-55s).
2. Tightens the Telegram evidence crop (y=402..1000) so zero empty dark space appears
   above the conversation and viewers immediately see: schema change, repair, and Maya's prompt.
3. Renders a large, single-line 2-row SQL Diff callout card beside the Telegram message:
   - gross_amount_cents - discount_cents
   + gross_amount_cents - COALESCE(discount_cents, promo_struct.discount_cents, 0)
4. Adds github.com/miheergathibandhe/SchemaCourt on the final 55-60s card.
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
    width: 1540px; padding: 68px 82px; border-radius: 24px;
    background: rgba(15, 23, 42, 0.94); border: 2px solid #1e293b;
    box-shadow: 0 25px 70px rgba(0,0,0,0.8);
  }
  .eyebrow {
    display: inline-block; padding: 8px 18px; border-radius: 999px;
    font-size: 17px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase;
    margin-bottom: 26px; background: #064e3b; color: #6ee7b7; border: 1px solid #10b981;
  }
  h1 { font-size: 74px; font-weight: 900; line-height: 1.08; margin-bottom: 24px; letter-spacing: -1.5px; color: #ffffff; }
  p.promise { font-size: 38px; font-weight: 600; color: #e2e8f0; line-height: 1.38; margin-bottom: 36px; }
  .sub-pill {
    display: inline-block; background: #090d16; border: 1px solid #334155;
    padding: 14px 24px; border-radius: 12px; font-size: 22px; color: #38bdf8; font-weight: 600;
  }
  .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; margin-top: 26px; }
  .card { background: #090d16; border: 1px solid #334155; border-radius: 16px; padding: 22px 24px; }
  .card-title { font-size: 18px; font-weight: 800; color: #38bdf8; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.6px; }
  .card-body { font-size: 20px; color: #e2e8f0; line-height: 1.4; }
  .code-pill {
    font-family: Consolas, monospace; background: #1e293b; color: #38bdf8;
    padding: 3px 10px; border-radius: 6px; font-size: 0.9em;
  }
  .repo-footer {
    margin-top: 28px; padding-top: 20px; border-top: 1px solid #1e293b;
    display: flex; align-items: center; justify-content: space-between;
  }
  .repo-link {
    font-family: Consolas, monospace; font-size: 24px; font-weight: 700;
    color: #f8fafc; background: #1e293b; border: 1px solid #3b82f6;
    padding: 10px 22px; border-radius: 10px;
  }
  .repo-tag { font-size: 18px; color: #94a3b8; font-weight: 600; }

  /* Full-width Green Verification Dashboard view (for 49-55s) */
  .dash-full {
    width: 1920px; height: 1080px; background: #0e1117; padding: 78px 88px 36px 88px;
    display: flex; flex-direction: column; justify-content: flex-start;
  }
  .dash-header { font-size: 30px; font-weight: 800; color: #fafafa; margin-bottom: 20px; display: flex; align-items: center; gap: 12px; }
  .banner-pass {
    background: #064e3b; border: 2px solid #10b981; border-radius: 12px;
    padding: 18px 26px; color: #ecfdf5; margin-bottom: 24px;
  }
  .banner-title { font-size: 25px; font-weight: 800; margin-bottom: 6px; }
  .banner-meta { font-size: 16.5px; opacity: 0.95; font-family: Consolas, monospace; }
  .metrics-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-bottom: 28px; padding-bottom: 24px; border-bottom: 1px solid #262730; }
  .m-card { background: #161b26; border: 1px solid #262f40; border-radius: 12px; padding: 16px 20px; }
  .m-label { font-size: 15px; color: #94a3b8; font-weight: 600; margin-bottom: 6px; }
  .m-val { font-size: 34px; font-weight: 800; color: #ffffff; margin-bottom: 8px; }
  .m-delta { display: inline-block; background: rgba(16, 185, 129, 0.18); color: #34d399; font-size: 14px; font-weight: 700; padding: 4px 10px; border-radius: 999px; }
  .dash-cols { display: grid; grid-template-columns: 1.25fr 1fr; gap: 32px; }
  .sec-title { font-size: 22px; font-weight: 700; color: #fafafa; margin-bottom: 14px; }
  table.tier-tbl { width: 100%; border-collapse: collapse; background: #161b26; border-radius: 10px; overflow: hidden; border: 1px solid #262f40; }
  table.tier-tbl th { background: #1e293b; color: #cbd5e1; font-size: 14.5px; text-align: left; padding: 12px 14px; font-weight: 700; }
  table.tier-tbl td { padding: 13px 14px; border-top: 1px solid #262f40; font-size: 15.5px; color: #f1f5f9; font-family: Consolas, monospace; }
  .sql-box {
    background: #161b26; border: 1px solid #262f40; border-radius: 10px;
    padding: 16px 20px; font-family: Consolas, monospace; font-size: 15px; line-height: 1.5; color: #e2e8f0;
  }
  .hl-coalesce { background: rgba(16, 185, 129, 0.22); color: #6ee7b7; padding: 2px 6px; border-radius: 4px; font-weight: 700; border: 1px solid #10b981; }
  .decision-pill {
    margin-top: 14px; background: rgba(6, 78, 59, 0.7); border: 1px solid #10b981;
    border-radius: 10px; padding: 13px 18px; color: #ecfdf5; font-size: 15.5px; line-height: 1.4;
  }
</style>
</head>
<body>
  <div id="stage"></div>
  <script>
    window.showSlide = function(htmlContent, isFullDash) {
      if (isFullDash) {
        document.getElementById('stage').innerHTML = htmlContent;
      } else {
        document.getElementById('stage').innerHTML = `<div class="slide">${htmlContent}</div>`;
      }
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
    display: flex; align-items: center; justify-content: space-between; padding: 0 28px; z-index: 10;
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

  /* Polish 3: Large, readable 2-line SQL Diff Card in Step 2 (17.5-31s) */
  .sql-diff-card {
    position: absolute; left: 930px; top: 380px; width: 955px;
    background: #090d16; border: 2px solid #38bdf8; border-radius: 14px;
    padding: 22px 24px; box-shadow: 0 20px 50px rgba(0,0,0,0.85);
    display: none; flex-direction: column; gap: 12px;
  }
  .diff-header {
    display: flex; align-items: center; justify-content: space-between;
    font-size: 16px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.8px;
  }
  .diff-file { font-family: Consolas, monospace; color: #f8fafc; background: #1e293b; padding: 3px 10px; border-radius: 6px; font-size: 15px; }
  .diff-line {
    font-family: Consolas, monospace; font-size: 18.5px; font-weight: 700;
    padding: 12px 14px; border-radius: 8px; white-space: nowrap;
  }
  .diff-del { background: rgba(127, 29, 29, 0.55); color: #fca5a5; border: 1px solid #ef4444; }
  .diff-add { background: rgba(6, 78, 59, 0.65); color: #6ee7b7; border: 1px solid #10b981; }
  .diff-note { font-size: 15.5px; color: #cbd5e1; line-height: 1.4; }

  /* Polish 1: 2 Full-Width Untruncated Metric Cards masking the squeezed 4-column row in Clip 3 */
  .split-metrics-mask {
    position: absolute; left: 685px; top: 322px; width: 1195px; height: 168px;
    background: #0e1117; padding: 6px 14px;
    display: none; grid-template-columns: 1fr 1fr; gap: 20px; align-items: center;
  }
  .sm-card {
    background: #161b26; border: 1px solid #2d3748; border-radius: 10px;
    padding: 14px 20px; height: 146px; display: flex; flex-direction: column; justify-content: center;
  }
  .sm-card.fail { border-color: #f87171; }
  .sm-card.pass { border-color: #10b981; }
  .sm-label { font-size: 15px; color: #94a3b8; font-weight: 600; margin-bottom: 6px; }
  .sm-val { font-size: 34px; font-weight: 800; color: #ffffff; margin-bottom: 8px; }
  .sm-badge { display: inline-block; font-size: 13.5px; font-weight: 700; padding: 4px 10px; border-radius: 999px; width: fit-content; }
  .sm-badge.red { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }
  .sm-badge.amber { background: rgba(245, 158, 11, 0.2); color: #fcd34d; }
  .sm-badge.green { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }

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

  <!-- Zoomed 2-Line SQL Diff Card for Step 2 -->
  <div class="sql-diff-card" id="sql-diff-card">
    <div class="diff-header">
      <span>🔍 Proposed Backward-Compatible Repair</span>
      <span class="diff-file">models/fct_revenue.sql</span>
    </div>
    <div class="diff-line diff-del">- gross_amount_cents - discount_cents</div>
    <div class="diff-line diff-add">+ gross_amount_cents - COALESCE(discount_cents, promo_struct.discount_cents, 0)</div>
    <div class="diff-note">
      ✅ Preserves Legacy <b>v2.8</b> scalar values &amp; falls back cleanly to nested <b>v3.0</b> struct—awaiting <b>@maya_data</b> approval.
    </div>
  </div>

  <!-- 2 Full-Width Untruncated Cards for Split-Screen Step 3 & Step 4a -->
  <div class="split-metrics-mask" id="split-metrics"></div>

  <div class="wispr-callout" id="wispr-box">
    <div style="font-size: 26px;">👈 🎙️</div>
    <div>
      <div class="wispr-title">HUMAN APPROVAL VIA WISPR FLOW VOICE</div>
      <div class="wispr-sub">AI proposes evidence; @maya_data controls the decision by voice</div>
    </div>
  </div>

  <script>
    window.configureOverlay = function(cfg) {
      const pill = document.getElementById('pill');
      pill.textContent = cfg.title;
      pill.className = 'part-pill ' + (cfg.color || '');
      document.getElementById('desc').textContent = cfg.desc;
      document.getElementById('wispr-box').style.display = cfg.showWispr ? 'flex' : 'none';
      document.getElementById('sql-diff-card').style.display = cfg.showSqlDiff ? 'flex' : 'none';

      const sm = document.getElementById('split-metrics');
      if (cfg.splitMode === 'failing') {
        sm.style.display = 'grid';
        sm.innerHTML = `
          <div class="sm-card fail">
            <div class="sm-label">Active Stream Model Output</div>
            <div class="sm-val">NULL (Failing)</div>
            <span class="sm-badge red">↓ -$17,200,000.00 unverified vs. baseline</span>
          </div>
          <div class="sm-card fail">
            <div class="sm-label">Switch Room Approval</div>
            <div class="sm-val">Pending Review</div>
            <span class="sm-badge amber">⏳ Awaiting @maya_data sign-off</span>
          </div>
        `;
      } else if (cfg.splitMode === 'verified') {
        sm.style.display = 'grid';
        sm.innerHTML = `
          <div class="sm-card pass">
            <div class="sm-label">Active Stream Model Output</div>
            <div class="sm-val">$17,200,000.00</div>
            <span class="sm-badge green">↑ $0.00 delta vs. simulated baseline</span>
          </div>
          <div class="sm-card pass">
            <div class="sm-label">Switch Room Approval</div>
            <div class="sm-val">Approved (@maya_data)</div>
            <span class="sm-badge green">✅ Dual-contract verified (100,000 rows)</span>
          </div>
        `;
      } else {
        sm.style.display = 'none';
      }
    };
  </script>
</body>
</html>
"""

SLIDE_CONTENTS = {
    "intro_hook": (
        4.0,
        False,
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
    "full_green_dash": (
        6.0,
        True,
        """
        <div class="dash-full">
          <div class="dash-header">📋 SchemaCourt — Data Contract Change Review</div>
          <div class="banner-pass">
            <div class="banner-title">✅ DUAL-CONTRACT VERIFIED (LEGACY v2.8 + DRIFTED v3.0)</div>
            <div class="banner-meta">
              Producer: checkout-service@v3.0.0-stripe (e89b44d) &nbsp;|&nbsp; Rows Verified: 100,000 Legacy + 100,000 Drifted &nbsp;|&nbsp; Measured Delta: $0.00 &nbsp;|&nbsp; Check Time: 18.4 ms
            </div>
          </div>
          <div class="metrics-row">
            <div class="m-card">
              <div class="m-label">Simulated Baseline Revenue</div>
              <div class="m-val">$17,200,000.00</div>
              <span class="m-delta">↑ 100,000 fixture rows</span>
            </div>
            <div class="m-card">
              <div class="m-label">Active Stream Model Output</div>
              <div class="m-val">$17,200,000.00</div>
              <span class="m-delta">↑ $0.00 delta vs. baseline</span>
            </div>
            <div class="m-card">
              <div class="m-label">Dual-Fixture Coverage</div>
              <div class="m-val">100k / 100k Rows</div>
              <span class="m-delta">↑ Legacy v2.8 + Drifted v3.0</span>
            </div>
            <div class="m-card">
              <div class="m-label">Switch Room Approval</div>
              <div class="m-val">Approved (@maya_data)</div>
              <span class="m-delta">↑ Commit e89b44d verified</span>
            </div>
          </div>
          <div class="dash-cols">
            <div>
              <div class="sec-title">Per-Tier Contract Verification (Legacy &amp; Drifted Fixtures)</div>
              <table class="tier-tbl">
                <thead>
                  <tr>
                    <th>Product Tier</th>
                    <th>Rows (Base / Active)</th>
                    <th>Baseline Net ($)</th>
                    <th>Legacy Fixture ($)</th>
                    <th>Drifted Fixture ($)</th>
                    <th>Delta ($)</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><b>Enterprise</b></td>
                    <td>20,000 / 20,000</td>
                    <td>$9,680,000.00</td>
                    <td>$9,680,000.00</td>
                    <td>$9,680,000.00</td>
                    <td>$0.00</td>
                    <td style="color:#34d399;font-weight:800;">✅ PASS</td>
                  </tr>
                  <tr>
                    <td><b>Growth</b></td>
                    <td>40,000 / 40,000</td>
                    <td>$5,710,000.00</td>
                    <td>$5,710,000.00</td>
                    <td>$5,710,000.00</td>
                    <td>$0.00</td>
                    <td style="color:#34d399;font-weight:800;">✅ PASS</td>
                  </tr>
                  <tr>
                    <td><b>Starter</b></td>
                    <td>40,000 / 40,000</td>
                    <td>$1,810,000.00</td>
                    <td>$1,810,000.00</td>
                    <td>$1,810,000.00</td>
                    <td>$0.00</td>
                    <td style="color:#34d399;font-weight:800;">✅ PASS</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div>
              <div class="sec-title">Patched <code>models/fct_revenue.sql</code></div>
              <div class="sql-box">
                SELECT<br>
                &nbsp;&nbsp;product_tier,<br>
                &nbsp;&nbsp;COUNT(*) AS total_transactions,<br>
                &nbsp;&nbsp;ROUND(SUM(gross_amount_cents) / 100.0, 2) AS gross_revenue_usd,<br>
                &nbsp;&nbsp;ROUND(SUM(<span class="hl-coalesce">COALESCE(discount_cents, promo_struct.discount_cents, 0)</span>) / 100.0, 2) AS total_discounts_usd,<br>
                &nbsp;&nbsp;ROUND(SUM(gross_amount_cents - <span class="hl-coalesce">COALESCE(discount_cents, promo_struct.discount_cents, 0)</span>) / 100.0, 2) AS net_revenue_usd<br>
                FROM read_parquet('data/active_stream.parquet')<br>
                GROUP BY product_tier ORDER BY net_revenue_usd DESC;
              </div>
              <div class="decision-pill">
                <b>Recorded Decision:</b> Approved by <code>@maya_data</code> for <code>checkout-service@v3.0.0-stripe</code> (<code>e89b44d</code>). Verified <code>100,000</code> Legacy + <code>100,000</code> Drifted rows (<code>$0.00</code> delta).
              </div>
            </div>
          </div>
        </div>
        """
    ),
    "outro_summary": (
        5.0,
        False,
        """
        <span class="eyebrow">✅ VERIFIED ACROSS 100,000 LEGACY &amp; DRIFTED FIXTURE ROWS</span>
        <h1 style="font-size: 60px;">AI Investigates &amp; Proposes.<br>Humans Control the Decision.</h1>
        <p class="promise" style="font-size: 26px; margin-bottom: 20px;">
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
        <div class="repo-footer">
          <span class="repo-link">github.com/miheergathibandhe/SchemaCourt</span>
          <span class="repo-tag">Flip the Switch Hackathon • Switch AI + Wispr Flow</span>
        </div>
        """
    ),
}

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

        # 1. Render transparent PNG overlays
        ov_page = browser.new_page(viewport={"width": 1920, "height": 1080})
        ov_page.goto(overlay_html.as_uri())

        overlays = [
            {
                "fname": "ov_1a_baseline.png",
                "title": "1. SIMULATED BASELINE PASSING",
                "desc": "checkout-service v2.8 matches contract -> $17.2M simulated baseline verified across 100,000 rows",
                "color": "green", "showWispr": False, "showSqlDiff": False, "splitMode": "none"
            },
            {
                "fname": "ov_1b_failing.png",
                "title": "1. SCHEMA CHANGE -> CONTRACT FAILING",
                "desc": "checkout-service v3.0 moves discount_cents into promo_struct -> $17.2M metric evaluates to NULL",
                "color": "red", "showWispr": False, "showSqlDiff": False, "splitMode": "none"
            },
            {
                "fname": "ov_2a_prompt.png",
                "title": "2. EVIDENCE & PROPOSED REPAIR",
                "desc": "Producer asks @SchemaCourtBot to diagnose the v3.0 schema break in the Switch Room",
                "color": "", "showWispr": False, "showSqlDiff": False, "splitMode": "none"
            },
            {
                "fname": "ov_2b_diagnosis.png",
                "title": "2. EVIDENCE & PROPOSED REPAIR",
                "desc": "@SchemaCourtBot reports schema impact, proposes COALESCE(...) diff & waits for @maya_data",
                "color": "", "showWispr": False, "showSqlDiff": True, "splitMode": "none"
            },
            {
                "fname": "ov_3_approval_wispr.png",
                "title": "3. HUMAN APPROVAL (WISPR FLOW)",
                "desc": "@maya_data approves the proposed repair by voice before any SQL model change is applied",
                "color": "purple", "showWispr": True, "showSqlDiff": False, "splitMode": "failing"
            },
            {
                "fname": "ov_3_approval_sent.png",
                "title": "3. HUMAN APPROVAL (WISPR FLOW)",
                "desc": "@maya_data approval received -> @SchemaCourtBot applies patch & runs dual-fixture check",
                "color": "purple", "showWispr": False, "showSqlDiff": False, "splitMode": "failing"
            },
            {
                "fname": "ov_4_verified_split.png",
                "title": "4. DUAL-CONTRACT PROOF ($0.00 DELTA)",
                "desc": "Verified across 100,000 Legacy + 100,000 Drifted rows -> Dashboard flips GREEN & decision logged",
                "color": "green", "showWispr": False, "showSqlDiff": False, "splitMode": "verified"
            },
            {
                "fname": "ov_4_verified_full.png",
                "title": "4. DUAL-CONTRACT PROOF ($0.00 DELTA)",
                "desc": "Full-width verification result: 100,000 Legacy + 100,000 Drifted rows passing with $0.00 delta",
                "color": "green", "showWispr": False, "showSqlDiff": False, "splitMode": "none"
            },
        ]
        for cfg in overlays:
            ov_page.evaluate("(c) => window.configureOverlay(c)", cfg)
            ov_page.screenshot(path=str(OUT_DIR / cfg["fname"]), omit_background=True)
        ov_page.close()

        # 2. Render lossless PNG slides (Intro, Full-Width Green Dash, Outro)
        slide_page = browser.new_page(viewport={"width": 1920, "height": 1080})
        slide_page.goto(slides_html.as_uri())

        for key, (dur, is_full_dash, html_body) in SLIDE_CONTENTS.items():
            slide_png = OUT_DIR / f"slide_{key}.png"
            out_mp4 = OUT_DIR / f"seg_{key}.mp4"
            slide_page.evaluate(
                "(args) => window.showSlide(args.h, args.f)",
                {"h": html_body, "f": is_full_dash}
            )
            slide_page.wait_for_timeout(100)
            slide_page.screenshot(path=str(slide_png))

            if is_full_dash:
                # Composite the top step bar on top of the full-width green verification shot
                run_ffmpeg(
                    ffmpeg_bin,
                    [
                        "-loop", "1", "-framerate", "60", "-i", str(slide_png),
                        "-i", str(OUT_DIR / "ov_4_verified_full.png"),
                        "-filter_complex", "[0:v][1:v]overlay=0:0,fps=60,format=yuv420p[out]",
                        "-map", "[out]",
                        "-t", str(dur),
                    ]
                    + VIDEO_ENCODE_FLAGS
                    + ["-an", str(out_mp4)],
                )
            else:
                run_ffmpeg(
                    ffmpeg_bin,
                    [
                        "-loop", "1", "-framerate", "60", "-i", str(slide_png),
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
    align_left: bool = False,
) -> None:
    """
    Extracts `clip_play_sec` starting at `start_sec`, crops tightly around active content,
    and locks duration to `total_segment_sec`.
    """
    freeze_sec = max(0.0, round(total_segment_sec - clip_play_sec, 3))
    tpad = f",tpad=stop_mode=clone:stop_duration={freeze_sec + 0.5}" if freeze_sec > 0 else ""
    x_pad = "24" if align_left else "(ow-iw)/2"

    filter_complex = (
        f"[0:v]trim=start={start_sec}:duration={clip_play_sec},setpts=PTS-STARTPTS,"
        f"{crop_filter},"
        f"scale=1920:1024:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad=1920:1080:{x_pad}:56+(1024-ih)/2:#090d16,fps=60{tpad}[vid];"
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

    print("[1/9] Rendering cards, SQL diff callout, 2-card split overlay & full-width green dashboard...")
    render_slides_and_overlays(ffmpeg_bin, slides_html, overlay_html)

    # 04-09s (5.0s): Full-Width Green Baseline Dashboard
    print("[2/9] 04.0-09.0s (5.0s): Full-width Green Baseline Dashboard...")
    seg_1a = OUT_DIR / "seg_1a_baseline.mp4"
    build_locked_segment(
        ffmpeg_bin, clip1_src, OUT_DIR / "ov_1a_baseline.png", seg_1a,
        crop_filter="crop=1776:904:72:138",
        start_sec=2.2, clip_play_sec=5.0, total_segment_sec=5.0,
    )

    # 09-14s (5.0s): Full-Width Red Failing Dashboard (in-place flip)
    print("[3/9] 09.0-14.0s (5.0s): Full-width Red Failing Dashboard...")
    seg_1b = OUT_DIR / "seg_1b_failing.mp4"
    build_locked_segment(
        ffmpeg_bin, clip1_src, OUT_DIR / "ov_1b_failing.png", seg_1b,
        crop_filter="crop=1776:904:72:138",
        start_sec=13.8, clip_play_sec=1.2, total_segment_sec=5.0,
    )

    # 14.0-17.5s (3.5s): Tight zoom on Telegram prompt & @SchemaCourtBot trigger
    print("[4/9] 14.0-17.5s (3.5s): Tight zoom on Telegram prompt...")
    seg_2a = OUT_DIR / "seg_2a_prompt.mp4"
    build_locked_segment(
        ffmpeg_bin, clip2_src, OUT_DIR / "ov_2a_prompt.png", seg_2a,
        crop_filter="crop=1150:540:268:495",
        start_sec=2.2, clip_play_sec=3.5, total_segment_sec=3.5,
    )

    # 17.5-31.0s (13.5s): Tight crop on Bot Diagnosis + @maya_data prompt (y=402..1000 -> ZERO empty upper space!)
    #                     aligned left so the right-hand 2-line SQL Diff Card sits beside it with zero cutoff.
    print("[5/9] 17.5-31.0s (13.5s): Tight Telegram evidence crop + readable 2-line SQL Diff card...")
    seg_2b = OUT_DIR / "seg_2b_diagnosis.mp4"
    build_locked_segment(
        ffmpeg_bin, clip2_src, OUT_DIR / "ov_2b_diagnosis.png", seg_2b,
        crop_filter="crop=820:598:268:402",
        start_sec=14.8, clip_play_sec=3.2, total_segment_sec=13.5,
        align_left=True,
    )

    # 31.0-39.0s (8.0s): Split-screen Wispr Flow approval (with 2 full-width untruncated dashboard cards)
    print("[6/9] 31.0-39.0s (8.0s): @maya_data voice approval + untruncated 2-card dashboard view...")
    seg_3a = OUT_DIR / "seg_3a_wispr.mp4"
    build_locked_segment(
        ffmpeg_bin, clip3_src, OUT_DIR / "ov_3_approval_wispr.png", seg_3a,
        crop_filter="crop=1710:905:140:135",
        start_sec=3.8, clip_play_sec=8.0, total_segment_sec=8.0,
    )

    # 39.0-43.0s (4.0s): Approval sent & agent applying patch
    print("[7/9] 39.0-43.0s (4.0s): Approval sent & patch executing...")
    seg_3b = OUT_DIR / "seg_3b_apply.mp4"
    build_locked_segment(
        ffmpeg_bin, clip3_src, OUT_DIR / "ov_3_approval_sent.png", seg_3b,
        crop_filter="crop=1710:905:140:135",
        start_sec=18.8, clip_play_sec=4.0, total_segment_sec=4.0,
    )

    # 43.0-49.0s (6.0s): Split-screen live flip to Green + Telegram Verification & Decision Recorded
    print("[8/9] 43.0-49.0s (6.0s): Split-screen live recovery + Telegram Decision Recorded...")
    seg_4a = OUT_DIR / "seg_4a_verified_split.mp4"
    build_locked_segment(
        ffmpeg_bin, clip3_src, OUT_DIR / "ov_4_verified_split.png", seg_4a,
        crop_filter="crop=1710:905:140:135",
        start_sec=23.5, clip_play_sec=5.5, total_segment_sec=6.0,
    )

    # 49.0-55.0s (6.0s): Dedicated Full-Width Green Verification Dashboard Shot (seg_full_green_dash.mp4)
    print("[9/9] 49.0-55.0s (6.0s) Full-Width Green Dashboard + 55.0-60.0s (5.0s) Final Card with GitHub link...")

    ordered_files = [
        OUT_DIR / "seg_intro_hook.mp4",      # 00.0 - 04.0s (4.0s)
        seg_1a,                              # 04.0 - 09.0s (5.0s)
        seg_1b,                              # 09.0 - 14.0s (5.0s)
        seg_2a,                              # 14.0 - 17.5s (3.5s)
        seg_2b,                              # 17.5 - 31.0s (13.5s)
        seg_3a,                              # 31.0 - 39.0s (8.0s)
        seg_3b,                              # 39.0 - 43.0s (4.0s)
        seg_4a,                              # 43.0 - 49.0s (6.0s)
        OUT_DIR / "seg_full_green_dash.mp4", # 49.0 - 55.0s (6.0s)
        OUT_DIR / "seg_outro_summary.mp4",   # 55.0 - 60.0s (5.0s)
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
    print(f"\n🎉 FINAL POLISHED 60.00-SECOND MASTER READY ({size_mb} MB):\n   {final_output}")

    videos_dest = Path("C:/Users/mihee/Videos/Screen Recordings") / "SchemaCourt_Final_60s.mp4"
    try:
        shutil.copy2(final_output, videos_dest)
        print(f"   Mirrored to: {videos_dest}")
    except Exception as e:
        print(f"   Note: Could not mirror to Screen Recordings: {e}")


if __name__ == "__main__":
    main()
