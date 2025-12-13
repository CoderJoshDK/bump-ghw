# bump-ghw

Bump your github workflow versions! An easy to use local CLI to update your github action yamls.

## Rational

We follow [best practices and only output the commit SHA](https://blog.rafaelgss.dev/why-you-should-pin-actions-by-commit-hash) for specific versions.

bump-ghw is useful for those repos that don't have systems to automatically update dependencies.
But if possible, use renovate!

## Roadmap

This CLI tool is very much a WIP. The following are things I plan to implement into this tool.

- [ ] Ability to convert tag pins into SHA pins (but not update).
- [ ] Update to but ask to increment major version
- [ ] [Support docker sources](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#example-using-a-docker-hub-action)
- [ ] [Support actions in a subdirectory](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#example-using-a-public-action-in-a-subdirectory)

### Internal TODOs

- [ ] Drop githubkit dependency (way too overkill for this tool)
- [ ] Cache responses
