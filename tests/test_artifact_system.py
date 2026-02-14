import pytest

from pr5.artifact_system import ArtifactProcessor


def test_add_artifact_valid_magical():
    ap = ArtifactProcessor()
    art = ap.add_artifact("Orb", 10, True)
    assert art == {"name": "Orb", "power": 10, "type": "magical"}
    assert ap.artifacts == [art]


@pytest.mark.parametrize("name", [None, "", "   "])
def test_add_artifact_invalid_name(name):
    ap = ArtifactProcessor()
    with pytest.raises(ValueError):
        ap.add_artifact(name, 10, True)


def test_add_artifact_rejects_non_numeric_power():
    ap = ArtifactProcessor()
    with pytest.raises(TypeError):
        ap.add_artifact("X", "10", True)


@pytest.mark.parametrize("power", [0, -1, -0.1])
def test_add_artifact_power_must_be_positive(power):
    ap = ArtifactProcessor()
    with pytest.raises(ValueError):
        ap.add_artifact("X", power, True)


def test_add_artifact_type_normal_when_not_magical():
    ap = ArtifactProcessor()
    art = ap.add_artifact("Stone", 5, False)
    assert art["type"] == "normal"


def test_calculate_total_power_only_magical_and_empty():
    ap = ArtifactProcessor()
    assert ap.calculate_total_power() == 0
    ap.add_artifact("A", 10, True)
    ap.add_artifact("B", 5, False)
    ap.add_artifact("C", 7, True)
    assert ap.calculate_total_power() == 17


def test_get_most_powerful_empty_returns_none():
    ap = ArtifactProcessor()
    assert ap.get_most_powerful() is None


def test_get_most_powerful_first_on_tie_and_updates_on_greater():
    ap = ArtifactProcessor()
    a1 = ap.add_artifact("A1", 10, True)
    a2 = ap.add_artifact("A2", 10, True)
    a3 = ap.add_artifact("A3", 11, True)
    assert ap.get_most_powerful() == a3
    # tie should keep first among equal max (if A3 removed in logic, still check tie behaviour)
    ap2 = ArtifactProcessor()
    b1 = ap2.add_artifact("B1", 10, True)
    b2 = ap2.add_artifact("B2", 10, True)
    assert ap2.get_most_powerful() == b1
    assert ap2.get_most_powerful() != b2


def test_remove_artifact_removes_all_occurrences_and_returns_count():
    ap = ArtifactProcessor()
    ap.add_artifact("Dup", 1, True)
    ap.add_artifact("X", 2, True)
    ap.add_artifact("Dup", 3, False)
    removed = ap.remove_artifact("Dup")
    assert removed == 2
    assert [a["name"] for a in ap.artifacts] == ["X"]


def test_remove_artifact_not_found_returns_0_and_none_raises():
    ap = ArtifactProcessor()
    ap.add_artifact("A", 1, True)
    assert ap.remove_artifact("B") == 0
    with pytest.raises(ValueError):
        ap.remove_artifact(None)


def test_get_artifacts_by_type_case_insensitive_and_validation():
    ap = ArtifactProcessor()
    ap.add_artifact("A", 1, True)
    ap.add_artifact("B", 2, False)

    assert [a["name"] for a in ap.get_artifacts_by_type("MAGICAL")] == ["A"]
    assert [a["name"] for a in ap.get_artifacts_by_type("normal")] == ["B"]
    assert ap.get_artifacts_by_type("unknown") == []

    with pytest.raises(ValueError):
        ap.get_artifacts_by_type(None)
    with pytest.raises(ValueError):
        ap.get_artifacts_by_type("")

def test_get_artifacts_by_type_empty_list_returns_empty():
    ap = ArtifactProcessor()
    assert ap.get_artifacts_by_type("magical") == []
    assert ap.get_artifacts_by_type("normal") == []


def test_calculate_total_power_ignores_normal_even_if_stronger():
    ap = ArtifactProcessor()
    ap.add_artifact("Nuke", 10_000, False)   # normal
    ap.add_artifact("Wand", 3, True)         # magical
    assert ap.calculate_total_power() == 3


def test_add_artifact_allows_float_power_if_positive():
    ap = ArtifactProcessor()
    art = ap.add_artifact("Floaty", 1.5, True)
    assert art["power"] == 1.5
    assert art["type"] == "magical"
