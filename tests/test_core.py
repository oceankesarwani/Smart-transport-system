"""Regression, boundary, equivalence and independent expanded-state routing checks."""
import math
import random
import networkx as nx
import numpy as np
import pandas as pd
import pytest
from src.routing.router import SmartTransitRouter
from src.routing.cost_functions import compute_congestion_penalty as penalty, calculate_edge_cost
from src.routing.graph_builder import TransitGraphBuilder
from src.pipeline.data_loader import DataLoader
from src.model.crowd_predictor import CrowdPredictor, chronological_split


def graph(edges):
    g=nx.MultiDiGraph()
    for u,v,line,minutes in edges:
        g.add_edge(u,v,line_name=line,base_time_mins=minutes,distance_km=1)
    return g


@pytest.mark.parametrize('rho,expected',[(0,0),(.35,0),(.5,1.2),(.7,2.8),(1,5.95)])
def test_penalty_boundaries(rho,expected):
    assert penalty(rho)==pytest.approx(expected)


def test_penalty_continuity_monotonicity():
    values=[penalty(float(v)) for v in np.linspace(0,1,1001)]
    assert values==sorted(values)
    for t in [.35,.7]:
        assert abs(penalty(t-1e-8)-penalty(t+1e-8))<1e-5


@pytest.mark.parametrize('bad',[-.1,1.01,float('nan'),float('inf')])
def test_invalid_congestion(bad):
    with pytest.raises(ValueError): penalty(bad)


@pytest.mark.parametrize('position',[0,4,5,6])
@pytest.mark.parametrize('bad',[-1,float('nan'),float('inf')])
def test_invalid_cost_parameters(position,bad):
    args=[2,.5,'a','b',1,2,4];args[position]=bad
    with pytest.raises(ValueError): calculate_edge_cost(*args)


def test_transfer_cost_and_zero_crowd():
    assert calculate_edge_cost(3,1,'a','b',1,0,4)==7
    assert calculate_edge_cost(3,1,None,'b',1,0,4)==3


def test_parallel_lines_transfer_and_ties():
    g=graph([('a','b','red',1),('a','b','blue',2),('b','c','blue',1),('a','d','red',2),('d','c','red',2)])
    router=SmartTransitRouter(g); crowd=dict.fromkeys(g,.8)
    route=router.find_naive_route('a','c',crowd)
    assert route['total_time_mins']==3
    assert [e['line_name'] for e in route['segments']]==['blue','blue']
    assert router.find_crowd_aware_route('a','c',crowd,0)==route
    transferred=SmartTransitRouter(graph([('a','b','x',1),('b','c','y',1)])).find_naive_route('a','c')
    assert transferred['transfers']==1
    assert transferred['total_time_mins']==6
    assert transferred['transfer_time_mins']==4


def test_diversion_and_identity():
    router=SmartTransitRouter(graph([('a','b','x',1),('b','c','x',1),('a','d','x',2),('d','c','x',2)]))
    crowd={'a':.1,'b':1,'c':.1,'d':.1}
    result=router.compare_routes('a','c',crowd,2)
    assert result['smart_route']['stations']==['a','d','c']
    assert result['analytics']['crowd_reduction_percent']>0
    identity=router.find_crowd_aware_route('b','b',crowd,1)
    assert identity['avg_congestion']==1
    assert identity['total_time_mins']==0
    assert len(identity['bottlenecks'])==1


def test_signed_worsening_not_clamped():
    # Avoiding a short expensive crowded intermediate may increase arithmetic mean via path length.
    router=SmartTransitRouter(graph([('a','b','x',1),('b','d','x',1),('d','c','x',1),('a','c','x',4)]))
    crowd={'a':.9,'b':.4,'d':.4,'c':.9}
    r=router.compare_routes('a','c',crowd,5)
    assert r['analytics']['crowd_reduction_percent']<0


