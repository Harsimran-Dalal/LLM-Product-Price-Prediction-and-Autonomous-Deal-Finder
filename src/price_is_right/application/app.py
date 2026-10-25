"""Gradio interface for The Price is Right."""

from __future__ import annotations

import html
import logging
import queue
import threading
import time

import gradio as gr
import plotly.graph_objects as go

from .framework import DealAgentFramework
from .logging_utils import reformat


class QueueHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put(self.format(record))


def format_logs(log_data: list[str]) -> str:
    output = "<br>".join(log_data[-18:])
    return (
        '<div style="height:400px; overflow-y:auto; border:1px solid #ccc; '
        f'background-color:#222229; padding:10px">{output}</div>'
    )


class App:
    def __init__(self):
        self.agent_framework: DealAgentFramework | None = None

    def get_agent_framework(self) -> DealAgentFramework:
        if self.agent_framework is None:
            self.agent_framework = DealAgentFramework()
        return self.agent_framework

    @staticmethod
    def table_for(opportunities) -> list[list[str]]:
        return [
            [
                opportunity.deal.product_description,
                f"${opportunity.deal.price:.2f}",
                f"${opportunity.estimate:.2f}",
                f"${opportunity.discount:.2f}",
                opportunity.deal.url,
            ]
            for opportunity in opportunities
        ]

    @staticmethod
    def get_plot():
        _, vectors, colors = DealAgentFramework.get_plot_data(max_datapoints=800)
        figure = go.Figure(
            data=[
                go.Scatter3d(
                    x=vectors[:, 0],
                    y=vectors[:, 1],
                    z=vectors[:, 2],
                    mode="markers",
                    marker={"size": 2, "color": colors, "opacity": 0.7},
                )
            ]
        )
        figure.update_layout(
            scene={
                "xaxis_title": "x",
                "yaxis_title": "y",
                "zaxis_title": "z",
                "aspectmode": "manual",
                "aspectratio": {"x": 2.2, "y": 2.2, "z": 1},
                "camera": {"eye": {"x": 1.6, "y": 1.6, "z": 0.8}},
            },
            height=400,
            margin={"r": 5, "b": 1, "l": 5, "t": 2},
        )
        return figure

    def run_with_logging(self, initial_log_data: list[str]):
        log_queue: queue.Queue = queue.Queue()
        result_queue: queue.Queue = queue.Queue()
        handler = QueueHandler(log_queue)
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S %z"))
        logger = logging.getLogger()
        logger.addHandler(handler)

        def worker() -> None:
            try:
                result_queue.put((True, self.table_for(self.get_agent_framework().run())))
            except Exception as error:
                logging.exception("Price run failed")
                result_queue.put((False, error))

        threading.Thread(target=worker, daemon=True).start()
        try:
            current_logs = list(initial_log_data or [])
            initial_table = self.table_for(self.get_agent_framework().memory)
            while True:
                while True:
                    try:
                        current_logs.append(reformat(log_queue.get_nowait()))
                    except queue.Empty:
                        break

                try:
                    succeeded, result = result_queue.get_nowait()
                except queue.Empty:
                    yield current_logs, format_logs(current_logs), initial_table
                    time.sleep(0.1)
                    continue

                if not succeeded:
                    current_logs.append(f"Run failed: {html.escape(str(result))}")
                    yield current_logs, format_logs(current_logs), initial_table
                else:
                    yield current_logs, format_logs(current_logs), result
                break
        finally:
            logger.removeHandler(handler)

    def run(self) -> None:
        with gr.Blocks(title="The Price is Right", fill_width=True) as ui:
            log_data = gr.State([])
            gr.Markdown(
                '<div style="text-align:center;font-size:24px"><strong>The Price is Right</strong> '
                "- Autonomous agent framework that hunts for deals</div>"
            )
            gr.Markdown(
                '<div style="text-align:center;font-size:14px">A specialist model, frontier model, '
                "and RAG pipeline collaborate to find online deals.</div>"
            )
            opportunities = gr.Dataframe(
                headers=["Deal", "Price", "Estimate", "Discount", "URL"],
                wrap=True,
                column_widths=[6, 1, 1, 1, 3],
                row_count=10,
                col_count=5,
                max_height=400,
            )
            with gr.Row():
                logs = gr.HTML()
                plot = gr.Plot(value=self.get_plot(), show_label=False)

            ui.load(self.run_with_logging, inputs=log_data, outputs=[log_data, logs, opportunities])
            timer = gr.Timer(value=300, active=True)
            timer.tick(self.run_with_logging, inputs=log_data, outputs=[log_data, logs, opportunities])

            def select_opportunity(selected: gr.SelectData) -> None:
                framework = self.get_agent_framework()
                framework.init_agents_as_needed()
                row = selected.index[0]
                if 0 <= row < len(framework.memory):
                    framework.planner.messenger.alert(framework.memory[row])

            opportunities.select(select_opportunity)

        ui.launch(share=False, inbrowser=True)

