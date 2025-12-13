import string

from hypothesis import given
from hypothesis import strategies as st

from bump_ghw import repos

USER = st.from_regex(r"^[a-zA-Z0-9-]{1,39}$", fullmatch=True).filter(
    lambda s: not s.startswith("-") and not s.endswith("-") and "--" not in s
)
REPO_NAME = st.from_regex(r"^[a-zA-Z0-9._-]{1,100}$", fullmatch=True).filter(
    lambda s: s not in (".", "..")
)

SHA = st.text("0123456789abcdefABCDEF", min_size=6, max_size=40)
REF = st.text(string.ascii_letters + string.digits + "-._/", min_size=1).filter(
    lambda s: not s.endswith(("/", "."))
    and not s.startswith(("/", "."))
    and ".." not in s
    and "//" not in s
    and "./" not in s
    and "/." not in s
)


@given(USER, REPO_NAME, SHA, REF)
def test_finding_repos(user: str, repo_name: str, sha: str, ref: str) -> None:
    fake_action = f"\t\t \t\tuses: {user}/{repo_name}@{sha} # {ref} "
    repo = list(repos.finditer(fake_action))
    assert len(repo) == 1
    repo = repo[0]

    assert repo.group("owner") == user
    assert repo.group("repo") == repo_name
    assert repo.group("version") == sha
    assert repo.group("tag") == f"# {ref} "

    assert len(repos.findall("")) == 0
