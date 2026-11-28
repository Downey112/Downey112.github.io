#!/usr/bin/env python3
"""build_pixel.py — restyle Luqman Hakim's portfolio homepage as a mid-2000s
maximalist "pixel lobby" page.

Run from the repo root (the directory that contains classic/):

    python build_pixel.py

What it does
------------
1.  Reads  classic/index.html  (the real, minimalist homepage) with
    BeautifulSoup (html.parser).
2.  Extracts every piece of real content verbatim (str(tag) /
    decode_contents()): meta tags, hero, stats, project cards, more
    projects, skills / experience / education / certifications, footer.
3.  Rewrites  ../assets/  and  ../about/  paths for a root-level output.
4.  Writes a single self-contained  index.html  at the repo root in the
    retro pixel style (inline <style>, small inline <script>, Google
    Fonts link, no site.css), keeping the ids projects / more-projects /
    skills / experience / certifications / main so deep links survive.
5.  Prints a summary of what was extracted and fails loudly (exit code 1)
    if any count is zero or if the output still contains "../assets".

Dependencies: Python 3.13 stdlib + beautifulsoup4 4.15.

Conventions: any text this script builds itself is html-escaped (esc/escq);
fragments copied out of the source page are inserted as-is, so wording is
never rewritten.
"""

import html
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

SRC = Path("classic/index.html")
OUT = Path("index.html")

CLASSIC_URL = "classic/"
LINKEDIN_CERTS_URL = (
    "https://www.linkedin.com/in/luqmansyahrulnizam/details/certifications/"
)

FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Bungee&family=Chewy&'
    'family=Comic+Neue:ital,wght@0,400;0,700;1,400&family=Lilita+One&'
    'family=Pacifico&family=Pixelify+Sans:wght@400;700&family=Press+Start+2P&'
    'family=Saira+Stencil+One&family=Silkscreen:wght@400;700&family=VT323&'
    'display=swap" rel="stylesheet">'
)

# Pixel city skyline — original art adapted from the "Pixel Lobby Hotel"
# reference page (neon HOTEL sign changed to KL, marked decorative).
SKYLINE_SVG = (
    '<svg class="hdr-sky" viewBox="0 0 220 90" aria-hidden="true" focusable="false">\n'
    '<rect x="0" y="0" width="220" height="90" fill="#1b2a55"/>\n'
    '<rect x="12" y="12" width="2" height="2" fill="#fff"/><rect x="60" y="8" width="2" height="2" fill="#fff"/>\n'
    '<rect x="150" y="14" width="2" height="2" fill="#fff"/><rect x="188" y="20" width="2" height="2" fill="#fff"/>\n'
    '<circle cx="200" cy="14" r="7" fill="#fff7c0"/><rect x="194" y="16" width="4" height="4" fill="#1b2a55"/>\n'
    '<polygon points="2,88 2,50 12,50 12,38 22,38 22,88" fill="#5a8fd6"/>\n'
    '<rect x="6" y="56" width="4" height="4" fill="#fff8b0"/><rect x="14" y="56" width="4" height="4" fill="#fff8b0"/>\n'
    '<rect x="6" y="66" width="4" height="4" fill="#fff8b0"/><rect x="14" y="66" width="4" height="4" fill="#8fb6d6"/>\n'
    '<rect x="6" y="76" width="4" height="4" fill="#fff8b0"/>\n'
    '<polygon points="26,88 26,18 36,18 36,8 56,8 56,88" fill="#7aa7e0"/>\n'
    '<rect x="30" y="24" width="4" height="4" fill="#fff8b0"/><rect x="40" y="24" width="4" height="4" fill="#fff8b0"/>\n'
    '<rect x="48" y="24" width="4" height="4" fill="#fff8b0"/><rect x="30" y="36" width="4" height="4" fill="#8fb6d6"/>\n'
    '<rect x="40" y="36" width="4" height="4" fill="#fff8b0"/><rect x="48" y="36" width="4" height="4" fill="#fff8b0"/>\n'
    '<rect x="30" y="48" width="4" height="4" fill="#fff8b0"/><rect x="40" y="48" width="4" height="4" fill="#fff8b0"/>\n'
    '<rect x="30" y="60" width="4" height="4" fill="#fff8b0"/><rect x="48" y="60" width="4" height="4" fill="#fff8b0"/>\n'
    '<polygon points="60,88 60,58 70,58 70,44 90,44 90,88" fill="#6b9bd8"/>\n'
    '<rect x="64" y="64" width="4" height="4" fill="#fff8b0"/><rect x="76" y="64" width="4" height="4" fill="#8fb6d6"/>\n'
    '<rect x="64" y="74" width="4" height="4" fill="#fff8b0"/><rect x="76" y="74" width="4" height="4" fill="#fff8b0"/>\n'
    '<polygon points="94,88 94,24 104,24 104,14 124,14 124,88" fill="#8db4e8"/>\n'
    '<rect x="111" y="0" width="3" height="14" fill="#4a6a9a"/><circle cx="112.5" cy="1" r="2.5" fill="#ff5050"/>\n'
    '<rect x="106" y="30" width="16" height="10" fill="#14143c"/>\n'
    '<text x="114" y="38" text-anchor="middle" font-family="Silkscreen, monospace" font-size="6" fill="#ffd23f">KL</text>\n'
    '<rect x="98" y="44" width="4" height="4" fill="#fff8b0"/><rect x="110" y="44" width="4" height="4" fill="#fff8b0"/>\n'
    '<rect x="98" y="56" width="4" height="4" fill="#fff8b0"/><rect x="116" y="56" width="4" height="4" fill="#8fb6d6"/>\n'
    '<polygon points="128,88 128,52 138,52 138,34 158,34 158,88" fill="#6b9bd8"/>\n'
    '<rect x="132" y="58" width="4" height="4" fill="#fff8b0"/><rect x="144" y="58" width="4" height="4" fill="#fff8b0"/>\n'
    '<rect x="132" y="68" width="4" height="4" fill="#fff8b0"/><rect x="144" y="68" width="4" height="4" fill="#fff8b0"/>\n'
    '<polygon points="162,88 162,28 172,28 172,48 192,48 192,88" fill="#7aa7e0"/>\n'
    '<rect x="166" y="54" width="4" height="4" fill="#fff8b0"/><rect x="178" y="54" width="4" height="4" fill="#fff8b0"/>\n'
    '<rect x="166" y="66" width="4" height="4" fill="#8fb6d6"/><rect x="178" y="66" width="4" height="4" fill="#fff8b0"/>\n'
    '<polygon points="196,88 196,40 204,40 204,30 216,30 216,88" fill="#5a8fd6"/>\n'
    '<rect x="199" y="46" width="4" height="4" fill="#fff8b0"/><rect x="208" y="46" width="4" height="4" fill="#fff8b0"/>\n'
    '<rect x="63" y="40" width="10" height="6" fill="#ffd23f"/><rect x="71" y="35" width="6" height="6" fill="#ffd23f"/>\n'
    '<rect x="77" y="37" width="3" height="3" fill="#ff8c00"/><rect x="72" y="36" width="2" height="2" fill="#222"/>\n'
    '<rect x="0" y="88" width="220" height="2" fill="#0d1c30"/>\n'
    '</svg>'
)

