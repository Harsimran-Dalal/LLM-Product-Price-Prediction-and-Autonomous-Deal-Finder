# Price Is Right: Product Price Prediction & Autonomous Deal Finder

An end-to-end machine-learning and agentic application that estimates the fair value of products, finds live deals, and presents the best opportunities in a Gradio dashboard.

This repository started as a week-by-week learning project and has been reorganized into a reproducible engineering story:

1. **Prepare trustworthy product data** from Amazon metadata and normalize noisy descriptions.
2. **Train and compare price estimators**, progressing from simple baselines to neural and language-model approaches.
3. **Turn the estimator into a deal-finding system** with RSS scanning, retrieval-augmented pricing, agent orchestration, persistence, notifications, and a UI.

The notebooks are preserved as an experiment record with descriptive names. The maintained code is now in [`src/price_is_right/`](src/price_is_right/).

## Why this project is interesting

- Converts messy product metadata into structured, model-ready examples.
- Uses LLM preprocessing to make descriptions more consistent before regression.
- Combines specialist, frontier, neural-network, and retrieval-based signals instead of trusting one prediction.
- Uses planning and messaging agents to scan deals, estimate value, rank opportunities, and notify a user.
- Keeps the final runtime separate from exploratory notebooks and generated data.

## Architecture

```text
RSS deal feeds
      |
      v
ScannerAgent -> DealSelection
      |
      v
Preprocessor -> EnsembleAgent
                    |-- SpecialistAgent
                    |-- FrontierAgent + product vector store
                    `-- NeuralNetworkAgent
      |
      v
PlanningAgent -> Opportunity -> memory.json / optional notification
      |
      v
Gradio application
```

The canonical package is organized by responsibility:

```text
.
├── src/price_is_right/
│   ├── training/               # data parsing, preprocessing, and model training
│   ├── agents/                 # scanning, pricing, planning, and messaging
│   └── application/            # orchestration, persistence, logging, and UI
├── notebooks/
│   ├── 01_data_preparation/    # dataset and preprocessing experiments
│   ├── 02_model_evaluation/    # metrics and model comparisons
│   └── 03_autonomous_deal_finder/ # agent and application experiments
├── data/                       # local generated runtime state
├── .env.example
├── pyproject.toml
└── uv.lock
```

## Development progression

The notebook names describe the actual work; there are no ambiguous `day1`, `day2`, or `results` files:

```text
01_data_preparation/
  01_dataset_exploration
  02_data_cleaning_and_parsing
  03_llm_preprocessing
  04_neural_price_model
  05_batch_inference
  06_redemption_training
  07_redemption_inference
  08_phase_results

02_model_evaluation/
  01_evaluation_setup
  02_model_comparison
  03_ensemble_evaluation
  04_final_validation
  05_phase_results

03_autonomous_deal_finder/
  01_agent_foundations
  02_deal_scanning
  03_price_estimation
  04_agent_orchestration
  05_gradio_application
  06_phase_results
