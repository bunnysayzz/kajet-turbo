import datetime
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import pytest
from loki_source import (
    LokiConfigError,
    SshTarget,
    _to_unix_ns,
    _warn_if_capped,
    _warn_if_stale,
    build_selector,
    parse_query_range_response,
)

SSH_ENV = ("KAJET_LOG_SSH_HOST", "KAJET_LOG_SSH_USER", "KAJET_LOG_SSH_KEY")


def test_build_selector_base():
    sel = build_selector("mcp", "produkcja")
    assert sel == (
        '{coolify_projectName="kajet-turbo", '
        'service="kajet-mcp", '
        'coolify_environmentName="produkcja"}'
    )


def test_build_selector_with_min_level_warning():
    sel = build_selector("mcp", "produkcja", min_level="warning")
    assert sel == (
        '{coolify_projectName="kajet-turbo", '
        'service="kajet-mcp", '
        'coolify_environmentName="produkcja", '
        'level=~"warning|error|critical"}'
    )


def test_build_selector_with_msg_filter():
    """msg stopped being a Loki label (per-UUID cardinality), so it filters the line."""
    sel = build_selector("mcp", "produkcja", msg_filter=["save_note", "note_updated"])
    assert sel == (
        '{coolify_projectName="kajet-turbo", '
        'service="kajet-mcp", '
        'coolify_environmentName="produkcja"} '
        '| json | msg=~"save_note|note_updated"'
    )


def test_build_selector_env_alias_normalizes():
    # matches analyze-logs.py's existing prod/production -> produkcja, dev/development -> develop
    assert 'coolify_environmentName="produkcja"' in build_selector("mcp", "prod")
    assert 'coolify_environmentName="develop"' in build_selector("mcp", "dev")


def test_parse_query_range_response_flattens_and_sorts():
    data = {
        "data": {
            "result": [
                {
                    "stream": {"container": "kajet-mcp-abc"},
                    "values": [
                        ["1700000002000000000", '{"ts": "2026-01-01T00:00:02Z", "msg": "b"}'],
                        ["1700000000000000000", '{"ts": "2026-01-01T00:00:00Z", "msg": "a"}'],
                    ],
                },
                {
                    "stream": {"container": "kajet-mcp-def"},
                    "values": [
                        ["1700000001000000000", '{"ts": "2026-01-01T00:00:01Z", "msg": "c"}'],
                    ],
                },
            ]
        }
    }
    events = parse_query_range_response(data)
    assert [e["msg"] for e in events] == ["a", "c", "b"]


def test_parse_query_range_response_skips_unparseable_lines():
    data = {
        "data": {
            "result": [
                {
                    "stream": {},
                    "values": [
                        ["1700000000000000000", "not json at all"],
                        ["1700000001000000000", '{"ts": "2026-01-01T00:00:01Z", "msg": "ok"}'],
                    ],
                }
            ]
        }
    }
    events = parse_query_range_response(data)
    assert len(events) == 1
    assert events[0]["msg"] == "ok"


def test_parse_query_range_response_empty_result():
    assert parse_query_range_response({"data": {"result": []}}) == []


def test_to_unix_ns_now_is_close_to_current_time():
    assert abs(_to_unix_ns("now") - int(time.time() * 1e9)) < 2_000_000_000  # within 2s


def test_to_unix_ns_relative_duration():
    now_ns = int(time.time() * 1e9)
    one_hour_ago_ns = _to_unix_ns("1h")
    assert abs((now_ns - one_hour_ago_ns) - 3600 * 1_000_000_000) < 2_000_000_000


def test_to_unix_ns_iso_timestamp():
    assert _to_unix_ns("2026-01-01T00:00:00") == int(
        datetime.datetime.fromisoformat("2026-01-01T00:00:00").timestamp() * 1e9
    )


def test_warn_if_capped_warns_on_5000_entries(capsys):
    """Verify warning is printed to stderr when result is exactly 5000 entries."""
    events = [{"msg": f"event_{i}"} for i in range(5000)]
    _warn_if_capped(events)
    captured = capsys.readouterr()
    assert "warning: Loki result capped at 5000 entries" in captured.err
    assert "Narrow --since, or add --mode errors" in captured.err


