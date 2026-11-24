"""Reproduce chronological model selection and final test evaluation."""
import json
from pathlib import Path
from src.pipeline.data_loader import DataLoader
from src.model.crowd_predictor import CrowdPredictor, chronological_split
from src.config import BASE_DIR


def train_model():
    df = DataLoader.load_crowd_data()
    predictor = CrowdPredictor()
    metrics = predictor.train_and_evaluate(*chronological_split(df))
    predictor.save()
    results = BASE_DIR / 'results'
    results.mkdir(exist_ok=True)
    (results / 'model_metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print(json.dumps(metrics,indent=2))
    return metrics


if __name__ == '__main__':
    train_model()
