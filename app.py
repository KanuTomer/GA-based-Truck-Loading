"""Gradio entry point for the GA-Based Truck Loading demo."""

import gradio as gr


def build_app() -> gr.Blocks:
    with gr.Blocks(title="GA-Based Truck Loading") as demo:
        gr.Markdown(
            """
            # GA-Based Truck Loading

            A visual demo for GA-based route packing and truck loading.

            Milestone 0 is complete: this app shell is ready for dataset upload,
            truck presets, proposed-model execution, and 3D packing visualization
            in later milestones.
            """
        )

    return demo


if __name__ == "__main__":
    build_app().launch()