```

### Phase 1 — Data and baselines

The first phase loads Amazon product metadata, removes unusable records, extracts weight and product details, and creates the `Item` representation. LLM preprocessing then rewrites inconsistent descriptions into a compact title/category/brand/description/details format. A residual neural network and batch utilities establish the first learned price predictor.

**Error-reduction decisions:** price and text bounds remove outliers, descriptions are truncated to control noise and token cost, and preprocessing is separated from model inference so it can be measured independently.

### Phase 2 — Evaluation and comparison

The second phase makes evaluation explicit with shared error reporting, mean squared error, R², error-trend plots, and sampled comparisons. This turns a single prediction into measurable experiments and makes it possible to compare prompting, fine-tuning, neural, and ensemble approaches.

**Error-reduction decisions:** holdout evaluation, consistent metrics, and visual error inspection expose systematic failures instead of optimizing only for a few examples.

### Phase 3 — Autonomous deal finding

The final phase connects the price estimator to real deal feeds. The scanner selects high-quality deals, the pricing ensemble estimates fair value, the planner ranks opportunities, and the application persists results and displays them in Gradio. ChromaDB supplies the product retrieval layer used by the frontier agent.

**Error-reduction decisions:** multiple pricing signals, structured Pydantic outputs, product retrieval, explicit opportunity discounts, and persisted memory reduce dependence on one model response and prevent losing useful results between runs.

## Key numbers and results

The repository contains one explicitly recorded training run and several measurable runtime safeguards. Numbers below are reported values or implementation settings, not estimates.

| Area | Metric or setting | Value | Why it matters |
|---|---|---:|---|
| Price model | Training epochs in the recorded redemption run | **5** | A fixed training budget makes the experiment repeatable. |
| Price model | Final training loss | **0.2446** | Lower than the initial recorded training loss of **0.5463**. |
| Price model | Final validation loss | **0.3944** | Lower than the initial recorded validation loss of **0.4324**. |
| Price model | Final validation mean absolute error | **$53.15** | The recorded average absolute price error after epoch 5. |
| Price model | Best recorded validation MAE | **$53.15** | The best value in the 5-epoch run. |
| Data filtering | Accepted price range | **$0.50–$999.49** | Removes implausible and extreme price records before training. |
| Data filtering | Minimum product text length | **600 characters** | Avoids training on descriptions with too little product information. |
| Data preparation | Maximum text per source field | **3,000 characters** | Controls noisy input size before combining fields. |
| Data preparation | Maximum combined text | **4,000 characters** | Controls token usage and model input variance. |
| Deal scanning | RSS entries inspected per feed | **10** | Keeps each scan bounded and predictable. |
| Deal selection | Deals requested from the scanner | **5** | Produces a focused shortlist for price estimation. |
| Price ensemble | Frontier model contribution | **80%** | Gives the retrieval/frontier estimate the primary weight. |
| Price ensemble | Specialist model contribution | **10%** | Adds an independent model signal. |
| Price ensemble | Neural model contribution | **10%** | Adds a learned regression signal. |
| Opportunity ranking | Application refresh interval | **300 seconds / 5 minutes** | Periodically checks for new opportunities. |
| Visualization | Maximum vector-store points for the plot | **800** | Keeps the dashboard visualization responsive. |

The evaluation framework reports **mean absolute error**, **mean squared error**, **R²**, and a **95% confidence interval** for future runs. The notebooks do not contain a complete comparable metric table for every model, so no additional model scores are claimed here.

## Quick start

### 1. Install

Python 3.11+ is required. With `uv`:

```powershell
uv sync
```

Or install the project in editable mode:

```powershell
python -m pip install -e .
```

### 2. Configure credentials

Copy `.env.example` to `.env` and fill in the providers you intend to use. At minimum, the scanner needs `OPENAI_API_KEY`; the selected pricing agents may also use `ANTHROPIC_API_KEY` and `HF_TOKEN`. Pushover variables are optional.

### 3. Prepare the vector store

The frontier agent expects a ChromaDB collection named `products`. Build it from the existing historical data workflow, or provide an equivalent persisted collection under `data/products_vectorstore/`.

### 4. Run the application

```powershell
uv run price-is-right
```

The equivalent module command is:

```powershell
python -m price_is_right
```

The UI scans for deals on startup and refreshes on its timer. Generated state is written to `data/` and is intentionally not committed.

## Validation

Compile the maintained package without starting external services:

```powershell
python -m compileall -q src
```

Run a smoke import after dependencies are installed:

```powershell
python -c "from price_is_right import App, DealAgentFramework; print(App.__name__, DealAgentFramework.__name__)"
```

## Reproducibility and repository hygiene

- Keep API keys in `.env`; never commit them.
- Keep ChromaDB, model weights, and generated opportunity memory in `data/`.
- Use `notebooks/01_*`, `notebooks/02_*`, and `notebooks/03_*` for experiments and historical evidence.
- Put maintained production code under `src/price_is_right/`.
- Record model names, prompts, metrics, and dataset changes in the relevant notebook before promoting code into the package.

## Summary

**Product Price Prediction & Autonomous Deal Finder** — Built a staged Python ML and agentic system that cleans and preprocesses Amazon product metadata, trains and evaluates price estimators, combines neural/retrieval/LLM pricing signals, scans RSS deal feeds, ranks opportunities, persists results in ChromaDB/JSON, and serves a Gradio dashboard.

**Technologies:** Python, PyTorch, scikit-learn, Pydantic, Hugging Face Datasets, LiteLLM, OpenAI-compatible APIs, ChromaDB, Gradio, Plotly, and uv.