def test_zero_denominator_and_unchanged():
    router=SmartTransitRouter(graph([('a','b','x',1)]))
    result=router.compare_routes('a','b',{'a':0,'b':0},0)
    assert result['analytics']['crowd_reduction_percent']==0
    assert not result['analytics']['is_different_path']


def test_invalid_disconnected_and_missing_predictions():
    g=graph([('a','b','x',1)]);g.add_node('c')
    router=SmartTransitRouter(g)
    assert router.compare_routes('a','c',dict.fromkeys(g,.2))['status']=='FAILED'
    with pytest.raises(ValueError): router.find_naive_route('x','a')
    with pytest.raises(ValueError): router.find_naive_route('a','x')
    with pytest.raises(ValueError): router.find_naive_route('a','b',{'a':.2})
    with pytest.raises(ValueError): router.find_crowd_aware_route('a','a',dict.fromkeys(g,.2),-1)
    g['a']['b'][0]['base_time_mins']=-1
    with pytest.raises(ValueError): router.find_naive_route('a','b')


@pytest.mark.parametrize('seed',range(12))
def test_independent_expanded_networkx(seed):
    rng=random.Random(seed)
    edges=[(str(u),str(v),line,rng.randint(0,8)) for u in range(5) for v in range(5) if u!=v for line in ['r','b'] if rng.random()<.35]
    g=graph(edges);g.add_nodes_from(map(str,range(5)))
    crowd={s:rng.random() for s in g}
    router=SmartTransitRouter(g)
    for preference in [0,2]:
        expanded=nx.DiGraph()
        start=('0',None);end=('sink',None)
        states=[start]+[(s,line) for s in g for line in ['r','b']]
        for u,last in states:
            for _,v,data in g.out_edges(u,data=True):
                cost=data['base_time_mins']+(4 if last is not None and last!=data['line_name'] else 0)+2.5*preference*penalty(crowd[v])
                state=(v,data['line_name'])
                old=expanded.get_edge_data((u,last),state,{}).get('weight',math.inf)
                expanded.add_edge((u,last),state,weight=min(old,cost))
        for line in ['r','b']:
            expanded.add_edge(('4',line),end,weight=0)
        expanded.add_node(start)
        result=router.find_crowd_aware_route('0','4',crowd,preference)
        if nx.has_path(expanded,start,end):
            assert result['effective_cost']==pytest.approx(nx.shortest_path_length(expanded,start,end,weight='weight'))
        else:
            assert result is None


@pytest.fixture(scope='module')
def predictor():
    return CrowdPredictor.load()


def test_feature_generation_no_leakage(predictor):
    df=DataLoader.load_crowd_data().head(50)
    x=predictor._engineer_features(df)
    corrupt=df.copy();corrupt['congestion_index']=1;corrupt['inflow_count']=999999;corrupt['is_peak']=123
    pd.testing.assert_frame_equal(x,predictor._engineer_features(corrupt))
    assert np.allclose(x.hour_sin**2+x.hour_cos**2,1)
    assert 'congestion_index' not in x


@pytest.mark.parametrize('kwargs',[{'hour':-1},{'hour':24},{'hour':float('nan')},{'day_of_week':7},{'day_of_week':1.5},{'weather':'Snow'},{'special_event':2},{'station_ids':['missing']}])
def test_prediction_invalid_inputs(predictor,kwargs):
    params=dict(station_ids=['S01'],hour=9,day_of_week=1,weather='Clear',special_event=0);params.update(kwargs)
    with pytest.raises(ValueError): predictor.predict_network(**params)


