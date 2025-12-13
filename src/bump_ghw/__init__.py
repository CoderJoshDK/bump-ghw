from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from githubkit import GitHub

if TYPE_CHECKING:
    from collections.abc import Callable

    from githubkit import TokenAuthStrategy, UnauthAuthStrategy

app = typer.Typer()

# NOTE: this regex consumes invalid repo names. They will be rejected by the github API
# and not a concern here
repos = re.compile(
    r"(\s*uses:\s*)(?P<owner>[a-zA-Z0-9-]{1,39})\/(?P<repo>[a-zA-Z0-9_.-]{1,100})@(?P<version>\w*)\s*(?P<tag>#?\s*.*)"
)
# ref: <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsuses>

# WARN: does not support docker
# WARN: does not support paths inside a repo
# WARN


def gh_replace_latest_repo(
    gh: GitHub[UnauthAuthStrategy] | GitHub[TokenAuthStrategy],
) -> Callable[[re.Match[str]], str]:
    def replace_latest_repo(repo: re.Match[str]) -> str:
        output = gh.rest.repos.list_tags(repo.group("owner"), repo.group("repo"))
        latest_version = output.parsed_data[0]
        latest_name = latest_version.name
        latest_sha = latest_version.commit.sha

        if (version := repo.group("version")) != latest_sha:
            return (
                repo.group(0)
                .replace(version, latest_sha)
                .replace(repo.group("tag"), f"# {latest_name}")
            )
        return repo.group(0)

    return replace_latest_repo


@app.command()
def bump(
    gh_token: Annotated[
        str | None, typer.Option(help="The GitHub API token to use.")
    ] = None,
) -> None:
    gh = GitHub(gh_token)

    if (workflow_path := Path(".github") / Path("workflows")) and workflow_path.is_dir():
        for file in workflow_path.iterdir():
            with file.open("r+") as fp:
                f: str = fp.read()
                replace_latest_repo = gh_replace_latest_repo(gh)
                updated_yaml = repos.sub(replace_latest_repo, f)
                _ = fp.seek(0)
                _ = fp.write(updated_yaml)

    else:
        ...
        # No files


if __name__ == "__main__":
    app()
