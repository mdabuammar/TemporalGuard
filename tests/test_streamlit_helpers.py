from temporalguard.frontend.streamlit_helpers import build_dashboard_state


def test_build_dashboard_state_returns_mapping():
    assert build_dashboard_state({"mode": "demo"}) == {"mode": "demo"}
