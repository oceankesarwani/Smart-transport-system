from src.pipeline.data_loader import DataLoader
from src.model.crowd_predictor import CrowdPredictor
from src.routing.router import SmartTransitRouter

def run_quick_check():
    stations=DataLoader.load_stations()
    model=CrowdPredictor.load()
    crowd=model.predict_network(stations.station_id.tolist(),9,1)
    result=SmartTransitRouter().compare_routes('S02','S03',crowd,2)
    assert result['status']=='SUCCESS'
    print(result)

if __name__=='__main__':
    run_quick_check()
