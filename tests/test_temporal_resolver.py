from app.temporal.resolver import TemporalResolver
from app.temporal.models import TemporalValidity

def test_temporal_current(monkeypatch):
    monkeypatch.setattr("app.temporal.resolver.is_latest_version", lambda n, v: True)
    monkeypatch.setattr("app.temporal.resolver.get_temporal_relations_for_target", lambda n, v: [])
    
    assert TemporalResolver.resolve_validity(1, 1) == TemporalValidity.CURRENT

def test_temporal_outdated_historical(monkeypatch):
    # Not latest version
    monkeypatch.setattr("app.temporal.resolver.is_latest_version", lambda n, v: False)
    assert TemporalResolver.resolve_validity(1, 1) == TemporalValidity.SUPERSEDED_OUTDATED

def test_temporal_outdated_superseded(monkeypatch):
    # Is latest of its own notice, but superseded by another
    from app.models.obligation import TemporalRelation, TemporalRelationType
    from app.temporal.repository import ConfirmedTemporalRelation
    
    monkeypatch.setattr("app.temporal.resolver.is_latest_version", lambda n, v: True)
    monkeypatch.setattr("app.temporal.resolver.get_temporal_relations_for_target", lambda n, v: [
        ConfirmedTemporalRelation(
            relation=TemporalRelation(relation_type=TemporalRelationType.SUPERSEDES, target_notice_id=1),
            is_confirmed=True
        )
    ])
    
    assert TemporalResolver.resolve_validity(1, 1) == TemporalValidity.SUPERSEDED_OUTDATED

def test_temporal_outdated_superseded_unconfirmed(monkeypatch):
    # Is latest of its own notice, but superseded by an UNCONFIRMED edge
    from app.models.obligation import TemporalRelation, TemporalRelationType
    from app.temporal.repository import ConfirmedTemporalRelation
    
    monkeypatch.setattr("app.temporal.resolver.is_latest_version", lambda n, v: True)
    monkeypatch.setattr("app.temporal.resolver.get_temporal_relations_for_target", lambda n, v: [
        ConfirmedTemporalRelation(
            relation=TemporalRelation(relation_type=TemporalRelationType.SUPERSEDES, target_notice_id=1),
            is_confirmed=False
        )
    ])
    
    # Must be UNKNOWN, not SUPERSEDED_OUTDATED
    assert TemporalResolver.resolve_validity(1, 1) == TemporalValidity.UNKNOWN