def test_warn_if_capped_no_warning_under_5000(capsys):
    """Verify no warning when result is under 5000 entries."""
    events = [{"msg": f"event_{i}"} for i in range(4999)]
    _warn_if_capped(events)
    captured = capsys.readouterr()
    assert captured.err == ""


def test_warn_if_capped_no_warning_over_5000(capsys):
    """Verify no warning when result is over 5000 entries (shouldn't happen but be safe)."""
    events = [{"msg": f"event_{i}"} for i in range(5001)]
    _warn_if_capped(events)
    captured = capsys.readouterr()
    assert captured.err == ""


def _event_aged(seconds: float) -> dict:
    """One event whose ts is `seconds` behind now, in the Z-suffixed form Loki emits."""
    when = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=seconds)
    return {"ts": when.isoformat().replace("+00:00", "Z"), "msg": "event"}


def test_warn_if_stale_warns_when_newest_event_lags(capsys):
    _warn_if_stale([_event_aged(600)], "now")
    captured = capsys.readouterr()
    assert "warning: newest Loki event is" in captured.err
    assert "may not match" in captured.err


def test_warn_if_stale_silent_on_fresh_window(capsys):
    _warn_if_stale([_event_aged(5)], "now")
    assert capsys.readouterr().err == ""


def test_warn_if_stale_silent_for_historical_window(capsys):
    """A window ending in the past is expected to lag — only `until=now` implies freshness."""
    _warn_if_stale([_event_aged(86400)], "2026-01-01T00:00:00")
    assert capsys.readouterr().err == ""


def test_warn_if_stale_silent_without_events(capsys):
    _warn_if_stale([], "now")
    assert capsys.readouterr().err == ""


def test_warn_if_stale_silent_on_unparseable_ts(capsys):
    """A malformed ts is the line parser's problem, not a staleness signal."""
    _warn_if_stale([{"ts": "not a timestamp"}, {"msg": "no ts at all"}], "now")
    assert capsys.readouterr().err == ""


def _set_ssh_env(monkeypatch, **overrides: str | None) -> None:
    """Set the three SSH variables, with `None` meaning "unset this one"."""
    values = {"KAJET_LOG_SSH_HOST": "logs.example", "KAJET_LOG_SSH_USER": "reader"}
    values["KAJET_LOG_SSH_KEY"] = "/keys/reader"
    values.update(overrides)
    for var in SSH_ENV:
        value = values[var]
        if value is None:
            monkeypatch.delenv(var, raising=False)
        else:
            monkeypatch.setenv(var, value)


def test_ssh_target_from_env_reads_all_three(monkeypatch):
    _set_ssh_env(monkeypatch)
    assert SshTarget.from_env() == SshTarget(host="logs.example", user="reader", key="/keys/reader")


def test_ssh_target_from_env_names_the_single_missing_variable(monkeypatch):
    _set_ssh_env(monkeypatch, KAJET_LOG_SSH_USER=None)
    with pytest.raises(LokiConfigError) as excinfo:
        SshTarget.from_env()
    message = str(excinfo.value)
    assert "KAJET_LOG_SSH_USER is unset" in message
    assert "KAJET_LOG_SSH_HOST" not in message
    assert "--source docker-logs" in message


def test_ssh_target_from_env_names_every_missing_variable_at_once(monkeypatch):
    """One failed run should report the whole gap, not the first hole in it."""
    _set_ssh_env(monkeypatch, KAJET_LOG_SSH_HOST=None, KAJET_LOG_SSH_USER=None)
    with pytest.raises(LokiConfigError) as excinfo:
        SshTarget.from_env()
    message = str(excinfo.value)
    assert "KAJET_LOG_SSH_HOST, KAJET_LOG_SSH_USER are unset" in message


def test_ssh_target_from_env_treats_blank_as_missing(monkeypatch):
    _set_ssh_env(monkeypatch, KAJET_LOG_SSH_KEY="   ")
    with pytest.raises(LokiConfigError, match="KAJET_LOG_SSH_KEY"):
        SshTarget.from_env()


def test_ssh_target_from_env_strips_surrounding_whitespace(monkeypatch):
    _set_ssh_env(monkeypatch, KAJET_LOG_SSH_HOST=" logs.example\n")
    assert SshTarget.from_env().host == "logs.example"