SCRIPT = """<script>
(function () {
  'use strict';
  /* The only dynamic bit: a periodic wiggle on the (constant, real)
     "Projects shipped" counter. No fake numbers are ever generated. */
  var el = document.getElementById('shipped');
  if (!el) { return; }
  var box = el.parentElement;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { return; }
  setInterval(function () {
    box.classList.add('wig');
    setTimeout(function () { box.classList.remove('wig'); }, 330);
  }, 4200);
})();
</script>"""

CSS = r"""/* ==== LUQMAN HAKIM — pixel portfolio, mid-2000s maximalist skin ==== */
*{box-sizing:border-box}
html,body{min-height:100%;margin:0;min-width:1000px;
  font:12px/1.5 Verdana,Tahoma,Geneva,sans-serif;color:#222;background-color:#9ec3e8;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16'%3E%3Cpath d='M8 1L15 4.5 8 8 1 4.5Z' fill='%23dff0ff' stroke='%238fb6d6' stroke-width='1'/%3E%3Cpath d='M1 4.5L8 8 8 15 1 11.5Z' fill='%23bcd7ef' stroke='%238fb6d6' stroke-width='1'/%3E%3Cpath d='M15 4.5L8 8 8 15 15 11.5Z' fill='%23a9cdec' stroke='%238fb6d6' stroke-width='1'/%3E%3C/svg%3E")}
a{color:#0b4fa8}
a:focus-visible,button:focus-visible,[tabindex]:focus-visible{outline:2px dashed #d81e3f;outline-offset:2px}
.page{width:960px;margin:14px auto 30px;position:relative}
.skip-link{position:absolute;left:-999px;top:0;z-index:99;background:#ffd23f;color:#5a3200;padding:6px 10px;
  font-family:'Silkscreen',monospace;font-size:10px;text-decoration:none;border:2px solid #5a3200}
.skip-link:focus{left:8px;top:8px}

/* ---------- ticker ---------- */
.ticker{background:#101323;border:2px solid #454f6e;border-radius:4px;color:#ffe14d;
  font-family:'VT323',monospace;font-size:17px;letter-spacing:1px;padding:3px 6px;margin-bottom:8px}

/* ---------- header ---------- */
.hdr{position:relative;margin:0 0 10px;padding:16px 18px 12px;
  background:linear-gradient(#eaf5ff 0%,#c8e2f7 55%,#a9cdec 100%);
  border:3px solid #2e4a6e;border-radius:10px;box-shadow:4px 4px 0 rgba(0,0,0,.25)}
.hdr-left{width:430px}
.logo{margin:0;font-family:'Bungee',cursive;font-size:29px;line-height:1.1;
  color:#ff4d6d;text-shadow:3px 3px 0 #7a1f33,6px 6px 0 rgba(0,0,0,.22);letter-spacing:1px}
.logo .t1{color:#ffd23f}.logo .t2{color:#54d1c8}.logo .t3{color:#ff8fb1}
.tagline{font-family:'Chewy',cursive;font-size:18px;color:#2e4a6e;margin:6px 0 10px}
.counter{display:inline-block;font-family:'Press Start 2P',monospace;font-size:10px;
  background:#101323;color:#7cfc9a;border:2px inset #666;padding:7px 10px;border-radius:3px}
.counter.wig{animation:wig .32s ease}
@keyframes wig{25%{transform:rotate(-2.5deg) scale(1.06)}75%{transform:rotate(2deg) scale(1.02)}}
.hdr-sky{position:absolute;right:14px;top:10px;width:330px;filter:drop-shadow(2px 2px 0 rgba(0,0,0,.2))}
.hdr-note{margin:8px 0 0;font-family:'Comic Neue',cursive;font-size:12px;color:#5c3b1e;font-style:italic}

/* ---------- nav tabs ---------- */
.nav{list-style:none;display:flex;gap:5px;margin:0;padding:0 4px;flex-wrap:wrap}
.nav a{display:block;padding:8px 18px;text-decoration:none;color:#0d2a4a;
  font-family:'Silkscreen',monospace;font-size:11px;
  background:linear-gradient(#a5d3f5 0%,#5f9bd0 100%);border:2px outset #7ab5e8;
  border-radius:7px 7px 0 0;text-shadow:1px 1px 0 #dcefff}
.nav a:hover{background:linear-gradient(#c9e6ff 0%,#7fb3e0 100%)}
.nav .on a{background:linear-gradient(#ffe28a 0%,#ffab3d 100%);border-color:#ffd23f;color:#5a3200}
.nav li:nth-child(2){transform:rotate(-1.5deg)}
.nav li:nth-child(4){transform:rotate(1.8deg) translateY(2px)}
.nav li:nth-child(6){transform:rotate(-1deg) translateY(-1px)}

/* ---------- cert banner "ad" strip ---------- */
.adstrip{position:relative;min-height:96px;margin:12px 0;display:flex;align-items:center;gap:18px;
  padding:12px 20px 12px 84px;
  background:repeating-linear-gradient(45deg,#141b33 0 18px,#1b2447 18px 36px);
  border:3px ridge #ffd23f;border-radius:6px;overflow:hidden;transform:rotate(-.6deg)}
.adstrip .adtag{position:absolute;left:0;top:0;background:#ffd23f;color:#5a3200;
  font-family:'Silkscreen',monospace;font-size:8px;padding:3px 6px;
  border-right:2px solid #5a3200;border-bottom:2px solid #5a3200}
.adbig{font-family:'Bungee',cursive;font-size:17px;line-height:1.3;color:#ffd23f;
  text-shadow:3px 3px 0 #a10f2b;max-width:500px}
.adbig .blink{color:#ff5252;animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:.15}}
.adsmall{font-family:'Pacifico',cursive;font-size:14px;color:#9fd0ff}
.adcta{margin-left:auto;font-family:'Lilita One',cursive;font-size:16px;color:#fff;white-space:nowrap;
  background:linear-gradient(#7ce07c,#2f9e2f);border:3px outset #63c563;padding:9px 16px;
  border-radius:8px;text-decoration:none;text-shadow:1px 1px 0 #145214}
.adcta:hover{filter:brightness(1.08)}

/* ---------- full-width project hall ---------- */
.hall{display:grid;grid-template-columns:1fr 1fr;gap:18px 16px;align-items:start;margin-top:6px}
.hall>*{margin-bottom:0!important;width:auto!important;margin-left:0!important;margin-right:0!important}
.hall>*:nth-child(4n+2){margin-top:22px!important}
.hall>*:nth-child(4n+3){margin-top:-10px!important}
.morehall{margin-top:22px;transform:rotate(-.4deg)}
.moregrid{display:grid;grid-template-columns:repeat(3,1fr);gap:4px 18px;align-items:start}
/* ---------- 3-column layout ---------- */
.layout{display:flex;gap:14px;align-items:flex-start;margin-top:4px;position:relative}
.colL{width:172px;flex:none;margin-top:18px}
.colC{flex:1;min-width:0}
.colR{width:216px;flex:none;margin-top:-6px}

.box{background:#fff;border:2px solid #2e4a6e;border-radius:7px;
  box-shadow:3px 3px 0 rgba(0,0,0,.28);margin-bottom:16px;overflow:hidden}
.box>h3,.box>h2{margin:0;padding:6px 10px;font-weight:400;font-size:15px;color:#fff;
  border-bottom:2px solid rgba(0,0,0,.35);text-shadow:1px 1px 0 rgba(0,0,0,.45)}
.box .bd{padding:9px 10px}

.h-news>h3,.h-news>h2{font-family:'Chewy',cursive;background:linear-gradient(#7ab5e8,#3d6da0)}
.h-room>h3,.h-room>h2{font-family:'Bungee',cursive;font-size:12px;background:linear-gradient(#ff9d6b,#d84f1f)}
.h-lb>h3,.h-lb>h2{font-family:'Press Start 2P',monospace;font-size:10px;background:linear-gradient(#8e6fd8,#5a3fa0)}
.h-shout>h3,.h-shout>h2{font-family:'Lilita One',cursive;background:linear-gradient(#6fcf97,#2b8a55)}
.h-poll>h3,.h-poll>h2{font-family:'Saira Stencil One',sans-serif;letter-spacing:1px;background:linear-gradient(#f2a63c,#b56a10)}
.h-picks>h3,.h-picks>h2{font-family:'Pixelify Sans',cursive;background:linear-gradient(#ef7fae,#b03a72)}
.h-status>h3,.h-status>h2{font-family:'VT323',monospace;font-size:19px;background:linear-gradient(#5f9bd0,#2e4a6e)}
.h-hot>h3,.h-hot>h2{font-family:'Silkscreen',monospace;font-size:11px;background:linear-gradient(#ff8fb1,#c22553)}
.h-pals>h3,.h-pals>h2{font-family:'Chewy',cursive;background:linear-gradient(#54d1c8,#1f8a82)}
.h-link>h3,.h-link>h2{font-family:'Saira Stencil One',sans-serif;background:linear-gradient(#9fd0ff,#3d6da0)}

/* scatter / rotations / staggered offsets */
.rA{transform:rotate(-1.1deg)}
.rB{transform:rotate(1.3deg)}
.rC{transform:rotate(-2.1deg)}
.rD{transform:rotate(2.3deg)}
.rE{transform:rotate(.7deg) translateX(-8px)}
.pr1{transform:rotate(-1.2deg)}
.pr2{transform:rotate(1.5deg)}
.pr3{transform:rotate(-.9deg) translateX(-6px)}
.pr4{transform:rotate(1.1deg) translateX(6px)}
.pr5{transform:rotate(-1.4deg)}
.offL{width:88%;margin-left:auto}
.push{margin-left:14px}

/* ---------- stickers / badges ---------- */
.badgenew{position:absolute;top:-26px;left:-30px;width:56px;height:56px;display:flex;
  align-items:center;justify-content:center;text-align:center;border-radius:50%;
  background:#ff3b30;color:#fff;border:2px dashed #fff;font-family:'Press Start 2P',monospace;
  font-size:8px;line-height:1.3;transform:rotate(-14deg);box-shadow:2px 3px 0 rgba(0,0,0,.3);z-index:5;padding:4px}
.hotstar{position:absolute;top:-20px;right:-8px;width:74px;height:74px;display:flex;align-items:center;
  justify-content:center;text-align:center;background:#ffd23f;color:#7a1f33;
  font-family:'Press Start 2P',monospace;font-size:7px;line-height:1.4;transform:rotate(11deg);
  clip-path:polygon(50% 0,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);
  z-index:5;padding:6px;filter:drop-shadow(2px 2px 0 rgba(0,0,0,.25))}
.hotstar span{transform:rotate(-8deg);display:block}
.credstick{position:absolute;right:-24px;top:96px;z-index:6;transform:rotate(-9deg);
  font-family:'Pacifico',cursive;font-size:16px;color:#7a1f33;background:#ffd23f;
  border:2px solid #b8860b;border-radius:12px;padding:5px 12px;box-shadow:2px 3px 0 rgba(0,0,0,.3)}
.flt{position:absolute;z-index:7;pointer-events:none;box-shadow:2px 3px 0 rgba(0,0,0,.3)}
.flt.wow{left:-46px;top:560px;transform:rotate(-16deg);background:#54d1c8;color:#0d2a4a;
  font-family:'Bungee',cursive;font-size:14px;padding:6px 10px;border:2px solid #0d2a4a;border-radius:4px}
.flt.tape{left:470px;top:-8px;width:90px;height:22px;background:rgba(255,240,160,.8);transform:rotate(4deg);box-shadow:none}
.flt.rad{right:-58px;top:880px;transform:rotate(12deg);background:#fff;color:#c22553;
  font-family:'Pacifico',cursive;font-size:15px;padding:4px 12px;border:2px dashed #c22553;border-radius:20px}
.flt.pix{right:-52px;top:1450px;transform:rotate(-8deg);background:#101323;color:#ffd23f;
  font-family:'Press Start 2P',monospace;font-size:8px;padding:8px;border:2px solid #ffd23f}

/* ---------- enter box ---------- */
.enter{padding:14px 10px 16px;text-align:center;border:3px double #b8860b;border-radius:9px;
  background:
    radial-gradient(circle at 30% 20%,rgba(255,255,255,.9),rgba(255,255,255,0) 60%),
    repeating-linear-gradient(90deg,#fff9d6 0 14px,#ffef9c 14px 28px);
  box-shadow:3px 3px 0 rgba(0,0,0,.28);margin-bottom:16px}
.enter h2{margin:0 0 10px;font-family:'Saira Stencil One',sans-serif;font-size:19px;color:#7a1f33;letter-spacing:2px}
.bigbtn{display:inline-block;font-family:'Bungee',cursive;font-size:23px;color:#fff;
  background:linear-gradient(#ffc36b 0%,#ff5e3a 45%,#e8321f 100%);
  border:3px outset #ff9d2e;border-radius:14px;padding:13px 34px 11px;
  text-shadow:2px 2px 0 #7a1f1f;text-decoration:none;
  box-shadow:0 6px 0 #a32414,0 11px 16px rgba(0,0,0,.35)}
.bigbtn:hover{filter:brightness(1.08)}
.bigbtn:active{transform:translateY(4px);box-shadow:0 2px 0 #a32414}
.enter .fine{font-size:10px;color:#7a5a1f;margin-top:8px}

/* ---------- section header bars ---------- */
.sechdr{margin:0 0 14px;font-family:'Saira Stencil One',sans-serif;font-size:16px;letter-spacing:1px;color:#fff;
  background:linear-gradient(#f2a63c,#b56a10);border:2px solid #7a4a00;border-radius:7px;padding:8px 13px;
  text-shadow:1px 1px 0 rgba(0,0,0,.4);box-shadow:3px 3px 0 rgba(0,0,0,.28);transform:rotate(-.5deg)}
.colR .sechdr{font-size:13px}

/* ---------- project boxes ---------- */
.proj{margin-bottom:20px}
.proj>h3{padding:8px 12px}
.pmeta{display:block;font-family:'Silkscreen',monospace;font-size:7px;letter-spacing:1px;margin-bottom:3px}
.ptitle{display:block}
.pstat{display:inline-block;font-family:'VT323',monospace;font-size:14px;background:rgba(0,0,0,.4);
  border:1px solid rgba(255,255,255,.4);padding:0 7px;border-radius:4px;margin-top:4px}
.flag{display:inline-block;font-family:'Press Start 2P',monospace;font-size:7px;background:#ffd23f;color:#5a3200;
  border:1px dashed #b8860b;padding:2px 5px;margin-right:5px;vertical-align:middle}
.project-desc{font-size:11px}
.project-desc ul{margin:4px 0 8px;padding-left:17px;list-style:square}
.project-desc li{margin-bottom:5px}
.project-desc code{font-family:'Courier New',monospace;background:#eaf5ff;border:1px solid #bcd7ef;padding:0 3px}
.project-shots{display:flex;gap:10px;overflow-x:auto;padding:9px 6px;margin:6px 0 10px;
  background:#eaf5ff;border:2px inset #9ec3e8}
.project-shots figure{margin:0;flex:none;max-width:235px}
.project-shots img{height:150px;width:auto;display:block;border:2px solid #2e4a6e;border-radius:3px;background:#fff}
.project-shots figcaption{font-family:'VT323',monospace;font-size:13px;color:#b56a10;margin-top:2px}

/* tech tags as tilted mini badges (cycled colours) */
.tech-pill{display:inline-block;margin:2px 3px 2px 0;padding:2px 6px;border-radius:8px;
  font-family:'Press Start 2P',monospace;font-size:6px;color:#fff;background:#c22553;
  border:1px dashed rgba(255,255,255,.6);transform:rotate(-3deg)}
.tech-pill:nth-of-type(3n+1){background:#2b8a55;transform:rotate(2deg)}
.tech-pill:nth-of-type(3n){background:#3d6da0;transform:rotate(-1deg)}

/* project links as chunky 3D buttons */
.project-link{display:inline-block;margin:4px 6px 2px 0;padding:5px 12px;text-decoration:none;
  font-family:'Lilita One',cursive;font-size:13px;color:#fff;
  background:linear-gradient(#7ce07c,#2f9e2f);border:3px outset #63c563;border-radius:8px;
  text-shadow:1px 1px 0 #145214;box-shadow:0 4px 0 #1c6b1c}
.project-link:hover{filter:brightness(1.08)}
.project-link:active{transform:translateY(3px);box-shadow:0 1px 0 #1c6b1c}
.project-footer{display:flex;flex-wrap:wrap;gap:6px;align-items:center;justify-content:space-between;
  border-top:2px dashed #b9cfe6;padding-top:7px;margin-top:4px}
.project-footer>span{font-family:'Silkscreen',monospace;font-size:8px;background:#fff;
  border:1px solid #9ec3e8;border-radius:6px;padding:2px 7px;color:#2e4a6e}

/* ---------- left column: about / stats / contact / certs ---------- */
.aboutme{font-size:10.5px}
.hero-actions{margin-top:9px;display:flex;flex-direction:column;gap:7px}
.hero-actions .btn-primary{display:block;text-align:center;text-decoration:none;
  font-family:'Lilita One',cursive;font-size:12px;color:#fff;
  background:linear-gradient(#ffc36b,#ff5e3a);border:3px outset #ff9d2e;border-radius:9px;padding:8px 10px;
  text-shadow:1px 1px 0 #7a1f1f;box-shadow:0 4px 0 #a32414}
.hero-actions .btn-primary:hover{filter:brightness(1.08)}
.hero-actions .btn-primary:active{transform:translateY(3px);box-shadow:0 1px 0 #a32414}
.hero-actions .link-secondary{display:block;text-align:center;font-family:'Silkscreen',monospace;font-size:9px}

.stats-list{margin:0}
.stats-list .stat{padding:6px 0;border-bottom:1px dashed #b9cfe6}
.stats-list .stat:last-child{border-bottom:0}
.stats-list dt{font-family:'Chewy',cursive;font-size:13px;color:#2e4a6e}
.stats-list .stat-value{margin:0;font-family:'VT323',monospace;font-size:20px;color:#2b8a55}
.stats-list .stat-sub{margin:0;font-size:9px;color:#667}

.contact-list{margin:0;padding:0;list-style:none}
.contact-list li{overflow-wrap:anywhere;padding:4px 2px;border-bottom:1px dotted #bfe0cd;list-style:none}
.contact-list li:last-child{border-bottom:0}

.cert-exam{font-family:'VT323',monospace;font-size:14px;line-height:1.35;background:#101323;color:#7cfc9a;
  border:2px inset #555;padding:7px 9px;margin:0 0 9px}
.cert-exam span{display:block;color:#ffd23f;letter-spacing:1px}
.cert-list{margin:0}
.cert-list dt{font-family:'Chewy',cursive;font-size:12px;color:#5a3fa0;margin-top:7px;padding:1px 3px}
.cert-list dd{margin:0 0 3px;font-size:10px;color:#333;padding:0 3px}
.cert-list dt.isnew,.cert-list dd.isnew{background:#fff3b0;border:1px dashed #b8860b;border-radius:4px}
.newbadge{display:inline-block;font-family:'Press Start 2P',monospace;font-size:7px;color:#fff;background:#ff3b30;
  border:1px dashed #fff;border-radius:4px;padding:2px 5px;margin-left:4px;vertical-align:middle;
  animation:blink .9s steps(1) infinite}

/* ---------- right column: skills / experience / education ---------- */
.skill-row{padding:6px 0;border-bottom:1px dashed #cbb8ec}
.skill-row:last-child{border-bottom:0}
.skill-cat{font-family:'Chewy',cursive;font-size:13px;color:#8c2a56;margin-bottom:3px}

.timeline-list{margin:0}
.timeline-item{padding:7px 0;border-bottom:1px dashed #b9cfe6}
.timeline-item:last-child{border-bottom:0}
.timeline-head{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px;
  font-family:'Pixelify Sans',cursive;font-size:11px;font-weight:700;color:#0d2a4a}
.timeline-date{font-family:'VT323',monospace;font-size:14px;color:#b56a10;white-space:nowrap}
.timeline-sub{margin:3px 0 0;font-size:10px;color:#444}

/* ---------- more projects (compact list) ---------- */
.mini-card{padding:7px 0;border-bottom:1px dashed #ffd1e0}
.mini-card:last-child{border-bottom:0}
.mini-title{margin:0;font-family:'Pixelify Sans',cursive;font-size:12px;color:#8c0f38}
.mini-desc{margin:3px 0 4px;font-size:10px;color:#555}
.mini-card .project-link{font-size:11px;padding:4px 10px}

/* ---------- 88x31 buttons ---------- */
.tbtn{display:block;width:88px;height:31px;margin:8px auto 0;line-height:31px;text-align:center;
  font-family:'Silkscreen',monospace;font-size:8px;text-decoration:none;border:2px outset #ccc;
  border-radius:2px;overflow:hidden;white-space:nowrap}
.tbtn.a{background:linear-gradient(#333,#000);color:#7cfc9a}
.tbtn.b{background:linear-gradient(#ffd23f,#e2a100);color:#5a3200}
.tbtn:hover{filter:brightness(1.15)}

/* ---------- footer ---------- */
.footer{margin-top:8px;background:linear-gradient(#2e4a6e,#0d1c30);border:3px solid #08111f;
  border-radius:9px;padding:14px 16px;color:#cfe0f4}
.footer a{color:#ffd23f;text-decoration:none}
.footer a:hover{text-decoration:underline}
.fname{text-align:center;margin:0 0 10px;font-family:'Pixelify Sans',cursive;font-size:13px;color:#ffd23f}
.flinks-list{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;gap:4px 12px;
  margin:0 0 12px;padding:0;font-size:10px;text-align:center}
.fbadges{display:flex;justify-content:center;align-items:center;gap:8px;flex-wrap:wrap;margin:12px 0}
.fbadge{display:inline-block;font-family:'Silkscreen',monospace;font-size:8px;padding:2px 7px;
  border:1px solid #5f7ea3;border-radius:2px;background:#16273f;color:#9fd0ff}
.odigits{display:flex;justify-content:center;gap:2px;margin:10px 0}
.odigits span{font-family:'VT323',monospace;font-size:22px;background:#000;color:#7cfc9a;
  border:1px inset #454f6e;padding:1px 6px}
.fcopy{text-align:center;font-size:10px;color:#8fa3c8;margin:10px 0 0}

@media (prefers-reduced-motion:reduce){
  .adbig .blink,.newbadge,.counter.wig{animation:none}
}
"""

