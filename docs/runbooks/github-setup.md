# Publish to GitHub

## One-time setup

```powershell
gh auth login
```

Choose: GitHub.com → HTTPS → Login with browser.

## Create public repository and push

From the repository root:

```powershell
gh repo create ParsLex --public --source=. --remote=origin --push --description "Enterprise Domain-Adaptive Legal AI Platform"
```

If the repo name is taken, use a unique name:

```powershell
gh repo create parslex-legal-ai --public --source=. --remote=origin --push
```

## Push tags

```powershell
git push origin --tags
```
