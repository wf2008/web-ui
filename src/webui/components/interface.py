from src.webui.components.browser_settings_tab import create_browser_settings_tab

def create_ui(theme_name="Ocean"):
    # ... (existing code for other tabs) ...

    with gr.Tab(" Run Agent"):
        create_browser_use_agent_tab(ui_manager)

    # --- ADD NEW VNC TAB HERE ---
    with gr.TabItem(" Live Browser View"):
        with gr.Column():
            vnc_html = gr.HTML()  # Placeholder for dynamic VNC iframe
            def refresh_vnc_iframe():
                vnc_url = os.environ.get("VNC_URL")
                if vnc_url:
                    return f'<iframe src="{vnc_url}/vnc.html" width="100%" height="700px" style="border:none;"></iframe>'
                else:
                    return "<div>VNC URL not set. Please run the GitHub Actions workflow to start the browser.</div>"
            refresh_btn = gr.Button("Refresh VNC")
            refresh_btn.click(refresh_vnc_iframe, outputs=vnc_html)
            vnc_html.value = refresh_vnc_iframe()
    # --- END OF NEW CODE ---

    with gr.TabItem(" Load & Save Config"):
        create_load_save_config_tab(ui_manager)

    return demo
