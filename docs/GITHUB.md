# Publish under Zhecen-Zhou0309

## First publication

1. Open [New repository](https://github.com/new?name=liverpool-squad-audit).
2. Select owner `Zhecen-Zhou0309` and repository name `liverpool-squad-audit`. Choose Public for a visible portfolio project or Private for private development.
3. Leave README, license and `.gitignore` initialization disabled and create an empty repository.
4. Open a terminal in the existing local project and run:

```bash
git status
git log --oneline
git remote -v
git push -u origin main
git push origin v0.1.1
```

The local origin is already configured. After a successful push, visit [the project repository](https://github.com/Zhecen-Zhou0309/liverpool-squad-audit) and inspect Commits, Tags and Actions.

Use the Git repository or history bundle to preserve commits. Uploading files through the website or extracting a normal source ZIP does not restore the existing history. Avoid reinitializing the project and collapsing it into a new initial commit.

## Restore the history bundle

Save `liverpool-squad-audit-history.bundle` locally. Adjust the example path if it is not in Downloads:

```bash
git clone -b main ~/Downloads/liverpool-squad-audit-history.bundle liverpool-squad-audit
cd liverpool-squad-audit
git remote set-url origin https://github.com/Zhecen-Zhou0309/liverpool-squad-audit.git
git push -u origin main
git push origin v0.1.1
```

A bundle preserves commits, authors, ancestry and tags. It excludes ignored raw data, which is supplied in a separate input backup. A normal source ZIP is useful for browsing code but does not preserve Git history.

## Use GitHub Desktop

Create the empty repository on the website first. Sign in to GitHub Desktop as `Zhecen-Zhou0309`, choose File → Add Local Repository, select this project, and use Push origin to upload main while preserving history. Push the release tag with the command above.

The connected GitHub app and system Git manage authentication separately. If the terminal requests authentication, use GitHub Desktop or a configured SSH key or credential manager. A GitHub account password is not Git HTTPS authentication.

## Build a useful commit history

Commit each meaningful, reviewable change: a data importer, a minute-accounting fix, an edge-case test or a documented assumption. Multiple commits on the same day retain separate records but remain dated that day. Continued development naturally builds history over time.

Commits support traceability; reproducibility also requires locked dependencies and preserved inputs.

Reference: [GitHub's local project upload guide](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
