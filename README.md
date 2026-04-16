# Agency Ops

Runbooks and skills for managing client sites, analytics, deployments, and cross-referencing tools.

## Skills

| Skill | Description |
|---|---|
| [ga-cross-reference](skills/ga-cross-reference/SKILL.md) | Verify and fix Google Analytics measurement IDs across client sites using the GA Admin API |

## Infrastructure Notes

- **Deployment:** `~/projects/mem-deploy/bin/push` on local machine
- **Contact/Form server:** `ssh mem-contact`
- **Analytics credentials:** `mem-contact:~/analytics-dashboard/.env`
- **Asset backup:** `bk-1`
- **Primary web server:** `main-1`
