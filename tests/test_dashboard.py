from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_dashboard_workflow():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'src/ui/app.py')).run(timeout=45)
    assert not app.exception
    assert len(app.metric)==5
    app.slider[1].set_value(0.0).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value=='+0.00%'
    app.selectbox[1].set_value('S02').run(timeout=30)
    assert not app.exception
    assert app.metric[3].value=='0.0 min'
    app.selectbox[1].set_value('S09')
    app.selectbox[2].set_value(5)
    app.selectbox[3].set_value('Storm')
    app.checkbox[0].set_value(True).run(timeout=30)
    assert not app.exception
    assert len(app.dataframe)>=1
