"""
models/chronos_model.py — Amazon Chronos pre-trained Time-Series Foundation Model.

Chronos (Ansari et al., 2024) is a pre-trained probabilistic time-series
model based on T5. It tokenises time-series values and performs zero-shot
or fine-tuned forecasting without any domain-specific training.

Model sizes available (from smallest to largest):
  chronos-t5-tiny   ~8M  params  (fastest, least accurate)
  chronos-t5-mini   ~20M params
  chronos-t5-small  ~46M params  ← recommended default
  chronos-t5-base   ~200M params
  chronos-t5-large  ~710M params (best accuracy, needs GPU)

Installation
------------
  pip install chronos-forecasting

Weights are downloaded from HuggingFace on first use:
  amazon/chronos-t5-small

Note: HuggingFace access required (https://huggingface.co). If running in
a restricted network, set HF_ENDPOINT or use --use_chronos False.

References
----------
  Ansari et al. (2024) "Chronos: Learning the Language of Time Series"
  https://arxiv.org/abs/2403.07815
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

_CHRONOS_IMPORT_ERROR: str | None = None

try:
    import torch
    from chronos import ChronosPipeline   # pip install chronos-forecasting
    CHRONOS_AVAILABLE = True
except ImportError as e:
    CHRONOS_AVAILABLE = False
    _CHRONOS_IMPORT_ERROR = str(e)


class ChronosForecaster:
    """
    Zero-shot probabilistic forecasting with Amazon Chronos.

    If the package / model weights are unavailable the class returns None
    predictions so the ensemble can fall back gracefully.

    Parameters
    ----------
    model_size      : one of "tiny", "mini", "small", "base", "large"
    num_samples     : Monte-Carlo samples for uncertainty (default 20)
    context_length  : number of historical observations fed to the model
                      (max 512 for Chronos T5 family)
    """

    def __init__(
        self,
        model_size: str = "small",
        num_samples: int = 20,
        context_length: int = 512,
    ):
        self.model_size = model_size
        self.num_samples = num_samples
        self.context_length = min(context_length, 512)
        self.pipeline = None
        self.available = CHRONOS_AVAILABLE
        self._load_error: str | None = _CHRONOS_IMPORT_ERROR

    # ------------------------------------------------------------------

    def load(self, device: str = "cpu", verbose: bool = True) -> "ChronosForecaster":
        """Download / load model weights from HuggingFace."""
        if not CHRONOS_AVAILABLE:
            if verbose:
                print(f"  [Chronos] ⚠  chronos-forecasting not installed: "
                      f"{_CHRONOS_IMPORT_ERROR}\n"
                      f"           Run: pip install chronos-forecasting\n"
                      f"           Skipping Chronos — ensemble will use "
                      f"LightGBM + Prophet only.")
            return self

        model_id = f"amazon/chronos-t5-{self.model_size}"
        try:
            if verbose:
                print(f"  [Chronos] Loading {model_id} on {device} …")
            self.pipeline = ChronosPipeline.from_pretrained(
                model_id,
                device_map=device,
                torch_dtype=torch.bfloat16 if device != "cpu" else torch.float32,
            )
            if verbose:
                print(f"  [Chronos] Model loaded ✓")
        except Exception as exc:
            self.available = False
            self._load_error = str(exc)
            if verbose:
                print(f"  [Chronos] ⚠  Could not load model: {exc}\n"
                      f"           (HuggingFace access may be required)\n"
                      f"           Falling back to LightGBM + Prophet only.")
        return self

    # ------------------------------------------------------------------

    def predict(
        self,
        df: pd.DataFrame,
        horizons: dict[str, int],
    ) -> dict[str, dict] | None:
        """
        Parameters
        ----------
        df       : full history DataFrame (uses last `context_length` rows)
        horizons : {"1w": 5, "1m": 21, "1y": 252}

        Returns
        -------
        dict or None (None if Chronos unavailable → ensemble skips it)
        """
        if not self.available or self.pipeline is None:
            return None

        try:
            import torch

            close = df["Close"].values.astype(np.float32)
            context = close[-self.context_length:]
            context_tensor = torch.tensor(context).unsqueeze(0)  # (1, T)

            current_price = float(close[-1])
            max_h = max(horizons.values())

            # Chronos generates a full forecast distribution
            # quantiles shape: (num_quantiles, batch, prediction_length)
            quantiles_levels = [0.1, 0.5, 0.9]
            forecast = self.pipeline.predict(
                context=context_tensor,
                prediction_length=max_h,
                num_samples=self.num_samples,
                limit_prediction_length=False,
            )
            # forecast shape: (batch=1, num_samples, prediction_length)
            samples = forecast[0].numpy()          # (num_samples, max_h)

            results: dict = {}
            for name, h in horizons.items():
                horizon_samples = samples[:, h - 1]   # price at step h
                price    = float(np.median(horizon_samples))
                price_lo = float(np.percentile(horizon_samples, 10))
                price_hi = float(np.percentile(horizon_samples, 90))

                # Clip to physically plausible range (> 0, < 10× current)
                price    = max(price,    current_price * 0.01)
                price_lo = max(price_lo, current_price * 0.01)
                price_hi = min(price_hi, current_price * 10.0)

                results[name] = {
                    "price":      price,
                    "low":        price_lo,
                    "high":       price_hi,
                    "log_return": np.log(price / current_price),
                }

            return results

        except Exception as exc:
            warnings.warn(f"[Chronos] Inference failed: {exc}. "
                          "Falling back to LightGBM + Prophet.")
            return None