def test_prediction_boundaries_persistence_and_errors(predictor,tmp_path):
    for hour in [0,23]:
        value=predictor.predict_single('S01',hour,6,'Storm',1)
        assert 0<=value<=1
    assert predictor.predict_network([],9)=={}
    with pytest.raises(ValueError): CrowdPredictor().predict_single('S01',9)
    with pytest.raises(ValueError): CrowdPredictor().save(tmp_path/'new.pkl')
    with pytest.raises(FileNotFoundError): CrowdPredictor.load(tmp_path/'missing')
    bad=tmp_path/'bad.pkl';bad.write_text('broken')
    with pytest.raises(ValueError): CrowdPredictor.load(bad)
    import joblib
    joblib.dump({'schema_version':1},bad)
    with pytest.raises(ValueError): CrowdPredictor.load(bad)
    joblib.dump({'schema_version':2,'sklearn':__import__('sklearn').__version__,'predictor':'invalid'},bad)
    with pytest.raises(ValueError): CrowdPredictor.load(bad)
    predictor.save(tmp_path/'good.pkl')
    assert CrowdPredictor.load(tmp_path/'good.pkl').predict_single('S01',9)==predictor.predict_single('S01',9)


def test_chronological_splits():
    df=DataLoader.load_crowd_data().sample(frac=1,random_state=9)
    a,b,c=chronological_split(df)
    assert a.timestamp.max()<b.timestamp.min()<c.timestamp.min()
    assert b.timestamp.max()<c.timestamp.min()
    assert len(a)+len(b)+len(c)==len(df)
    with pytest.raises(ValueError): chronological_split(df.head(1))


def test_graph_schema_and_unknown_endpoint():
    stations=DataLoader.load_stations();routes=DataLoader.load_routes()
    g=TransitGraphBuilder.build_network_graph(stations,routes)
    assert len(g)==20 and nx.is_strongly_connected(g)
    assert len(g['S02']['S04'])==2
    routes.loc[0,'from_station']='bad'
    with pytest.raises(ValueError): TransitGraphBuilder.build_network_graph(stations,routes)


@pytest.mark.parametrize('kind',['stations','routes','crowd_data'])
def test_loader_missing_schema_and_file(kind,tmp_path):
    load=getattr(DataLoader,'load_'+kind)
    with pytest.raises(FileNotFoundError): load(tmp_path/'missing')
    path=tmp_path/'empty.csv';pd.DataFrame({'wrong':[1]}).to_csv(path,index=False)
    with pytest.raises(ValueError): load(path)


@pytest.mark.parametrize('kind,column,value',[
 ('stations','capacity',0),('stations','latitude',100),('stations','name',None),
 ('routes','base_time_mins',-1),('routes','distance_km',float('inf')),('routes','line_name',None),
 ('crowd_data','congestion_index',1.1),('crowd_data','hour',24),('crowd_data','weather','Snow'),
 ('crowd_data','timestamp','broken'),('crowd_data','day_of_week',3)])
def test_loader_malformed(kind,column,value,tmp_path):
    load=getattr(DataLoader,'load_'+kind);df=load()
    df.loc[0,column]=value
    path=tmp_path/'bad.csv';df.to_csv(path,index=False)
    with pytest.raises((ValueError,TypeError)): load(path)


def test_duplicate_data(tmp_path):
    for kind in ['stations','crowd_data']:
        load=getattr(DataLoader,'load_'+kind);df=load()
        path=tmp_path/'duplicate.csv';pd.concat([df,df.head(1)]).to_csv(path,index=False)
        with pytest.raises(ValueError): load(path)
import pytest
from src.model.crowd_predictor import CrowdPredictor
from src.pipeline.data_loader import DataLoader


def test_training_rejects_overlapping_periods():
    df=DataLoader.load_crowd_data()
    with pytest.raises(ValueError,match='disjoint chronological'):
        CrowdPredictor().train_and_evaluate(df.head(100),df.head(100),df.head(100))

def test_generator_reproduces_committed_history(tmp_path):
    from data.generate_dataset import generate_crowd_data
    output=tmp_path/'history.csv'
    generated=generate_crowd_data(str(output),seed=42,days=60)
    committed=pd.read_csv('data/historical_crowd.csv')
    pd.testing.assert_frame_equal(generated,committed)
