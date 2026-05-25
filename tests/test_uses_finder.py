import string

from hypothesis import given
from hypothesis import strategies as st

from bump_ghw import REPOS

USER = st.from_regex(r"^[a-zA-Z0-9-]{1,39}$", fullmatch=True).filter(
    lambda s: not s.startswith("-") and not s.endswith("-") and "--" not in s
)
REPO_NAME = st.from_regex(r"^[a-zA-Z0-9._-]{1,100}$", fullmatch=True).filter(
    lambda s: s not in (".", "..")
)

SHA = st.text("0123456789abcdefABCDEF", min_size=6, max_size=40)
# Technically a ref can be any character, not just ascii. But there should be no reason to
# use those characters except for malicious reasons. If a valid use case can be presented,
# I will modify my assumptions.
REF = st.text(string.ascii_letters + string.digits + "-._/", min_size=1).filter(
    lambda s: (
        not s.endswith(("/", "."))
        and not s.startswith(("/", "."))
        and ".." not in s
        and "//" not in s
        and "./" not in s
        and "/." not in s
    )
)
# Non-newline whitespace allowed before `uses:`
INDENT = st.text(" \t", min_size=0, max_size=8)


@given(USER, REPO_NAME, SHA, REF, INDENT)
def test_finding_repos_with_tag(
    user: str, repo_name: str, sha: str, ref: str, indent: str
) -> None:
    fake_action = f"{indent}uses: {user}/{repo_name}@{sha} # {ref} "
    repos = list(REPOS.finditer(fake_action))
    assert len(repos) == 1
    repo = repos[0]

    assert repo.group("indent") == indent
    assert repo.group("owner") == user
    assert repo.group("repo") == repo_name
    assert repo.group("ref") == sha
    # Greedy `#[^\n]*` captures the trailing space too.
    assert repo.group("tag") == f"# {ref} "


@given(USER, REPO_NAME, SHA, INDENT)
def test_finding_repos_without_tag(
    user: str, repo_name: str, sha: str, indent: str
) -> None:
    fake_action = f"{indent}uses: {user}/{repo_name}@{sha}"
    repos = list(REPOS.finditer(fake_action))
    assert len(repos) == 1
    repo = repos[0]

    assert repo.group("indent") == indent
    assert repo.group("owner") == user
    assert repo.group("repo") == repo_name
    assert repo.group("ref") == sha
    assert repo.group("tag") is None


def test_empty_input_matches_nothing() -> None:
    assert REPOS.findall("") == []


def test_anchored_per_line_in_multiline_yaml() -> None:
    yaml = (
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - name: checkout\n"
        "        uses: actions/checkout@abc123 # v4\n"
        "      - name: setup\n"
        "        uses: actions/setup-python@def456\n"
        "      - run: echo hi\n"
    )
    matches = list(REPOS.finditer(yaml))
    assert len(matches) == 2

    first, second = matches
    assert first.group("owner") == "actions"
    assert first.group("repo") == "checkout"
    assert first.group("ref") == "abc123"
    assert first.group("tag") == "# v4"

    assert second.group("owner") == "actions"
    assert second.group("repo") == "setup-python"
    assert second.group("ref") == "def456"
    assert second.group("tag") is None


def test_substitution_preserves_surrounding_lines() -> None:
    yaml = "        uses: actions/checkout@oldsha # v3\n      - run: echo done\n"
    replaced = REPOS.sub(
        lambda m: (
            f"{m.group('indent')}uses: {m.group('owner')}/{m.group('repo')}@NEWSHA # v4"
        ),
        yaml,
    )
    assert replaced == (
        "        uses: actions/checkout@NEWSHA # v4\n      - run: echo done\n"
    )


def test_substitution_handles_missing_tag() -> None:
    """Regression: previously str.replace('', '# v4') would corrupt the line."""
    yaml = "        uses: actions/checkout@oldsha\n"
    replaced = REPOS.sub(
        lambda m: (
            f"{m.group('indent')}uses: {m.group('owner')}/{m.group('repo')}@NEWSHA # v4"
        ),
        yaml,
    )
    assert replaced == "        uses: actions/checkout@NEWSHA # v4\n"