# Box-header style / rotation / offset cycles for project cards.
HDR_STYLES = ("h-news", "h-room", "h-lb", "h-poll", "h-picks", "h-status", "h-hot", "h-pals")
ROTS = ("pr1", "pr2", "pr3", "pr4", "pr5")
OFFS = ("", "push", "offL")


# ---------------------------------------------------------------- helpers

TOP_CARDS = 4


def fixpaths(fragment: str) -> str:
    """classic/ lives one level below the repo root, so links copied out of
    it must be rewritten for a root-level index.html."""
    return fragment.replace('"../assets/', '"assets/').replace('"../about/', '"about/')


def esc(text: str) -> str:
    """Escape text the script itself built (text-node context)."""
    return html.escape(text, quote=False)


def escq(text: str) -> str:
    """Escape text the script itself built (attribute context)."""
    return html.escape(text, quote=True)


def req(parent, css: str, what: str):
    node = parent.select_one(css) if parent is not None else None
    if node is None:
        print(
            f"build_pixel.py: FATAL: could not find {what} (selector: {css})",
            file=sys.stderr,
        )
        sys.exit(1)
    return node


# ---------------------------------------------------------------- builders

def project_box(card, index: int) -> str:
    """One maximalist box per source article.project-card. All content is
    copied verbatim; only the wrapper, header layout and classes are new."""
    title_html = req(card, "h3.project-title", "project title").decode_contents()
    category = card.get("data-category", "")
    meta_tag = card.select_one(".card-meta")
    stat_tag = card.select_one(".card-stat")
    label_tag = card.select_one(".card-label")
    shots_tag = card.select_one(".project-shots")
    desc_html = req(card, ".project-desc", "project description").decode_contents()
    tech_tag = card.select_one(".tech-stack")
    foot_tag = card.select_one(".project-footer")

    cls = (
        "box proj "
        + HDR_STYLES[index % len(HDR_STYLES)]
        + " "
        + ROTS[index % len(ROTS)]
    )
    off = OFFS[index % len(OFFS)]
    if off:
        cls += " " + off

    parts = [f'<article class="{cls}" data-category="{escq(category)}">']
    parts.append("<h3>")
    if label_tag is not None:
        parts.append(f'<span class="flag">{label_tag.decode_contents()}</span>')
    if meta_tag is not None:
        parts.append(f'<span class="pmeta">{meta_tag.decode_contents()}</span>')
    parts.append(f'<span class="ptitle">{title_html}</span>')
    if stat_tag is not None:
        parts.append(f'<span class="pstat">{stat_tag.decode_contents()}</span>')
    parts.append("</h3>")
    parts.append('<div class="bd">')
    if shots_tag is not None:
        parts.append(fixpaths(str(shots_tag)))
    parts.append(f'<div class="project-desc">{desc_html}</div>')
    if tech_tag is not None:
        parts.append(fixpaths(str(tech_tag)))
    if foot_tag is not None:
        parts.append(fixpaths(str(foot_tag)))
    parts.append("</div></article>")
    return "".join(parts)


