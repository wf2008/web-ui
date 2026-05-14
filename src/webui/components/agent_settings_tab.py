import asyncio
import os
import uuid
import gradio as gr
from browser_use.agent.views import AgentHistoryList
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from langchain_ollama import ChatOllama
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from src.controller.custom_controller import CustomController
from src.webui.webui_manager import WebuiManager

def _get_ollama_llm():
    base_url = os.environ.get("OLLAMA_BASE_URL")
    if not base_url:
        raise ValueError("OLLAMA_BASE_URL not set")
    return ChatOllama(
        model="huihui_ai/qwen2.5-coder-abliterate",
        base_url=base_url,
        temperature=0.6,
        num_ctx=16000
    )

async def run_agent(webui_manager, task):
    llm = _get_ollama_llm()
    cdp = os.environ.get("CDP_URL")
    if not cdp:
        raise ValueError("CDP_URL not set")
    if cdp.startswith("https://"):
        cdp = "wss://" + cdp[8:]
    browser = CustomBrowser(
        config=BrowserConfig(
            headless=False,
            cdp_url=cdp,
            new_context_config=BrowserContextConfig(window_width=1280, window_height=1100)
        )
    )
    ctx = await browser.new_context()
    controller = CustomController()
    agent = BrowserUseAgent(
        task=task,
        llm=llm,
        browser=browser,
        browser_context=ctx,
        controller=controller,
        use_vision=True
    )
    agent.state.agent_id = str(uuid.uuid4())
    await agent.run(max_steps=100)
    await ctx.close()
    await browser.close()

async def handle_submit(webui_manager, task):
    if not task:
        gr.Warning("Please enter a task.")
        yield {}
        return
    webui_manager.bu_chat_history.append({"role": "user", "content": task})
    yield {c.user_input: gr.update(interactive=False), c.run_btn: gr.update(interactive=False)}
    try:
        await run_agent(webui_manager, task)
        webui_manager.bu_chat_history.append({"role": "assistant", "content": "✅ Task completed."})
    except Exception as e:
        webui_manager.bu_chat_history.append({"role": "assistant", "content": f"❌ Error: {e}"})
    finally:
        yield {c.user_input: gr.update(interactive=True), c.run_btn: gr.update(interactive=True), c.chatbot: gr.update(value=webui_manager.bu_chat_history)}

def handle_clear(webui_manager):
    webui_manager.bu_chat_history = []
    return {c.chatbot: gr.update(value=[]), c.user_input: gr.update(value="")}

c = {}
def create_browser_use_agent_tab(webui_manager):
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
