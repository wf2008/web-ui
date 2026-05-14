import os
import uuid
import gradio as gr
from langchain_ollama import ChatOllama
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
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
        num_ctx=16000,
    )

def _normalize_cdp_url(url: str) -> str:
    if url.startswith("https://"):
        return "wss://" + url[len("https://"):]
    if url.startswith("http://"):
        return "ws://" + url[len("http://"):]
    return url

async def run_agent(webui_manager, task):
    llm = _get_ollama_llm()
    cdp = os.environ.get("CDP_URL")
    if not cdp:
        raise ValueError("CDP_URL not set")
    browser = CustomBrowser(
        config=BrowserConfig(
            headless=False,
            cdp_url=_normalize_cdp_url(cdp),
            new_context_config=BrowserContextConfig(window_width=1280, window_height=1100),
        )
    )
    ctx = None
    try:
        ctx = await browser.new_context()
        controller = CustomController()
        agent = BrowserUseAgent(
            task=task,
            llm=llm,
            browser=browser,
            browser_context=ctx,
            controller=controller,
            use_vision=True,
        )
        agent.state.agent_id = str(uuid.uuid4())
        await agent.run(max_steps=100)
    finally:
        if ctx:
            await ctx.close()
        await browser.close()

async def handle_submit(webui_manager, task, components):
    task = (task or "").strip()
    if not task:
        gr.Warning("Please enter a task.")
        yield {components["user_input"]: gr.update(interactive=True),
               components["run_btn"]: gr.update(interactive=True)}
        return
    webui_manager.bu_chat_history.append({"role": "user", "content": task})
    yield {components["user_input"]: gr.update(value="", interactive=False),
           components["run_btn"]: gr.update(interactive=False),
           components["chatbot"]: gr.update(value=webui_manager.bu_chat_history)}
    try:
        await run_agent(webui_manager, task)
        webui_manager.bu_chat_history.append({"role": "assistant", "content": "✅ Task completed."})
    except Exception as e:
        webui_manager.bu_chat_history.append({"role": "assistant", "content": f"❌ Error: {e}"})
    yield {components["user_input"]: gr.update(interactive=True),
           components["run_btn"]: gr.update(interactive=True),
           components["chatbot"]: gr.update(value=webui_manager.bu_chat_history)}

def handle_clear(webui_manager, components):
    webui_manager.bu_chat_history = []
    return {components["chatbot"]: gr.update(value=[]),
            components["user_input"]: gr.update(value="")}

def create_browser_use_agent_tab(webui_manager: WebuiManager):
    webui_manager.init_browser_use_agent()
    with gr.Column():
        chatbot = gr.Chatbot(label="Conversation", height=500, type="messages", value=webui_manager.bu_chat_history)
        user_input = gr.Textbox(label="Your Task", placeholder="Describe what you want the AI to do...", lines=3)
        with gr.Row():
            run_btn = gr.Button("▶️ Run", variant="primary")
            clear_btn = gr.Button("🗑️ Clear")
    components = {"chatbot": chatbot, "user_input": user_input, "run_btn": run_btn, "clear_btn": clear_btn}
    webui_manager.add_components("browser_use_agent", components)

    async def submit_wrapper(task):
        async for update in handle_submit(webui_manager, task, components):
            yield update
    def clear_wrapper():
        return handle_clear(webui_manager, components)

    run_btn.click(fn=submit_wrapper, inputs=[user_input], outputs=[user_input, run_btn, chatbot])
    user_input.submit(fn=submit_wrapper, inputs=[user_input], outputs=[user_input, run_btn, chatbot])
    clear_btn.click(fn=clear_wrapper, inputs=[], outputs=[chatbot, user_input])
