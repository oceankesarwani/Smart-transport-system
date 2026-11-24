"""Predeclared full OD grid across scenario regimes and comfort weights."""
import json
import time
from itertools import permutations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.config import BASE_DIR
from src.pipeline.data_loader import DataLoader
from src.model.crowd_predictor import CrowdPredictor
from src.routing.router import SmartTransitRouter

SCENARIOS = [
 ('morning',9,1,'Clear',0),('evening',18,3,'Clear',0),
 ('off_peak',12,1,'Clear',0),('weekend',17,5,'Clear',0),
 ('rain',9,1,'Rain',0),('storm',18,3,'Storm',0),
 ('event',18,4,'Clear',1)]
WEIGHTS=[0,1,2,5]


def run_benchmark(output_dir=None):
    stations=DataLoader.load_stations().station_id.tolist()
    predictor=CrowdPredictor.load()
    router=SmartTransitRouter()
    records=[]
    prediction_times=[]
    for scenario,hour,day,weather,event in SCENARIOS:
        t=time.perf_counter()
        crowd=predictor.predict_network(stations,hour,day,weather,event)
        prediction_times.append((time.perf_counter()-t)*1000)
        for origin,destination in permutations(stations,2):
            for comfort in WEIGHTS:
                t=time.perf_counter()
                result=router.compare_routes(origin,destination,crowd,comfort)
                elapsed=(time.perf_counter()-t)*1000
                a,b=result['naive_route'],result['smart_route']
                record=dict(scenario=scenario,hour=hour,day=day,weather=weather,event=event,
                    origin=origin,destination=destination,comfort=comfort,routing_pair_ms=elapsed,
                    baseline_path='>'.join(a['stations']),smart_path='>'.join(b['stations']),
                    reduction_percent=result['analytics']['crowd_reduction_percent'],
                    changed=result['analytics']['is_different_path'])
                for prefix,route in [('baseline',a),('smart',b)]:
                    record.update({prefix+'_mean':route['avg_congestion'],prefix+'_max':route['max_congestion'],
                        prefix+'_high':len(route['bottlenecks']),prefix+'_minutes':route['total_time_mins'],
                        prefix+'_transfers':route['transfers']})
                records.append(record)
    out=Path(output_dir) if output_dir else BASE_DIR/'results';out.mkdir(parents=True,exist_ok=True)
    df=pd.DataFrame(records)
    df.to_csv(out/'routing_benchmark.csv',index=False)
    delta=df.baseline_mean-df.smart_mean
    best=df.loc[df.reduction_percent.idxmax()].to_dict()
    summary={'scenarios':len(df),'regimes':len(SCENARIOS),'weights':WEIGHTS,
        'improved_percent':float((delta>1e-12).mean()*100),
        'equal_exposure_percent':float((delta.abs()<=1e-12).mean()*100),
        'worsened_percent':float((delta < -1e-12).mean()*100),
        'unchanged_itinerary_percent':float((~df.changed).mean()*100),
        'mean_reduction_percent':float(df.reduction_percent.mean()),
        'mean_baseline_exposure':float(df.baseline_mean.mean()),
        'mean_smart_exposure':float(df.smart_mean.mean()),
        'mean_time_delta_minutes':float((df.smart_minutes-df.baseline_minutes).mean()),
        'mean_routing_pair_ms':float(df.routing_pair_ms.mean()),
        'p95_routing_pair_ms':float(df.routing_pair_ms.quantile(.95)),
        'mean_network_prediction_ms':float(np.mean(prediction_times)),
        'largest_reduction_demo':best,
        'demo':df[(df.scenario=='storm') & (df.origin=='S04') & (df.destination=='S14') & (df.comfort==2)].iloc[0].to_dict()}
    (out/'routing_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    groups=df.groupby('scenario')[['baseline_mean','smart_mean']].mean()
    ax=groups.plot.bar(color=['#2563eb','#059669'],figsize=(9,4),rot=0)
    ax.set(ylabel='Mean predicted station congestion [0,1]',xlabel='',title='Full-grid simulation results across all comfort weights')
    ax.legend(['Conventional','Crowd-aware']);plt.tight_layout();plt.savefig(out/'routing_comparison.png',dpi=180);plt.close()
    ax=df.groupby('comfort').reduction_percent.mean().plot(marker='o',color='#059669',figsize=(7,3.5))
    ax.set(xlabel='Comfort preference',ylabel='Mean signed exposure reduction (%)',title='Preference sensitivity across every OD pair and regime')
    plt.tight_layout();plt.savefig(out/'preference_sensitivity.png',dpi=180);plt.close()
    print(json.dumps(summary,indent=2))
    return summary

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir')
    run_benchmark(parser.parse_args().output_dir)
