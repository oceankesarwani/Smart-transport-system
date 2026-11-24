"""Deterministic scenario features and validation-selected congestion regression."""
from pathlib import Path
import platform
import joblib
import sklearn
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from src.config import MODEL_FILE


def chronological_split(df):
    df = df.sort_values(['timestamp', 'station_id']).reset_index(drop=True)
    dates = pd.to_datetime(df.timestamp).dt.normalize().unique()
    if len(dates) < 5:
        raise ValueError('At least five days required for chronological splits')
    a, b = int(len(dates)*.6), int(len(dates)*.8)
    day = pd.to_datetime(df.timestamp).dt.normalize()
    return df[day < dates[a]], df[(day >= dates[a]) & (day < dates[b])], df[day >= dates[b]]


def regression_metrics(actual, predicted):
    return {'MAE': float(mean_absolute_error(actual, predicted)),
            'RMSE': float(np.sqrt(mean_squared_error(actual, predicted))),
            'R2': float(r2_score(actual, predicted))}


class CrowdPredictor:
    def __init__(self):
        self.model = None
        self.station_encoder = {}
        self.feature_columns = []
        self.metrics = {}

    def _engineer_features(self, df, fit_encoder=False):
        df = df.copy()
        if fit_encoder:
            self.station_encoder = {s:i for i,s in enumerate(sorted(df.station_id.unique()))}
        if not self.station_encoder or not set(df.station_id).issubset(self.station_encoder):
            raise ValueError('Unknown station or missing fitted station encoder')
        for col, lo, hi in [('hour',0,23), ('day_of_week',0,6)]:
            values = pd.to_numeric(df[col], errors='raise')
            if not values.between(lo,hi).all() or not np.isfinite(values).all():
                raise ValueError(f'Invalid {col}')
        if not (df.day_of_week % 1 == 0).all():
            raise ValueError('Day of week must be an integer')
        if 'weather' not in df:
            df['weather'] = 'Clear'
        if not df.weather.isin(['Clear','Rain','Storm']).all():
            raise ValueError('Invalid weather')
        if 'special_event' not in df:
            df['special_event'] = 0
        if not df.special_event.isin([0,1]).all():
            raise ValueError('Invalid special_event')
        x = pd.DataFrame(index=df.index)
        for name, period in [('hour',24),('day_of_week',7)]:
            x[name+'_sin'] = np.sin(2*np.pi*df[name]/period)
            x[name+'_cos'] = np.cos(2*np.pi*df[name]/period)
        x['is_weekend'] = (df.day_of_week >= 5).astype(int)
        # Derived identically in training and inference; ignore stored proxy flags.
        x['is_peak'] = (df.hour.between(8,10) | df.hour.between(17,20)).astype(int)
        x['special_event'] = df.special_event
        for w in ['Clear','Rain','Storm']:
            x['weather_'+w] = (df.weather == w).astype(int)
        for s in self.station_encoder:
            x['st_'+s] = (df.station_id == s).astype(int)
        self.feature_columns = list(x.columns)
        return x

    def train_and_evaluate(self, train_df, validation_df, test_df=None):
        # Legacy two-frame callers split their training period again, keeping the supplied final test untouched.
        if test_df is None:
            test_df = validation_df
            dates = pd.to_datetime(train_df.timestamp).dt.normalize()
            boundary = sorted(dates.unique())[int(len(dates.unique())*.8)]
            validation_df, train_df = train_df[dates >= boundary], train_df[dates < boundary]
        xt = self._engineer_features(train_df, True)
        xv = self._engineer_features(validation_df)
        candidates = {
            'Historical mean': DummyRegressor(strategy='mean'),
            'Ridge': Ridge(alpha=1),
            'Random Forest': RandomForestRegressor(n_estimators=80,max_depth=14,random_state=42,n_jobs=1),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=140,learning_rate=.08,max_depth=4,random_state=42)
        }
        validation = {}
        for name, model in candidates.items():
            model.fit(xt, train_df.congestion_index)
            validation[name] = regression_metrics(validation_df.congestion_index,np.clip(model.predict(xv),0,1))
        selected = min(validation, key=lambda n: validation[n]['RMSE'])
        self.model = candidates[selected]
        # Refit selected architecture on train + validation, then evaluate once on held-out final dates.
        development = pd.concat([train_df,validation_df])
        self.model.fit(self._engineer_features(development),development.congestion_index)
        test_predictions = np.clip(self.model.predict(self._engineer_features(test_df)),0,1)
        self.metrics = regression_metrics(test_df.congestion_index,test_predictions)
        self.metrics.update(best_model_name=selected, validation_benchmarks=validation,
            splits={name:{'rows':len(frame),'start':str(frame.timestamp.min()),'end':str(frame.timestamp.max())}
                    for name,frame in [('train',train_df),('validation',validation_df),('test',test_df)]},
            python=platform.python_version(), sklearn=sklearn.__version__, seed=42)
        return self.metrics

    def predict_network(self, station_ids, hour, day_of_week=1, weather='Clear', special_event=0):
        if self.model is None:
            raise ValueError('Model is not trained; run python -m src.model.train')
        if not station_ids:
            return {}
        frame = pd.DataFrame({'station_id':station_ids,'hour':hour,'day_of_week':day_of_week,
                              'weather':weather,'special_event':special_event})
        preds = np.clip(self.model.predict(self._engineer_features(frame)),0,1)
        if not np.isfinite(preds).all():
            raise ValueError('Nonfinite model prediction')
        return dict(zip(station_ids,map(float,preds)))

    def predict_single(self, station_id, hour, day_of_week=1, weather='Clear', special_event=0):
        return self.predict_network([station_id],hour,day_of_week,weather,special_event)[station_id]

    def save(self, filepath=None):
        if self.model is None:
            raise ValueError('Cannot save untrained model')
        path = Path(filepath or MODEL_FILE)
        path.parent.mkdir(parents=True,exist_ok=True)
        joblib.dump({'schema_version':2,'sklearn':sklearn.__version__,'predictor':self},path)
        return str(path)

    @classmethod
    def load(cls, filepath=None):
        path = Path(filepath or MODEL_FILE)
        if not path.exists():
            raise FileNotFoundError(f'Model missing: {path}. Run python -m src.model.train')
        try:
            payload = joblib.load(path)
            if payload.get('schema_version') != 2 or payload.get('sklearn') != sklearn.__version__:
                raise ValueError('Model version incompatible')
            predictor = payload['predictor']
            if not isinstance(predictor,cls) or predictor.model is None:
                raise ValueError('Invalid model payload')
            return predictor
        except Exception as exc:
            raise ValueError('Model unavailable or incompatible. Run python -m src.model.train') from exc
