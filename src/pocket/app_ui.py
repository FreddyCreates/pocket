"""POCKET production UI — multi-agent desk (not a demo shell)."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<meta name="theme-color" content="#000000"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="description" content="POCKET — host co-pilot. Fusion Sense, agents, API."/>
<title>POCKET</title>
<style>
:root{
  --bg:#09090b; --bg2:#0c0c0e; --panel:#141416; --panel2:#1a1a1e;
  --line:rgba(255,255,255,.07); --line2:rgba(255,255,255,.12); --text:#e4e4e7; --muted:#71717a;
  --fg:#fafafa; --accent:#10a37f; --accent2:#0d8c6c; --blue:#60a5fa;
  --amber:#eab308; --red:#f87171; --violet:#a78bfa; --cyan:#22d3ee;
  --radius:10px; --radius-sm:8px;
  --font:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --shadow:0 0 0 1px rgba(255,255,255,.05);
  --focus:0 0 0 2px rgba(16,163,127,.35);
  --side-w:248px; --rail-w:288px;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%;margin:0}
body{font-family:var(--font);background:var(--bg);color:var(--text);overflow:hidden;-webkit-font-smoothing:antialiased;font-size:13.5px;color-scheme:dark}
button,input,textarea,select{font:inherit;color:inherit}
button{cursor:pointer}
button:disabled,textarea:disabled,select:disabled{opacity:.4;cursor:not-allowed}
button:focus-visible,a:focus-visible,select:focus-visible,textarea:focus-visible,.icon:focus-visible,.sitem:focus-visible{outline:none;box-shadow:var(--focus);border-radius:6px}
::selection{background:rgba(16,163,127,.35);color:var(--fg)}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}
  .live-dot,.sa-dot.run{animation:none!important}
}
a{color:var(--accent);text-decoration:none}
a:hover{color:var(--accent2)}
/* scrollbars — product density */
.slist,.transcript,.rr-body,.wt-body,.rail > div{scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.12) transparent}
.slist::-webkit-scrollbar,.transcript::-webkit-scrollbar,.rr-body::-webkit-scrollbar{width:6px;height:6px}
.slist::-webkit-scrollbar-thumb,.transcript::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:99px}
.app{display:grid;grid-template-columns:var(--side-w) minmax(0,1fr) var(--rail-w);grid-template-rows:48px 1fr;height:100vh;height:100dvh}
.top{grid-column:1/-1;display:flex;align-items:center;gap:10px;padding:0 14px;border-bottom:1px solid var(--line);background:rgba(9,9,11,.92);backdrop-filter:blur(18px);z-index:20}
.brand{display:flex;align-items:center;gap:9px;font-weight:650;letter-spacing:-.03em;font-size:13.5px;color:var(--fg);user-select:none}
.brand .mark{width:22px;height:22px;border-radius:7px;background:linear-gradient(145deg,var(--accent),#0a7a5f);display:grid;place-items:center;font-size:11px;font-weight:800;color:#041;box-shadow:0 0 0 1px rgba(16,163,127,.3)}
.top .grow{flex:1;min-width:8px}
.top-meta{display:flex;gap:5px;flex-wrap:wrap;align-items:center}
.top-links{display:flex;gap:1px;align-items:center;background:rgba(255,255,255,.03);padding:2px;border-radius:9px;border:1px solid var(--line)}
.top-links a{color:var(--muted);font-size:12px;font-weight:550;padding:5px 11px;border-radius:7px;text-decoration:none;transition:color .12s,background .12s}
.top-links a:hover{color:var(--text);background:rgba(255,255,255,.05);text-decoration:none}
.top-links a.on-desk{color:var(--fg);background:var(--panel2);box-shadow:var(--shadow)}
.top-back{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:8px;padding:5px 10px;font-size:12px;font-weight:600;display:inline-flex;align-items:center;gap:4px}
.top-back:hover{color:var(--fg);background:rgba(255,255,255,.05);border-color:var(--line2)}
/* Production boot splash */
.boot-splash{position:fixed;inset:0;z-index:200;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#050508;transition:opacity .45s ease,visibility .45s;pointer-events:none}
.boot-splash.done{opacity:0;visibility:hidden;pointer-events:none}
.boot-splash .boot-mark{width:52px;height:52px;border-radius:14px;background:linear-gradient(145deg,#10a37f,#0a7a5f);color:#041;display:grid;place-items:center;font-size:22px;font-weight:800;box-shadow:0 0 0 1px rgba(16,163,127,.4),0 12px 40px rgba(16,163,127,.25);animation:bootPop .7s cubic-bezier(.2,1.2,.4,1) both}
.boot-splash .boot-title{margin-top:18px;font-size:20px;font-weight:650;letter-spacing:-.04em;color:#fafafa;animation:bootFade .6s .15s both}
.boot-splash .boot-sub{margin-top:6px;font-size:12.5px;color:#71717a;animation:bootFade .6s .25s both}
.boot-splash .boot-bar{width:120px;height:3px;border-radius:99px;background:rgba(255,255,255,.08);margin-top:22px;overflow:hidden;animation:bootFade .5s .3s both}
.boot-splash .boot-bar i{display:block;height:100%;width:40%;border-radius:99px;background:linear-gradient(90deg,#10a37f,#34d399);animation:bootSlide 1.1s ease-in-out infinite}
@keyframes bootPop{from{transform:scale(.6);opacity:0}to{transform:scale(1);opacity:1}}
@keyframes bootFade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes bootSlide{0%{transform:translateX(-100%)}100%{transform:translateX(280%)}}
/* Browser mode: stays INSIDE POCKET — chrome always has ← Desk (never hijacks whole app) */
.browser-layer{position:fixed;inset:0;z-index:70;display:none;flex-direction:column;background:var(--bg)}
.browser-layer.open{display:flex}
.browser-chrome{flex:0 0 auto;display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--line);background:rgba(9,9,11,.96);backdrop-filter:blur(14px)}
.browser-chrome .b-back{border:1px solid rgba(16,163,127,.45);background:rgba(16,163,127,.12);color:#6ee7b7;border-radius:8px;padding:7px 12px;font-size:12.5px;font-weight:700;cursor:pointer;white-space:nowrap}
.browser-chrome .b-back:hover{background:rgba(16,163,127,.22);color:#fff}
.browser-chrome button.b-ico{border:1px solid var(--line);background:var(--panel);color:var(--text);border-radius:8px;padding:7px 10px;font-size:12px;font-weight:600;cursor:pointer}
.browser-chrome button.b-ico:hover{border-color:var(--line2);color:var(--fg)}
.browser-chrome input{flex:1;min-width:0;border:1px solid var(--line);background:#0c0c0e;color:var(--fg);border-radius:8px;padding:8px 12px;font-size:13px}
.browser-chrome .b-go{border:0;background:var(--accent);color:#041;border-radius:8px;padding:8px 14px;font-size:12.5px;font-weight:700;cursor:pointer}
.browser-chrome .b-go:hover{background:var(--accent2)}
.browser-quick{flex:0 0 auto;display:flex;flex-wrap:wrap;gap:6px;padding:8px 12px;border-bottom:1px solid var(--line);background:var(--bg2)}
.browser-quick button{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:999px;padding:5px 10px;font-size:11px;font-weight:550;cursor:pointer}
.browser-quick button:hover{color:var(--fg);border-color:var(--line2)}
.browser-stage{flex:1;min-height:0;position:relative;background:#000}
.browser-stage iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:#0a0a0a}
.browser-blocked{position:absolute;inset:0;display:none;align-items:center;justify-content:center;flex-direction:column;gap:12px;padding:32px;text-align:center;color:var(--muted);background:rgba(9,9,11,.94)}
.browser-blocked.show{display:flex}
.browser-blocked h3{margin:0;color:var(--fg);font-size:16px;font-weight:650}
.browser-blocked p{margin:0;max-width:420px;font-size:13px;line-height:1.5}
.browser-blocked .btn-primary{border:0;background:var(--accent);color:#041;border-radius:9px;padding:10px 16px;font-weight:700;cursor:pointer}
.chip{font-size:10.5px;font-weight:550;padding:3px 8px;border-radius:999px;border:1px solid var(--line);color:var(--muted);background:transparent;letter-spacing:.01em}
.chip.on{color:#6ee7b7;border-color:rgba(16,163,127,.4);background:rgba(16,163,127,.1)}
.chip.off{color:#fca5a5;border-color:rgba(248,113,113,.3);background:rgba(248,113,113,.08)}
.chip.warn{color:#fde047;border-color:rgba(234,179,8,.3);background:rgba(234,179,8,.08)}
.side,.rail{background:var(--bg2);border-right:1px solid var(--line);display:flex;flex-direction:column;min-height:0}
.rail{border-right:0;border-left:1px solid var(--line);min-width:280px;max-width:360px}
.ai-sum,.ai-prev,.ai-bus{margin:0 10px 10px;padding:10px 11px;border-radius:10px;border:1px solid var(--line);background:var(--panel)}
.ai-sum h3,.ai-prev h3,.ai-bus h3{margin:0 0 8px;font-size:10.5px;font-weight:650;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.ai-sum .body{font-size:11.5px;line-height:1.5;color:var(--text);max-height:160px;overflow:auto;white-space:pre-wrap}
.ai-sum .meta{font-size:10px;color:var(--muted);margin-top:6px}
.ai-prev .pv{border:1px solid var(--line);border-radius:8px;padding:7px 8px;margin-bottom:6px;background:rgba(0,0,0,.25);cursor:pointer}
.ai-prev .pv:hover{border-color:rgba(16,163,127,.35)}
.ai-prev .pv b{display:block;font-size:11px;color:var(--fg);margin-bottom:3px}
.ai-prev .pv pre{margin:0;font-size:10px;line-height:1.4;color:var(--muted);max-height:72px;overflow:hidden;white-space:pre-wrap;font-family:var(--mono)}
.ai-prev .tree{font-size:10.5px;font-family:var(--mono);color:var(--muted);max-height:100px;overflow:auto;line-height:1.45}
.ai-bus .bm{font-size:10.5px;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.04);color:var(--muted);line-height:1.4}
.ai-bus .bm b{color:var(--accent);font-weight:600}
.ai-bus .bm .hm{font-family:var(--mono);font-size:9px;opacity:.7}
.side-h{padding:12px 12px 6px;display:flex;justify-content:space-between;align-items:center;font-size:10.5px;font-weight:650;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.icon{border:1px solid transparent;background:transparent;color:var(--muted);border-radius:7px;padding:5px 7px;font-size:12px;transition:background .12s,color .12s}
.icon:hover{color:var(--text);background:rgba(255,255,255,.05)}
.actions{display:flex;flex-direction:column;gap:1px;padding:0 8px 8px}
.actions button{text-align:left;border:0;background:transparent;border-radius:9px;padding:9px 11px;font-size:13px;font-weight:500;color:var(--text);transition:background .12s}
.actions button:hover{background:rgba(255,255,255,.04)}
.actions button:active{background:rgba(16,163,127,.1)}
.actions button b{font-weight:600;letter-spacing:-.01em}
.actions button small{display:block;color:var(--muted);font-weight:400;margin-top:2px;font-size:11px;line-height:1.35}
.actions .more-btn{color:var(--muted);font-size:11.5px;padding:8px 11px;font-weight:500}
.actions .more-agents{display:none;flex-direction:column;gap:1px}
.actions .more-agents.open{display:flex}
.toolrow{padding:0 10px 10px;display:grid;gap:6px}
.toolrow button,.toolrow label.btn{display:block;width:100%;text-align:center;border:1px solid var(--line);background:transparent;border-radius:8px;padding:7px;font-size:11.5px;font-weight:550;color:var(--muted);transition:border-color .12s,color .12s,background .12s}
.toolrow button:hover,label.btn:hover{color:var(--text);border-color:var(--line2);background:rgba(255,255,255,.03)}
#fileInput{display:none}
.slist{flex:1;overflow:auto;padding:4px 8px 14px;min-height:72px}
.stack-card{margin:0 10px 10px;padding:9px 11px;border-radius:10px;border:1px solid var(--line);background:var(--panel);font-size:11px;line-height:1.4}
.stack-card .sk{display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04)}
.stack-card .sk:last-child{border-bottom:0}
.stack-card .sk b{font-weight:600;color:var(--fg);font-size:11px}
.stack-card .sk span.on{color:#6ee7b7;font-weight:550}
.stack-card .sk span.off{color:#f87171;font-weight:550}
.slist .hint{color:var(--muted);font-size:11.5px;padding:10px 8px;line-height:1.5}
.sitem{display:flex;gap:8px;padding:9px 10px;border-radius:9px;border:1px solid transparent;margin-bottom:2px;cursor:pointer;transition:background .12s,border-color .12s}
.sitem:hover{background:rgba(255,255,255,.03)}
.sitem.on{background:rgba(16,163,127,.08);border-color:rgba(16,163,127,.22)}
.dot{width:7px;height:7px;border-radius:50%;margin-top:5px;flex:0 0 auto}
.sitem b{display:block;font-size:12.5px;font-weight:600;letter-spacing:-.01em}
.sitem .meta{font-size:10.5px;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sitem .x{margin-left:auto;border:0;background:transparent;color:var(--muted);font-size:15px;padding:0 4px;line-height:1;opacity:.6}
.sitem .x:hover{color:var(--red);opacity:1}
.main{display:flex;flex-direction:column;min-width:0;min-height:0;background:var(--bg)}
.main-h{padding:10px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:8px;min-height:48px;background:rgba(9,9,11,.5)}
.main-h h1{margin:0;font-size:13.5px;font-weight:600;letter-spacing:-.02em;color:var(--fg)}
.tag{font-size:10.5px;font-weight:550;padding:2px 8px;border-radius:999px;background:transparent;border:1px solid var(--line);color:var(--muted)}
.main-h select{margin-left:auto;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:5px 8px;font-size:11.5px;color:var(--muted)}
.transcript{flex:1;overflow:auto;padding:18px 22px 24px;display:flex;flex-direction:column;gap:2px}
.empty{margin:auto;max-width:380px;text-align:center;color:var(--muted);line-height:1.55;padding:28px 18px}
.empty .mark{
  width:32px;height:32px;border-radius:9px;background:linear-gradient(145deg,var(--accent),#0a7a5f);color:#041;
  display:grid;place-items:center;font-size:14px;font-weight:800;margin:0 auto 14px;
  box-shadow:0 0 0 1px rgba(16,163,127,.35),0 8px 24px rgba(16,163,127,.12)
}
.empty h2{color:var(--fg);font-size:18px;margin:0 0 8px;font-weight:600;letter-spacing:-.03em}
.empty p{font-size:13px;margin:0;color:var(--muted)}
.empty .empty-actions{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:18px}
.empty .empty-actions button{
  border:1px solid var(--line);background:var(--panel);color:var(--text);border-radius:999px;
  padding:7px 14px;font-size:12px;font-weight:550
}
.empty .empty-actions button:hover{border-color:rgba(16,163,127,.4);color:var(--fg);background:rgba(16,163,127,.08)}
.empty kbd{
  font-family:var(--mono);font-size:11px;padding:1px 5px;border-radius:4px;
  border:1px solid var(--line);background:var(--panel);color:var(--fg)
}
/* Antigravity-style clean chat */
.msg{border:0;border-radius:0;background:transparent;overflow:visible;max-width:720px;width:100%;margin:0 auto}
.msg.user{margin-top:18px}
.msg.user .mb{
  white-space:pre-wrap;font-size:14px;line-height:1.55;font-family:var(--font);
  padding:12px 16px;border-radius:14px;background:var(--panel);border:1px solid var(--line);
  color:var(--fg);max-height:none
}
.msg.agent .mb{
  white-space:pre-wrap;font-size:14px;line-height:1.65;font-family:var(--font);
  padding:6px 4px 10px;color:var(--text);max-height:none;overflow:visible
}
.msg.agent .mb.prose p{margin:0 0 .7em}
.msg.agent .mb.prose p:last-child{margin:0}
.msg.agent .mb.prose strong{color:var(--fg);font-weight:600}
.msg.agent .mb.prose code{font-family:var(--mono);font-size:12.5px;background:rgba(255,255,255,.06);padding:1px 5px;border-radius:4px}
.msg.agent .mb.prose pre{
  font-family:var(--mono);font-size:12px;line-height:1.45;background:#0a0a0a;border:1px solid var(--line);
  border-radius:8px;padding:10px 12px;overflow:auto;max-height:280px;margin:.6em 0;color:#b7f0c6
}
.msg .mh{display:flex;justify-content:space-between;gap:8px;padding:4px 4px 2px;background:transparent;border:0;font-size:11px;font-weight:500;color:var(--muted)}
.msg .mb.term{background:#0a0a0a;color:#b7f0c6;max-height:280px;min-height:36px;font-family:var(--mono);font-size:12.5px;line-height:1.5;padding:12px 14px;border-radius:10px;border:1px solid var(--line);overflow:auto}
.msg.running .mh{color:var(--blue)}
.msg.failed .mh{color:var(--red)}
.msg.done .mh{color:var(--accent)}
.msg.cancelled .mh{color:#f59e0b}
/* Clean chat · model thinking animation */
.msg.user{max-width:640px}
.msg.agent .mh{opacity:.85;letter-spacing:.01em}
.msg.agent .mb.prose{max-width:680px}
.think-row{
  max-width:720px;width:100%;margin:4px auto 8px;display:flex;align-items:center;gap:12px;
  padding:8px 6px;color:var(--muted);font-size:12.5px;font-weight:500
}
.think-orb{
  width:26px;height:26px;border-radius:50%;position:relative;flex:0 0 auto;
  background:radial-gradient(circle at 32% 32%,#6ee7b7,var(--accent) 48%,#0a7a5f 82%);
  box-shadow:0 0 0 0 rgba(16,163,127,.4);animation:thinkPulse 1.35s ease-in-out infinite
}
.think-orb::after{
  content:"";position:absolute;inset:-5px;border-radius:50%;
  border:2px solid transparent;border-top-color:var(--violet);border-right-color:var(--cyan);
  animation:thinkSpin .9s linear infinite
}
.think-dots span{
  display:inline-block;width:5px;height:5px;margin:0 2px;border-radius:50%;background:var(--accent);
  animation:thinkDot 1.15s ease-in-out infinite
}
.think-dots span:nth-child(2){animation-delay:.14s}
.think-dots span:nth-child(3){animation-delay:.28s}
.think-label{color:var(--muted)}
.think-label b{color:var(--fg);font-weight:600}
@keyframes thinkPulse{0%,100%{box-shadow:0 0 0 0 rgba(16,163,127,.35);transform:scale(1)}50%{box-shadow:0 0 0 12px rgba(16,163,127,0);transform:scale(1.06)}}
@keyframes thinkSpin{to{transform:rotate(360deg)}}
@keyframes thinkDot{0%,80%,100%{opacity:.25;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}
.live-dot{
  width:7px;height:7px;border-radius:50%;background:var(--accent);display:inline-block;margin-right:6px;vertical-align:middle;
  box-shadow:0 0 0 0 rgba(16,163,127,.5);animation:thinkPulse 1.4s ease-in-out infinite
}
.novae-pill{
  display:inline-flex;align-items:center;gap:6px;padding:2px 8px;border-radius:999px;font-size:10.5px;font-weight:650;
  border:1px solid rgba(167,139,250,.35);color:#c4b5fd;background:rgba(124,58,237,.12)
}
/* Infinite Wiki profile cards in chat */
.wiki-card{
  max-width:720px;width:100%;margin:8px auto 10px;border:1px solid rgba(16,163,127,.28);
  border-radius:12px;background:linear-gradient(165deg,rgba(16,163,127,.07),var(--panel));
  overflow:hidden;box-shadow:0 0 0 1px rgba(0,0,0,.2)
}
.wiki-card .wc-head{
  display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border-bottom:1px solid var(--line)
}
.wiki-card .wc-badge{
  flex:0 0 auto;font-size:10px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;
  color:#041;background:var(--accent);border-radius:6px;padding:3px 7px
}
.wiki-card .wc-title{flex:1;min-width:0}
.wiki-card .wc-title b{display:block;font-size:12.5px;color:var(--fg);word-break:break-all}
.wiki-card .wc-title span{font-size:11px;color:var(--muted)}
.wiki-card .wc-ast{
  font-size:10px;font-weight:700;padding:2px 7px;border-radius:999px;border:1px solid var(--line);color:var(--muted)
}
.wiki-card .wc-ast.ts{color:#a78bfa;border-color:rgba(167,139,250,.4)}
.wiki-card .wc-sum{padding:8px 12px;font-size:12px;color:var(--muted);line-height:1.45;border-bottom:1px solid rgba(255,255,255,.04)}
.wiki-card .wc-syms{display:flex;flex-wrap:wrap;gap:6px;padding:10px 12px 12px}
.wiki-card .wc-sym{
  display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:rgba(0,0,0,.25);
  border-radius:8px;padding:5px 8px;font-size:11.5px;color:var(--text);cursor:pointer;transition:border-color .12s,background .12s
}
.wiki-card .wc-sym:hover{border-color:rgba(16,163,127,.5);background:rgba(16,163,127,.1);color:var(--fg)}
.wiki-card .wc-sym b{font-family:var(--mono);font-weight:600;font-size:11px;color:var(--accent)}
.wiki-card .wc-sym em{font-style:normal;color:var(--muted);font-size:10.5px}
.wiki-card .wc-actions{display:flex;flex-wrap:wrap;gap:6px;padding:0 12px 12px}
.wiki-card .wc-actions button{
  border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:8px;
  padding:6px 10px;font-size:11.5px;font-weight:600
}
.wiki-card .wc-actions button:hover{color:var(--fg);border-color:var(--line2);background:rgba(255,255,255,.04)}
.wiki-card .wc-actions button.primary{background:var(--accent);color:#041;border-color:transparent}
.wiki-slice{
  max-width:720px;width:100%;margin:6px auto 12px;border:1px solid var(--line);border-radius:10px;
  background:#0a0a0c;overflow:auto;max-height:280px
}
.wiki-slice pre{margin:0;padding:10px 12px;font-family:var(--mono);font-size:11.5px;line-height:1.45;color:#b7f0c6;white-space:pre}
.sess-ctl{font-size:12px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:transparent;color:var(--muted);cursor:pointer}
.sess-ctl:hover{color:var(--fg);border-color:var(--muted)}
.sess-ctl.hot{color:#fbbf24;border-color:rgba(251,191,36,.45);background:rgba(251,191,36,.08)}
#btnEnd:hover{color:#f87171;border-color:rgba(248,113,113,.4)}
.worked-meta{
  max-width:720px;width:100%;margin:2px auto 0;padding:2px 4px 8px;
  font-size:11px;color:var(--muted);display:flex;align-items:center;gap:8px;flex-wrap:wrap
}
.worked-meta summary{cursor:pointer;list-style:none;user-select:none;color:var(--muted)}
.worked-meta summary::-webkit-details-marker{display:none}
.worked-meta summary:hover{color:var(--text)}
.worked-meta .wm-body{margin-top:6px;padding:8px 10px;border-radius:8px;border:1px solid var(--line);background:var(--panel);font-size:11px;line-height:1.45;color:var(--muted);font-family:var(--mono);max-height:120px;overflow:auto;white-space:pre-wrap}
.subagents-panel{
  max-width:720px;width:100%;margin:8px auto 12px;border:1px solid var(--line);
  border-radius:10px;background:var(--panel);overflow:hidden
}
.subagents-panel > summary{
  display:flex;align-items:center;gap:8px;padding:10px 12px;cursor:pointer;list-style:none;
  font-size:12px;font-weight:550;color:var(--text);user-select:none
}
.subagents-panel > summary::-webkit-details-marker{display:none}
.subagents-panel > summary:hover{background:rgba(255,255,255,.03)}
.subagents-panel > summary .sa-label{flex:1}
.subagents-panel > summary .sa-chev{
  color:var(--muted);font-size:10px;margin-left:4px;transition:transform .15s ease
}
.subagents-panel[open] > summary .sa-chev{transform:rotate(90deg);color:var(--accent)}
.subagents-panel .spin{
  width:11px;height:11px;border:2px solid rgba(16,163,127,.2);border-top-color:var(--accent);
  border-radius:50%;animation:sa-spin .7s linear infinite;flex:0 0 auto
}
@keyframes sa-spin{to{transform:rotate(360deg)}}
.subagents-panel .sa-list{padding:0 8px 10px;display:flex;flex-direction:column;gap:2px}
.subagents-panel .sa-row,.sa-row{
  display:flex;align-items:center;gap:8px;padding:7px 8px;border-radius:8px;font-size:12px
}
.subagents-panel .sa-row:hover,.rail .sa-row:hover{background:rgba(255,255,255,.03)}
.sa-dot{width:7px;height:7px;border-radius:50%;flex:0 0 auto;background:var(--muted)}
.sa-dot.run{background:var(--accent);box-shadow:0 0 0 3px rgba(16,163,127,.15);animation:pulse 1.2s infinite}
.sa-dot.done{background:var(--accent);opacity:.85}
.sa-dot.ready{background:var(--cyan);opacity:.75}
.sa-dot.mesh{background:var(--violet);opacity:.8}
.sa-dot.fail{background:var(--red)}
.sa-name{font-weight:600;color:var(--fg);letter-spacing:.02em;font-size:12px}
.sa-meta{color:var(--muted);font-size:11px;margin-left:auto;text-align:right;max-width:55%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sa-src{font-size:9px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);padding:1px 5px;border-radius:4px;border:1px solid var(--line);flex:0 0 auto}
.sa-src.headless{color:var(--violet);border-color:rgba(179,157,219,.35)}
.sa-src.design{color:var(--cyan);border-color:rgba(86,212,221,.35)}
.sa-src.latin{color:var(--accent);border-color:rgba(16,163,127,.3)}
.composer{padding:12px 18px 16px;border-top:1px solid var(--line);background:linear-gradient(180deg,transparent,rgba(0,0,0,.25) 30%,var(--bg))}
.composer-inner{max-width:720px;margin:0 auto;width:100%}
.presets{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.presets button{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:999px;padding:5px 11px;font-size:11px;font-weight:500;transition:all .12s}
.presets button:hover{color:var(--text);border-color:var(--line2);background:var(--panel)}
.box{
  display:flex;gap:8px;align-items:flex-end;background:var(--panel);
  border:1px solid var(--line);border-radius:14px;padding:8px 10px;
  transition:border-color .15s ease, box-shadow .15s ease;
  box-shadow:0 1px 0 rgba(255,255,255,.03) inset
}
.box:focus-within{border-color:rgba(16,163,127,.5);box-shadow:var(--focus),0 1px 0 rgba(255,255,255,.03) inset}
.box textarea{flex:1;min-height:48px;max-height:160px;resize:none;border:0;outline:0;background:transparent;padding:9px 6px;line-height:1.45;color:var(--text);font-size:14px}
.box textarea::placeholder{color:var(--muted)}
.box .iconbtn{border:0;background:transparent;border-radius:8px;padding:8px 10px;font-size:13px;color:var(--muted)}
.box .iconbtn:hover{color:var(--text);background:rgba(255,255,255,.04)}
.box .iconbtn.hot{color:var(--red);background:rgba(248,113,113,.1)}
.box .send{
  background:var(--accent);color:#041;border:0;border-radius:10px;
  padding:10px 16px;font-weight:650;font-size:13px;min-width:68px;
  transition:background .12s,transform .08s
}
.box .send:hover{background:var(--accent2)}
.box .send:active{transform:scale(.98)}
.box .send:disabled{opacity:.35;cursor:not-allowed;transform:none}
.composer-bar{display:flex;align-items:center;gap:10px;margin-top:8px;padding:0 2px}
.model-pick{
  background:transparent;border:1px solid transparent;border-radius:7px;padding:4px 8px;
  font-size:11.5px;color:var(--muted);max-width:180px
}
.model-pick:hover,.model-pick:focus{outline:0;border-color:var(--line);color:var(--text);background:var(--panel)}
.composer-hint{font-size:11px;color:var(--muted);margin-left:auto}
.composer-hint kbd{font-family:var(--mono);font-size:10px;padding:1px 5px;border-radius:4px;border:1px solid var(--line);background:var(--panel);color:var(--muted)}
.slash-menu,.mention-menu{
  display:none;margin:0 0 8px;border:1px solid var(--line);border-radius:10px;background:var(--panel);
  overflow:hidden;max-height:200px;overflow-y:auto
}
.slash-menu.open,.mention-menu.open{display:block}
.slash-menu button,.mention-menu button{
  display:flex;align-items:center;gap:10px;width:100%;text-align:left;border:0;background:transparent;
  padding:9px 12px;font-size:12px;color:var(--text);border-bottom:1px solid var(--line)
}
.slash-menu button:last-child,.mention-menu button:last-child{border-bottom:0}
.slash-menu button:hover,.slash-menu button.on,
.mention-menu button:hover,.mention-menu button.on{background:rgba(16,163,127,.08)}
.slash-menu button b,.mention-menu button b{font-weight:600;min-width:72px;font-family:var(--mono);font-size:11px;color:var(--accent)}
.slash-menu button span,.mention-menu button span{color:var(--muted);font-size:11px;flex:1}
.mention-menu button .mdot{width:6px;height:6px;border-radius:50%;background:var(--cyan);flex:0 0 auto}
.mention-menu button .mdot.headless{background:var(--violet)}
.mention-menu button .mdot.latin{background:var(--accent)}
/* Clean dispatch result card in transcript */
.dispatch-card{
  max-width:720px;width:100%;margin:6px auto 10px;padding:10px 12px;border-radius:10px;
  border:1px solid rgba(16,163,127,.28);background:rgba(16,163,127,.06);
  font-size:12px;line-height:1.45;color:var(--text)
}
.dispatch-card .dc-h{display:flex;align-items:center;gap:8px;font-weight:600;color:var(--fg);margin-bottom:4px}
.dispatch-card .dc-h .ok{color:var(--accent);font-size:11px;font-weight:700;letter-spacing:.03em}
.dispatch-card .dc-agents{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.dispatch-card .dc-chip{
  font-family:var(--mono);font-size:11px;padding:3px 8px;border-radius:999px;
  border:1px solid var(--line);background:var(--bg);color:var(--fg)
}
.dispatch-card .dc-chip.fail{border-color:rgba(240,113,120,.4);color:var(--red)}
.dispatch-card .dc-note{margin-top:6px;font-size:11px;color:var(--muted)}
.walkthrough{margin:8px 10px;padding:0;border-radius:10px;border:1px solid var(--line);background:var(--panel);overflow:hidden}
.walkthrough .wt-h{padding:10px 12px 6px;font-size:11px;letter-spacing:.04em;color:var(--muted);font-weight:600;display:flex;justify-content:space-between;align-items:center}
.walkthrough .wt-body{padding:0 8px 10px;max-height:200px;overflow:auto}
.walkthrough .wt-step{display:flex;gap:8px;padding:6px 4px;font-size:12px;line-height:1.4;border-left:2px solid transparent;margin-left:4px;padding-left:8px}
.walkthrough .wt-step.on{border-left-color:var(--accent);color:var(--text)}
.walkthrough .wt-step.done{border-left-color:rgba(16,163,127,.35);color:var(--muted)}
.walkthrough .wt-n{flex:0 0 16px;font-size:10px;font-weight:700;color:var(--muted);padding-top:2px;font-family:var(--mono)}
.walkthrough .wt-step.on .wt-n{color:var(--accent)}
.walkthrough .wt-empty{font-size:11px;color:var(--muted);padding:4px 6px;line-height:1.45}
.rail-roster{margin:8px 10px;padding:0;border-radius:10px;border:1px solid var(--line);background:var(--panel);overflow:hidden}
.rail-roster .rr-h{padding:10px 12px 6px;font-size:11px;letter-spacing:.04em;color:var(--muted);font-weight:600;display:flex;justify-content:space-between;align-items:center;gap:8px}
.rail-roster .rr-meta{display:flex;align-items:center;gap:6px;font-weight:500}
.rail-roster .rr-body{padding:0 6px 10px;max-height:260px;overflow:auto}
.rail-roster .rr-empty{font-size:11px;color:var(--muted);padding:6px 8px;line-height:1.4}
.rail-roster .rr-sec{font-size:10px;letter-spacing:.05em;color:var(--muted);padding:8px 8px 4px;font-weight:600;text-transform:uppercase}
.mesh-pill{
  font-size:10px;font-weight:700;letter-spacing:.03em;padding:2px 7px;border-radius:999px;
  border:1px solid rgba(86,212,221,.35);color:var(--cyan);background:rgba(86,212,221,.08)
}
.mesh-pill.off{border-color:var(--line);color:var(--muted);background:transparent}
.sa-count{font-weight:500;color:var(--muted)}
.rail .card{margin:8px 10px;padding:12px 13px;border-radius:11px;border:1px solid var(--line);background:var(--panel)}
.rail .card h3{margin:0 0 9px;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:650}
.rail .grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.rail .grid div{background:var(--bg);border-radius:8px;padding:8px}
.rail .grid span{display:block;font-size:10px;color:var(--muted)}
.rail .grid strong{font-size:14px;font-weight:600}
.rail .btns{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.rail .btns button{border:1px solid var(--line);background:transparent;border-radius:7px;padding:6px 9px;font-size:11px;font-weight:500;color:var(--muted)}
.rail .btns button:hover{color:var(--text);border-color:var(--line2)}
.rail .hint{font-size:11px;color:var(--muted);line-height:1.4}
.svc{padding:8px;border:1px solid var(--line);border-radius:10px;margin-bottom:6px;background:var(--bg)}
.svc .row{display:flex;justify-content:space-between;align-items:center;gap:6px}
.svc b{font-size:12px}
.svc .st{font-size:10px;font-weight:800}
.svc .st.live{color:var(--accent)}
.svc .st.down{color:var(--red)}
.svc .act{display:flex;gap:6px;margin-top:6px}
.svc .act button,.svc .act a{font-size:11px;font-weight:650;padding:5px 8px;border-radius:7px;border:1px solid var(--line);background:var(--panel2);color:var(--text);text-decoration:none}
.hint{font-size:11px;color:var(--muted);line-height:1.45;padding:4px 2px}
.live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--accent);margin-right:5px;animation:pulse 1.2s infinite}
@keyframes pulse{50%{opacity:.35}}
.toast{
  position:fixed;bottom:18px;left:50%;transform:translateX(-50%);
  background:#111;border:1px solid var(--line);color:var(--text);
  padding:10px 16px;border-radius:10px;font-size:13px;font-weight:500;z-index:10000;
  box-shadow:0 8px 28px rgba(0,0,0,.45),0 0 0 1px rgba(255,255,255,.04);
  display:none;max-width:min(480px,92vw);text-align:center
}
.toast.show{display:block}
.toast.ok{border-color:rgba(16,163,127,.4);color:#86efac}
.toast.err{border-color:rgba(240,113,120,.4);color:#fca5a5}
.gate{position:fixed;inset:0;z-index:10050;background:rgba(0,0,0,.9);backdrop-filter:blur(8px);display:none;align-items:center;justify-content:center;padding:20px;pointer-events:auto}
.gate.open{display:flex}
.gate .card{width:100%;max-width:380px;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:26px;box-shadow:0 24px 64px rgba(0,0,0,.55);pointer-events:auto;position:relative;z-index:1}
.gate h2{margin:0 0 6px;font-size:18px;letter-spacing:-.03em;font-weight:600;color:var(--fg)}
.gate p{margin:0 0 14px;color:var(--muted);font-size:13px;line-height:1.45}
.gate label{display:block;font-size:12px;color:var(--muted);margin:10px 0 4px;font-weight:500}
.gate input{width:100%;padding:10px 12px;border-radius:8px;border:1px solid var(--line);background:#0a0a0a;margin-bottom:4px;color:var(--fg)}
.gate .primary{width:100%;margin-top:14px;border:0;border-radius:8px;padding:11px;font-weight:600;background:var(--accent);color:#041;cursor:pointer}
.gate .primary:disabled{opacity:.55;cursor:wait}
.gate .secondary{width:100%;margin-top:8px;border:1px solid var(--line);border-radius:8px;padding:10px;font-weight:500;background:transparent;color:var(--muted);cursor:pointer}
.gate .err{color:#fca5a5;font-size:12px;margin-top:10px;min-height:18px;line-height:1.4;white-space:pre-wrap}
.tabs{display:flex;gap:6px;margin-bottom:10px}
.tabs button{flex:1;border:1px solid var(--line);background:transparent;border-radius:8px;padding:8px;font-size:12px;font-weight:500;color:var(--muted)}
.tabs button.on{color:var(--text);border-color:rgba(16,163,127,.4);background:rgba(16,163,127,.1)}
/* Computer (default) */
body.device-computer .phone-nav{display:none}
body.device-computer .phone-only{display:none!important}
/* scrim only when rail drawer open on narrow computer */
body.device-computer:not(.rail-open) .scrim{display:none!important}
/* Tablet: keep 3-col when wide enough; drawer if cramped */
body.device-tablet .app{grid-template-columns:220px minmax(0,1fr) 280px;grid-template-rows:52px 1fr}
body.device-tablet .phone-nav{display:none}
body.device-tablet .phone-only{display:none!important}
body.device-tablet .menu-btn.rail-toggle{display:inline-flex}
/* Phone: single column chat + drawers + bottom nav */
body.device-phone{overflow:hidden}
body.device-phone .app{
  grid-template-columns:1fr;
  grid-template-rows:52px 1fr 56px;
  height:100dvh;
  padding-bottom:env(safe-area-inset-bottom,0);
}
body.device-phone .top{padding:0 10px;gap:8px}
body.device-phone .top-meta{display:none}
body.device-phone .side{
  position:fixed;left:0;top:52px;bottom:56px;width:min(88vw,320px);z-index:40;
  transform:translateX(-105%);transition:transform .22s ease;
  border-right:1px solid var(--line);border-bottom:0;max-height:none;
  box-shadow:8px 0 30px rgba(0,0,0,.4);
}
body.device-phone.side-open .side{transform:translateX(0)}
body.device-phone .rail{
  position:fixed;right:0;top:52px;bottom:56px;width:min(90vw,340px);z-index:40;
  transform:translateX(105%);transition:transform .22s ease;
  border-left:1px solid var(--line);display:flex;
  box-shadow:-8px 0 30px rgba(0,0,0,.4);
}
body.device-phone.rail-open .rail{transform:translateX(0)}
body.device-phone .main{grid-row:2;min-height:0}
body.device-phone .main-h{padding:8px 12px;flex-wrap:wrap;gap:6px;min-height:auto}
body.device-phone .main-h h1{font-size:14px}
body.device-phone .main-h select{margin-left:0;width:100%;max-width:100%}
body.device-phone .transcript{padding:12px}
body.device-phone .msg .mb.term{max-height:min(40vh,280px);font-size:12.5px}
body.device-phone .msg .mb.prose{font-size:13.5px}
body.device-phone .composer{padding:8px 10px calc(10px + env(safe-area-inset-bottom,0))}
body.device-phone .composer-bar{flex-wrap:wrap}
body.device-phone .composer-hint{display:none}
body.device-phone .box{padding:8px;border-radius:12px}
body.device-phone .box textarea{min-height:44px;font-size:16px} /* prevent iOS zoom */
body.device-phone .box .send{padding:12px 14px;min-height:44px}
body.device-phone .actions button{padding:12px;min-height:48px}
body.device-phone .presets{gap:8px}
body.device-phone .presets button{padding:8px 12px;font-size:12px}
body.device-phone .computer-only{display:none!important}
.phone-nav{
  display:none;grid-column:1;grid-row:3;border-top:1px solid var(--line);
  background:rgba(17,17,19,.96);backdrop-filter:blur(12px);
  align-items:stretch;justify-content:space-around;padding:4px 6px env(safe-area-inset-bottom,4px);
  z-index:50;
}
body.device-phone .phone-nav{display:flex}
.phone-nav button{
  flex:1;border:0;background:transparent;color:var(--muted);font-size:10px;font-weight:700;
  padding:6px 4px;border-radius:10px;display:flex;flex-direction:column;align-items:center;gap:2px;
}
.phone-nav button span{font-size:18px;line-height:1}
.phone-nav button.on{color:var(--accent);background:#0c1f14}
.scrim{display:none;position:fixed;inset:52px 0 56px 0;background:rgba(0,0,0,.45);z-index:30}
body.device-phone.side-open .scrim,body.device-phone.rail-open .scrim{display:block}
.device-chip.phone{color:#7dd3fc;border-color:#0e7490;background:#083344}
.device-chip.tablet{color:#c4b5fd;border-color:#6d28d9;background:#2e1065}
.device-chip.computer{color:#86efac;border-color:#166534;background:#052e16}
.menu-btn{display:none;border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:8px 10px;font-size:14px;font-weight:700}
body.device-phone .menu-btn{display:inline-flex}
/* Right Context rail MUST stay visible on computer (was blank: display:none under 1100px) */
.rail{min-width:240px;display:flex;flex-direction:column;min-height:0;overflow:hidden}
body.device-computer .rail{display:flex!important}
@media(max-width:1100px){
  /* Shrink columns — never hide Context on desktop */
  body.device-computer .app{grid-template-columns:200px minmax(0,1fr) 260px}
  body.device-computer .rail{min-width:220px}
}
@media(max-width:900px){
  body.device-computer .app{grid-template-columns:0 minmax(0,1fr) 240px}
  body.device-computer .side{display:none}
  body.device-computer .menu-btn.side-toggle{display:inline-flex}
  body.device-computer .rail{display:flex!important;min-width:200px}
}
@media(max-width:720px){
  /* Very narrow: rail as overlay drawer, with toggle */
  body.device-computer .app{grid-template-columns:1fr}
  body.device-computer .rail{
    position:fixed;right:0;top:48px;bottom:0;width:min(92vw,320px);z-index:40;
    transform:translateX(105%);transition:transform .2s ease;
    border-left:1px solid var(--line);box-shadow:-8px 0 30px rgba(0,0,0,.45);
    display:flex!important;
  }
  body.device-computer.rail-open .rail{transform:translateX(0)}
  body.device-computer .menu-btn.rail-toggle{display:inline-flex}
  body.device-computer.rail-open .scrim{display:block!important;z-index:30}
}
</style>
</head>
<body class="device-computer">
<div class="boot-splash" id="bootSplash" aria-hidden="false">
  <div class="boot-mark">P</div>
  <div class="boot-title">POCKET</div>
  <div class="boot-sub">Production host co-pilot</div>
  <div class="boot-bar" aria-hidden="true"><i></i></div>
</div>
<div class="scrim" id="scrim" onclick="closeDrawers()"></div>
<div class="browser-layer" id="browserLayer" aria-hidden="true">
  <div class="browser-chrome" role="toolbar" aria-label="POCKET Browser">
    <button type="button" class="b-back" id="btnBrowserDesk" onclick="closeBrowser()" title="Back to POCKET desk">← Desk</button>
    <button type="button" class="b-ico" onclick="browserHistBack()" title="Page back">◀</button>
    <button type="button" class="b-ico" onclick="browserHistFwd()" title="Page forward">▶</button>
    <button type="button" class="b-ico" onclick="browserReload()" title="Reload">↻</button>
    <input id="browserUrl" type="url" placeholder="https://… or /studio" autocomplete="off" spellcheck="false"
      onkeydown="if(event.key==='Enter'){event.preventDefault();browserGo()}"/>
    <button type="button" class="b-go" onclick="browserGo()" title="Load in browser pane">Go</button>
    <button type="button" class="b-ico" onclick="browserOpenNewTab()" title="Open in a new tab">New tab</button>
  </div>
  <div class="browser-quick">
    <button type="button" onclick="browserQuick('/tour')">Overview</button>
    <button type="button" onclick="browserQuick('/studio')">Studio</button>
    <button type="button" onclick="browserQuick('/get')">Get POCKET</button>
    <button type="button" onclick="browserQuick('/developers')">API</button>
    <button type="button" onclick="browserQuick('/download')">Download</button>
    <button type="button" onclick="browserQuick('https://pocket.medinatechlabs.net/')">Public host</button>
  </div>
  <div class="browser-stage">
    <iframe id="browserFrame" title="POCKET Browser" sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox allow-downloads allow-modals"></iframe>
    <div class="browser-blocked" id="browserBlocked">
      <h3>This site won’t load inside the pane</h3>
      <p>POCKET desk stays open. Use <b style="color:var(--fg)">New tab</b> for sites that block embedding — or pick Studio / Overview above (those open in-pane with ← Desk always available).</p>
      <button type="button" class="btn-primary" onclick="browserOpenNewTab()">Open in new tab</button>
    </div>
  </div>
</div>
<div class="app">
  <header class="top">
    <button type="button" class="top-back" id="btnBack" onclick="goAppBack()" title="Back">← Back</button>
    <button type="button" class="menu-btn phone-only side-toggle" id="btnAgents" onclick="toggleSide()" aria-label="Agents">☰</button>
    <div class="brand" onclick="goDeskHome()" style="cursor:pointer" title="POCKET desk"><div class="mark">P</div>POCKET</div>
    <nav class="top-links" aria-label="Product">
      <a href="/tour">Overview</a>
      <a href="/desk" class="on-desk">Desktop</a>
      <a href="/phone">Phone</a>
      <a href="/work">Work Studio</a>
      <a href="/curiosities">Curiosities</a>
      <a href="/developers">API</a>
      <a href="/studio">Studio</a>
      <a href="/forge">Forge</a>
      <a href="/auro/">Auro</a>
      <a href="#" id="navBrowser" onclick="event.preventDefault();openBrowser('/tour')">Browser</a>
    </nav>
    <span class="chip device-chip computer" id="deviceChip" title="Client device">Computer</span>
    <div class="grow"></div>
    <div class="top-meta" id="topMeta"></div>
    <span class="chip" id="userChip">signed out</span>
    <button type="button" class="icon" id="logoutBtn" onclick="doLogout()" title="Sign out" style="display:none">Out</button>
    <button type="button" class="menu-btn rail-toggle" id="btnSys" onclick="toggleRail()" aria-label="AI workspace panel" title="AI summary · previews · subagents · bus">Workspace</button>
  </header>

  <aside class="side" id="sidePanel">
    <div class="side-h"><span>Agents</span><button class="icon" onclick="refreshSessions();refreshStack()" title="Refresh">↻</button></div>
    <div class="stack-card" id="stackCard" title="Lab stack">
      <div class="sk"><b>POCKET</b><span class="on" id="stPocket">desk</span></div>
      <div class="sk"><b>NEXUS</b><span class="off" id="stNexus">…</span></div>
      <div class="sk"><b>MESIE</b><span class="off" id="stMesie">…</span></div>
      <div class="sk"><b>Mesh</b><span class="off" id="stMesh">…</span></div>
    </div>
    <div class="actions">
      <button onclick="newSess('codex')" title="Codex coding agent"><b>Codex</b><small>Code on this host</small></button>
      <button onclick="newSess('grok')"><b>Grok</b><small>Code &amp; research</small></button>
      <button onclick="newSess('wsl_native')" title="Native WSL Linux agent — first-class host hands"><b>WSL</b><small>Native Linux · ~/pocket-wsl</small></button>
      <button onclick="newSess('build')" title="Multi-agent ship loop — surpass Emergent"><b>Build</b><small>Plan→code→test→ship loop</small></button>
      <button onclick="newSess('dual')" title="Cortex dialogue + silent Subcortex"><b>Dual loop</b><small>Talk while world works</small></button>
      <button onclick="newSess('wiki')" title="Infinite Wiki hierarchical codebase"><b>Infinite Wiki</b><small>Profile cards · line slices</small></button>
      <button onclick="newSess('swarm')" title="Always-on multi-agent swarm"><b>Swarm</b><small>Always-on pulses</small></button>
      <button onclick="newSess('use_case')" title="Real product use cases"><b>Use cases</b><small>12 Emergent+ pipelines</small></button>
      <button onclick="newSess('custom_agent')" title="Custom agents with tools + sub-agents"><b>Custom agent</b><small>Builder · tools · subs</small></button>
      <button type="button" onclick="location.href='/work'"><b>Work Studio</b><small>Types · loops · design</small></button>
      <button type="button" onclick="location.href='/curiosities'"><b>Curiosities</b><small>Dream · Duel · Capsules</small></button>
      <button onclick="newSess('duel')" title="Two agents propose, judge picks"><b>Duel</b><small>FORGE vs AESTHETE</small></button>
      <button onclick="newSess('dream')" title="Idle consolidation dreams"><b>Dream</b><small>Night consolidator</small></button>
      <button onclick="activateNovae('GROK_NOVAE')" title="Grok Novae hands in platform workspace"><b>Grok Novae</b><small>Hands · browser + day ops</small></button>
      <button onclick="activateNovae('CODEX_NOVAE')" title="Codex Novae hands in platform workspace"><b>Codex Novae</b><small>Hands · code + forge</small></button>
      <button onclick="newSess('claude')"><b>Claude</b><small>If installed</small></button>
      <button onclick="newSess('offload')" title="Queue real-world work; free the chat"><b>Offload</b><small>Real-world queue · proof packs</small></button>
      <button onclick="newSess('cowork')" title="Desktop embody · demos · screen record"><b>Cowork</b><small>Desk + record · not deep code</small></button>
      <button onclick="newSess('git')" title="Sovereign git vault inside POCKET"><b>Git</b><small>Vault repos · zip export</small></button>
      <button onclick="newSess('plan')"><b>Plan</b><small>Planning only</small></button>
      <button onclick="newSess('nexus')"><b>NEXUS</b><small>MERIDIAN intelligence</small></button>
      <button onclick="newSess('mesie')"><b>MESIE</b><small>Spectral · colony compute</small></button>
      <button onclick="newSess('auro')"><b>Auro14B</b><small>Native LMR · RO14B</small></button>
      <button type="button" class="more-btn" onclick="toggleMoreAgents()">More agents ▾</button>
      <div class="more-agents" id="moreAgents">
        <button onclick="newSess('archon')"><b>ARCHON</b><small>Orchestrator</small></button>
        <button type="button" onclick="openBrowser('/tour')"><b>Browser</b><small>In-app pane · ← Desk always</small></button>
        <button onclick="newSess('browser')"><b>Browser agent</b><small>Edge · X · Copilot</small></button>
        <button onclick="newSess('desktop')"><b>Desktop</b><small>Open apps · MS host</small></button>
        <button onclick="newSess('web')"><b>Web</b><small>Search · fetch</small></button>
        <button onclick="newSess('capture')"><b>Capture</b><small>Screenshot</small></button>
        <button onclick="newSess('repos')"><b>Repos</b><small>Git · GitHub</small></button>
        <button onclick="newSess('guppy')"><b>Guppy</b><small>Local fish agent</small></button>
        <button onclick="newSess('agent')"><b>Doer</b><small>≤10 silent steps</small></button>
        <button onclick="newSess('copilot')"><b>Copilot</b><small>Windows</small></button>
        <button onclick="newSess('handoff')"><b>Handoff</b><small>Defer plan</small></button>
        <button class="admin-only" onclick="newSess('term')"><b>Term</b><small>Host shell (admin)</small></button>
        <button class="admin-only" onclick="newSess('shell')"><b>Shell</b><small>Host PS (admin)</small></button>
      </div>
    </div>
    <div class="toolrow">
      <label class="btn" for="fileInput">Upload</label>
      <input id="fileInput" type="file" multiple />
      <div class="hint" id="uploadNote"></div>
    </div>
    <div class="side-h" style="padding-top:4px"><span>Sessions</span></div>
    <div class="slist" id="slist"><div class="hint">Sign in, then start NEXUS, MESIE, Codex, or Term. Sessions appear here.</div></div>
  </aside>

  <section class="main">
    <div class="main-h">
      <h1 id="mainTitle">Select an agent</h1>
      <span class="tag" id="mainTag">—</span>
      <span class="tag" id="mainWs">workspace</span>
      <select id="wsSelect"></select>
      <div class="grow"></div>
      <button type="button" class="icon sess-ctl" id="btnStop" onclick="stopActiveSession()" title="Stop running work (keep transcript)" style="display:none">Stop</button>
      <button type="button" class="icon sess-ctl" id="btnEnd" onclick="endActiveSession()" title="End session (stop work + close tab)" style="display:none">End</button>
    </div>
    <div class="transcript" id="transcript">
      <div class="empty">
        <div class="mark">P</div>
        <h2>First-class host co-pilot</h2>
        <p>Ship on this machine. Cortex talks · Subcortex works · Infinite Wiki scales code · Swarm stays on.</p>
        <p style="margin-top:8px;font-size:12px;color:var(--muted)"><kbd>@</kbd> dispatch · <kbd>/</kbd> actions · right rail = workspace</p>
        <div class="empty-actions">
          <button type="button" onclick="newSess('codex')">Codex</button>
          <button type="button" onclick="newSess('grok')">Grok</button>
          <button type="button" onclick="newSess('wiki')">Infinite Wiki</button>
          <button type="button" onclick="newSess('build')">Build</button>
          <button type="button" onclick="newSess('dual')">Dual loop</button>
          <button type="button" onclick="newSess('swarm')">Swarm</button>
          <button type="button" onclick="activateNovae('CODEX_NOVAE')">Codex Novae</button>
          <button type="button" onclick="activateNovae('GROK_NOVAE')">Grok Novae</button>
          <button type="button" onclick="location.href='/work'">Work Studio</button>
          <button type="button" onclick="location.href='/curiosities'">Curiosities</button>
          <button type="button" onclick="newSess('duel')">Duel</button>
          <button type="button" onclick="newSess('dream')">Dream</button>
          <button type="button" onclick="location.href='/phone'">Phone</button>
        </div>
      </div>
    </div>
    <div class="composer">
      <div class="composer-inner">
      <div class="presets" id="presets"></div>
      <div class="slash-menu" id="slashMenu" role="listbox" aria-label="Actions"></div>
      <div class="mention-menu" id="mentionMenu" role="listbox" aria-label="Mention agents"></div>
      <div class="box">
        <button class="iconbtn" id="micBtn" type="button" title="Voice to text" onclick="toggleMic()" disabled aria-label="Microphone">🎙</button>
        <textarea id="input" placeholder="Message…  @DESIGN @FORGE @ARCHON  /actions" disabled rows="2"></textarea>
        <button class="send" id="sendBtn" disabled onclick="sendMsg()">Send</button>
      </div>
      <div class="composer-bar">
        <select id="modelPick" class="model-pick" title="Agent / model" aria-label="Agent model">
          <option value="">Session agent</option>
          <option value="codex">Codex</option>
          <option value="grok">Grok</option>
          <option value="claude">Claude</option>
          <option value="plan">Plan</option>
          <option value="build">Build loop</option>
          <option value="wiki">Infinite Wiki</option>
          <option value="use_case">Use cases</option>
          <option value="custom_agent">Custom agent</option>
          <option value="archon">ARCHON</option>
          <option value="guppy">GUPPY</option>
          <option value="browser">Browser</option>
          <option value="nexus">NEXUS</option>
          <option value="mesie">MESIE</option>
          <option value="auro">Auro14B</option>
        </select>
        <span class="composer-hint"><kbd>@</kbd> · <kbd>/</kbd> · <kbd>Ctrl</kbd>+<kbd>Enter</kbd></span>
      </div>
      </div>
    </div>
  </section>

  <aside class="rail" id="contextRail" aria-label="AI workspace panel">
    <div class="side-h">
      <span>AI workspace</span>
      <span style="display:flex;gap:4px;align-items:center">
        <button class="icon" onclick="refreshAiWorkspace();pollSubagents();connectAll();refreshStack()" title="Refresh workspace">↻</button>
        <button class="icon rail-toggle" onclick="toggleRail()" title="Close" style="display:none" id="railCloseBtn">✕</button>
      </span>
    </div>
    <div style="flex:1;overflow:auto;padding:0 0 8px">
      <div class="ai-sum" id="aiSumCard">
        <h3>Session summary</h3>
        <div class="body" id="aiSummary">Auto-updates as you work · no re-scan tax for agents</div>
        <div class="meta" id="aiSumMeta">token saver · CONTEXT.md injected each turn</div>
      </div>
      <div class="ai-prev" id="aiPrevCard">
        <h3>Previews</h3>
        <div id="aiPreviews"><div class="hint" style="font-size:11px;color:var(--muted)">Docs · agent output · local files appear here</div></div>
        <div class="tree" id="aiTree" style="margin-top:8px"></div>
      </div>
      <div class="ai-bus" id="aiBusCard">
        <h3>Agent bus · hashed</h3>
        <div id="aiBus"><div class="hint" style="font-size:11px;color:var(--muted)">Mesh envelopes · swarm notes · freq-coding</div></div>
      </div>
      <div class="ai-sum" id="offloadCard">
        <h3>Offload · real world</h3>
        <div class="body" id="offloadList" style="max-height:100px">Queue multi-step desk work · free chat turn</div>
        <div class="meta"><button type="button" class="icon" onclick="refreshOffload()" style="border:1px solid var(--line);padding:2px 8px">Refresh tickets</button></div>
      </div>
      <div class="walkthrough" id="walkthrough">
        <div class="wt-h"><span>Walkthrough</span><span id="wtCount" style="font-weight:500;color:var(--muted)">0</span></div>
        <div class="wt-body" id="walkthroughBody">
          <div class="wt-empty">Steps appear as agents work · @dispatch fills this</div>
        </div>
      </div>
      <div class="rail-roster">
        <div class="rr-h">
          <span>Subagents · activate with @</span>
          <span class="rr-meta">
            <span class="mesh-pill off" id="meshDrive" title="Mesh disk root">E: mesh</span>
            <span class="sa-count" id="saCount" title="Mesh agent count">0</span>
          </span>
        </div>
        <div class="rr-body" id="subagentRoster">
          <div class="rr-empty">DESIGN · FORGE · SENTINEL · RESEARCH · SHIP — stay here, not in the chat drop</div>
        </div>
      </div>
      <div class="card">
        <h3>Status</h3>
        <div class="grid">
          <div><span>Heart</span><strong id="heartLabel">—</strong></div>
          <div><span>Stream</span><strong id="uStream">0</strong></div>
          <div><span>Tokens</span><strong id="uTok">0</strong></div>
          <div><span>POCK</span><strong id="uBal">—</strong></div>
        </div>
        <div class="hint" id="thought" style="margin-top:8px"></div>
      </div>
      <div class="card">
        <h3>Vision</h3>
        <img id="liveVision" alt="live" style="width:100%;border-radius:8px;border:1px solid var(--line);margin-top:2px;min-height:72px;background:#0a0a0a;object-fit:contain"/>
        <div class="hint" id="liveVisionMeta" style="margin-top:4px"></div>
        <div class="btns">
          <button type="button" onclick="fullPageRender()">Full page</button>
          <button type="button" onclick="visionObserve()">Understand</button>
          <button type="button" onclick="streamToggle()">Stream</button>
        </div>
        <pre id="visionOut" style="display:none;margin-top:6px;max-height:90px;overflow:auto;font-size:10px;background:#0a0a0a;padding:6px;border-radius:8px;color:var(--muted);white-space:pre-wrap"></pre>
      </div>
      <div class="card">
        <h3>Run</h3>
        <textarea id="orchChat" rows="2" style="width:100%;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px;resize:vertical;font-size:12px;color:var(--text)" placeholder="e.g. screenshot and sense page"></textarea>
        <div class="btns">
          <button type="button" onclick="orchChatSend(false)">Run</button>
          <button type="button" onclick="orchChatSend(true)">Record</button>
        </div>
        <pre id="orchOut" style="display:none;margin-top:6px;max-height:100px;overflow:auto;font-size:10px;background:#0a0a0a;padding:6px;border-radius:8px;color:#86efac;white-space:pre-wrap"></pre>
      </div>
      <div class="card" style="display:none">
        <h3>Activity</h3>
        <div id="liveActions" style="max-height:140px;overflow:auto;font-size:11px;margin-top:2px;font-family:var(--mono);line-height:1.45;color:var(--muted)"></div>
      </div>
      <div class="card">
        <h3>API</h3>
        <div class="hint">Keys for Grok, Codex, Claude, apps</div>
        <div class="btns">
          <a class="icon" href="/developers" style="text-decoration:none;border:1px solid var(--line);padding:6px 9px;border-radius:7px">Developers</a>
          <button type="button" onclick="createApiKey()">New key</button>
          <button type="button" onclick="loadAiCatalog()">Catalog</button>
        </div>
        <pre id="aiOut" style="display:none;margin-top:6px;max-height:120px;overflow:auto;font-size:10px;background:#0a0a0a;padding:6px;border-radius:8px;color:var(--muted);white-space:pre-wrap"></pre>
      </div>
      <div class="card" style="display:none">
        <div id="liveList"></div>
        <div id="deployList"></div>
        <pre id="deployLog"></pre>
        <div id="pubUrl"></div>
        <pre id="doctorOut"></pre>
        <button type="button" onclick="pixelText()" id="pixelTextBtn"></button>
        <button type="button" onclick="spawnDynamic()" id="spawnBtn"></button>
        <button type="button" onclick="runCampaign()" id="campBtn"></button>
        <button type="button" onclick="runDoctor()" id="docBtn"></button>
        <button type="button" onclick="deployKind('static')"></button>
        <button type="button" onclick="deployKind('npm')"></button>
        <button type="button" onclick="deployKind('python')"></button>
        <button type="button" onclick="quickDesktop()"></button>
        <button type="button" onclick="quickWeb()"></button>
        <button type="button" onclick="quickNexus()"></button>
      </div>
      <div class="card phone-only">
        <h3>Device</h3>
        <div class="hint" id="deviceDetail">Detecting…</div>
      </div>
    </div>
  </aside>

  <nav class="phone-nav" id="phoneNav" aria-label="Phone navigation">
    <button type="button" id="navAgents" onclick="toggleSide()"><span>☰</span>Agents</button>
    <button type="button" class="on" id="navChat" onclick="closeDrawers();focusChat()"><span>💬</span>Chat</button>
    <button type="button" id="navSys" onclick="toggleRail()"><span>⚙</span>System</button>
  </nav>
</div>
<div class="toast" id="toast"></div>

<div class="gate" id="loginGate" role="dialog" aria-modal="true" aria-labelledby="loginTitle">
  <div class="card">
    <h2 id="loginTitle">Sign in · POCKET</h2>
    <p id="loginBlurb"><b style="color:var(--fg)">Company host</b> · ItsNotAI Labs / Medina Tech Labs. <b style="color:var(--fg)">Owner</b> = ACCESS.txt. <b style="color:var(--fg)">Team seats</b> use their own username/password — never the owner login.</p>
    <div class="tabs">
      <button type="button" class="on" id="tabLogin" onclick="setAuthTab('login')">Sign in</button>
      <button type="button" id="tabReg" onclick="setAuthTab('register')">Create my seat</button>
    </div>
    <div id="loginPane">
      <form id="loginForm" autocomplete="on" onsubmit="event.preventDefault();doLogin();return false;">
      <label for="loginUser">Your username</label>
      <input id="loginUser" name="username" value="pocket" placeholder="owner: pocket" autocomplete="username"/>
      <label for="loginPass">Your password</label>
      <input id="loginPass" name="password" type="password" autocomplete="current-password" placeholder="from ACCESS.txt"/>
      <label style="display:flex;gap:8px;align-items:center;margin-top:8px"><input type="checkbox" id="loginRemember" checked/> Remember session on this device</label>
      <button class="primary" id="loginBtn" type="submit">Continue</button>
      </form>
      <button class="secondary" id="localUnlockBtn" type="button" style="display:none" title="Localhost only">Unlock this PC (no password)</button>
    </div>
    <div id="regPane" style="display:none">
      <p style="font-size:12px;color:var(--muted);margin:0 0 10px;line-height:1.45">This creates <b style="color:var(--fg)">your own</b> account. You do not log into the owner. Paste the <b style="color:var(--fg)">pk_seat_…</b> key the owner minted for you.</p>
      <label>Seat invite key</label>
      <input id="regInvite" placeholder="pk_seat_… (not the owner password)"/>
      <label>Choose username</label>
      <input id="regUser" autocomplete="username" placeholder="your name"/>
      <label>Choose password (min 8)</label>
      <input id="regPass" type="password" autocomplete="new-password"/>
      <label>Display name</label>
      <input id="regDisplay" placeholder="optional"/>
      <label style="display:flex;gap:8px;align-items:flex-start;margin-top:10px;font-size:12px;color:var(--muted);font-weight:500">
        <input type="checkbox" id="regTerms" style="margin-top:3px"/>
        <span>I accept the <a href="/v1/legal" target="_blank" rel="noopener">terms</a>. Market seats get <b>your</b> local sandbox + virtual files — never the founder’s personal disk.</span>
      </label>
      <button class="primary" id="regBtn" type="button">Create my seat</button>
    </div>
    <div class="err" id="loginErr"></div>
  </div>
</div>

<script>
const $=id=>document.getElementById(id);
const MODE_COLOR={codex:'#22c55e',claude:'#f59e0b',shell:'#3b82f6',wsl:'#8b5cf6',wsl_native:'#8b5cf6',linux:'#8b5cf6',ask:'#f59e0b',plan:'#eab308',grok:'#06b6d4',handoff:'#a1a1aa',term:'#34d399',desktop:'#a78bfa',web:'#38bdf8',nexus:'#f472b6',mesie:'#a78bfa',auro:'#fbbf24',auro14b:'#fbbf24',ro14b:'#fbbf24',him:'#fbbf24',agent:'#fb7185',doer:'#fb7185',guppy:'#38bdf8',browser:'#f97316',capture:'#a3e635',repos:'#94a3b8',copilot:'#818cf8',archon:'#f43f5e',alpha:'#f43f5e',workers:'#e11d48',novae_grok:'#a78bfa',novae_codex:'#34d399',novae:'#a78bfa',offload:'#fbbf24',build:'#f472b6',ship:'#f472b6',use_case:'#fb7185',emergent:'#f472b6',loop:'#f472b6',custom_agent:'#c084fc'};
const LATIN_WORKERS=['ARCHON','HYDRA','SCRUTATOR','SCRIPTOR','PORTARIUS','OCULUS','SPECULUM','REPOSITOR','CONSILIARIUS','TABELLARIUS','NAVIGATOR','GUPPY'];
const MESH_AGENTS=['DESIGN','AESTHETE','LAYOUT','MOTION','FORGE_HEADLESS','SENTINEL_HEADLESS','RESEARCH_HEADLESS','SHIP_HEADLESS','GROK_NOVAE','CODEX_NOVAE'];
const MESH_AGENT_ROLES={
  DESIGN:'UI + product craft',
  AESTHETE:'Visual taste',
  LAYOUT:'Structure + spacing',
  MOTION:'Motion + feedback',
  FORGE_HEADLESS:'Build / test / package',
  SENTINEL_HEADLESS:'Security + audit',
  RESEARCH_HEADLESS:'Research packs',
  SHIP_HEADLESS:'Release / beta ship',
  FORGE:'→ FORGE_HEADLESS',
  SENTINEL:'→ SENTINEL_HEADLESS',
  RESEARCH:'→ RESEARCH_HEADLESS',
  SHIP:'→ SHIP_HEADLESS',
  DESIGNER:'→ DESIGN',
  UI:'→ DESIGN',
  UX:'→ AESTHETE',
  CSS:'→ LAYOUT',
  ANIM:'→ MOTION'
};
const MENTION_ALIASES=['DESIGN','DESIGNER','UI','UX','AESTHETE','LAYOUT','MOTION','CSS','ANIM','FORGE','FORGE_HEADLESS','SENTINEL','SENTINEL_HEADLESS','RESEARCH','RESEARCH_HEADLESS','SHIP','SHIP_HEADLESS'];
let sessions=[], activeId=null, pollTimer=null, status=null, micRec=null, micOn=false, authTab='login';
window.__pocketBootAt=Date.now();
let liveSeq=0, liveTimer=null, subagentTimer=null;
let subagentState=[], subagentCatalog=[], liveAgentHits={}, walkthroughSteps=[];
let meshInfo={agent_count:0, mesh_root:'', drive:''};
let DEVICE={kind:'computer',label:'Computer',remote:false};
let ME={user:'',role:'member',display:''};
const SLASH_ACTIONS=[
  {cmd:'help', label:'Show actions', fill:'/help'},
  {cmd:'workers', label:'List Latin workers', fill:'workers'},
  {cmd:'screenshot', label:'Capture screen (OCULUS)', fill:'@OCULUS screenshot'},
  {cmd:'status', label:'Agent status', fill:'status'},
  {cmd:'demo', label:'Run focused demo', fill:'@ARCHON focused demo'},
  {cmd:'sense', label:'Sense page (vision)', fill:'@OCULUS sense page'},
  {cmd:'design', label:'Dispatch DESIGN', fill:'@DESIGN '},
  {cmd:'forge', label:'Dispatch FORGE headless', fill:'@FORGE_HEADLESS '},
  {cmd:'ship', label:'Dispatch SHIP headless', fill:'@SHIP_HEADLESS '},
];
function mentionRoster(){
  const names=new Set([...LATIN_WORKERS, ...MESH_AGENTS, ...MENTION_ALIASES]);
  (subagentCatalog||[]).forEach(w=>{
    const n=String(w.name||w.id||'').toUpperCase();
    if(n && n.length>=2) names.add(n);
  });
  return Array.from(names).sort();
}
function mentionKind(name){
  const n=String(name||'').toUpperCase();
  if(['DESIGN','DESIGNER','UI','UX','AESTHETE','LAYOUT','MOTION','CSS','ANIM'].includes(n)) return 'design';
  if(n.includes('HEADLESS')||['FORGE','SENTINEL','RESEARCH','SHIP'].includes(n)) return 'headless';
  if(LATIN_WORKERS.includes(n)) return 'latin';
  return 'mesh';
}
function mentionLabel(name){
  const n=String(name||'').toUpperCase();
  return MESH_AGENT_ROLES[n]||(LATIN_WORKERS.includes(n)?'Latin worker':'Mesh agent');
}

function toggleMoreAgents(){
  const el=$('moreAgents'); if(!el) return;
  el.classList.toggle('open');
}
function toast(msg, kind){
  const t=$('toast'); if(!t) return;
  t.textContent=String(msg||'');
  t.classList.remove('ok','err');
  if(kind==='ok'||kind==='err') t.classList.add(kind);
  t.classList.add('show');
  clearTimeout(toast._t);
  toast._t=setTimeout(()=>{ t.classList.remove('show','ok','err'); }, 3200);
}

/** Detect phone vs computer (and tablet). UA + viewport + touch + pointer. */
function detectDevice(){
  const ua=navigator.userAgent||'';
  const w=Math.min(window.innerWidth||0, screen.width||0)||window.innerWidth||0;
  const h=window.innerHeight||0;
  const touch=('ontouchstart' in window)||(navigator.maxTouchPoints>0);
  let coarse=false;
  try{ coarse=!!window.matchMedia && window.matchMedia('(pointer: coarse)').matches; }catch(_){}
  let standalone=false;
  try{ standalone=!!(window.navigator.standalone||window.matchMedia('(display-mode: standalone)').matches); }catch(_){}
  const platform=navigator.platform||navigator.userAgentData&&navigator.userAgentData.platform||'';
  const uaPhone=/Mobile|Android.*Mobile|iPhone|iPod|webOS|BlackBerry|IEMobile|Opera Mini|Windows Phone/i.test(ua);
  const uaTablet=/iPad|Android(?!.*Mobile)|Tablet|Kindle|Silk/i.test(ua);
  // iPadOS 13+ often reports MacIntel with touch
  const iPadDesktopUA=/Macintosh/i.test(ua) && touch && navigator.maxTouchPoints>1;

  let kind='computer';
  if(uaPhone || (w>0 && w<=720 && (touch||coarse) && !/Windows NT|CrOS/i.test(ua))) kind='phone';
  else if(uaTablet || iPadDesktopUA || (w>720 && w<=1024 && (touch||coarse) && !/Windows NT/i.test(ua))) kind='tablet';
  else kind='computer';

  // Narrow desktop browser window stays computer (mouse primary)
  if(kind==='phone' && !uaPhone && !iPadDesktopUA && !coarse && w>0 && w<=720) kind='computer';

  const label={phone:'Phone',tablet:'Tablet',computer:'Computer'}[kind];
  DEVICE={
    kind, label, remote: kind==='phone'||kind==='tablet',
    width:w, height:h, touch, coarse, standalone,
    platform: String(platform||'').slice(0,80),
    ua: String(ua).slice(0,200),
    source:'client',
    at: Date.now()
  };
  try{ sessionStorage.setItem('pocket_device', JSON.stringify(DEVICE)); }catch(_){}
  return DEVICE;
}

function applyDevice(){
  const d=DEVICE||detectDevice();
  document.body.classList.remove('device-phone','device-tablet','device-computer','side-open','rail-open');
  document.body.classList.add('device-'+d.kind);
  const chip=$('deviceChip');
  if(chip){
    chip.textContent=d.label;
    chip.className='chip device-chip '+d.kind;
    chip.title=d.kind+' · '+d.width+'x'+d.height+(d.touch?' · touch':'')+(d.remote?' · remote':' · local UI');
  }
  const det=$('deviceDetail');
  if(det){
    det.innerHTML=`<b>${d.label}</b> · ${d.width}×${d.height}<br>`+
      `${d.remote?'Remote UI (jobs still run on the host PC)':'Computer UI'}<br>`+
      `touch=${!!d.touch} coarse=${!!d.coarse} PWA=${!!d.standalone}`;
  }
  const blurb=$('loginBlurb');
  if(blurb){
    blurb.textContent=d.kind==='phone'
      ? 'Phone remote desk. You control agents on the host PC. Password required.'
      : (d.kind==='tablet'
        ? 'Tablet remote desk for your PC. Password required on public access.'
        : 'Multi-agent desk for your PC. Password required on public access.');
  }
  document.title=d.kind==='phone'?'POCKET · Phone':(d.kind==='tablet'?'POCKET · Tablet':'POCKET');
  updatePhoneNav();
}

function toggleSide(){
  if(DEVICE.kind!=='phone') return;
  document.body.classList.toggle('side-open');
  document.body.classList.remove('rail-open');
  updatePhoneNav();
}
function toggleRail(){
  // Phone + narrow computer: drawer; wide computer rail is always on-screen
  document.body.classList.toggle('rail-open');
  document.body.classList.remove('side-open');
  updatePhoneNav();
  const close=$('railCloseBtn');
  if(close) close.style.display=document.body.classList.contains('rail-open')?'inline-flex':'none';
}
function closeDrawers(){
  document.body.classList.remove('side-open','rail-open');
  updatePhoneNav();
}
function focusChat(){
  closeDrawers();
  try{ $('input').focus(); }catch(_){}
}
function updatePhoneNav(){
  if(DEVICE.kind!=='phone') return;
  const side=document.body.classList.contains('side-open');
  const rail=document.body.classList.contains('rail-open');
  const a=$('navAgents'), c=$('navChat'), s=$('navSys');
  if(a) a.classList.toggle('on', side);
  if(s) s.classList.toggle('on', rail);
  if(c) c.classList.toggle('on', !side && !rail);
}

function authHeaders(){
  const h={'Content-Type':'application/json'};
  const tok=sessionStorage.getItem('pocket_token')||localStorage.getItem('pocket_token')||'';
  const u=sessionStorage.getItem('pocket_user')||localStorage.getItem('pocket_user')||'';
  // Prefer session token only (production — no password in storage)
  if(tok){
    h['X-Pocket-Token']=tok;
    h['Authorization']='Bearer '+tok;
  }
  // Tell server: phone | tablet | computer
  h['X-Pocket-Device']=(DEVICE&&DEVICE.kind)||'computer';
  if(u) h['X-Pocket-User']=u;
  return h;
}
async function api(path, opts){
  opts=opts||{};
  opts.headers=Object.assign({}, authHeaders(), opts.headers||{});
  let r;
  try{
    r=await fetch(path, opts);
  }catch(net){
    const err=new Error('Network: '+(net&&net.message||'Failed to fetch')+' — is host on :8787?');
    err.code='network';
    throw err;
  }
  if(r.status===401){
    const err=new Error('Login required');
    err.code='auth';
    // Don't thrash gate on every background poll — only clear session on explicit auth fail
    // (boot / doLogout decide when to show gate)
    throw err;
  }
  if(r.status===429){ const e=new Error('Too many failed logins'); e.code='rate'; throw e; }
  if(!r.ok){
    const t=(await r.text()).slice(0,300);
    const e=new Error(t||('HTTP '+r.status));
    e.code='http';
    e.status=r.status;
    throw e;
  }
  const ct=r.headers.get('content-type')||'';
  if(ct.includes('application/json')) return r.json();
  return {text: await r.text()};
}
function setLoginErr(msg){
  const el=$('loginErr');
  if(el) el.textContent=msg||'';
  if(msg) try{ toast(msg,'err'); }catch(_){}
}
function showGate(){
  dismissBootSplash(true);
  const g=$('loginGate');
  if(!g) return;
  g.classList.add('open');
  g.style.display='flex';
  // Localhost: offer one-click unlock
  const local=location.hostname==='127.0.0.1'||location.hostname==='localhost';
  const lub=$('localUnlockBtn');
  if(lub) lub.style.display=local?'block':'none';
  const u=$('loginUser');
  if(u && !u.value) u.value='pocket';
  try{ ($('loginPass')||u).focus(); }catch(_){}
}
function hideGate(){
  const g=$('loginGate');
  if(!g) return;
  g.classList.remove('open');
  g.style.display='none';
}
function setAuthTab(t){
  authTab=t;
  const tl=$('tabLogin'), tr=$('tabReg'), lp=$('loginPane'), rp=$('regPane');
  if(tl) tl.classList.toggle('on', t==='login');
  if(tr) tr.classList.toggle('on', t==='register');
  if(lp) lp.style.display=t==='login'?'block':'none';
  if(rp) rp.style.display=t==='register'?'block':'none';
  setLoginErr('');
}
function storeSession(user, token, rem){
  // Always keep sessionStorage; persist to localStorage when remembered (default true)
  try{
    sessionStorage.setItem('pocket_user', user||'');
    sessionStorage.setItem('pocket_token', token||'');
    sessionStorage.removeItem('pocket_pass');
    localStorage.removeItem('pocket_pass');
    const persist = rem!==false;
    if(persist && token){
      localStorage.setItem('pocket_user', user||'');
      localStorage.setItem('pocket_token', token||'');
    }
  }catch(e){ console.warn('storeSession', e); }
}
async function finishLogin(u, token){
  storeSession(u, token, true);
  hideGate();
  dismissBootSplash(true);
  try{
    await boot({afterLogin:true});
    toast('Signed in as '+u,'ok');
  }catch(bootErr){
    hideGate();
    toast('Signed in — desk loading…','ok');
    console.warn('boot after login', bootErr);
  }
}
async function tryDesktopAutoLogin(force){
  // Electron / localhost only — host issues operator session without typing password
  if(location.hostname!=='127.0.0.1' && location.hostname!=='localhost') return false;
  if(!force && (sessionStorage.getItem('pocket_token')||localStorage.getItem('pocket_token'))) return false;
  try{
    const r=await fetch('/v1/auth/desktop',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    if(!r.ok) return false;
    const j=await r.json();
    if(!j.ok||!j.token) return false;
    await finishLogin((j.user&&j.user.user)||'pocket', j.token);
    return true;
  }catch(_){ return false; }
}
async function doLogin(){
  try{
    const uEl=$('loginUser'), pEl=$('loginPass'), btn=$('loginBtn');
    const u=(uEl&&uEl.value||'').trim();
    const p=(pEl&&pEl.value||'');
    if(!u||!p){
      setLoginErr('Username and password required.\nOwner: user pocket + password from %USERPROFILE%\\.pocket\\ACCESS.txt');
      return;
    }
    setLoginErr('Signing in…');
    if(btn) btn.disabled=true;
    const r=await fetch('/v1/auth/login',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({user:u,password:p,username:u})
    });
    let j={};
    try{ j=await r.json(); }catch(_){ j={ok:false,error:'Login returned non-JSON (HTTP '+r.status+')'}; }
    if(!r.ok||!j.ok){
      // Localhost fallback: desktop unlock if password login fails
      if((location.hostname==='127.0.0.1'||location.hostname==='localhost')){
        const auto=await tryDesktopAutoLogin(true);
        if(auto){ if(btn) btn.disabled=false; return; }
      }
      setLoginErr(j.error||('Login failed HTTP '+r.status)+'\nTry owner user "pocket" + ACCESS.txt password, or Unlock this PC.');
      if(btn) btn.disabled=false;
      return;
    }
    if(!j.token){ setLoginErr('Server returned no session token'); if(btn) btn.disabled=false; return; }
    await finishLogin(u, j.token);
    if(btn) btn.disabled=false;
  }catch(e){
    setLoginErr(String(e.message||e)+' — host not reachable on :8787. Run Ensure-POCKET-Up / Start-POCKET.');
    const btn=$('loginBtn'); if(btn) btn.disabled=false;
  }
}
async function doRegister(){
  try{
    if(!$('regTerms')||!$('regTerms').checked){
      $('loginErr').textContent='Accept the terms to register';
      return;
    }
    const j=await fetch('/v1/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      invite:$('regInvite').value.trim(),
      user:$('regUser').value.trim(),
      password:$('regPass').value,
      display:$('regDisplay').value.trim(),
      accepted_terms:true
    })}).then(r=>r.json());
    if(!j.ok){ $('loginErr').textContent=j.error||'Register failed'; return; }
    storeSession(j.user, j.token||'', true);
    hideGate();
    await boot();
    toast('Account created — welcome');
  }catch(e){ $('loginErr').textContent=String(e.message||e); }
}
async function doLogout(){
  try{
    await api('/v1/auth/logout',{method:'POST',body:JSON.stringify({})});
  }catch(_){}
  sessionStorage.clear();
  localStorage.removeItem('pocket_token');
  localStorage.removeItem('pocket_pass');
  ME={user:'',role:'member',display:''};
  showGate();
  toast('Signed out');
}
function applyRoleUI(){
  const admin = (ME.role||'')==='admin';
  document.querySelectorAll('.admin-only').forEach(el=>{
    el.style.display = admin ? '' : 'none';
  });
  const lb=$('logoutBtn');
  if(lb) lb.style.display = ME.user ? 'inline-flex' : 'none';
  if($('userChip')) $('userChip').textContent = ME.user ? ((ME.display||ME.user)+' · '+ME.role) : 'signed out';
}
async function boot(opts){
  opts=opts||{};
  ensureLivePoll();
  detectDevice();
  applyDevice();
  try{ localStorage.removeItem('pocket_pass'); sessionStorage.removeItem('pocket_pass'); }catch(_){}
  // Mirror localStorage → sessionStorage so one tab stays signed in
  if(!sessionStorage.getItem('pocket_token') && localStorage.getItem('pocket_token')){
    sessionStorage.setItem('pocket_token', localStorage.getItem('pocket_token'));
    sessionStorage.setItem('pocket_user', localStorage.getItem('pocket_user')||'');
  }
  let has = sessionStorage.getItem('pocket_token')||localStorage.getItem('pocket_token');
  if(!has && !opts.afterLogin){
    // Desktop/localhost: auto session so Electron feels like a normal app
    const auto=await tryDesktopAutoLogin();
    if(auto) return;
    has = sessionStorage.getItem('pocket_token')||localStorage.getItem('pocket_token');
  }
  if(!has){ showGate(); dismissBootSplash(); return; }

  // Auth check only — 401 returns to gate; anything else keeps session
  try{
    const me=await api('/v1/auth/me',{method:'POST',body:JSON.stringify({})});
    if(me&&me.user){ ME=me.user; }
    else if(me&&me.ok===false){ showGate(); dismissBootSplash(); return; }
  }catch(e){
    if(e&&e.code==='auth'){ showGate(); dismissBootSplash(); return; }
    // network/http: stay optimistic if we have a token after login
    if(!opts.afterLogin){ /* still try to load UI */ }
  }
  hideGate();
  applyRoleUI();
  try{
    status=await api('/v1/status');
  }catch(e){
    if(e&&e.code==='auth'){ showGate(); return; }
    status={ok:true,degraded:true,version:'',engine:{},how:{}};
  }
  try{
    const e=status.engine||{};
    const pub=status.public_url||(status.how&&status.how.phone_anywhere);
    if($('topMeta')){
      const fc = status.first_class || status.class;
      const grade = status.class || status.grade || '';
      const classOn = status.first_class===true || grade==='A' || grade==='S';
      $('topMeta').innerHTML =
        chip('Codex',e.codex)+chip('Grok',e.grok)+chip('Worker',e.worker_alive)+
        `<span class="chip ${pub&&String(pub).startsWith('http')?'on':'warn'}">${pub&&String(pub).startsWith('http')?'Public':'LAN'}</span>`+
        (grade?`<span class="chip ${classOn?'on':'warn'}" title="GET /v1/class">Class ${esc(String(grade))}</span>`:'')+
        `<span class="chip on">v${status.version||''}</span>`+
        `<span class="chip device-chip ${DEVICE.kind}">${DEVICE.label}</span>`;
    }
    if($('pubUrl')) $('pubUrl').innerHTML = pub&&String(pub).startsWith('http') ? ('Public <a href="'+pub+'" target="_blank">'+pub+'</a>') : 'Public host not set';
    const sel=$('wsSelect');
    if(sel){
      sel.innerHTML='';
      (e.workspaces||[]).forEach(w=>{
        if(w.exists===false) return;
        const o=document.createElement('option'); o.value=w.id; o.textContent=w.label; sel.appendChild(o);
      });
      if(!sel.options.length){ const o=document.createElement('option'); o.value='workspace'; o.textContent='workspace'; sel.appendChild(o); }
    }
    if($('userChip')) $('userChip').textContent = (ME.display||ME.user)||sessionStorage.getItem('pocket_user')||'user';
  }catch(_){}

  // Soft-load panels — never bounce to login for panel failures
  await Promise.allSettled([
    refreshSessions().catch(()=>{}),
    refreshLive().catch(()=>{}),
    refreshUsage().catch(()=>{}),
    refreshOrganism().catch(()=>{}),
    refreshStack().catch(()=>{}),
  ]);
  try{ await api('/v1/live/connect',{method:'POST',body:JSON.stringify({service:'all'})}); }catch(_){}
  ensureLivePoll();
  try{ pollSubagents(); }catch(_){}
  if(!boot._timers){
    boot._timers=true;
    setInterval(()=>{ try{ refreshLive(); }catch(_){} }, 8000);
    setInterval(()=>{ try{ refreshUsage(); }catch(_){} }, 12000);
    setInterval(()=>{ try{ refreshSessions(); }catch(_){} }, 5000);
    setInterval(()=>{ try{ refreshOrganism(); }catch(_){} }, 5000);
  }
  dismissBootSplash();
}
function dismissBootSplash(immediate){
  const el=$('bootSplash');
  if(!el) return;
  const finish=()=>{ el.classList.add('done'); el.setAttribute('aria-hidden','true'); el.style.pointerEvents='none'; };
  if(immediate || el.classList.contains('done')){ finish(); return; }
  // Minimum show so the production intro is visible
  const minMs=400;
  const started=window.__pocketBootAt||Date.now();
  const wait=Math.max(0, minMs-(Date.now()-started));
  setTimeout(finish, wait);
}
function goAppBack(){
  // Browser mode first: never leave the app via back when pane is open
  if($('browserLayer')&&$('browserLayer').classList.contains('open')){ closeBrowser(); return; }
  try{
    if(history.length>1 && document.referrer && document.referrer.indexOf(location.origin)===0){
      history.back();
      return;
    }
  }catch(_){}
  location.href='/desk';
}
function goDeskHome(){
  closeBrowser();
  if(location.pathname!=='/desk' && location.pathname!=='/' && location.pathname!=='/app' && location.pathname!=='/desktop' && location.pathname!=='/chat'){
    location.href='/desk';
    return;
  }
  activeId=null;
  showEmpty();
  refreshSessions();
}
function openBrowser(url){
  const layer=$('browserLayer');
  if(!layer) return;
  layer.classList.add('open');
  layer.setAttribute('aria-hidden','false');
  document.body.classList.add('browser-open');
  const raw=url!=null?String(url):($('browserUrl').value||'/tour');
  $('browserUrl').value=raw.startsWith('http')||raw.startsWith('/')?raw:('https://'+raw);
  browserGo();
  setTimeout(()=>{ try{ $('browserUrl').focus(); }catch(_){} }, 80);
}
function closeBrowser(){
  const layer=$('browserLayer');
  if(!layer) return;
  layer.classList.remove('open');
  layer.setAttribute('aria-hidden','true');
  document.body.classList.remove('browser-open');
  const frame=$('browserFrame');
  if(frame){
    try{ frame.src='about:blank'; }catch(_){}
  }
  const blk=$('browserBlocked');
  if(blk) blk.classList.remove('show');
}
function normalizeBrowserUrl(raw){
  let u=String(raw||'').trim();
  if(!u) return location.origin+'/tour';
  if(u.startsWith('/')) return location.origin+u;
  if(!/^https?:\/\//i.test(u)) u='https://'+u;
  return u;
}
function browserIsSameOrigin(u){
  try{ return new URL(u, location.href).origin===location.origin; }catch(_){ return false; }
}
function browserQuick(pathOrUrl){
  $('browserUrl').value=pathOrUrl;
  browserGo();
}
/** Load in the in-app browser pane — desk stays mounted; ← Desk always visible. */
function browserGo(){
  const u=normalizeBrowserUrl($('browserUrl').value);
  $('browserUrl').value=u;
  try{ sessionStorage.setItem('pocket_browser_last', u); }catch(_){}
  const frame=$('browserFrame');
  const blk=$('browserBlocked');
  if(blk) blk.classList.remove('show');
  if(!frame) return;
  // Same-origin product pages embed cleanly. External may hit X-Frame-Options.
  frame.onload=function(){
    if(blk) blk.classList.remove('show');
    // If same-origin and empty body, treat as fail
    try{
      const doc=frame.contentDocument;
      if(doc && doc.location && doc.location.href==='about:blank') return;
    }catch(_){ /* cross-origin loaded — ok */ }
  };
  frame.onerror=function(){ if(blk) blk.classList.add('show'); };
  try{
    frame.src=u;
  }catch(e){
    if(blk) blk.classList.add('show');
  }
  // Many external sites refuse iframe after a blank paint — offer new tab, keep chrome
  if(!browserIsSameOrigin(u)){
    setTimeout(()=>{
      try{
        // still open — user may see content; if blocked, browser shows empty; nudge gently
        const blk2=$('browserBlocked');
        // Don't force blocked UI for all external; only if we detect nothing after load
      }catch(_){}
    }, 2500);
  }
}
function browserHistBack(){
  try{ $('browserFrame').contentWindow.history.back(); }catch(_){ toast('Page back works on in-pane pages'); }
}
function browserHistFwd(){
  try{ $('browserFrame').contentWindow.history.forward(); }catch(_){ toast('Page forward works on in-pane pages'); }
}
function browserReload(){
  try{ $('browserFrame').contentWindow.location.reload(); }catch(_){ browserGo(); }
}
/** Optional: leave the pane and open a real Edge tab */
function browserOpenNewTab(){
  const u=normalizeBrowserUrl($('browserUrl').value);
  window.open(u,'_blank','noopener');
  toast('Opened in new tab — desk is still here');
}
function chip(name,on){ return `<span class="chip ${on?'on':'off'}">${name}</span>`; }

async function refreshOrganism(){
  try{
    const o=await api('/v1/organism');
    const h=o.heart||{}, b=o.brain||{};
    $('heartLabel').textContent=(h.bpm||'—')+' bpm';
    $('thought').textContent=b.thought||o.motto||'';
  }catch(_){}
}
async function refreshStack(){
  try{
    const j=await api('/v1/stack');
    const nx=j.nexus||{}, me=j.mesie||{}, mh=j.mesh||{};
    const set=(id,ok,label)=>{ const el=$(id); if(!el) return; el.textContent=label; el.className=ok?'on':'off'; };
    set('stPocket', true, 'live');
    set('stNexus', !!nx.ok, nx.ok?((nx.workers||[]).length+' workers'):'missing');
    set('stMesie', !!me.ok, me.ok?((me.engine_count||0)+' eng'):'missing');
    set('stMesh', !!mh.ok, mh.ok?((mh.agent_count||0)+' @ E:'):'off');
  }catch(_){
    ['stNexus','stMesie','stMesh'].forEach(id=>{ const el=$(id); if(el){ el.textContent='offline'; el.className='off'; }});
  }
}
async function refreshSessions(){
  try{
    const j=await api('/v1/sessions?limit=40');
    sessions=j.sessions||[];
    renderSessionList();
    if(activeId){
      try{ renderTranscript(await api('/v1/sessions/'+activeId)); }catch(_){}
    }
  }catch(e){
    const box=$('slist');
    if(box) box.innerHTML='<div class="hint">Sessions need sign-in. Use the login panel, then click NEXUS / MESIE / Codex above.</div>';
  }
}
function renderSessionList(){
  const box=$('slist'); if(!box) return; box.innerHTML='';
  if(!sessions.length){ box.innerHTML='<div class="hint">No sessions yet. Start <b>NEXUS</b>, <b>MESIE</b>, Codex, or Term — they show here.</div>'; return; }
  sessions.forEach(s=>{
    const d=document.createElement('div');
    d.className='sitem'+(s.id===activeId?' on':'');
    const last=(s.messages&&s.messages.length)?s.messages[s.messages.length-1]:null;
    const preview=last?((last.text||last.result||'').slice(0,42)):(s.mode);
    const thr=s.engine_thread_id||s.codex_session_id||'';
    const thrHint=thr?(s.mode==='codex'?' · thread '+(thr.slice(0,8)+'…'):' · bound'):' · new thread';
    const resumeN=s.engine_resumes?(' · r'+s.engine_resumes):'';
    d.innerHTML=`<div class="dot" style="background:${s.color||MODE_COLOR[s.mode]||'#22c55e'}"></div>
      <div style="min-width:0;flex:1"><b>${esc(s.title||s.mode)}</b><div class="meta">${s.mode} · ${s.status||'idle'}${thrHint}${resumeN} · ${esc(preview)}</div></div>
      <button class="x" title="Close">×</button>`;
    d.onclick=e=>{ if(e.target.classList.contains('x')){ closeSess(s.id); return; } selectSess(s.id); };
    box.appendChild(d);
  });
}
async function newSess(mode){
  try{
    const ws=$('wsSelect').value||'workspace';
    const j=await api('/v1/sessions',{method:'POST',body:JSON.stringify({mode, workspace:ws, device:DEVICE})});
    await refreshSessions();
    await selectSess(j.id);
    if(DEVICE.kind==='phone') closeDrawers();
    toast((mode||'session')+' · '+DEVICE.label);
  }catch(e){ toast('Could not start session: '+e.message); }
}
/** Activate Grok/Codex Novae hands in platform workspace (not founder personal disk for market). */
async function activateNovae(id){
  try{
    const n=await api('/v1/novae/activate',{method:'POST',body:JSON.stringify({id, goal:'desk activate', host_power:true})});
    if(!n.ok && n.error) throw new Error(n.error);
    toast((n.title||id)+' · hands active');
    if(n.session_id){
      await refreshSessions();
      await selectSess(n.session_id);
    } else if(n.mode){
      await newSess(n.mode);
    }
    if(DEVICE.kind==='phone') closeDrawers();
    try{ pollSubagents(); }catch(_){}
  }catch(e){ toast('Novae: '+(e.message||e),'err'); }
}
async function closeSess(id){
  try{
    // Stop running Grok/Codex jobs before deleting the tab
    try{ await api('/v1/sessions/'+id+'/stop',{method:'POST',body:JSON.stringify({reason:'session closed'})}); }catch(_){}
    await api('/v1/sessions/'+id,{method:'DELETE'});
    if(activeId===id){ activeId=null; showEmpty(); }
    refreshSessions();
  }catch(e){ toast('Close failed'); }
}
async function stopActiveSession(){
  if(!activeId) return;
  try{
    const r=await api('/v1/sessions/'+activeId+'/stop',{method:'POST',body:JSON.stringify({reason:'stopped by user'})});
    const n=(r.cancelled_jobs||[]).length;
    toast(n?('Stopped '+n+' job'+(n===1?'':'s')):'Nothing running');
    await selectSess(activeId);
    refreshSessions();
  }catch(e){ toast('Stop failed: '+e.message,'err'); }
}
async function endActiveSession(){
  if(!activeId) return;
  const id=activeId;
  await closeSess(id);
  toast('Session ended');
}
function updateSessionControls(s){
  const stop=$('btnStop'), end=$('btnEnd');
  if(!stop||!end) return;
  if(!s||!activeId){ stop.style.display='none'; end.style.display='none'; return; }
  end.style.display='inline-flex';
  const running=(s.messages||[]).some(m=>m.status==='running'||m.status==='queued') || s.status==='running';
  stop.style.display=running?'inline-flex':'none';
  stop.classList.toggle('hot', !!running);
}
async function selectSess(id){
  activeId=id;
  if(pollTimer) clearInterval(pollTimer);
  try{
    const s=await api('/v1/sessions/'+id);
    renderSessionList();
    renderTranscript(s);
    $('input').disabled=false; $('sendBtn').disabled=false; $('micBtn').disabled=false; $('input').focus();
    setPresets(s.mode);
    pollTimer=setInterval(async()=>{
      try{
        const fresh=await api('/v1/sessions/'+id);
        renderTranscript(fresh);
        let stok=0;
        (fresh.messages||[]).forEach(m=>{ if(m.status==='running') stok+=(m.stream_tokens||0); });
        $('uStream').textContent=stok.toLocaleString();
      }catch(_){}
    },900);
  }catch(e){ toast('Open session failed'); }
}
function showEmpty(){
  $('mainTitle').textContent='Select an agent';
  $('mainTag').textContent='—';
  $('mainWs').textContent='workspace';
  updateSessionControls(null);
  $('input').disabled=true; $('sendBtn').disabled=true; $('micBtn').disabled=true;
  const sub = DEVICE.kind==='phone'
    ? 'Tap Agents to start. Jobs run on the host PC.'
    : (DEVICE.kind==='tablet'
      ? 'Start an agent. Jobs run on the host.'
      : 'Start an agent on the left, then send a message.');
  $('transcript').innerHTML=`<div class="empty"><div class="mark">P</div><h2>What are you working on?</h2><p>${esc(sub)}</p></div>`;
  $('presets').innerHTML='';
}
function emptyHint(mode){
  const m={
    desktop:'Try: list apps · open notepad · open edge https://…',
    web:'Try: search … · fetch https://…',
    nexus:'Try: list · run Bridge list_servers',
    term:'Type a host PowerShell command.',
    shell:'One-shot shell command on the host.',
    plan:'Describe the goal — plan only, no writes.',
    grok:'Message Grok. New messages stop the previous turn so work reorganizes. Use Stop / End in the header.',
    codex:'Message Codex. New messages stop the previous turn. Use Stop / End in the header.',
    wsl:'Native Linux hands. Try: status · ! ls -la · run: git status · force: for soft-danger cmds.',
    wsl_native:'Native WSL agent. Workspace ~/pocket-wsl. status · ! cmd · run: cmd. Founder-host only.',
    linux:'Alias of WSL native agent.',
    build:'Multi-agent ship loop (Emergent+). Try: list · parity · use_case:fullstack_web_app · or describe an app.',
    ship:'Same as Build — plan→design→code→test→fix→ship until done.',
    use_case:'Real use cases. Try: list · fullstack_web_app · api_microservice · test_troubleshoot.',
    emergent:'Emergent-parity factory. parity · use_case:multi_agent_swarm.',
    custom_agent:'Build agents with tools+subs. create Name: role · or run AgentId task.',
    wiki:'Infinite Wiki. profile PATH · read_lines PATH A B · symbol NAME · index ROOT · search Q — never dump whole files.',
    infinite_wiki:'Hierarchical code: Profile Card then line slices only.',
    codebase:'Same as Infinite Wiki.',
    agent:'Silent multi-step (≤10). lookup … · schedule daily …',
    doer:'Silent multi-step (≤10). No chat — executes.',
    guppy:'help · lookup … · open apps · schedule daily …',
    browser:'Research, compose, open Edge / X.',
    capture:'screenshot · snip',
    repos:'list repos · open my 5 repos · analyze …',
    copilot:'introduce · open · open web',
    archon:'workers · focused demo · @OCULUS screenshot',
    alpha:'workers · demo · @mentions',
    workers:'workers — list Latin roster',
    handoff:'Plan package only.'
  };
  return m[mode]||'Send a message. Use @ to dispatch workers.';
}
function workedSeconds(m){
  const start=Number(m.at||0), end=Number(m.finished_at||m.stream_updated_at||0);
  if(start&&end&&end>=start) return Math.max(1, Math.round(end-start));
  if(start&&(m.status==='running'||m.status==='queued')) return Math.max(1, Math.round(Date.now()/1000 - start));
  return 0;
}
/** Parse explicit @NAME mentions (ARCHON, DESIGN, FORGE_HEADLESS, …). */
function parseMentions(text){
  const found=[];
  const re=/@([A-Za-z][A-Za-z0-9_]*)/g;
  let m;
  while((m=re.exec(String(text||'')))){
    const name=String(m[1]||'').toUpperCase();
    if(!name||found.includes(name)) continue;
    // Latin, mesh/headless, aliases, or any named agent ≥2 chars
    if(LATIN_WORKERS.includes(name) || MESH_AGENTS.includes(name) || MENTION_ALIASES.includes(name) || name.length>=2){
      found.push(name);
    }
  }
  return found;
}
function hasAtMention(text){
  return /@[A-Za-z]/.test(String(text||''));
}
function mentionWorkers(text){
  const raw=String(text||'');
  const upper=raw.toUpperCase();
  const fromAt=parseMentions(raw);
  const bare=LATIN_WORKERS.concat(MESH_AGENTS).filter(w=>new RegExp('\\b'+w+'\\b').test(upper));
  return Array.from(new Set(fromAt.concat(bare)));
}
/** Summarize dispatch API payload into a short human line (no raw dumps). */
function summarizeDispatchResult(j, name){
  if(!j||typeof j!=='object') return '';
  const mentions=j.mentions||[];
  const n=j.dispatched!=null?j.dispatched:1;
  if(j.ok===false){
    const err=(j.error||j.message||'').toString().slice(0,120);
    return err||'failed';
  }
  // Prefer nested run summary without dumping full objects
  let note='';
  try{
    const results=j.results||[];
    const mine=results.find(r=>String(r.agent||'').toUpperCase()===String(name||'').toUpperCase())||results[0];
    const run=mine&&mine.run;
    if(run&&typeof run==='object'){
      if(typeof run.message==='string'&&run.message.trim()) note=run.message.trim().slice(0,140);
      else if(typeof run.brief==='string') note=run.brief.trim().slice(0,140);
      else if(run.ok!=null) note=run.ok?'ok':'failed';
    }
  }catch(_){}
  if(!note && mentions.length) note='mesh · '+n+' agent'+(n===1?'':'s');
  return note;
}
/** Append a clean dispatch card into the chat transcript (not JSON dumps). */
function showDispatchInline(dispatched, message){
  const box=$('transcript');
  if(!box) return;
  // Clear empty state
  const empty=box.querySelector('.empty');
  if(empty) box.innerHTML='';
  const ok=dispatched.filter(d=>d.ok);
  const fail=dispatched.filter(d=>!d.ok);
  const card=document.createElement('div');
  card.className='dispatch-card';
  const chips=dispatched.map(d=>{
    const tip=d.ok?(d.summary||'dispatched'):(d.error||'failed');
    return `<span class="dc-chip ${d.ok?'':'fail'}" title="${esc(tip)}">@${esc(d.name)}</span>`;
  }).join('');
  const note=ok.map(d=>d.summary).filter(Boolean).slice(0,2).join(' · ')
    || (message?String(message).slice(0,100):'');
  card.innerHTML=`<div class="dc-h"><span class="ok">${fail.length&&!ok.length?'DISPATCH':'DISPATCHED'}</span>
    <span>${ok.length} ok${fail.length?(' · '+fail.length+' failed'):''}</span></div>
    <div class="dc-agents">${chips}</div>
    ${note?`<div class="dc-note">${esc(note)}</div>`:''}`;
  box.appendChild(card);
  box.scrollTop=box.scrollHeight;
}
/** POST /v1/subagents/dispatch {name, message} for each @MENTION. Soft-fails if route missing. */
async function dispatchMentions(text){
  const names=parseMentions(text);
  if(!names.length) return {dispatched:[], endpointMissing:false};
  const message=String(text||'').replace(/@[A-Za-z][A-Za-z0-9_]*/g,' ').replace(/\s+/g,' ').trim()||text;
  const dispatched=[];
  let endpointMissing=false;
  for(const name of names){
    try{
      const r=await fetch('/v1/subagents/dispatch',{
        method:'POST',
        headers:authHeaders(),
        body:JSON.stringify({name, message})
      });
      if(r.status===404){
        endpointMissing=true;
        break;
      }
      const raw=await r.text();
      let j={};
      try{ j=raw?JSON.parse(raw):{}; }catch(_){ j={}; }
      if(r.ok){
        const summary=summarizeDispatchResult(j, name);
        dispatched.push({name, ok:true, summary});
        liveAgentHits[name]={t:Date.now(),message:(summary||message).slice(0,160),status:'running'};
        // Also mark canonical headless ids when short alias used
        if(name==='FORGE') liveAgentHits['FORGE_HEADLESS']=liveAgentHits[name];
        if(name==='SENTINEL') liveAgentHits['SENTINEL_HEADLESS']=liveAgentHits[name];
        if(name==='SHIP') liveAgentHits['SHIP_HEADLESS']=liveAgentHits[name];
        if(name==='RESEARCH') liveAgentHits['RESEARCH_HEADLESS']=liveAgentHits[name];
        if(name==='DESIGN'||name==='DESIGNER'||name==='UI') liveAgentHits['DESIGN']={t:Date.now(),message:(summary||message).slice(0,160),status:'running'};
        walkthroughSteps.push({
          agent:name,
          message:'Dispatched · '+(summary||message.slice(0,100)||'run'),
          kind:'dispatch',
          ts:new Date().toISOString().slice(11,19)
        });
      } else {
        let err=j.error||j.message||('HTTP '+r.status);
        if(typeof err!=='string') err='HTTP '+r.status;
        dispatched.push({name, ok:false, error:String(err).slice(0,160)});
      }
    }catch(e){
      dispatched.push({name, ok:false, error:String(e.message||e).slice(0,160)});
    }
  }
  if(dispatched.length){
    showDispatchInline(dispatched, message);
    const okNames=dispatched.filter(d=>d.ok).map(d=>d.name);
    if(okNames.length) toast('Dispatched @'+okNames.join(' @'), 'ok');
    else toast('Dispatch failed', 'err');
    renderWalkthrough(walkthroughSteps);
    try{ pollSubagents(); }catch(_){}
  }
  return {dispatched, endpointMissing, message};
}
function resolveSlash(text){
  const t=String(text||'').trim();
  if(!t.startsWith('/')) return t;
  const body=t.slice(1).trim();
  if(!body) return t;
  const sp=body.indexOf(' ');
  const cmd=(sp<0?body:body.slice(0,sp)).toLowerCase();
  const arg=(sp<0?'':body.slice(sp+1)).trim();
  if(cmd==='help'||cmd==='actions'){
    return 'Available actions: '+SLASH_ACTIONS.map(a=>'/'+a.cmd).join(' · ')+
      '\nLatin: '+LATIN_WORKERS.map(w=>'@'+w).join(' ')+
      '\nMesh: '+MESH_AGENTS.map(w=>'@'+w).join(' ');
  }
  const hit=SLASH_ACTIONS.find(a=>a.cmd===cmd);
  if(hit && hit.fill && hit.fill.startsWith('/')) return resolveSlash(hit.fill+(arg?' '+arg:''));
  if(hit) return (hit.fill+(arg?' '+arg:'')).trim();
  return t;
}
function closeComposerMenus(){
  const sm=$('slashMenu'); if(sm){ sm.classList.remove('open'); sm.innerHTML=''; }
  const mm=$('mentionMenu'); if(mm){ mm.classList.remove('open'); mm.innerHTML=''; }
}
function updateSlashMenu(){
  const el=$('slashMenu');
  const input=$('input');
  if(!el||!input) return;
  const v=String(input.value||'');
  // Prefer @mention menu when typing a mention token
  if(currentMentionQuery(v)!=null){ el.classList.remove('open'); el.innerHTML=''; return; }
  if(!v.startsWith('/') || v.includes('\n')){
    el.classList.remove('open'); el.innerHTML=''; return;
  }
  const q=v.slice(1).split(/\s/)[0].toLowerCase();
  const items=SLASH_ACTIONS.filter(a=>!q||a.cmd.startsWith(q)||a.label.toLowerCase().includes(q));
  if(!items.length){ el.classList.remove('open'); el.innerHTML=''; return; }
  el.innerHTML='';
  items.forEach(a=>{
    const b=document.createElement('button');
    b.type='button'; b.setAttribute('role','option');
    b.innerHTML=`<b>/${esc(a.cmd)}</b><span>${esc(a.label)}</span>`;
    b.onclick=()=>{ input.value=a.fill; el.classList.remove('open'); el.innerHTML=''; input.focus(); };
    el.appendChild(b);
  });
  el.classList.add('open');
}
/** Return partial mention token after last @ (or null if not in @-mode). */
function currentMentionQuery(v){
  const s=String(v||'');
  // Active when last @ has no space after it yet
  const m=s.match(/(^|[\s])@([A-Za-z0-9_]*)$/);
  if(!m) return null;
  return String(m[2]||'').toUpperCase();
}
function updateMentionMenu(){
  const el=$('mentionMenu');
  const input=$('input');
  if(!el||!input) return;
  const v=String(input.value||'');
  const q=currentMentionQuery(v);
  if(q==null){ el.classList.remove('open'); el.innerHTML=''; return; }
  // Hide slash while mentioning
  const sm=$('slashMenu'); if(sm){ sm.classList.remove('open'); sm.innerHTML=''; }
  const roster=mentionRoster();
  const items=roster.filter(n=>!q||n.startsWith(q)||n.includes(q)).slice(0,14);
  // Always surface DESIGN + headless near top when query empty / matching
  const priority=['DESIGN','FORGE_HEADLESS','SENTINEL_HEADLESS','RESEARCH_HEADLESS','SHIP_HEADLESS','ARCHON','OCULUS','SCRIPTOR'];
  items.sort((a,b)=>{
    const ia=priority.indexOf(a), ib=priority.indexOf(b);
    if(ia>=0||ib>=0) return (ia<0?99:ia)-(ib<0?99:ib);
    return a.localeCompare(b);
  });
  if(!items.length){ el.classList.remove('open'); el.innerHTML=''; return; }
  el.innerHTML='';
  items.forEach(n=>{
    const b=document.createElement('button');
    b.type='button'; b.setAttribute('role','option');
    const kind=mentionKind(n);
    b.innerHTML=`<span class="mdot ${kind}"></span><b>@${esc(n)}</b><span>${esc(mentionLabel(n))}</span>`;
    b.onclick=()=>{
      // Replace trailing @partial with full @NAME + space
      const cur=String(input.value||'');
      input.value=cur.replace(/@([A-Za-z0-9_]*)$/, '@'+n+' ');
      el.classList.remove('open'); el.innerHTML='';
      input.focus();
    };
    el.appendChild(b);
  });
  el.classList.add('open');
}
function inlineSubagentsFromMsg(m, mode){
  const names=new Set(mentionWorkers(m.text||'').concat(mentionWorkers(m.result||'')));
  (subagentState||[]).forEach(w=>{ if(w&&w.name) names.add(String(w.name).toUpperCase()); });
  Object.keys(liveAgentHits||{}).forEach(k=>{ if(liveAgentHits[k] && (Date.now()-liveAgentHits[k].t)<90000) names.add(k); });
  if(m.status==='running'||m.status==='queued'){
    const eng=String(m.engine||mode||'').toUpperCase();
    if(eng) names.add(eng);
  }
  return Array.from(names).map(n=>{
    const hit=liveAgentHits[n];
    const dyn=(subagentState||[]).find(w=>String(w.name||'').toUpperCase()===n);
    return {
      name:n,
      status: dyn?(dyn.status||'running'):(hit?(hit.status||'running'):((m.status==='running'||m.status==='queued')?'running':'done')),
      goal: dyn?(dyn.goal||''):(hit?(hit.message||''):''),
      steps: dyn?dyn.steps:undefined
    };
  });
}
function renderTranscript(s){
  if(!s) return;
  $('mainTitle').textContent=s.title||s.mode;
  const thr=s.engine_thread_id||s.codex_session_id||'';
  const thrTag=thr?(' · thread '+(String(thr).slice(0,8)+'…')):'';
  const anyRun=(s.messages||[]).some(m=>m.status==='running'||m.status==='queued');
  $('mainTag').textContent=s.mode+(anyRun||s.status==='running'?' · running':'')+thrTag+(s.engine_resumes?(' · resumes '+s.engine_resumes):'');
  $('mainWs').textContent=s.workspace||'workspace';
  updateSessionControls(s);
  const mp=$('modelPick');
  if(mp && !mp.dataset.userSet){ try{ mp.value=s.mode||''; }catch(_){} }
  const box=$('transcript');
  const msgs=s.messages||[];
  if(!msgs.length){
    box.innerHTML=`<div class="empty"><div class="mark">P</div><h2>${esc(s.title||s.mode)}</h2><p>${esc(emptyHint(s.mode))}</p></div>`;
    return;
  }
  const stick = box.scrollHeight - box.scrollTop - box.clientHeight < 80;
  box.innerHTML='';
  const anyRunning=msgs.some(m=>m.status==='running'||m.status==='queued');
  msgs.forEach(m=>{
    const u=document.createElement('div');
    u.className='msg user';
    u.innerHTML=`<div class="mb">${esc(m.text||'')}</div>`;
    box.appendChild(u);
    const sec=workedSeconds(m);
    if(sec && (m.status==='done'||m.status==='failed'||m.status==='cancelled'||m.status==='running'||m.result||m.error)){
      const meta=document.createElement('details');
      meta.className='worked-meta';
      const label=m.status==='running'||m.status==='queued'
        ? `Working · ${sec}s`
        : (m.status==='cancelled' ? `Stopped · ${sec}s` : `Worked for ${sec}s`);
      const eng=m.engine||s.mode||'';
      const tok=m.stream_tokens?` · ~${m.stream_tokens} tok`:'';
      const stExtra=m.status==='failed'?' · failed':(m.status==='cancelled'?' · cancelled':'');
      meta.innerHTML=`<summary>${esc(label)}${esc(stExtra)} · ${esc(eng)}${esc(tok)}</summary>
        <div class="wm-body">${esc((m.error||m.result||'').slice(0,1200)||'No detail')}</div>`;
      box.appendChild(meta);
    }
    // Subagents stay on the RIGHT rail (Antigravity-style) — not a chat drop bar.
    // Only surface a tiny hint in-transcript when user explicitly @mentioned someone.
    const mentioned=mentionWorkers(m.text||'');
    if(mentioned.length){
      const hint=document.createElement('div');
      hint.className='worked-meta';
      hint.innerHTML=`<span style="color:var(--accent)">@ ${esc(mentioned.join(' · '))}</span>
        <span style="color:var(--muted)">· live status on right Workspace rail</span>`;
      box.appendChild(hint);
      // Keep roster warm
      try{ pollSubagents(); }catch(_){}
    }
    if(m.status==='running'||m.status==='queued'||m.status==='cancelled'||m.result||m.error){
      const streaming=(m.status==='running'||m.status==='queued');
      const isTerm=s.mode==='term'||s.mode==='shell'||s.mode==='wsl';
      const eng=m.engine||s.mode||'agent';
      const tok=m.stream_tokens?` · ~${m.stream_tokens} tok`:'';
      // Clean thinking state — orb animation while model works
      if(streaming && !(m.result||m.error||m.stream_preview)){
        const tr=document.createElement('div');
        tr.className='think-row';
        const novae=String(s.mode||'').includes('novae');
        tr.innerHTML=`<div class="think-orb" aria-hidden="true"></div>
          <span class="think-label"><b>${esc(eng)}</b> thinking${novae?' · Novae hands':''}</span>
          <span class="think-dots" aria-hidden="true"><span></span><span></span><span></span></span>
          <span style="margin-left:auto;font-size:11px;opacity:.75">${esc(String(workedSeconds(m)||0)+'s')}${esc(tok)}</span>`;
        box.appendChild(tr);
      } else {
        const a=document.createElement('div');
        a.className='msg agent '+(m.status||'');
        const raw=m.result||m.error||(streaming?'':(m.status==='cancelled'?'Stopped — send a new message to reorganize.':''));
        const novaeBadge=String(s.mode||'').includes('novae')?' <span class="novae-pill">Novae</span>':'';
        a.innerHTML=`<div class="mh"><span><span class="live-dot" style="display:${streaming?'inline-block':'none'}"></span>${esc(eng)}${novaeBadge}${esc(tok)}</span><span>${esc(m.status||'')}</span></div>
          <div class="mb ${isTerm?'term':'prose'}">${isTerm?formatAgentBody(raw):formatProseBody(raw||(streaming?'…':''))}</div>`;
        box.appendChild(a);
      }
    }
  });
  if(s.mode==='term' && s.terminal && s.terminal.log_tail){
    const a=document.createElement('div');
    a.className='msg agent';
    a.innerHTML=`<div class="mh"><span><span class="live-dot"></span>terminal ${s.terminal.alive?'live':'off'}</span><span>pid ${s.terminal.pid||'—'}</span></div><div class="mb term">${esc(s.terminal.log_tail)}</div>`;
    box.appendChild(a);
  }
  if(anyRunning) ensureLivePoll();
  if(stick) box.scrollTop=box.scrollHeight;
  // Keep AI workspace rail in sync with this session
  try{ refreshAiWorkspace(); }catch(_){}
}
let _aiWsTimer=null;
async function refreshAiWorkspace(){
  try{
    const ws=($('wsSelect')&&$('wsSelect').value)||'parallax';
    const sid=activeId||'';
    const q='/v1/ai-workspace?workspace='+encodeURIComponent(ws)+'&session_id='+encodeURIComponent(sid);
    const j=await api(q);
    const sum=$('aiSummary'), meta=$('aiSumMeta'), prev=$('aiPreviews'), tree=$('aiTree'), bus=$('aiBus');
    if(sum){
      const t=(j.summary||'').trim();
      sum.textContent=t||'No turns yet — send a message; summary auto-builds (no LLM tax).';
    }
    if(meta){
      meta.textContent=(j.cwd?j.cwd+' · ':'')+'ctx ~'+(j.context_chars||0)+' chars · '+(j.updated_h||'live')
        +(j.token_tips&&j.token_tips[0]?(' · '+j.token_tips[0]):'');
    }
    if(prev){
      const list=j.previews||[];
      if(!list.length){
        prev.innerHTML='<div class="hint" style="font-size:11px;color:var(--muted)">Agent outputs &amp; docs preview here after work</div>';
      } else {
        prev.innerHTML='';
        list.forEach(p=>{
          const el=document.createElement('div');
          el.className='pv';
          el.innerHTML='<b>'+esc(p.name||'preview')+'</b><pre>'+esc((p.preview||'').slice(0,500))+'</pre>';
          el.onclick=()=>{ try{ navigator.clipboard.writeText(p.preview||''); toast('Preview copied'); }catch(_){ } };
          prev.appendChild(el);
        });
      }
    }
    if(tree){
      const files=j.index||[];
      tree.innerHTML=files.slice(0,24).map(f=>esc(f.path||'')).join('<br>')||'<span style="color:var(--muted)">index empty — will build on first job</span>';
    }
    if(bus){
      const msgs=j.bus||[];
      if(!msgs.length){
        bus.innerHTML='<div class="hint" style="font-size:11px;color:var(--muted)">Hashed swarm notes appear as agents finish</div>';
      } else {
        bus.innerHTML=msgs.slice(0,8).map(m=>
          '<div class="bm"><b>'+esc(m.from||'?')+'</b> → '+esc(m.to||'?')
          +' <span class="hm">'+(m.hmac?esc(m.hmac):'')+'</span><br>'
          +esc((m.body||'').slice(0,160))+'</div>'
        ).join('');
      }
    }
  }catch(e){
    const sum=$('aiSummary');
    if(sum && !sum.dataset.had) sum.textContent='Workspace API warming…';
  }
}
function ensureAiWorkspacePoll(){
  if(_aiWsTimer) return;
  _aiWsTimer=setInterval(()=>{ if(activeId) refreshAiWorkspace(); refreshOffload(); }, 4000);
}
async function refreshOffload(){
  try{
    const j=await api('/v1/offload?limit=8');
    const el=$('offloadList'); if(!el) return;
    const tasks=j.tasks||[];
    if(!tasks.length){ el.textContent='No tickets yet · start Offload agent or POST /v1/offload'; return; }
    el.innerHTML=tasks.slice(0,6).map(t=>
      '<div style="margin:0 0 6px"><b style="color:var(--accent)">'+esc(t.status||'')+'</b> '+
      esc((t.id||'').slice(0,14))+' · '+esc((t.goal||'').slice(0,80))+'</div>'
    ).join('');
  }catch(_){}
}
function setPresets(mode){
  const box=$('presets'); box.innerHTML='';
  const sets={
    codex:[['Ship code','Implement one concrete production fix in this workspace, run the smallest check, summarize the diff.'],['Continue','Continue from where you left off — code first, not a research essay.'],['Health','List top risks and missing tests, then fix the highest-risk one if small.']],
    grok:[['Ship code','Implement one useful code improvement, verify briefly, report files changed.'],['Explain','Summarize this project in 8 bullets.'],['Stop & reorganize','Stop prior work. Inventory production gaps and ship one concrete code fix.']],
    offload:[['Desk proof','capability snapshot then screenshot then note: operator away embodiment sprint'],['Open edge','open edge https://pocket.medinatechlabs.net/'],['Refresh workspace','workspace_refresh for parallax then screenshot']],
    cowork:[['Record demo','record demo: open edge https://pocket.medinatechlabs.net/ then screenshot'],['Desk tour','open notepad then screenshot then deliver note: cowork tour'],['No record','without record: capability snapshot and screenshot']],
    git:[['Create repo','create repo my-app'],['List','list repos'],['Help','help']],
    ghost:[['Hash chain','chain hash a|b|c'],['Phi','phi 21'],['Digest','digest this prompt']],
    plan:[['Next features','Plan only: next 5 product features, ordered, with risks. No code.'],['Phone UX','Plan only: improve mobile UX. No implementation.']],
    term:[['List','Get-ChildItem'],['Python','python --version'],['Git','git status']],
    shell:[['Dir','dir'],['Git','git status']],
    wsl:[['Status','status'],['Workspace','! ls -la ~/pocket-wsl'],['Tools','! which python3 node npm git'],['Git','run: git status']],
    wsl_native:[['Status','status'],['Workspace','! ls -la ~/pocket-wsl'],['Tools','! which python3 node npm git'],['Git','run: git status']],
    linux:[['Status','status'],['Workspace','! ls -la ~/pocket-wsl']],
    build:[['List use cases','list'],['Parity','parity'],['Full-stack app','use_case:fullstack_web_app'],['SaaS dashboard','use_case:saas_dashboard'],['API service','use_case:api_microservice']],
    ship:[['Full-stack','use_case:fullstack_web_app'],['Ship swarm','use_case:multi_agent_swarm']],
    use_case:[['List','list'],['Web app','fullstack_web_app'],['API','api_microservice'],['Custom agent','agent_inside_product'],['Test-fix','test_troubleshoot']],
    emergent:[['Parity matrix','parity'],['Beat Emergent web app','use_case:fullstack_web_app'],['Swarm until done','use_case:multi_agent_swarm']],
    custom_agent:[['List','list'],['Create support','create SupportAgent: customer support specialist'],['Help','help']],
    wiki:[['Help','help'],['Profile server.py','profile C:/Users/Medin/OneDrive/pocket-os/src/pocket/server.py'],['Read lines 164-190','read_lines C:/Users/Medin/OneDrive/pocket-os/src/pocket/server.py 164 190'],['Find symbol','symbol get_file_profile'],['Index pocket src','index C:/Users/Medin/OneDrive/pocket-os/src/pocket'],['Search','search orchestrator']],
    infinite_wiki:[['Help','help'],['Profile','profile C:/Users/Medin/OneDrive/pocket-os/src/pocket/infinite_wiki.py'],['Symbol','symbol read_file_lines']],
    codebase:[['Help','help'],['Search','search infinite wiki']],
    handoff:[['Defer plan','Package a full research plan for multi-user seats and cost.']],
    claude:[['Review','Review for bugs and missing tests.']],
    agent:[['Lookup+bring back','lookup multi-agent desktop AI platforms 2026'],['Edge+calc+snip','open edge https://pocket.medinatechlabs.net/ then open calc then open snip'],['Daily schedule','schedule daily lookup AI agent news'],['10-step style','open explorer then open notepad then lookup POCKET multi-agent desk']],
    doer:[['3-step desk','open edge https://example.com then open notepad then open calc'],['Lookup','lookup Cloudflare tunnels'],['Schedule','schedule daily lookup market brief']],
    guppy:[['Who','help'],['Lookup','lookup multi-agent desk platforms'],['Open Copilot query','open copilot POCKET host co-pilot'],['Daily fetch','schedule daily lookup AI and markets'],['Status','status'],['Schedule list','schedule list']],
    browser:[['Help','help'],['Research→Tweet','look up multi-agent desktop AI then write a tweet for my page https://x.com/ItsnotAILabs'],['Tweet only','tweet Shipping POCKET Browser mode — real desk agents from ItsNotAI Labs'],['Open X','open x'],['Win Copilot','open copilot'],['Web Copilot','open copilot web multi-agent platforms'],['Lookup','lookup Cloudflare named tunnels'],['Open 5 repos','open my 5 repos'],['Screenshot','screenshot'],['Use Grok','engine:grok look up AI agents and draft a tweet for https://x.com/ItsnotAILabs'],['Use Codex','engine:codex research POCKET and draft a launch tweet']],
    capture:[['Screenshot','screenshot'],['Snip tool','snip'],['Help','help']],
    repos:[['Analyze Brain AI','analyze brain ai'],['Analyze Imagine','analyze imagine'],['Open 5 repos','open my 5 repos'],['List repos','list repos'],['gh status','gh status'],['New git repo','new repo pocket-demo'],['Help','help']],
    copilot:[['Introduce+send','introduce'],['As Grok','introduce as Grok: multi-agent desk on this PC'],['Open app','open'],['Web','open web'],['Help','help']],
    archon:[['Workers','workers'],['WOW demo','wow showcase fundable'],['Focused demo','focused demo'],['Chat workflow','screenshot then notepad'],['Skills list','list skills'],['Screenshot','screenshot']],
    workers:[['List','workers'],['ARCHON help','ARCHON help'],['SCRUTATOR brain','SCRUTATOR analyze neuroemergence-core']],
    desktop:[['List apps','list apps'],['Copilot','open copilot'],['Antigravity','open antigravity'],['Snip','open snip'],['Screen clip','open screenclip'],['Notepad','open notepad'],['Explorer','open explorer'],['Edge+URL','open edge https://pocket.medinatechlabs.net/'],['VS Code','open code'],['Cursor','open cursor'],['Chrome','open chrome'],['Discord','open discord'],['Teams','open teams'],['GitHub Desktop','open github'],['Word','open word'],['Excel','open excel'],['Calc','open calc'],['Multi-step','open edge https://example.com then open notepad then open calc'],['Settings','open settings'],['Task Manager','open taskmgr']],
    web:[['Search','search multi agent desktop AI platforms 2026'],['Fetch','fetch https://example.com'],['Research','research Cloudflare tunnel named vs quick tunnel']],
    nexus:[['List','list'],['Bridge servers','run Bridge list_servers'],['Status','help']]
  };
  (sets[mode]||[]).forEach(([label,text])=>{
    const b=document.createElement('button'); b.type='button'; b.textContent=label;
    b.onclick=()=>{$('input').value=text};
    box.appendChild(b);
  });
}
function formatAgentBody(body){
  // Allow data-URI screenshots from capture agent; escape everything else
  const s=String(body||'');
  const re=/!\[([^\]]*)\]\((data:image\/[a-zA-Z+]+;base64,[A-Za-z0-9+/=]+)\)/g;
  let html='', last=0, m;
  while((m=re.exec(s))){
    html+=esc(s.slice(last,m.index));
    html+=`<div style="margin:8px 0"><img alt="${esc(m[1]||'shot')}" src="${m[2]}" style="max-width:100%;border-radius:8px;border:1px solid var(--line)"/></div>`;
    last=m.index+m[0].length;
  }
  html+=esc(s.slice(last));
  return html;
}
function polishChatText(raw){
  // Client-side mirror of pocket.reply_format — strip CLI chrome so convo looks good
  let s=String(raw||'');
  if(!s) return '';
  // Fix common mojibake
  const pairs=[['â€™',"'"],['â€˜',"'"],['â€œ','"'],['â€\u009d','"'],['â€”','—'],['â€“','-'],['â€¦','...'],['Â·','·'],['Â ',' '],['â†’','→'],['\uFFFD','']];
  pairs.forEach(([a,b])=>{ if(s.includes(a)) s=s.split(a).join(b); });
  const banner=/^(Reading additional input from stdin\.?|OpenAI Codex v[\d.]+|-{3,}|workdir:.+|model:.+|provider:.+|approval:.+|sandbox:.+|reasoning (?:effort|summaries):.+|session id:.+|tokens used|\d{1,3}(?:,\d{3})*$|user$|codex$|\[stream_tokens[^\]]*\]|\[llm_tokens[^\]]*\]|\[pocket_session[^\]]*\]|\[engine=[^\]]+\]|\[cli=[^\]]+\]|\[research_package=[^\]]+\])\s*$/i;
  const lines=s.replace(/\r\n/g,'\n').replace(/\r/g,'\n').split('\n');
  const kept=[];
  let skipUser=false;
  lines.forEach(line=>{
    const t=line.trim();
    if(/^user$/i.test(t)){ skipUser=true; return; }
    if(skipUser){
      if(/^\[Client device:/i.test(t) || !t){ return; }
      skipUser=false;
      if(/^codex$/i.test(t)) return;
    }
    if(banner.test(t)) return;
    kept.push(line);
  });
  s=kept.join('\n').replace(/\n{3,}/g,'\n\n').trim();
  // Unstick run-on stream blobs when almost no newlines
  if((s.match(/\n/g)||[]).length < Math.max(3, s.length/500)){
    s=s.replace(/([.!?])([A-Z][a-z])/g,'$1\n\n$2');
  }
  // Prefer text after last "tokens used" summary block
  const parts=s.split(/\ntokens used\n[\d,]+\s*\n/i);
  if(parts.length>=2 && parts[parts.length-1].trim().length>40) s=parts[parts.length-1].trim();
  return s;
}
function extractProse(raw){
  let s=String(raw||'').trim();
  if(!s) return '';
  if(s==='Thinking…'||s==='… running …') return s;
  s=polishChatText(s);
  // Prefer human fields when result is JSON dump
  if((s.startsWith('{')||s.startsWith('[')) && s.length>2){
    try{
      const j=JSON.parse(s);
      if(typeof j==='string') return j;
      if(j && typeof j==='object'){
        for(const k of ['message','brief','summary','text','result','answer','output','content','note']){
          if(typeof j[k]==='string' && j[k].trim()) return polishChatText(j[k]);
        }
        if(Array.isArray(j.steps)){
          return j.steps.map((st,i)=>{
            if(typeof st==='string') return (i+1)+'. '+st;
            return (i+1)+'. '+(st.skill||st.name||st.action||'')+' '+(st.message||st.prompt||st.status||'');
          }).join('\n');
        }
        if(j.ok!=null && j.message) return String(j.message);
        // compact non-noisy keys only
        const skip=new Set(['ok','status','id','job_id','session_id','ts','created_at','finished_at']);
        const lines=[];
        Object.keys(j).forEach(k=>{
          if(skip.has(k)) return;
          const v=j[k];
          if(v==null||v==='') return;
          if(typeof v==='string'||typeof v==='number'||typeof v==='boolean') lines.push(k+': '+v);
        });
        if(lines.length) return lines.join('\n');
      }
    }catch(_){}
  }
  return s;
}
function lightMarkdown(text){
  // Escape then light markdown: **bold**, `code`, fenced pre, lists, headings
  let s=esc(text);
  s=s.replace(/```([\s\S]*?)```/g,(_,code)=>'<pre>'+code+'</pre>');
  s=s.replace(/`([^`\n]+)`/g,'<code>$1</code>');
  s=s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
  // line-level: headings + bullets
  const blocks=s.split(/\n{2,}/).map(block=>{
    const lines=block.split('\n');
    const allBullets=lines.every(ln=>/^\s*([-*]|\d+\.)\s+/.test(ln)||!ln.trim());
    if(allBullets && lines.some(ln=>ln.trim())){
      const items=lines.filter(ln=>ln.trim()).map(ln=>'<li>'+ln.replace(/^\s*([-*]|\d+\.)\s+/,'')+'</li>').join('');
      return '<ul style="margin:0.4em 0 0.6em 1.1em;padding:0">'+items+'</ul>';
    }
    const rendered=lines.map(ln=>{
      if(/^#{1,3}\s+/.test(ln)){
        const lvl=Math.min(3,(ln.match(/^#+/)||['#'])[0].length);
        const t=ln.replace(/^#{1,3}\s+/,'');
        return '<div class="md-h" style="font-weight:700;font-size:'+(lvl===1?'1.05em':lvl===2?'1em':'0.95em')+';margin:0.5em 0 0.25em">'+t+'</div>';
      }
      if(/^\s*([-*]|\d+\.)\s+/.test(ln)) return '<div class="md-li" style="padding-left:1em">• '+ln.replace(/^\s*([-*]|\d+\.)\s+/,'')+'</div>';
      return ln;
    }).join('<br>');
    return '<p style="margin:0.45em 0">'+rendered+'</p>';
  });
  return blocks.join('');
}
function formatProseBody(body){
  // Infinite Wiki Profile Card JSON → interactive card UI
  const wikiHtml = tryRenderWikiCard(body);
  if(wikiHtml) return wikiHtml;
  const prose=extractProse(body);
  // keep image embeds from original
  const imgs=[];
  const re=/!\[([^\]]*)\]\((data:image\/[a-zA-Z+]+;base64,[A-Za-z0-9+/=]+)\)/g;
  let m, src=String(body||'');
  while((m=re.exec(src))){
    imgs.push(`<div style="margin:8px 0"><img alt="${esc(m[1]||'shot')}" src="${m[2]}" style="max-width:100%;border-radius:8px;border:1px solid var(--line)"/></div>`);
  }
  const cleaned=prose.replace(/!\[[^\]]*\]\(data:image\/[a-zA-Z+]+;base64,[A-Za-z0-9+/=]+\)/g,'').trim();
  // Collapse engine meta into a small dim line when still present
  let main=cleaned;
  const metaLines=[];
  main=main.split('\n').filter(ln=>{
    if(/^\[(engine|cli|research_package|pocket_session|stream_tokens|llm_tokens)/i.test(ln.trim())){
      metaLines.push(ln.trim().replace(/^\[|\]$/g,''));
      return false;
    }
    return true;
  }).join('\n').trim();
  const metaHtml=metaLines.length
    ? `<div class="mh-meta" style="opacity:0.55;font-size:11px;margin-bottom:6px">${esc(metaLines.slice(0,3).join(' · '))}</div>`
    : '';
  return metaHtml+lightMarkdown(main||(imgs.length?'':'…'))+imgs.join('');
}
/** Parse Profile Card / goto JSON from agent output and render interactive UI. */
function tryRenderWikiCard(body){
  const raw=String(body||'').trim();
  if(!raw || raw[0]!=='{' ) return '';
  let j=null;
  try{ j=JSON.parse(raw); }catch(_){
    // try first JSON object embedded
    const i=raw.indexOf('{'), k=raw.lastIndexOf('}');
    if(i>=0 && k>i){
      try{ j=JSON.parse(raw.slice(i,k+1)); }catch(__){ return ''; }
    } else return '';
  }
  if(!j || typeof j!=='object') return '';
  // goto_definition payload
  if(Array.isArray(j.definitions)){
    return renderGotoCard(j);
  }
  // profile card
  if(j.ok && (j.symbols || j.sections) && (j.path || j.schema==='pocket.file_profile.v1')){
    return renderProfileCard(j);
  }
  return '';
}
function renderProfileCard(card){
  const path=card.path||'';
  const id='wc_'+Math.random().toString(36).slice(2,9);
  const ast=card.ast_engine||'heuristic';
  const syms=(card.symbols||[]).slice(0,24);
  const symHtml=syms.map(s=>{
    const n=s.name||'?';
    const ln=s.line||1;
    const en=s.end_line||ln;
    return `<button type="button" class="wc-sym" data-wiki-open="1" data-path="${esc(path)}" data-name="${esc(n)}" data-start="${ln}" data-end="${en}" title="Open definition L${ln}–L${en}">
      <b>${esc(n)}</b><em>${esc(s.kind||'sym')} · L${ln}–L${en}</em>
    </button>`;
  }).join('') || '<span style="color:var(--muted);font-size:12px">No symbols</span>';
  return `<div class="wiki-card" id="${id}" data-wiki-path="${esc(path)}">
    <div class="wc-head">
      <span class="wc-badge">Wiki</span>
      <div class="wc-title"><b>${esc(card.name||path.split(/[/\\\\]/).pop()||'file')}</b>
        <span>${esc(card.language||'')} · ${esc(String(card.line_count||'?'))} lines · ${esc(String((card.deps||[]).length))} deps</span>
      </div>
      <span class="wc-ast ${ast==='tree-sitter'?'ts':''}" title="AST engine">${esc(ast)}</span>
    </div>
    <div class="wc-sum">${esc((card.summary||'').slice(0,280))}</div>
    <div class="wc-syms">${symHtml}</div>
    <div class="wc-actions">
      <button type="button" class="primary" data-wiki-open-top="1" data-path="${esc(path)}" data-name="${esc((syms[0]&&syms[0].name)||'')}" data-start="${(syms[0]&&syms[0].line)||1}" data-end="${(syms[0]&&syms[0].end_line)||40}">Open definition</button>
      <button type="button" data-wiki-slice="1" data-path="${esc(path)}" data-start="1" data-end="40">Read head</button>
      <button type="button" data-wiki-copy="1" data-path="${esc(path)}">Copy path</button>
    </div>
    <div class="wiki-slice" id="${id}_slice" style="display:none"><pre></pre></div>
  </div>`;
}
function renderGotoCard(g){
  const defs=g.definitions||[];
  const rows=defs.slice(0,12).map(d=>`
    <button type="button" class="wc-sym" data-wiki-open="1" data-path="${esc(d.path||'')}" data-name="${esc(d.name||g.name||'')}" data-start="${d.line||1}" data-end="${d.end_line||(d.line||1)}">
      <b>${esc(d.name||'?')}</b><em>${esc((d.path||'').split(/[/\\\\]/).pop()||'')} · L${d.line||'?'}–L${d.end_line||'?'} ${d.via?('· '+d.via):''}</em>
    </button>`).join('') || '<span style="color:var(--muted);font-size:12px">No definitions</span>';
  return `<div class="wiki-card">
    <div class="wc-head">
      <span class="wc-badge">Def</span>
      <div class="wc-title"><b>goto ${esc(g.name||'')}</b>
        <span>${defs.length} hit(s)${g.from_path?(' · from '+esc(String(g.from_path).split(/[/\\\\]/).pop()||''))):''}</span>
      </div>
    </div>
    <div class="wc-syms">${rows}</div>
  </div>`;
}
async function openWikiDefinition(path, name, start, end){
  if(!path){ toast('No path','err'); return; }
  const s=Number(start)||1, e=Number(end)|| (s+30);
  try{
    // Prefer goto when we have a name (cross-file)
    if(name){
      try{
        const g=await api('/v1/wiki/goto',{method:'POST',body:JSON.stringify({name, from_path:path})});
        const d=(g.definitions||[])[0];
        if(d && d.path){
          path=d.path; start=d.line||s; end=d.end_line||e;
        }
      }catch(_){}
    }
    const slice=await api('/v1/wiki/lines',{method:'POST',body:JSON.stringify({path, start:Number(start)||s, end:Number(end)||e})});
    if(!slice.ok){ toast(slice.error||'read failed','err'); return; }
    // Find nearest card slice pane or append under transcript
    let host=document.querySelector('.wiki-card[data-wiki-path="'+CSS.escape(path)+'"] .wiki-slice');
    if(!host){
      // last wiki-card slice or create ephemeral
      const cards=document.querySelectorAll('.wiki-card .wiki-slice');
      host=cards[cards.length-1]||null;
    }
    if(!host){
      const box=$('transcript');
      const wrap=document.createElement('div');
      wrap.className='wiki-slice';
      wrap.innerHTML='<pre></pre>';
      box.appendChild(wrap);
      host=wrap;
      box.scrollTop=box.scrollHeight;
    }
    host.style.display='block';
    const pre=host.querySelector('pre');
    if(pre) pre.textContent = (name?('// '+name+' @ '+path+'\n'):('// '+path+'\n'))+(slice.text||'');
    toast((name||'slice')+' · L'+(slice.start)+'–L'+(slice.end));
  }catch(e){ toast('Open definition: '+(e.message||e),'err'); }
}
// Event delegation for wiki card buttons
document.addEventListener('click', (ev)=>{
  const t=ev.target.closest('[data-wiki-open],[data-wiki-open-top],[data-wiki-slice],[data-wiki-copy]');
  if(!t) return;
  ev.preventDefault();
  const path=t.getAttribute('data-path')||'';
  const name=t.getAttribute('data-name')||'';
  const start=t.getAttribute('data-start')||'1';
  const end=t.getAttribute('data-end')||'40';
  if(t.hasAttribute('data-wiki-copy')){
    try{ navigator.clipboard.writeText(path); toast('Path copied'); }catch(_){ toast(path); }
    return;
  }
  if(t.hasAttribute('data-wiki-slice')){
    openWikiDefinition(path, '', start, end);
    return;
  }
  openWikiDefinition(path, name, start, end);
});
function saDotClass(w){
  const st=String(w.status||'idle').toLowerCase();
  if(/run|active|busy|queue|created/.test(st)) return 'run';
  if(/fail|error/.test(st)) return 'fail';
  if(/done|ok/.test(st)) return 'done';
  const src=String(w.source||'').toLowerCase();
  const name=String(w.name||w.id||'').toUpperCase();
  if(src==='mesh'||MESH_AGENTS.includes(name)||name.includes('HEADLESS')||name==='DESIGN') return 'mesh';
  if(/ready|idle|catalog/.test(st)) return 'ready';
  return '';
}
function saSrcBadge(w){
  const name=String(w.name||w.id||'').toUpperCase();
  const src=String(w.source||'').toLowerCase();
  if(name==='DESIGN'||name==='DESIGNER'||src==='design') return '<span class="sa-src design">design</span>';
  if(name.includes('HEADLESS')||src==='headless') return '<span class="sa-src headless">headless</span>';
  if(src==='latin'||LATIN_WORKERS.includes(name)) return '<span class="sa-src latin">latin</span>';
  if(src==='mesh') return '<span class="sa-src headless">mesh</span>';
  if(src==='dynamic'||src==='dispatch') return '<span class="sa-src">live</span>';
  return '';
}
function updateMeshChrome(){
  const cnt=$('saCount');
  const drive=$('meshDrive');
  const n=meshInfo.agent_count||0;
  if(cnt){
    cnt.textContent=String(n||subagentState.length||0);
    cnt.title=n?('Mesh agents: '+n):'Subagents';
  }
  if(drive){
    const root=String(meshInfo.mesh_root||'');
    const onE=/^E:/i.test(root)||String(meshInfo.drive||'').toUpperCase()==='E:';
    if(root){
      drive.style.display='inline-flex';
      drive.textContent=onE?'E: mesh':(String(meshInfo.drive||root.slice(0,2)||'mesh'));
      drive.className='mesh-pill'+(onE?'':' off');
      drive.title=root;
    } else {
      drive.style.display='none';
    }
  }
}
function renderSubagents(list){
  subagentState=Array.isArray(list)?list:[];
  const roster=$('subagentRoster');
  updateMeshChrome();
  if(roster){
    if(!subagentState.length){
      roster.innerHTML='<div class="rr-empty">Idle — use @DESIGN / @FORGE / @ARCHON</div>';
    } else {
      roster.innerHTML='';
      // Section: mesh core (DESIGN + headless) then live others
      const meshCore=subagentState.filter(w=>{
        const n=String(w.name||w.id||'').toUpperCase();
        const src=String(w.source||'');
        return MESH_AGENTS.includes(n)||src==='mesh'||src==='headless'||src==='design';
      });
      const live=subagentState.filter(w=>{
        const n=String(w.name||w.id||'').toUpperCase();
        const src=String(w.source||'');
        return !MESH_AGENTS.includes(n)&&src!=='mesh'&&src!=='headless'&&src!=='design';
      });
      const paint=(arr, label)=>{
        if(!arr.length) return;
        if(label){
          const sec=document.createElement('div');
          sec.className='rr-sec';
          sec.textContent=label;
          roster.appendChild(sec);
        }
        arr.forEach(w=>{
          const row=document.createElement('div');
          row.className='sa-row';
          const dot=saDotClass(w);
          row.innerHTML=`<span class="sa-dot ${dot}"></span>${saSrcBadge(w)}<span class="sa-name">${esc(w.name||w.id||'?')}</span>
            <span class="sa-meta">${esc(w.goal||w.role||w.job||w.status||'')}${w.steps!=null?(' · '+w.steps):''}</span>`;
          roster.appendChild(row);
        });
      };
      // Prefer fixed DESIGN + 4 headless order
      const coreOrder=MESH_AGENTS.slice();
      const orderedCore=[];
      coreOrder.forEach(id=>{
        const hit=meshCore.find(w=>String(w.name||w.id||'').toUpperCase()===id);
        if(hit) orderedCore.push(hit);
      });
      meshCore.forEach(w=>{
        const n=String(w.name||w.id||'').toUpperCase();
        if(!coreOrder.includes(n) && !orderedCore.includes(w)) orderedCore.push(w);
      });
      paint(orderedCore, orderedCore.length?'Mesh':'');
      paint(live, live.length?'Active':'');
    }
  }
  // Live-refresh open inline accordions from current roster
  try{
    document.querySelectorAll('.subagents-panel[open] .sa-list').forEach(listEl=>{
      if(!subagentState.length) return;
      listEl.innerHTML='';
      subagentState.forEach(w=>{
        const row=document.createElement('div');
        row.className='sa-row';
        const dot=saDotClass(w);
        row.innerHTML=`<span class="sa-dot ${dot}"></span><span class="sa-name">${esc(w.name||w.id||'?')}</span>
          <span class="sa-meta">${esc(w.goal||w.role||w.status||'')}</span>`;
        listEl.appendChild(row);
      });
    });
  }catch(_){}
}
function renderWalkthrough(steps){
  walkthroughSteps=Array.isArray(steps)?steps.slice(-24):walkthroughSteps;
  const body=$('walkthroughBody');
  const c=$('wtCount');
  if(c) c.textContent=String(walkthroughSteps.length);
  if(!body) return;
  if(!walkthroughSteps.length){
    body.innerHTML='<div class="wt-empty">Steps appear as agents work.</div>';
    return;
  }
  body.innerHTML='';
  walkthroughSteps.forEach((st,i)=>{
    const d=document.createElement('div');
    const last=i===walkthroughSteps.length-1;
    d.className='wt-step '+(last?'on':'done');
    d.innerHTML=`<span class="wt-n">${i+1}</span><div><b style="font-weight:600;color:var(--fg)">${esc(st.agent||st.kind||'step')}</b>
      <div style="color:var(--muted);font-size:11px;margin-top:2px">${esc(st.message||'')}</div></div>`;
    body.appendChild(d);
  });
  body.scrollTop=body.scrollHeight;
}
async function pollSubagents(){
  const byName={};
  // Primary: unified registry GET /v1/subagents (latin + mesh DESIGN/headless + dynamic)
  try{
    const j=await api('/v1/subagents');
    const arr=j.subagents||j.workers||j.items||[];
    if(j.mesh && typeof j.mesh==='object'){
      meshInfo={
        agent_count:Number(j.mesh.agent_count||0)||0,
        mesh_root:String(j.mesh.mesh_root||''),
        drive:String(j.mesh.drive||'')
      };
    }
    if(Array.isArray(arr)){
      subagentCatalog=arr;
      arr.forEach(w=>{
        // Prefer canonical id (FORGE_HEADLESS) over display name
        const id=String(w.id||'').toUpperCase().replace(/\s+/g,'_');
        let name=String(w.name||w.id||'SUB').toUpperCase().replace(/\s+/g,'_');
        if(MESH_AGENTS.includes(id)) name=id;
        if(!name) return;
        const st=String(w.status||'').toLowerCase();
        const live=/run|active|busy|queue|created/.test(st);
        const src=String(w.source||'');
        // Always surface DESIGN + 4 headless + design/headless sources + live
        const isMeshCore=MESH_AGENTS.includes(name)||src==='mesh'||src==='headless'||src==='design';
        if(live||isMeshCore){
          byName[name]={
            id:id||name, name,
            goal:w.goal||w.task||w.message||w.role||MESH_AGENT_ROLES[name]||'',
            status:live?(w.status||'running'):(w.status||'ready'),
            steps:w.steps, role:w.role, source:src||(isMeshCore?'mesh':'')
          };
        }
      });
    }
  }catch(_){}
  // Ensure DESIGN + 4 headless always appear even if registry soft-fails
  MESH_AGENTS.forEach(name=>{
    if(!byName[name]){
      byName[name]={
        id:name, name,
        goal:MESH_AGENT_ROLES[name]||'mesh',
        status:'ready',
        source:'mesh',
        role:MESH_AGENT_ROLES[name]||'mesh'
      };
    }
  });
  // Dynamic workers (extra live signal)
  try{
    const j=await api('/v1/workers/dynamic');
    (j.workers||[]).forEach(w=>{
      const name=String(w.name||w.id||'WORKER').toUpperCase();
      byName[name]={id:w.id,name,goal:w.goal||'',status:w.status||'running',steps:w.steps,source:'dynamic'};
    });
  }catch(_){}
  // Latin live daemon
  try{
    const j=await api('/v1/workers/live');
    const workers=j.workers||j.status||j.live||{};
    const list=Array.isArray(workers)?workers:Object.values(workers||{});
    const nowSec=Date.now()/1000;
    list.forEach(w=>{
      if(!w||typeof w!=='object') return;
      const name=String(w.id||w.name||'').toUpperCase();
      if(!name) return;
      const st=String(w.status||'idle').toLowerCase();
      const recent=w.last_at && (nowSec-Number(w.last_at))<120;
      if(/run|busy|active|queue/.test(st) || recent){
        byName[name]=byName[name]||{id:name,name,goal:w.last_job||'',status:w.status||'idle',steps:w.runs,source:'latin'};
        if(/run|busy|active|queue/.test(st)) byName[name].status=w.status;
        if(w.last_job) byName[name].goal=w.last_job;
      }
    });
  }catch(_){}
  // Mentions / dispatches from recent activity (override status → running)
  Object.keys(liveAgentHits).forEach(k=>{
    const hit=liveAgentHits[k];
    if(!hit||(Date.now()-hit.t)>120000) return;
    if(!byName[k]) byName[k]={id:k,name:k,goal:hit.message||'',status:hit.status||'running',source:'dispatch'};
    else {
      byName[k].status=hit.status||'running';
      if(hit.message) byName[k].goal=hit.message;
    }
  });
  // Fallback mesh status if not attached to /v1/subagents
  if(!meshInfo.mesh_root){
    try{
      const m=await api('/v1/mesh');
      if(m&&m.ok!==false){
        meshInfo={
          agent_count:Number(m.agent_count||0)||Object.keys(byName).length,
          mesh_root:String(m.mesh_root||''),
          drive:String(m.drive||'')
        };
      }
    }catch(_){}
  }
  if(!meshInfo.agent_count) meshInfo.agent_count=Object.keys(byName).length;
  renderSubagents(Object.values(byName));
}
async function pollLiveActions(){
  try{
    const j=await api('/v1/live/events?after='+liveSeq);
    const evs=j.events||[];
    if(!evs.length) return;
    const box=$('liveActions');
    evs.forEach(e=>{
      liveSeq=Math.max(liveSeq, e.seq||0);
      const agent=String(e.agent||e.kind||'').toUpperCase();
      const msg=String(e.message||'');
      // Track latin / mesh / named workers for subagent panel
      let hitName=agent;
      const known=LATIN_WORKERS.concat(MESH_AGENTS);
      if(!known.includes(hitName)){
        const found=known.find(w=>agent.includes(w)||msg.toUpperCase().includes(w));
        if(found) hitName=found;
      }
      if(hitName && (known.includes(hitName)||agent)){
        liveAgentHits[hitName||agent]={t:Date.now(),message:msg,status:'running',role:e.role||'host'};
      }
      walkthroughSteps.push({agent:e.agent||e.kind||'host', message:msg, kind:e.kind, ts:e.ts});
      if(box){
        const line=document.createElement('div');
        const role=(e.role||'host');
        const col=role==='llm'?'#fbbf24':(role==='python'?'#34d399':'#94a3b8');
        line.innerHTML=`<span style="color:var(--muted)">${esc(e.ts||'')}</span> <b style="color:${col}">${esc(e.agent||e.kind||'')}</b> <span style="color:var(--muted)">[${esc(role)}]</span> ${esc(msg)}`;
        box.appendChild(line);
      }
    });
    if(box){
      box.scrollTop=box.scrollHeight;
      while(box.children.length>80) box.removeChild(box.firstChild);
    }
    renderWalkthrough(walkthroughSteps);
    // refresh roster when workers chatter
    pollSubagents();
  }catch(_){}
}
async function pollLiveVision(){
  try{
    const j=await api('/v1/live/vision');
    if(j.base64){
      const img=$('liveVision');
      if(img) img.src='data:'+(j.mime||'image/jpeg')+';base64,'+j.base64;
      const m=$('liveVisionMeta');
      if(m) m.textContent='seq '+(j.seq||0)+' · OCULUS first-class';
    }
  }catch(_){}
}
async function visionObserve(){
  try{
    const j=await api('/v1/vision/understand');
    const el=$('visionOut'); if(el){ el.style.display='block';
      el.textContent=(j.primary_modality||'')+'\n'+(j.why_primary||'')+'\n\n'+(j.brief||'').slice(0,1200); }
    toast('Primary: '+(j.primary_modality||'?'));
  }catch(e){ toast(e.message); }
}
async function pixelText(){
  try{
    const j=await api('/v1/pixel/text');
    const el=$('visionOut'); if(el){ el.style.display='block'; el.textContent=(j.text||j.brief||'').slice(0,2000); }
    toast('Pixel→text · '+(j.primary_modality||''));
  }catch(e){ toast(e.message); }
}
async function fullPageRender(){
  try{
    toast('Full page render…');
    const j=await api('/v1/vision/page');
    const el=$('visionOut'); if(el){ el.style.display='block';
      el.textContent=(j.brief||'')+'\n\ncounts '+JSON.stringify(j.counts||{})+'\n\n'+(j.page_text||'').slice(0,2500); }
    toast('Symbols '+(j.counts&&j.counts.symbols||0)+' · '+(j.primary_modality||''));
  }catch(e){ toast(e.message); }
}
let _streamOn=false;
async function streamToggle(){
  try{
    if(!_streamOn){
      await api('/v1/vision/stream/start',{method:'POST',body:JSON.stringify({interval:1.5})});
      _streamOn=true; toast('Vision stream ON');
      pollStream();
    }else{
      await api('/v1/vision/stream/stop',{method:'POST',body:JSON.stringify({})});
      _streamOn=false; toast('Vision stream OFF');
    }
  }catch(e){ toast(e.message); }
}
let _streamAfter=0;
async function pollStream(){
  if(!_streamOn) return;
  try{
    const j=await api('/v1/vision/stream?after='+_streamAfter);
    const latest=j.latest||(j.frames&&j.frames[j.frames.length-1]);
    if(latest){
      _streamAfter=latest.seq||_streamAfter;
      const el=$('visionOut'); if(el){ el.style.display='block';
        el.textContent='STREAM #'+latest.seq+' · '+(latest.primary_modality||'')+'\n'+(latest.brief||'')+'\n\n'+(latest.page_text_head||'').slice(0,1800); }
      if(latest.seq) $('liveVisionMeta').textContent='stream seq '+latest.seq+' · '+(latest.page_hint||'');
    }
  }catch(_){}
  if(_streamOn) setTimeout(pollStream, 1600);
}
async function spawnDynamic(){
  const goal=prompt('Worker goal (dynamic AI-style, not a fixed script):','explore the current screen and scroll like a user');
  if(!goal) return;
  try{
    const j=await api('/v1/workers/spawn',{method:'POST',body:JSON.stringify({goal,name:'AUTON',max_steps:8})});
    toast(j.message||j.name||'spawned');
    const el=$('orchOut'); if(el){ el.style.display='block'; el.textContent=JSON.stringify(j,null,2).slice(0,4000); }
  }catch(e){ toast(e.message); }
}
async function orchChatSend(record){
  const t=($('orchChat')&&$('orchChat').value||'').trim();
  if(!t){ toast('Type a workflow'); return; }
  try{
    toast('Platform API running…');
    const j=await api('/v1/orchestrator/chat',{method:'POST',body:JSON.stringify({text:t,prompt:t,record:!!record})});
    const el=$('orchOut'); if(el){ el.style.display='block'; el.textContent=JSON.stringify(j.result||j,null,2).slice(0,5000); }
    toast((j.result&&j.result.message)||'done');
  }catch(e){ toast(e.message); }
}
async function runCampaign(){
  const t=($('orchChat')&&$('orchChat').value||'').trim()||'POCKET host co-pilot research campaign';
  try{
    toast('Campaign via platform API…');
    const j=await api('/v1/campaigns/run',{method:'POST',body:JSON.stringify({topic:t,record:true,commercial:true})});
    const el=$('orchOut'); if(el){ el.style.display='block'; el.textContent=JSON.stringify(j.campaign||j,null,2).slice(0,5000); }
    toast((j.campaign&&j.campaign.message)||'campaign done');
  }catch(e){ toast(e.message); }
}
function ensureLivePoll(){
  if(liveTimer) return;
  liveTimer=setInterval(()=>{ pollLiveActions(); pollLiveVision(); }, 900);
  pollLiveActions();
  pollLiveVision();
  if(!subagentTimer){
    subagentTimer=setInterval(pollSubagents, 2500);
    pollSubagents();
  }
}
async function sendMsg(){
  if(!activeId){ toast('Start or select a session first'); return; }
  let text=$('input').value.trim();
  if(!text) return;
  // Resolve /actions before send
  if(text.startsWith('/')){
    const sm=$('slashMenu'); if(sm){ sm.classList.remove('open'); sm.innerHTML=''; }
    if(/^\/(help|actions)\b/i.test(text)){
      const resolved=resolveSlash(text);
      $('input').value='';
      const box=$('transcript');
      if(box && !box.querySelector('.msg')) box.innerHTML='';
      if(box){
        const u=document.createElement('div'); u.className='msg user';
        u.innerHTML=`<div class="mb">${esc(text)}</div>`; box.appendChild(u);
        const a=document.createElement('div'); a.className='msg agent done';
        a.innerHTML=`<div class="mh"><span>pocket</span><span>done</span></div>
          <div class="mb prose">${lightMarkdown(resolved)}</div>`;
        box.appendChild(a);
        box.scrollTop=box.scrollHeight;
      }
      return;
    }
    text=resolveSlash(text);
  }
  $('sendBtn').disabled=true;
  closeComposerMenus();
  ensureLivePoll();
  let dispatchNote=null;
  try{
    // Always fire dispatch when @ is present (DESIGN / headless / Latin / any @NAME)
    if(hasAtMention(text) || parseMentions(text).length){
      dispatchNote=await dispatchMentions(text);
      if(dispatchNote.endpointMissing){
        console.info('POST /v1/subagents/dispatch not available yet — session message carries work');
        toast('Mesh dispatch offline — message still sent', 'err');
      }
      // toast + inline card handled inside dispatchMentions
    }
    const sendRes=await api('/v1/sessions/'+activeId+'/messages',{method:'POST',body:JSON.stringify({
      text,
      workspace:$('wsSelect').value||'workspace',
      device:DEVICE,
      interrupt:true
    })});
    if(sendRes && sendRes.superseded_jobs && sendRes.superseded_jobs.length){
      toast('Stopped prior turn · running latest prompt');
    }
    $('input').value='';
    if(DEVICE.kind==='phone') closeDrawers();
    await selectSess(activeId);
    // Re-attach clean dispatch card after transcript reload (avoid raw JSON dumps)
    if(dispatchNote && dispatchNote.dispatched && dispatchNote.dispatched.length && !dispatchNote.endpointMissing){
      showDispatchInline(dispatchNote.dispatched, dispatchNote.message);
    }
  }catch(e){ toast('Send failed: '+e.message, 'err'); }
  $('sendBtn').disabled=false;
}
function toggleMic(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){ toast('Mic needs Chrome, Edge, or Safari'); return; }
  // Click again to turn OFF — otherwise stays on (continuous / restarts)
  if(micOn){
    micOn=false;
    try{ if(micRec) micRec.stop(); }catch(_){}
    $('micBtn').classList.remove('hot');
    toast('Mic off');
    return;
  }
  micOn=true;
  $('micBtn').classList.add('hot');
  toast('Mic on — stays listening until you click again');
  const startRec=()=>{
    if(!micOn) return;
    try{
      micRec=new SR();
      micRec.lang='en-US';
      micRec.interimResults=true;
      micRec.continuous=true;
      micRec.onresult=(e)=>{
        let final='';
        for(let i=e.resultIndex;i<e.results.length;i++){
          if(e.results[i].isFinal) final+=e.results[i][0].transcript;
        }
        if(final){
          const el=$('input');
          el.value=(el.value?el.value+' ':'')+final.trim();
        }
      };
      micRec.onerror=(ev)=>{
        // no-speech / aborted: keep intent ON and restart; only hard-fail ends session
        const hard=['not-allowed','service-not-allowed','audio-capture','network'];
        if(hard.includes(ev.error)){
          micOn=false;
          $('micBtn').classList.remove('hot');
          toast('Mic: '+(ev.error||'error'));
        }
      };
      micRec.onend=()=>{
        // Browser often stops after a phrase — stay ON by restarting
        if(micOn){
          setTimeout(()=>{ try{ if(micOn) startRec(); }catch(_){ } }, 280);
        } else {
          $('micBtn').classList.remove('hot');
        }
      };
      micRec.start();
    }catch(e){
      // Already started race — ignore; other errors toast
      if(String(e).indexOf('already')<0){
        toast('Mic start failed');
        micOn=false;
        $('micBtn').classList.remove('hot');
      }
    }
  };
  startRec();
}
async function uploadFiles(list){
  const ws=$('wsSelect').value||'workspace';
  const note=$('uploadNote');
  note.textContent='Uploading…';
  let ok=0, fail=0;
  for(const f of list){
    try{
      const b64=await fileToB64(f);
      const j=await api('/v1/files/upload',{method:'POST',body:JSON.stringify({workspace:ws,filename:f.name,content_base64:b64,size:f.size})});
      if(j.ok) ok++; else fail++;
    }catch(_){ fail++; }
  }
  note.textContent=`Uploaded ${ok}${fail?(' · failed '+fail):''} → ${ws}/uploads`;
  toast(note.textContent);
}
function fileToB64(file){
  return new Promise((res,rej)=>{
    const r=new FileReader();
    r.onload=()=>{ const s=String(r.result||''); const i=s.indexOf('base64,'); res(i>=0?s.slice(i+7):s); };
    r.onerror=rej; r.readAsDataURL(file);
  });
}
async function refreshLive(){
  try{
    const j=await api('/v1/live');
    const box=$('liveList'); box.innerHTML='';
    (j.services||[]).forEach(s=>{
      const d=document.createElement('div'); d.className='svc';
      const live=!!s.live;
      let acts='';
      if(s.url) acts+=`<a href="${s.url}" target="_blank">Open</a>`;
      if(s.connectable && !live) acts+=`<button type="button" data-id="${s.id}">Connect</button>`;
      d.innerHTML=`<div class="row"><b>${esc(s.name)}</b><span class="st ${live?'live':'down'}">${live?'LIVE':'DOWN'}</span></div><div class="act">${acts}</div>`;
      const btn=d.querySelector('button[data-id]');
      if(btn) btn.onclick=()=>connectOne(s.id);
      box.appendChild(d);
    });
  }catch(_){}
}
async function connectOne(id){
  try{ await api('/v1/live/connect',{method:'POST',body:JSON.stringify({service:id})}); toast('Connect requested'); setTimeout(refreshLive,1500);}catch(e){ toast(e.message); }
}
async function connectAll(){
  try{ await api('/v1/live/connect',{method:'POST',body:JSON.stringify({service:'all'})}); toast('Connecting services…'); setTimeout(refreshLive,2000);}catch(e){ toast(e.message); }
}
async function refreshUsage(){
  try{
    const u=await api('/v1/usage');
    $('uTok').textContent=(u.llm_tokens||u.est_tokens||0).toLocaleString();
  }catch(_){}
  try{
    const t=await api('/v1/tokenomics');
    $('uBal').textContent=(t.balance||0).toLocaleString();
  }catch(_){}
  try{
    const p=await api('/v1/platform');
    const y=p.you_have||{};
    const box=$('deployList'); box.innerHTML='';
    (p.deploys||[]).filter(d=>d.status==='running').forEach(d=>{
      const row=document.createElement('div');
      row.style.margin='4px 0';
      row.innerHTML=`<a href="${d.url_local||'#'}" target="_blank">${esc(d.title||d.id)}</a> <span>${d.kind||''}</span> `;
      if(d.id && d.log_path){
        const b=document.createElement('button'); b.type='button'; b.textContent='logs'; b.className='icon';
        b.onclick=async()=>{ const lg=await api('/v1/deploys/'+d.id+'/log'); const el=$('deployLog'); el.style.display='block'; el.textContent=lg.log_tail||'(empty)'; };
        row.appendChild(b);
      }
      box.appendChild(row);
    });
    if(!(p.deploys||[]).filter(d=>d.status==='running').length) box.textContent='No live deploys';
  }catch(_){}
}
async function deployKind(kind){
  try{
    const ws=$('wsSelect').value||'workspace';
    const j=await api('/v1/deploy',{method:'POST',body:JSON.stringify({kind,workspace:ws,title:ws+'-'+kind})});
    if(j.ok){
      if(j.url_local) window.open(j.url_local,'_blank');
      toast((kind)+' deploy ready');
      if(j.id){ try{ const lg=await api('/v1/deploys/'+j.id+'/log'); const el=$('deployLog'); el.style.display='block'; el.textContent=lg.log_tail||''; }catch(_){ } }
      refreshUsage();
    } else toast(j.error||'deploy failed');
  }catch(e){ toast('Deploy: '+e.message); }
}
async function openDoc(key){
  try{
    const j=await api('/v1/docs/'+key);
    const text=j.text||JSON.stringify(j,null,2);
    const w=window.open('','_blank');
    w.document.write('<pre style="white-space:pre-wrap;font:13px/1.45 ui-monospace,monospace;padding:16px;background:#0a0a0b;color:#e4e4e7">'+esc(text)+'</pre>');
  }catch(e){ toast('Doc failed: '+e.message); }
}
async function grokPull(){
  try{
    await api('/v1/grok/pull',{method:'POST',body:JSON.stringify({prompt:'Full status pull with research plan'})});
    toast('Research pull written');
  }catch(e){ toast(e.message); }
}
async function runDoctor(){
  try{
    let j;
    try{ j=await api('/v1/ready'); }catch(_){ j=await api('/v1/doctor'); }
    const el=$('doctorOut');
    el.style.display='block';
    if(j.items){
      el.textContent = 'POCKET '+j.version+' production '+j.ready_score+'\n'+
        'trust: '+(j.trust_model||'')+'\n'+
        (j.items||[]).map(c=>(c.ok?'OK ':'-- ')+c.id+' '+c.name+(c.detail?(' · '+c.detail):'')).join('\n');
    } else {
      el.textContent = 'POCKET '+j.version+' ready '+j.ready_score+'\n'+
        (j.checks||[]).map(c=>(c.ok?'OK ':'-- ')+c.name+' '+(c.detail||'')).join('\n');
    }
    toast('Ready '+(j.ready_score||''));
  }catch(e){ toast(e.message); }
}
async function quickDesktop(){
  try{
    await newSess('desktop');
    $('input').value='open notepad';
    await sendMsg();
  }catch(e){ toast(e.message); }
}
async function quickWeb(){
  try{
    await newSess('web');
    $('input').value='search multi agent desktop AI platforms';
    await sendMsg();
  }catch(e){ toast(e.message); }
}
async function quickNexus(){
  try{
    await newSess('nexus');
    $('input').value='list';
    await sendMsg();
  }catch(e){ toast(e.message); }
}
async function loadAiCatalog(){
  try{
    const j=await api('/v1/ai');
    const el=$('aiOut'); el.style.display='block';
    const agents=(j.agents||[]).map(a=>`${a.id} · ${a.tier} · ${a.pock} POCK · $${a.usd_hint}`).join('\n');
    el.textContent='POCKET AI API '+((j.product&&j.product.version)||'')+'\n'+
      'Sell starter $'+(j.sell&&j.sell.starter_usd)+' / pro $'+(j.sell&&j.sell.pro_usd)+'\n\n'+agents;
    toast('AI catalog loaded');
  }catch(e){ toast(e.message); }
}
async function createApiKey(){
  try{
    const j=await api('/v1/ai/keys',{method:'POST',body:JSON.stringify({name:'desk-'+Date.now(),tier:'pro'})});
    const el=$('aiOut'); el.style.display='block';
    el.textContent='API KEY (copy now — shown once):\n'+(j.key||'')+'\n\n'+
      (j.auth_header||'')+'\n\nid='+j.id+' tier='+j.tier;
    if(j.key){ try{ await navigator.clipboard.writeText(j.key); toast('API key copied'); }catch(_){ toast('API key created — copy from panel'); } }
    else toast(j.error||'key failed');
  }catch(e){ toast(e.message); }
}
async function runHeadless(agentId){
  try{
    const task=prompt('Task for headless agent "'+agentId+'":','')||'';
    if(!task) return;
    toast('Running '+agentId+'…');
    const j=await api('/v1/ai/agents/'+agentId+'/run',{method:'POST',body:JSON.stringify({task,sync:true,device:DEVICE})});
    const el=$('aiOut'); el.style.display='block';
    const body=typeof j.result==='string'?j.result:JSON.stringify(j.result||j,null,2);
    el.textContent='agent='+agentId+' ok='+j.ok+' status='+j.status+'\n\n'+(body||j.error||'').slice(0,6000);
    toast(j.ok?'Done '+agentId:'Failed '+agentId);
  }catch(e){ toast(e.message); }
}
function esc(s){return String(s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

// Login bindings — null-safe so a missing node never kills the rest of the desk JS
(function bindLogin(){
  const form=$('loginForm');
  if(form) form.addEventListener('submit',e=>{ e.preventDefault(); doLogin(); });
  const lb=$('loginBtn');
  if(lb){ lb.onclick=function(e){ if(e) e.preventDefault(); doLogin(); }; }
  const rb=$('regBtn');
  if(rb) rb.onclick=doRegister;
  const lp=$('loginPass');
  if(lp) lp.onkeydown=e=>{ if(e.key==='Enter'){ e.preventDefault(); doLogin(); } };
  const lub=$('localUnlockBtn');
  if(lub) lub.onclick=async()=>{
    setLoginErr('Unlocking this PC…');
    const ok=await tryDesktopAutoLogin(true);
    if(!ok) setLoginErr('Local unlock failed — is host running on :8787?');
  };
  // Expose for inline handlers
  window.doLogin=doLogin;
  window.doRegister=doRegister;
  window.setAuthTab=setAuthTab;
})();
const _inputEl=$('input');
if(_inputEl){
  _inputEl.addEventListener('keydown',e=>{
    if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){ e.preventDefault(); sendMsg(); }
    // Phone: Enter sends (Shift+Enter newline)
    if(e.key==='Enter' && !e.shiftKey && DEVICE.kind==='phone'){ e.preventDefault(); sendMsg(); }
    if(e.key==='Escape'){ closeComposerMenus(); }
    // Tab accepts first @mention suggestion
    if(e.key==='Tab'){
      const mm=$('mentionMenu');
      if(mm&&mm.classList.contains('open')){
        const first=mm.querySelector('button');
        if(first){ e.preventDefault(); first.click(); }
      }
    }
  });
  _inputEl.addEventListener('input',()=>{ updateMentionMenu(); updateSlashMenu(); });
}
const _fileIn=$('fileInput');
if(_fileIn) _fileIn.onchange=()=>{ const f=$('fileInput').files; if(f&&f.length) uploadFiles(f); $('fileInput').value=''; };
const _modelPick=$('modelPick');
if(_modelPick){
  _modelPick.addEventListener('change', async()=>{
    _modelPick.dataset.userSet='1';
    const mode=_modelPick.value;
    if(!mode) return;
    if(activeId){
      const cur=(sessions||[]).find(s=>s.id===activeId);
      if(cur && cur.mode===mode) return;
    }
    try{ await newSess(mode); toast('Switched to '+mode); }catch(e){ toast(e.message||'switch failed'); }
  });
}

// Device awareness: detect early + re-check on rotate/resize
detectDevice();
applyDevice();
let _devResizeT=null;
window.addEventListener('resize',()=>{
  clearTimeout(_devResizeT);
  _devResizeT=setTimeout(()=>{ detectDevice(); applyDevice(); }, 200);
});
window.addEventListener('orientationchange',()=>{ setTimeout(()=>{ detectDevice(); applyDevice(); }, 300); });

// boot — then honor ?agent=mesie|nexus|auro from landing cards
boot().then(async()=>{
  try{
    const q=new URLSearchParams(location.search||'');
    const agent=(q.get('agent')||'').toLowerCase();
    if(agent && (sessionStorage.getItem('pocket_token')||localStorage.getItem('pocket_token'))){
      const map={mesie:'mesie',nexus:'nexus',auro:'auro',auro14b:'auro',ro14b:'auro',grok:'grok',codex:'codex'};
      const mode=map[agent]||agent;
      if(['mesie','nexus','auro','grok','codex','claude','plan'].includes(mode)){
        await newSess(mode);
      }
    }
  }catch(_){}
  try{ ensureAiWorkspacePoll(); refreshAiWorkspace(); }catch(_){}
});
</script>
</body>
</html>
"""
