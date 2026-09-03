from investment_pipeline.enrichment.hn import is_relevant_hn_hit
from investment_pipeline.models import CandidateStartup


def test_generic_short_name_requires_domain_match():
    candidate = CandidateStartup(
        id="yc-1",
        name="Mount",
        website="https://mount.insure",
        one_liner="AI insurance carrier",
    )
    hit = {
        "title": "TabFS: Mount your Browser Tabs as a Filesystem",
        "url": "https://example.com/tabfs",
    }

    assert is_relevant_hn_hit(candidate, "mount.insure", hit) is False


def test_domain_match_is_relevant_for_generic_name():
    candidate = CandidateStartup(
        id="yc-1",
        name="Mount",
        website="https://mount.insure",
        one_liner="AI insurance carrier",
    )
    hit = {
        "title": "Launch HN: Mount",
        "url": "https://mount.insure",
    }

    assert is_relevant_hn_hit(candidate, "mount.insure", hit) is True


def test_compacted_words_do_not_create_false_positive():
    candidate = CandidateStartup(
        id="yc-2",
        name="Cotool",
        website="https://cotool.ai",
        one_liner="AI for security teams",
    )
    hit = {
        "title": "Whereismydata.co tool reveals which companies hold your personal data",
        "url": "https://example.com",
    }

    assert is_relevant_hn_hit(candidate, "cotool.ai", hit) is False


def test_multi_word_name_requires_phrase_boundary():
    candidate = CandidateStartup(
        id="yc-3",
        name="Fiber AI",
        website="https://www.fiber.ai/apis",
        one_liner="Data APIs for AI sales products",
    )
    hit = {
        "title": "America's Cup sailors plan to use rigid carbon-fiber airfoil",
        "url": "https://example.com/airfoil",
    }

    assert is_relevant_hn_hit(candidate, "fiber.ai", hit) is False


def test_subdomain_url_matches_candidate_domain():
    candidate = CandidateStartup(
        id="yc-4",
        name="Fiber AI",
        website="https://www.fiber.ai/apis",
        one_liner="Data APIs for AI sales products",
    )
    hit = {
        "title": "Launch HN: Data enrichment tool",
        "url": "https://blog.fiber.ai/launch",
    }

    assert is_relevant_hn_hit(candidate, "fiber.ai", hit) is True
