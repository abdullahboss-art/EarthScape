import os
os.environ["USE_MOCK_DB"] = "1"
import pandas as pd
from streamlit.testing.v1 import AppTest
import analytics

HERE = os.path.dirname(__file__)


def test_analytics_and_app():
    # --- data layer
    db = analytics.get_db()
    df = analytics.clean(pd.read_csv(os.path.join(HERE, "climate_sample.csv")))
    assert analytics.save(db, df) == 6576
    assert analytics.scan(db, df, analytics.DEFAULT_TH) > 0
    full = analytics.load(db)
    k = analytics.kpis(full, 30)
    assert 3.0 < k["sea_level"]["value"] < 4.2
    assert 0.1 < analytics.predict_delta(full, 2031)["slope"] < 0.4
    assert len(analytics.trend(full, "temperature")["forecast"]) == 12

    # --- website: register -> login -> open every page
    at = AppTest.from_file(os.path.join(HERE, "app.py"), default_timeout=90).run()
    assert not at.exception
    at.text_input(key="reg_name").input("Ali Khan"); at.text_input(key="reg_email").input("a@x.com"); at.text_input(key="reg_pw").input("secret1")
    at.button[1].click().run()                                       # "Sign up"
    assert db.users.find_one({"email": "a@x.com"})["role"] == "admin"   # first user = admin
    at.text_input(key="login_email").input("a@x.com"); at.text_input(key="login_pw").input("wrong")
    at.button[0].click().run()
    assert not at.session_state["user"] if "user" in at.session_state else True
    at.text_input(key="login_pw").input("secret1"); at.button[0].click().run()
    assert at.session_state["user"]["role"] == "admin"
    for page in ['📊 Dashboard', '⬆️ Data Upload', '🔔 Alerts', '💬 Support', '👥 Manage Users']:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, (page, at.exception)
