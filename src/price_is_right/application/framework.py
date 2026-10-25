"""Coordinate the scanner, pricing agents, notifications, and local state."""

from __future__ import annotations

import json
import logging
from typing import List

from .config import (
    LEGACY_MEMORY_FILE,
    LEGACY_VECTORSTORE_DIR,
    MEMORY_FILE,
    VECTORSTORE_DIR,
)

import chromadb
import numpy as np
from dotenv import load_dotenv
from sklearn.manifold import TSNE

from price_is_right.agents.deals import Opportunity
from price_is_right.agents.planning_agent import PlanningAgent

load_dotenv(override=True)

CATEGORIES = [
    "Appliances",
    "Automotive",
    "Cell_Phones_and_Accessories",
    "Electronics",
    "Musical_Instruments",
    "Office_Products",
    "Tools_and_Home_Improvement",
    "Toys_and_Games",
]
COLORS = ["red", "blue", "brown", "orange", "yellow", "green", "purple", "cyan"]


class DealAgentFramework:
    """Lazy-load the agent pipeline and persist surfaced opportunities."""

    DB = str(VECTORSTORE_DIR if VECTORSTORE_DIR.exists() or not LEGACY_VECTORSTORE_DIR.exists() else LEGACY_VECTORSTORE_DIR)
    MEMORY_FILENAME = str(MEMORY_FILE)

    def __init__(self):
        self._configure_logging()
        client = chromadb.PersistentClient(path=self.DB)
        self.memory = self.read_memory()
        self.collection = client.get_or_create_collection("products")
        self.planner = None

    @staticmethod
    def _configure_logging() -> None:
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        if not any(getattr(handler, "_price_is_right", False) for handler in logger.handlers):
            handler = logging.StreamHandler(sys.stdout)
            handler._price_is_right = True
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] [Agents] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S %z",
            ))
            logger.addHandler(handler)

    def init_agents_as_needed(self) -> None:
        if self.planner is None:
            logging.info("Initializing Agent Framework")
            self.planner = PlanningAgent(self.collection)
            logging.info("Agent Framework is ready")

    def read_memory(self) -> List[Opportunity]:
        memory_file = MEMORY_FILE if MEMORY_FILE.exists() else LEGACY_MEMORY_FILE
        if not memory_file.exists():
            return []
        with memory_file.open() as file:
            return [Opportunity(**item) for item in json.load(file)]

    def write_memory(self) -> None:
        with MEMORY_FILE.open("w") as file:
            json.dump([item.model_dump() for item in self.memory], file, indent=2)

    @classmethod
    def reset_memory(cls) -> None:
        data = []
        if MEMORY_FILE.exists():
            with MEMORY_FILE.open() as file:
                data = json.load(file)
        with MEMORY_FILE.open("w") as file:
            json.dump(data[:2], file, indent=2)

    def run(self) -> List[Opportunity]:
        self.init_agents_as_needed()
        logging.info("Kicking off Planning Agent")
        result = self.planner.plan(memory=self.memory)
        if result:
            self.memory.append(result)
            self.write_memory()
        return self.memory

    @classmethod
    def get_plot_data(cls, max_datapoints: int = 2000):
        client = chromadb.PersistentClient(path=cls.DB)
        collection = client.get_or_create_collection("products")
        result = collection.get(include=["embeddings", "documents", "metadatas"], limit=max_datapoints)
        embeddings = result.get("embeddings") or []
        vectors = np.array(embeddings)
        if len(embeddings) < 3:
            return result.get("documents") or [], np.zeros((len(embeddings), 3)), ["gray"] * len(embeddings)
        categories = [metadata["category"] for metadata in result["metadatas"]]
        colors = [COLORS[CATEGORIES.index(category)] if category in CATEGORIES else "gray" for category in categories]
        reduced_vectors = TSNE(n_components=3, random_state=42, n_jobs=-1).fit_transform(vectors)
        return result["documents"], reduced_vectors, colors
