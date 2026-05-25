from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from githubkit import GitHub

if TYPE_CHECKING:
    from collections.abc import Callable

    from githubkit import TokenAuthStrategy, UnauthAuthStrategy


# NOTE: this regex consumes invalid repo names. They will be rejected by the github API
# and not a concern here.
# Anchored per-line via re.MULTILINE so we never swallow surrounding newlines.
REPOS = re.compile(
    (
        r"^(?P<indent>[^\S\n]*)uses:[^\S\n]*"
        r"(?P<owner>[a-zA-Z0-9-]{1,39})/(?P<repo>[a-zA-Z0-9_.-]{1,100})"
        r"@(?P<ref>[a-zA-Z0-9_./-]+)"
        r"(?:[^\S\n]*(?P<tag>#[^\n]*))?[^\S\n]*$"
    ),
    re.MULTILINE,
)
# ref: <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsuses>

# WARN: does not support docker
# WARN: does not support paths inside a repo

app = typer.Typer()


def gh_replace_latest_repo(
    gh: GitHub[UnauthAuthStrategy] | GitHub[TokenAuthStrategy],
) -> Callable[[re.Match[str]], str]:
    def replace_latest_repo(repo: re.Match[str]) -> str:
        owner = repo.group("owner")
        name = repo.group("repo")
        output = gh.rest.repos.list_tags(owner, name)
        latest_version = output.parsed_data[0]
        latest_name = latest_version.name
        latest_sha = latest_version.commit.sha

        if (ref := repo.group("ref")) != latest_sha:
            # TODO: don't leave side-effect in replacement code
            qualified_repo_name = f"{owner}/{name}"
            typer.echo(
                (
                    f"{typer.style('Updated', fg=typer.colors.GREEN)} "
                    f"{qualified_repo_name} {ref} -> {latest_sha} "
                    f"({typer.style(latest_name, fg=typer.colors.GREEN)})"
                ),
            )
            indent = repo.group("indent")
            return f"{indent}uses: {owner}/{name}@{latest_sha} # {latest_name}"
        return repo.group(0)

    return replace_latest_repo


@app.command()
def bump(
    gh_token: Annotated[
        str | None, typer.Option(help="The GitHub API token to use.")
    ] = None,
) -> None:
    gh = GitHub(gh_token)
    replace_latest_repo = gh_replace_latest_repo(gh)

    yaml_suffixes = {".yml", ".yaml"}
    files: list[Path] = []

    # Workflow files: .github/workflows/*.{yml,yaml}
    workflow_path = Path(".github") / "workflows"
    if workflow_path.is_dir():
        files.extend(
            f
            for f in workflow_path.iterdir()
            if f.is_file() and f.suffix in yaml_suffixes
        )

    # Composite/local action files: .github/actions/**/action.{yml,yaml}
    actions_path = Path(".github") / "actions"
    if actions_path.is_dir():
        for suffix in yaml_suffixes:
            files.extend(actions_path.rglob(f"action{suffix}"))

    if not files:
        typer.echo("No workflows detected")
        return

    # TODO: provide feedback of what was updated and if things were checked ... etc
    for file in files:
        with file.open("r+") as fp:
            f: str = fp.read()
            updated_yaml = REPOS.sub(replace_latest_repo, f)
            _ = fp.seek(0)
            _ = fp.write(updated_yaml)
            _ = fp.truncate()
        typer.echo(f"Completed {file}")


if __name__ == "__main__":
    app()
