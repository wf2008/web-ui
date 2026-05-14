import gradio as gr
import os

from src.webui.webui_manager import WebuiManager
from src.webui.components.agent_settings_tab import create_agent_settings_tab
from src.webui.components.browser_settings_tab import create_browser_settings_tab
from src.webui.components.browser_use_agent_tab import create_browser_use_agent_tab
from src.webui.components.deep_research_agent_tab import create_deep_research_agent_tab
from src.webui.components.load_save_config_tab import create_load_save_config_tab

theme_map = {
    "Default": gr.themes.Default(),
    "Soft": gr.themes.Soft(),
    "Monochrome": gr.themes.Monochrome(),
    "Glass": gr.themes.Glass(),
    "Origin": gr.themes.Origin(),
    "Citrus": gr.themes.Citrus(),
    "Ocean": gr.themes.Ocean(),
    "Base": gr.themes.Base()
}


def create_ui(theme_name="Ocean"):
    css = """
    .gradio-container {
        width: 70vw !important; 
        max-width: 70% !important; 
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 10px !important;
    }
    .header-text {
        text-align: center;
        margin-bottom: 20px;
    }
    .tab-header-text {
        text-align: center;
    }
    .theme-section {
        margin-bottom: 10px;
        padding: 15px;
        border-radius: 10px;
    }
    """

    js_func = """
    function refresh() {
        const url = new URL(window.location);
        if (url.searchParams.get('__theme') !== 'dark') {
            url.searchParams.set('__theme', 'dark');
            window.location.href = url.href;
        }
    }
    """

    ui_manager = WebuiManager()

    with gr.Blocks(
            title="Browser Use WebUI", theme=theme_map[theme_name], css=css, js=js_func,
    ) as demo:
        with gr.Row():
            gr.Markdown(
                """
                # 🌐 Browser Use WebUI
                ### Control your browser with AI assistance
                """,
                elem_classes=["header-text"],
            )

        with gr.Tabs() as tabs:
            with gr.TabItem("⚙️ Agent Settings"):
                create_agent_settings_tab(ui_manager)

            with gr.TabItem("🌐 Browser Settings"):
                create_browser_settings_tab(ui_manager)

            with gr.TabItem("🤖 Run Agent"):
                create_browser_use_agent_tab(ui_manager)

            # ========== NEW VNC TAB ==========
            with gr.TabItem("🖥️ Live Browser"):
                vnc_url = os.environ.get("VNC_URL", "")
                if vnc_url:
                    clean_url = vnc_url.rstrip("/")
                    iframe_html = f'''
                    <iframe
                        src="{clean_url}/vnc.html?autoconnect=true&resize=scale&password=vncpassword"
                        width="100%"
                        height="650"
                        style="border: none; border-radius: 8px; background: #0a0a0a;"
                        allow="fullscreen"
                    ></iframe>
                    <p style="font-size: 0.85rem; color: #888; margin-top: 10px;">
                        🔍 <strong>Troubleshooting:</strong> If the browser doesn't appear,
                        ensure your GitHub Actions workflow is running and the tunnel is active.
                    </p>
                    '''
                    gr.HTML(iframe_html)
                else:
                    gr.HTML('''
                    <div style="padding: 50px; text-align: center; background: #1e1e1e; border-radius: 12px;">
                        <h3>🔴 VNC Not Available</h3>
                        <p>The VNC stream is offline.</p>
                        <p>👉 Run your <strong>GitHub Actions workflow</strong> to start the browser.</p>
                        <p>Once the workflow finishes, refresh this page.</p>
                    </div>
                    ''')
            # ========== END OF NEW VNC TAB ==========

            with gr.TabItem("🎁 Agent Marketplace"):
                gr.Markdown(
                    """
                    ### Agents built on Browser-Use
                    """,
                    elem_classes=["tab-header-text"],
                )
                with gr.Tabs():
                    with gr.TabItem("Deep Research"):
                        create_deep_research_agent_tab(ui_manager)

            with gr.TabItem("📁 Load & Save Config"):
                create_load_save_config_tab(ui_manager)

    return demo
