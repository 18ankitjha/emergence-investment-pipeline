from investment_pipeline.models import CandidateStartup
from investment_pipeline.sourcing.selection import batch_recency_score, candidate_relevance_score, select_candidates

TOPIC = "AI agents for SMB back-office workflows"


def make(name: str, one_liner: str, **kwargs) -> CandidateStartup:
    return CandidateStartup(id=f"yc-{name}", name=name, one_liner=one_liner, **kwargs)


def test_batch_recency_scores_recent_batches_higher():
    assert batch_recency_score("Summer 2026") > batch_recency_score("Winter 2024")
    assert batch_recency_score("Winter 2024") > batch_recency_score("Winter 2019")
    assert batch_recency_score("Winter 2019") < 0
    assert batch_recency_score(None) == 0
    assert batch_recency_score("no year here") == 0


def test_recent_seed_company_outranks_old_growth_company():
    fresh = make("Fresh", "AI agents that automate back-office finance workflows for SMBs", batch="Spring 2026", team_size=4)
    old = make("Old", "AI agents that automate back-office finance workflows for SMBs", batch="Winter 2020", team_size=80, stage="Growth")
    assert candidate_relevance_score(fresh, TOPIC) > candidate_relevance_score(old, TOPIC)


def test_acquired_company_is_pushed_out():
    good = make("Good", "AI workflow automation for SMB teams", batch="Summer 2025")
    acquired = make("Gone", "AI workflow automation for SMB teams", batch="Summer 2025", status="Acquired")
    selected = select_candidates([good, acquired], TOPIC, limit=1)
    assert selected == [good]
