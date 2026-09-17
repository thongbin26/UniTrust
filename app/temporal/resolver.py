from app.temporal.models import TemporalValidity
from app.temporal.repository import is_latest_version, get_temporal_relations_for_target
from app.models.obligation import TemporalRelationType

class TemporalResolver:
    @staticmethod
    def resolve_validity(notice_id: int, version_id: int) -> TemporalValidity:
        """
        Determines the current temporal validity of a notice version.
        """
        # Check if it's the latest version within its own notice
        if is_latest_version(notice_id, version_id):
            # Even if it's the latest version of this notice, check if it's explicitly superseded by ANOTHER notice
            relations = get_temporal_relations_for_target(notice_id, version_id)
            for conf_rel in relations:
                rel = conf_rel.relation
                if rel.relation_type in (TemporalRelationType.SUPERSEDES, TemporalRelationType.AMENDS):
                    if conf_rel.is_confirmed:
                        return TemporalValidity.SUPERSEDED_OUTDATED
                    else:
                        return TemporalValidity.UNKNOWN
            return TemporalValidity.CURRENT
        else:
            # It's an older historical version of the same notice
            return TemporalValidity.SUPERSEDED_OUTDATED
