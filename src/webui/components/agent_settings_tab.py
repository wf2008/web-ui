import asyncio
import json
import logging
import os
import uuid
from typing import Any, AsyncGenerator, Dict, Optional

import gradio as gr
from browser_use.agent.views import AgentHistoryList, AgentOutput
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.browser.views import BrowserState
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama

from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from src.controller.custom_controller import CustomController
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Helper: initialise Ollama LLM with the tunnel URL
# ------------------------------------------------------------------
def _init_ollama_llm() -> BaseChatModel:
    base_url = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_ENDPOINT")
    if not base_url:
        raise ValueError("OLLAMA_BASE_URL / OLLAMA_ENDPOINT not set – run GitHub Actions workflow first")
    logger.info(f"Initialising Ollama with base URL: {base_url}")
    return ChatOllama(
        model="huihui_ai/qwen2.5-coder-abliterate",
        base_url=base_url,
        temperature=0.6,
        num_ctx=16000,
    )

# ------------------------------------------------------------------
# Callbacks: display step output and final result in chat
# ------------------------------------------------------------------
def _format_agent_output(model_output: AgentOutput) -> str:
    content = ""
    if model_output:
        try:
            action_dump = [a.model_dump(exclude_none=True) for a in model_output.action]
            state_dump = model_output.current_state.model_dump(exclude_none=True)
            dump = {"current_state": state_dump, "action": action_dump}
            content = f"<pre><code class='language-json'>{json.dumps(dump, indent=4, ensure_ascii=False)}</code></pre>"
        except Exception as e:
            content = f"<pre><code>Error formatting output: {e}</code></pre>"
    return content

async def _new_step_callback(
    webui_manager: WebuiManager,
    state: BrowserState,
    output: AgentOutput,
    step_num: int,
):
    step_num -= 1
    img_html = ""
    if getattr(state, "screenshot", None):
        img_html = f'<img src="data:image/jpeg;base64,{state.screenshot}" style="max-width:800px;max-height:600px;object-fit:contain;" /><br/>'
    step_html = f"--- **Step {step_num}** ---<br/>{img_html}{_format_agent_output(output)}"
    webui_manager.bu_chat_history.append({"role": "assistant", "content": step_html})

def _done_callback(webui_manager: WebuiManager, history: AgentHistoryList):
    final = f"**Task Completed** – Duration: {history.total_duration_seconds():.2f}s, Tokens: {history.total_input_tokens()}"
    if history.final_result():
        final += f"\nFinal result: {history.final_result()}"
    webui_manager.bu_chat_history.append({"role": "assistant", "content": final})

# ------------------------------------------------------------------
# Core agent execution
# ------------------------------------------------------------------
async def run_agent_task(webui_manager: WebuiManager, task: str):
    # 1. Initialise Ollama LLM
    llm = _init_ollama_llm()

    # 2. Get CDP URL for remote browser
    cdp_url = os.environ.get("CDP_URL")
    if not cdp_url:
        raise ValueError("CDP_URL not set – run GitHub Actions workflow first")
    if cdp_url.startswith("https://"):
        cdp_url = "wss://" + cdp_url[8:]
    elif cdp_url.startswith("http://"):
        cdp_url = "ws://" + cdp_url[7:]

    # 3. Create browser and context
    browser = CustomBrowser(
        config=BrowserConfig(
            headless=False,
            disable_security=True,
            cdp_url=cdp_url,
            new_context_config=BrowserContextConfig(window_width=1280, window_height=1100),
        )
    )
    browser_context = await browser.new_context()

    # 4. Create controller (no MCP, no planner)
    controller = CustomController()

    # 5. Create agent
    agent = BrowserUseAgent(
        task=task,
        llm=llm,
        browser=browser,
        browser_context=browser_context,
        controller=controller,
        register_new_step_callback=lambda s, o, n: _new_step_callback(webui_manager, s, o, n),
        register_done_callback=lambda h: _done_callback(webui_manager, h),
        use_vision=True,
        max_input_tokens=128000,
        max_actions_per_step=10,
    )
    agent.state.agent_id = str(uuid.uuid4())

    # 6. Run agent
    await agent.run(max_steps=100)

    # 7. Cleanup
    await browser_context.close()
    await browser.close()

# ------------------------------------------------------------------
# UI and event handlers
# ------------------------------------------------------------------
async def handle_submit(webui_manager: WebuiManager, task: str) -> AsyncGenerator[Dict[gr.components.Component, Any], None]:
    if not task.strip():
        gr.Warning("Please enter a task.")
        yield {}  # 👈 Fixed: use yield instead of return {}
        return

    webui_manager.bu_chat_history.append({"role": "user", "content": task})
    # Disable UI while running
    yield {c.user_input: gr.update(interactive=False), c.run_btn: gr.update(interactive=False)}
    try:
        await run_agent_task(webui_manager, task)
    except Exception as e:
        webui_manager.bu_chat_history.append({"role": "assistant", "content": f"❌ Error: {e}"})
    finally:
        # Re-enable UI
        yield {c.user_input: gr.update(interactive=True), c.run_btn: gr.update(interactive=True), c.chatbot: gr.update(value=webui_manager.bu_chat_history)}

def handle_clear(webui_manager: WebuiManager):
    webui_manager.bu_chat_history = []
    webui_manager.bu_agent = None
    webui_manager.bu_current_task = None
    return {c.chatbot: gr.update(value=[]), c.user_input: gr.update(value="")}

# ------------------------------------------------------------------
# Create the tab (minimal UI)
# ------------------------------------------------------------------
def create_browser_use_agent_tab(webui_manager: WebuiManager):
    global c
    webui_manager.init_browser_use_agent()
    with gr.Column():
        chatbot = gr.Chatbot(label="Conversation", height=500, type="messages")
        user_input = gr.Textbox(label="Your Task", placeholder="Describe what you want the AI to do...", lines=3)
        with gr.Row():
            run_btn = gr.Button("▶️ Run", variant="primary")
            clear_btn = gr.Button("🗑️ Clear")
    c = {"chatbot": chatbot, "user_input": user_input, "run_btn": run_btn, "clear_btn": clear_btn}
    webui_manager.add_components("browser_use_agent", c)
    run_btn.click(fn=handle_submit, inputs=[user_input], outputs=[user_input, run_btn, chatbot], api_name=False)
    clear_btn.click(fn=lambda: handle_clear(webui_manager), inputs=[], outputs=[chatbot, user_input])
