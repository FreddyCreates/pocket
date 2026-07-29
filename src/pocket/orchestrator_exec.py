"""Skill dispatch table — maps skill ids to real host actions."""

from __future__ import annotations

import time
from typing import Any, Dict

from pocket.live_events import emit


def dispatch_skill(sid: str, *, prompt: str = "", params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    params = params or {}
    sid = (sid or "").lower().replace("-", "_")

    # Real discrete skills module
    if sid in {
        "github_one_page", "antigravity_explore", "github_desktop_peek",
        "email_hi_world", "research_interest", "record_start", "record_stop",
        "focused_demo",
    }:
        from pocket.skills_real import (
            skill_github_one_page,
            skill_antigravity_explore,
            skill_github_desktop_peek,
            skill_email_hi_world,
            skill_research_interest,
            skill_record_start,
            skill_record_stop,
            run_focused_demo,
        )
        return {
            "github_one_page": lambda: skill_github_one_page(prompt or params.get("repo") or ""),
            "antigravity_explore": skill_antigravity_explore,
            "github_desktop_peek": skill_github_desktop_peek,
            "email_hi_world": skill_email_hi_world,
            "research_interest": lambda: skill_research_interest(prompt or params.get("repo") or ""),
            "record_start": lambda: skill_record_start(params.get("label") or "orch"),
            "record_stop": skill_record_stop,
            "focused_demo": run_focused_demo,
        }[sid]()

    if sid == "wow_demo" or sid == "fundable_showcase":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(get_orchestrator().wow_plan(), record=True)

    if sid == "record_status":
        from pocket.screen_record import record_status

        return record_status()

    if sid in ("screenshot", "vision_latest"):
        from pocket.capture import capture_screen
        from pocket.live_vision import latest_frame, ensure_vision

        if sid == "vision_latest":
            ensure_vision()
            return latest_frame(include_image=True)
        return capture_screen()

    if sid in ("understand", "pixel_translate", "pixel_understand", "see_screen"):
        from pocket.pixel_translator import understand

        return understand(include_image=False)

    if sid in ("studio_auto", "viral_pack", "studio_render"):
        from pocket.video_studio import auto_viral_pack, render

        if sid == "studio_render":
            return render(
                params.get("source") or prompt,
                preset=params.get("preset") or "rotato_phone",
                title=params.get("title") or "POCKET",
                subtitle=params.get("subtitle") or "Host co-pilot",
                caption=params.get("caption") or "",
                cta=params.get("cta") or "ItsNotAI Labs",
            )
        return auto_viral_pack(
            params.get("source") or prompt or "",
            title=params.get("title") or "POCKET",
            subtitle=params.get("subtitle") or "Real host co-pilot",
            caption=params.get("caption") or "Studio polish",
            cta=params.get("cta") or "ItsNotAI Labs",
        )

    if sid in ("fusion_remake", "remake_page", "page_remake"):
        from pocket.fusion_remake import remake

        return remake(
            refresh_page=bool(params.get("refresh", True)),
            max_ui=int(params.get("max_ui") or 500),
        )

    if sid in ("rfe_synthesize", "rfe", "recursive_fusion", "rfe_v1"):
        from pocket.rfe_kernel import materialize

        return materialize(
            instruction_set=params.get("instruction_set") or params.get("instruction") or "FULL_SYNTHESIS",
            refresh=bool(params.get("refresh", True)),
            max_ui=int(params.get("max_ui") or 500),
        )

    if sid in ("imagine_compose", "imagine_still", "compose_device"):
        from pocket.imagine_studio import compose

        return compose(
            mode=params.get("mode") or params.get("preset") or "rotato_phone",
            image=params.get("image") or params.get("path") or "",
            title=params.get("title") or "POCKET",
            subtitle=params.get("subtitle") or prompt or "Host co-pilot",
        )

    if sid in ("vcomp_open", "virtual_computer", "open_computer"):
        from pocket.virtual_computer import open_computer

        return open_computer(label=params.get("label") or "main")

    if sid in ("vcomp_sense", "computer_sense"):
        from pocket.virtual_computer import sense_computer

        return sense_computer(max_ui=int(params.get("max_ui") or 500))

    if sid in ("vcomp_act", "computer_act"):
        from pocket.virtual_computer import act

        return act(params.get("action") or prompt or "sense", **{k: v for k, v in params.items() if k != "action"})

    if sid in ("mission_start", "long_mission"):
        from pocket.mission_loop import start_mission

        return start_mission(
            prompt or params.get("goal") or "host work",
            queue=params.get("queue") or params.get("steps"),
            max_hours=float(params.get("max_hours") or 3.0),
            name=params.get("name") or "MISSION",
        )

    if sid in ("workflow_run", "alpha_workflow"):
        from pocket.workflows_alpha import run_workflow

        return run_workflow(params.get("id") or prompt or "wf1")

    if sid in ("workflow_all", "alpha_all"):
        from pocket.workflows_alpha import run_all

        return run_all()

    if sid in ("pixel_text", "ocr_screen"):
        from pocket.pixel_translator import translate_to_text_only

        return translate_to_text_only()

    if sid in ("page_render", "full_page", "page_symbols", "render_page"):
        from pocket.page_renderer import render_full_page

        return render_full_page(
            max_ui=int(params.get("max_ui") or 800),
            include_ocr=bool(params.get("ocr", True)),
            include_visual=bool(params.get("visual", True)),
            include_image=bool(params.get("image", False)),
            visual_grid=int(params.get("grid") or 5),
        )

    if sid == "stream_start":
        from pocket.page_renderer import stream_start

        return stream_start(
            interval_sec=float(params.get("interval") or 1.5),
            max_ui=int(params.get("max_ui") or 500),
        )

    if sid == "stream_stop":
        from pocket.page_renderer import stream_stop

        return stream_stop()

    if sid in ("stream_latest", "stream_status", "page_stream"):
        from pocket.page_renderer import stream_latest, stream_status

        if sid == "stream_status":
            return stream_status()
        return {**stream_latest(after_seq=int(params.get("after") or 0)), "status": stream_status()}

    if sid == "screenshot_series":
        from pocket.capture import capture_screen

        n = int(params.get("n") or 3)
        frames = []
        for i in range(max(1, min(n, 8))):
            frames.append(capture_screen(max_width=800))
            time.sleep(0.6)
        return {"ok": all(f.get("ok") for f in frames), "frames": len(frames), "message": f"{len(frames)} screenshots", "shots": frames}

    if sid == "vision_start":
        from pocket.live_vision import ensure_vision

        ensure_vision()
        return {"ok": True, "message": "Live vision daemon on"}

    if sid == "snip_open":
        from pocket.capture import open_snipping_tool

        return open_snipping_tool()

    # Opens
    app_map = {
        "open_notepad": "notepad",
        "open_explorer": "explorer",
        "open_calc": "calc",
        "open_edge": "edge",
        "open_chrome": "chrome",
        "open_code": "code",
        "open_cursor": "cursor",
        "open_antigravity": "antigravity",
        "open_copilot": "copilot",
        "open_teams": "teams",
        "open_word": "word",
        "open_excel": "excel",
        "open_powerpoint": "powerpoint",
        "open_outlook": "outlook",
        "open_discord": "discord",
        "open_slack": "slack",
        "open_spotify": "spotify",
        "open_github_desktop": "github",
        "open_docker": "docker",
        "open_terminal": "wt",
        "open_settings": "settings",
        "open_taskmgr": "taskmgr",
        "open_paint": "paint",
        "open_snip": "snip",
        "open_claude_app": "claude_app",
        "open_chatgpt_app": "chatgpt",
        "open_metatrader": "metatrader",
    }
    if sid in app_map:
        from pocket.desktop import open_app

        return open_app(app_map[sid])

    if sid == "open_tradingview_app":
        from pocket.ui_maneuver import shell_start_appuser

        return shell_start_appuser("TradingView.Desktop_n534cwy3pjxzj!TradingView.Desktop")

    if sid in ("maximize_window",):
        from pocket.ui_click import maximize_foreground

        return maximize_foreground()

    if sid in ("close_window", "cleanup_foreground"):
        from pocket.ui_click import close_foreground_window

        return close_foreground_window()

    if sid == "scroll_down":
        from pocket.ui_click import scroll_page

        return scroll_page(int(params.get("n") or 3), direction="down")

    if sid == "scroll_up":
        from pocket.ui_click import scroll_page

        return scroll_page(int(params.get("n") or 2), direction="up")

    if sid == "scroll_read":
        from pocket.ui_click import scroll_page

        scroll_page(4, direction="down")
        time.sleep(0.35)
        scroll_page(1, direction="up")
        time.sleep(0.25)
        scroll_page(2, direction="down")
        return {"ok": True, "message": "Human-like scroll read"}

    if sid in ("type_hello", "notepad_write"):
        from pocket.skill_runner import notepad_type

        return notepad_type(prompt or params.get("text") or "hello from POCKET orchestrator")

    if sid == "explorer_new_file":
        from pocket.skill_runner import explorer_create_file

        return explorer_create_file(
            params.get("name") or "pocket-file.txt",
            params.get("content") or prompt or "POCKET",
        )

    if sid == "calc_sum":
        from pocket.skill_runner import calculator_sum

        return calculator_sum(params.get("expr") or "12+34=")

    if sid in ("powershell_cmd", "powershell_codex"):
        from pocket.skill_runner import powershell_command

        cmd = "codex" if sid == "powershell_codex" else (prompt or params.get("cmd") or "Get-Date")
        return powershell_command(cmd)

    # Edge URLs from suite
    if sid.startswith("edge_") or sid == "edge_url":
        from pocket.browser_mode import open_edge_url
        from pocket.ui_click import scroll_page, maximize_foreground, focus_window_title
        from pocket.ui_maneuver import focus_window_title as fwt

        url = params.get("url") or prompt
        preset = {
            "edge_spacex": "https://www.spacex.com/",
            "edge_tradingview": "https://www.tradingview.com/",
            "edge_github_home": "https://github.com/",
            "edge_x_home": "https://x.com/home",
            "edge_google": "https://www.google.com/",
            "edge_bing": "https://www.bing.com/",
            "edge_hn": "https://news.ycombinator.com/",
            "edge_reddit": "https://www.reddit.com/",
            "edge_linkedin": "https://www.linkedin.com/",
            "edge_youtube": "https://www.youtube.com/",
            "edge_wikipedia": "https://www.wikipedia.org/",
            "edge_arxiv": "https://arxiv.org/",
            "edge_github_trending": "https://github.com/trending",
            "edge_producthunt": "https://www.producthunt.com/",
            "edge_huggingface": "https://huggingface.co/",
            "edge_xai": "https://x.ai/",
            "edge_anthropic": "https://www.anthropic.com/",
            "edge_openai": "https://platform.openai.com/",
            "edge_grok_web": "https://grok.com/",
            "edge_claude_web": "https://claude.ai/",
            "edge_perplexity_web": "https://www.perplexity.ai/",
        }
        # skill_suite edge_* sites
        from pocket.skill_suite import _SITES

        for name, u in _SITES:
            preset[f"edge_{name}"] = u
        if sid in preset:
            url = preset[sid]
        if not url:
            return {"ok": False, "error": "url required"}
        r = open_edge_url(url, new_window=True)
        time.sleep(1.4)
        fwt("Edge")
        maximize_foreground()
        if params.get("scroll", True) and sid != "edge_url":
            scroll_page(4, direction="down")
        return {**r, "message": r.get("message") or f"Opened {url}"}

    if sid in ("tweet_compose", "tweet_hi_world"):
        from pocket.browser_mode import open_tweet_compose

        text = prompt or (
            "Hi world — POCKET host co-pilot is live. Latin workers + orchestrator + vision. "
            "ItsNotAI Labs / Medina Tech Labs."
        )
        return open_tweet_compose(text[:280])

    if sid == "email_draft" or sid == "email_research":
        from pocket.outlook_agent import create_draft

        return create_draft(
            subject=params.get("subject") or "POCKET draft",
            body=prompt or params.get("body") or "Draft from orchestrator",
        )

    if sid in ("copilot_open", "copilot_chat_send", "copilot_introduce"):
        from pocket.copilot_agent import paste_and_send_copilot, introduce_to_copilot
        from pocket.browser_mode import open_windows_copilot

        if sid == "copilot_open":
            return open_windows_copilot()
        if sid == "copilot_introduce":
            return introduce_to_copilot(prompt or "POCKET online")
        return paste_and_send_copilot(prompt or "Hello from POCKET orchestrator")

    if sid == "github_list":
        from pocket.repos import list_github_repos

        return list_github_repos(5)

    if sid == "github_clone":
        from pocket.repos import clone_repo

        return clone_repo(prompt or params.get("repo") or "")

    if sid in ("github_analyze",):
        from pocket.repos import analyze_github_repo

        return analyze_github_repo(prompt or params.get("repo") or "imagiEngine")

    if sid == "lookup_web" or sid == "research_company":
        from pocket.step_agent import _lookup_and_bring_back

        q = prompt or params.get("query") or "multi agent desktop"
        return _lookup_and_bring_back(q, open_ui=True)

    if sid == "list_apps":
        from pocket.desktop import list_apps

        apps = list_apps()
        return {"ok": True, "count": len(apps), "apps": apps[:40]}

    if sid == "list_skills":
        from pocket.skill_suite import all_skills, skill_count

        return {"ok": True, "count": skill_count(), "skills": [s["id"] for s in all_skills()]}

    if sid == "list_workers":
        from pocket.alpha_workers import list_workers

        return {"ok": True, "workers": list_workers()}

    if sid == "subagents_list":
        from pocket.subagents_panel import list_subagents

        return list_subagents()

    if sid in ("subagents_dispatch", "dispatch", "mention"):
        from pocket.subagent_dispatch import dispatch

        return dispatch(prompt or params.get("message") or "", agents=params.get("agents"))

    if sid in ("mesh_bootstrap", "headless_start"):
        from pocket.mesh_disk import bootstrap_core_agents
        from pocket.subagent_dispatch import start_headless_pack

        return {"ok": True, "bootstrap": bootstrap_core_agents(), "headless": start_headless_pack()}

    if sid == "daemon_status":
        from pocket.worker_daemon import live_state, ensure_daemon

        ensure_daemon()
        return live_state()

    if sid == "learn_list":
        from pocket.learn import list_learned

        return {"ok": True, "learned": list_learned()}

    if sid == "create_worker":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().create_worker(
            params.get("name") or prompt or "CUSTOM",
            params.get("skills") or ["screenshot", "scroll_read"],
        )

    # playbooks
    if sid == "dev_warm":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [
                {"skill": "open_cursor", "wait": 1.2},
                {"skill": "scroll_read"},
                {"skill": "open_terminal", "wait": 0.8},
                {"skill": "open_explorer"},
            ],
            record=False,
        )

    if sid == "market_glance":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [
                {"skill": "edge_tradingview", "wait": 1.2},
                {"skill": "scroll_read"},
                {"skill": "open_metatrader", "wait": 2.0},
                {"skill": "maximize_window"},
                {"skill": "close_window"},
            ],
            record=False,
        )

    if sid == "ship_pulse":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [
                {"skill": "github_one_page"},
                {"skill": "screenshot"},
                {"skill": "tweet_hi_world"},
            ],
            record=True,
        )

    if sid == "morning_desk":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [
                {"skill": "vision_start"},
                {"skill": "screenshot"},
                {"skill": "email_hi_world"},
                {"skill": "edge_calendar_google"},
            ],
            record=False,
        )

    if sid in ("warmup_office",):
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [{"skill": "open_word"}, {"skill": "open_excel"}, {"skill": "open_outlook"}],
            record=False,
        )

    if sid == "warmup_comms":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [{"skill": "open_teams"}, {"skill": "open_discord"}, {"skill": "open_slack"}],
            record=False,
        )

    if sid == "warmup_ai_ides":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [
                {"skill": "open_cursor", "wait": 1},
                {"skill": "close_window"},
                {"skill": "open_antigravity", "wait": 1},
                {"skill": "close_window"},
                {"skill": "open_code"},
            ],
            record=False,
        )

    if sid == "screenshot_then_notepad":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [{"skill": "screenshot"}, {"skill": "notepad_write", "prompt": "Screenshot captured by OCULUS — see vision tape."}],
            record=False,
        )

    if sid == "research_then_email":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [{"skill": "research_interest"}, {"skill": "email_hi_world"}],
            record=False,
        )

    if sid == "research_then_tweet":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [{"skill": "research_interest"}, {"skill": "tweet_hi_world"}],
            record=True,
        )

    if sid == "vision_burst":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [{"skill": "vision_start"}, {"skill": "screenshot_series", "params": {"n": 5}}],
            record=False,
        )

    if sid == "hydra_fanout":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute_plan(
            [
                {"skill": "open_calc"},
                {"skill": "open_notepad"},
                {"skill": "open_explorer"},
                {"skill": "edge_hn"},
            ],
            record=False,
        )

    if sid == "guppy_steps":
        from pocket.guppy import run_guppy

        text, err, eng = run_guppy(prompt or "open notepad then open calc then open explorer")
        return {"ok": not bool(err), "result": text, "error": err, "engine": eng}

    emit("orch", f"Unknown skill {sid}", agent="ORCHESTRATOR", role="host", level="error")
    return {"ok": False, "error": f"unknown skill: {sid}", "hint": "GET /v1/skills"}
