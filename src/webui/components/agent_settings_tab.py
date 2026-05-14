import logging
import gradio as gr
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


def create_agent_settings_tab(webui_manager: WebuiManager):
    """
    Minimal agent settings tab – only the essentials for self‑hosted Ollama.
    """
    tab_components = {}

    with gr.Group():
        override_system_prompt = gr.Textbox(
            label="Override system prompt", lines=4, interactive=True
        )
        extend_system_prompt = gr.Textbox(
            label="Extend system prompt", lines=4, interactive=True
        )

    with gr.Group():
        llm_temperature = gr.Slider(
            minimum=0.0,
            maximum=2.0,
            value=0.6,
            step=0.1,
            label="Temperature",
            info="Controls randomness in model outputs",
            interactive=True,
        )
        use_vision = gr.Checkbox(
            label="Use Vision", value=True, info="Send screenshot to LLM", interactive=True
        )
        ollama_num_ctx = gr.Slider(
            minimum=256,
            maximum=32768,
            value=16000,
            step=256,
            label="Context Length",
            info="Maximum context window (higher = slower, uses more memory)",
            interactive=True,
        )

    with gr.Group():
        max_steps = gr.Slider(
            minimum=1,
            maximum=1000,
            value=100,
            step=1,
            label="Max Run Steps",
            info="Maximum number of steps the agent will take",
            interactive=True,
        )
        max_actions = gr.Slider(
            minimum=1,
            maximum=100,
            value=10,
            step=1,
            label="Max Actions per Step",
            info="Maximum number of actions per step",
            interactive=True,
        )

    with gr.Group():
        max_input_tokens = gr.Number(
            label="Max Input Tokens", value=128000, precision=0, interactive=True
        )

    tab_components.update(
        {
            "override_system_prompt": override_system_prompt,
            "extend_system_prompt": extend_system_prompt,
            "llm_temperature": llm_temperature,
            "use_vision": use_vision,
            "ollama_num_ctx": ollama_num_ctx,
            "max_steps": max_steps,
            "max_actions": max_actions,
            "max_input_tokens": max_input_tokens,
        }
    )
    webui_manager.add_components("agent_settings", tab_components)