def mini_item(card) -> str:
    """Compact list entry for one source article.mini-card (verbatim)."""
    title_html = req(card, "h3.mini-title", "mini project title").decode_contents()
    desc_html = req(card, "p.mini-desc", "mini project description").decode_contents()
    tech_tag = card.select_one(".tech-stack")
    links_tag = card.select_one(".project-links")
    out = (
        '<article class="mini-card">'
        f'<h3 class="mini-title">{title_html}</h3>'
        f'<p class="mini-desc">{desc_html}</p>'
    )
    if tech_tag is not None:
        out += fixpaths(str(tech_tag))
    if links_tag is not None:
        out += fixpaths(str(links_tag))
    out += "</article>"
    return out


def panel_heading(panel, idx: int, fallback: str) -> str:
    h3s = panel.select("h3.panel-h")
    if len(h3s) > idx:
        return h3s[idx].get_text(" ", strip=True)
    return fallback


# ---------------------------------------------------------------- main

def main() -> int:
    if not SRC.is_file():
        print(f"build_pixel.py: FATAL: source file not found: {SRC}", file=sys.stderr)
        return 1

    raw = SRC.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")

    # ---- 1. head metas (copied as-is) ----
    keep_names = {"description", "theme-color", "twitter:card"}
    keep_props = {"og:type", "og:title", "og:description"}
    metas = []
    for m in soup.find_all("meta"):
        if m.get("name") in keep_names or m.get("property") in keep_props:
            metas.append(str(m))
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Portfolio"
    og_title_tag = soup.find("meta", attrs={"property": "og:title"})
    og_title = og_title_tag["content"] if og_title_tag else title
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    mdesc = meta_desc_tag["content"] if meta_desc_tag else ""

    # ---- 2. hero ----
    hero = req(soup, "section.hero", "hero section")
    name_text = req(hero, "#hero-title", "hero h1").get_text(" ", strip=True)
    name_words = name_text.split() or ["Luqman", "Hakim"]
    role_text = req(hero, ".hero-role", "hero role line").get_text(" ", strip=True)
    summary_html = fixpaths(req(hero, ".hero-summary", "hero summary").decode_contents())
    fact_text = req(hero, ".hero-fact", "hero fact line").get_text(" ", strip=True)
    actions_inner = fixpaths(req(hero, ".hero-actions", "hero actions").decode_contents())

    # ---- 3. stats row ----
    stats_html = fixpaths(str(req(soup, "section.stats-row dl.stats-list", "stats list")))

    # ---- 4. projects / more projects ----
    project_cards = soup.select("#projects article.project-card")
    more_cards = soup.select("#more-projects article.mini-card")
    n_projects = len(project_cards)
    n_more = len(more_cards)
    n_shipped = n_projects + n_more

    projects_h2 = req(soup, "#projects h2.section-title", "projects section title").decode_contents()
    more_h2 = req(soup, "#more-projects h2.section-title", "more projects section title").decode_contents()
    skills_h2 = req(soup, "#skills h2.section-title", "skills section title").decode_contents()

    # ---- 5. skills panels ----
    skills_section = req(soup, "section#skills", "skills section")
    panels = skills_section.select(".bio-panel")
    if len(panels) < 2:
        print("build_pixel.py: FATAL: expected two .bio-panel blocks in #skills", file=sys.stderr)
        return 1
    panel_a, panel_b = panels[0], panels[1]
    tech_heading = panel_heading(panel_a, 0, "Technical Stack")
    exp_heading = panel_heading(panel_a, 1, "Experience")
    edu_heading = panel_heading(panel_b, 0, "Education")
    cert_heading = panel_heading(panel_b, 1, "Certifications")
    skill_rows_html = "\n".join(fixpaths(str(r)) for r in panel_a.select(".skill-row"))
    exp_html = fixpaths(str(req(panel_a, ".timeline-list", "experience timeline")))
    edu_html = fixpaths(str(req(panel_b, ".timeline-list", "education timeline")))
    cert_exam_html = fixpaths(str(req(panel_b, ".cert-exam", "cert-exam block")))
    cert_list_tag = req(panel_b, "dl.cert-list", "cert list")

    # The new SAS entry, highlighted with a blinking NEW! badge (copied
    # verbatim; only the highlighting classes/badge are added).
    cert_soup = BeautifulSoup(str(cert_list_tag), "html.parser")
    cert_dl = cert_soup.find("dl")
    sas_dt = cert_dl.find("dt", string=re.compile(r"\bSAS\b"))
    if sas_dt is not None:
        sas_dt["class"] = sas_dt.get("class", []) + ["isnew"]
        sas_dd = sas_dt.find_next_sibling("dd")
        if sas_dd is not None:
            sas_dd["class"] = sas_dd.get("class", []) + ["isnew"]
        badge = cert_soup.new_tag("span", attrs={"class": "newbadge"})
        badge.string = "NEW!"
        sas_dt.append(" ")
        sas_dt.append(badge)
    cert_inner = cert_dl.decode_contents()

    # Facts for the ticker / banner, pulled from the source (never invented).
    sas_dt_orig = cert_list_tag.find("dt", string=re.compile(r"\bSAS\b"))
    sas_dd_orig = sas_dt_orig.find_next_sibling("dd") if sas_dt_orig is not None else None
    sas_name = ""
    sas_subline = ""
    if sas_dd_orig is not None:
        sas_name = " ".join(sas_dd_orig.get_text(" ", strip=True).split())
    if sas_dt_orig is not None:
        m2 = re.search(r"\(([^)]*)\)", sas_dt_orig.get_text())
        if m2:
            sas_subline = m2.group(1).strip()
    exam_text = " ".join(req(panel_b, ".cert-exam", "cert-exam block").get_text(" ", strip=True).split())

    ticker_items = []
    m = re.search(r"open to graduate AI Engineer roles[^.]*?from March 2027", mdesc)
    if m:
        phrase = m.group(0)
        ticker_items.append(phrase[0].upper() + phrase[1:])
    else:
        ticker_items.append(fact_text)
    if sas_name:
        item = "NEW CERT: " + sas_name
        datepart = re.sub(r"^new,?\s*", "", sas_subline, flags=re.IGNORECASE).strip()
        if datepart:
            item += f" ({datepart})"
        ticker_items.append(item)
    if exam_text:
        ticker_items.append(exam_text)
    ticker_items.append(f"{n_shipped} PROJECTS SHIPPED")
    if "graduating February 2027" in mdesc:
        ticker_items.append("Graduating February 2027")
    ticker_text = " &#9733; ".join(esc(t) for t in ticker_items)

    # ---- 6. footer + nav link targets ----
    footer_el = req(soup, "footer.site-footer", "site footer")
    footer_name_html = req(footer_el, ".footer-name", "footer name").decode_contents()
    footer_links_inner = fixpaths(req(footer_el, "ul.footer-links", "footer links").decode_contents())
    footer_copy_html = req(footer_el, ".footer-copy", "footer copyright").decode_contents()
    li_tag = footer_el.select_one('a[href*="linkedin.com"]')
    linkedin_href = li_tag["href"] if li_tag is not None else "https://linkedin.com/in/luqmansyahrulnizam"
    gh_href = "https://github.com/Downey112"
    about_href = "about/"
    for a in soup.select("header.site-nav a"):
        href = a.get("href", "")
        if "github.com" in href:
            gh_href = href
        if "about" in href:
            about_href = href[3:] if href.startswith("../") else href

    # ---- counts ----
    n_images = len(soup.find_all("img"))
    n_links = len(soup.find_all("a"))

    # ---- build the page ----
    logo_spans = " ".join(
        f'<span class="{"t123"[i % 3]}">{esc(w)}</span>' for i, w in enumerate(name_words)
    )

    enter_fine = "Graduating February 2027" if "graduating February 2027" in mdesc else role_text
    banner_main = ("NEW! " + sas_name) if sas_name else "NEW CERT!"
    banner_sub = sas_subline or "see the certifications list"

    head_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=1000">',
        f"<title>{esc(title)}</title>",
        *metas,
        FONTS_LINK,
        f"<style>\n{CSS}</style>",
        "</head>",
        "<body>",
    ]

    nav_html = ['<nav aria-label="Primary"><ul class="nav">']
    nav_items = [
        ("Projects", "#projects", False),
        ("More", "#more-projects", False),
        ("Skills", "#skills", False),
        ("About", about_href, False),
        ("GitHub", gh_href, True),
        ("Classic view", CLASSIC_URL, False),
    ]
    for i, (label, href, external) in enumerate(nav_items):
        on = ' class="on"' if i == 0 else ""
        ext = ' target="_blank" rel="noopener"' if external else ""
        nav_html.append(f'<li{on}><a href="{escq(href)}"{ext}>{esc(label)}</a></li>')
    nav_html.append("</ul></nav>")

    body_parts = []
    body_parts.append('<a class="skip-link" href="#main">Skip to content</a>')
    body_parts.append('<div class="page">')

    # ticker
    body_parts.append(
        '<div class="ticker">'
        '<marquee scrollamount="4" behavior="scroll" direction="left" '
        f'aria-label="Portfolio news ticker">{ticker_text}</marquee>'
        "</div>"
    )

    # header
    body_parts.append(
        f'<header class="hdr">\n'
        f'  <span class="badgenew" aria-hidden="true">NEW CERT!</span>\n'
        f'  <span class="hotstar" aria-hidden="true"><span>OPEN TO WORK</span></span>\n'
        f'  <span class="credstick" aria-hidden="true">Mar 2027</span>\n'
        f'  <div class="hdr-left">\n'
        f'    <h1 class="logo">{logo_spans}</h1>\n'
        f'    <p class="tagline">{esc(role_text)}</p>\n'
        f'    <p class="counter">Projects shipped: <span id="shipped">{n_shipped}</span></p>\n'
        f'    <p class="hdr-note">{esc(fact_text)}</p>\n'
        f"  </div>\n"
        f"  {SKYLINE_SVG}\n"
        f"</header>"
    )

    body_parts.append("".join(nav_html))

    # cert banner strip
    body_parts.append(
        f'<div class="adstrip" role="complementary" aria-label="New certification announcement">\n'
        f'  <span class="adtag">NEW</span>\n'
        f'  <span class="adbig">&#9733; <span class="blink">{esc(banner_main)}</span> &#9733;</span>\n'
        f'  <span class="adsmall">{esc(banner_sub)}</span>\n'
        f'  <a class="adcta" href="{escq(LINKEDIN_CERTS_URL)}" target="_blank" rel="noopener">View on LinkedIn</a>\n'
        f"</div>"
    )

    # 3-column layout
    body_parts.append('<main id="main">')
    body_parts.append('<div class="layout">')
    body_parts.append('<span class="flt wow" aria-hidden="true">WOW!</span>')
    body_parts.append('<span class="flt tape" aria-hidden="true"></span>')
    body_parts.append('<span class="flt rad" aria-hidden="true">so rad!!</span>')
    body_parts.append('<span class="flt pix" aria-hidden="true">LVL UP!</span>')

    # LEFT column
    body_parts.append('<div class="colL">')
    body_parts.append(
        f'<div class="box h-news rA">\n'
        f"  <h3>About me</h3>\n"
        f'  <div class="bd">\n'
        f'    <div class="aboutme">{summary_html}</div>\n'
        f'    <div class="hero-actions">{actions_inner}</div>\n'
        f"  </div>\n"
        f"</div>"
    )
    body_parts.append(
        f'<div class="box h-status rB">\n'
        f"  <h3>Stats</h3>\n"
        f'  <div class="bd">{stats_html}</div>\n'
        f"</div>"
    )
    body_parts.append(
        f'<div class="box h-shout rC">\n'
        f"  <h3>Contact</h3>\n"
        f'  <div class="bd"><ul class="contact-list">{footer_links_inner}</ul></div>\n'
        f"</div>"
    )
    body_parts.append(
        f'<div class="box h-lb rD" id="certifications">\n'
        f"  <h3>{esc(cert_heading)}</h3>\n"
        f"  <div class=\"bd\">\n"
        f"    {cert_exam_html}\n"
        f'    <dl class="cert-list">{cert_inner}</dl>\n'
        f"  </div>\n"
        f"</div>"
    )
    body_parts.append("</div>")  # colL

    # CENTRE column
    body_parts.append('<div class="colC">')
    body_parts.append(
        f'<div class="enter rC">\n'
        f"  <h2>&#9654; {esc(og_title)} &#9664;</h2>\n"
        f'  <a class="bigbtn" href="#projects">Enter my portfolio</a>\n'
        f'  <p class="fine">{esc(enter_fine)}</p>\n'
        f"</div>"
    )
    body_parts.append('<section id="projects">')
    body_parts.append(f'<h2 class="sechdr">{projects_h2}</h2>')
    for i, card in enumerate(project_cards[:TOP_CARDS]):
        body_parts.append(project_box(card, i))
    body_parts.append("</section>")
    body_parts.append("</div>")  # colC

    # RIGHT column
    body_parts.append('<div class="colR">')
    body_parts.append('<section id="skills">')
    body_parts.append(f'<h2 class="sechdr">{skills_h2}</h2>')
    body_parts.append(
        f'<div class="box h-picks rB">\n'
        f"  <h3>{esc(tech_heading)}</h3>\n"
        f'  <div class="bd">{skill_rows_html}</div>\n'
        f"</div>"
    )
    body_parts.append(
        f'<div class="box h-poll rD" id="experience">\n'
        f"  <h3>{esc(exp_heading)}</h3>\n"
        f'  <div class="bd">{exp_html}</div>\n'
        f"</div>"
    )
    body_parts.append(
        f'<div class="box h-status rA">\n'
        f"  <h3>{esc(edu_heading)}</h3>\n"
        f'  <div class="bd">{edu_html}</div>\n'
        f"</div>"
    )
    body_parts.append("</section>")  # skills
    body_parts.append(
        f'<div class="box h-link rB offL">\n'
        f"  <h3>Find me</h3>\n"
        f'  <div class="bd">\n'
        f'    <a class="tbtn a" href="{escq(gh_href)}" target="_blank" rel="noopener">GITHUB</a>\n'
        f'    <a class="tbtn b" href="{escq(linkedin_href)}" target="_blank" rel="noopener">LINKEDIN</a>\n'
        f'    <a class="tbtn a" href="{escq(CLASSIC_URL)}">CLASSIC VIEW</a>\n'
        f"  </div>\n"
        f"</div>"
    )
    body_parts.append("</div>")  # colR

    body_parts.append("</div>")  # layout
    # full-width project hall: remaining cards in a 2-column grid
    body_parts.append('<section class="hall" aria-label="Projects, continued">')
    for i, card in enumerate(project_cards[TOP_CARDS:], start=TOP_CARDS):
        body_parts.append(project_box(card, i))
    body_parts.append("</section>")
    body_parts.append(
        f'<section class="box h-hot morehall" id="more-projects">\n'
        f"  <h2>{more_h2}</h2>\n"
        f'  <div class="bd moregrid">{chr(10).join(mini_item(c) for c in more_cards)}</div>\n'
        f"</section>"
    )
    body_parts.append("</main>")  # main

    # footer
    digits = f"{n_shipped:06d}"
    odigits = "".join(f"<span>{d}</span>" for d in digits)
    body_parts.append(
        f'<footer class="footer">\n'
        f'  <p class="fname">{footer_name_html}</p>\n'
        f'  <ul class="flinks-list">{footer_links_inner}</ul>\n'
        f'  <div class="fbadges">\n'
        f'    <span class="fbadge">BEST VIEWED IN 1024x768</span>\n'
        f'    <span class="fbadge">MADE IN KL</span>\n'
        f'    <span class="fbadge">POWER BI INSIDE</span>\n'
        f"  </div>\n"
        f'  <div class="odigits" role="img" aria-label="Project counter: {n_shipped} projects shipped">{odigits}</div>\n'
        f'  <p class="fcopy">{footer_copy_html}</p>\n'
        f"</footer>"
    )
    body_parts.append("</div>")  # page
    body_parts.append(SCRIPT)
    body_parts.append("</body>\n</html>")

    page = "\n".join(head_parts + body_parts) + "\n"

    # ---- fail loudly on empty extractions / bad paths / lost anchors ----
    problems = []
    if n_projects == 0:
        problems.append("no project cards found in #projects")
    if n_more == 0:
        problems.append("no more-project items found in #more-projects")
    if n_images == 0:
        problems.append("no images found in the source page")
    if n_links == 0:
        problems.append("no links found in the source page")
    for anchor in ("projects", "more-projects", "skills", "experience", "certifications", "main"):
        if f'id="{anchor}"' not in page:
            problems.append(f'output is missing id="{anchor}"')
    if "../assets" in page:
        problems.append('output still contains "../assets" (path rewrite failed)')
    if "../about" in page:
        problems.append('output still contains "../about" (path rewrite failed)')
    if problems:
        for p in problems:
            print(f"build_pixel.py: FATAL: {p}", file=sys.stderr)
        return 1

    OUT.write_text(page, encoding="utf-8")

    # ---- summary ----
    print(f"build_pixel.py: wrote {OUT}")
    print(f"  project cards      : {n_projects}")
    print(f"  more-project items : {n_more}")
    print(f"  total shipped      : {n_shipped}")
    print(f"  images             : {n_images}")
    print(f"  links extracted    : {n_links}")
    print(f"  output size        : {OUT.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
