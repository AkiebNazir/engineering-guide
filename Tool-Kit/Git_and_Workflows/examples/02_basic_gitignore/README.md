# Basic Gitignore
**Goal:** Understand how to use `.gitignore` to prevent sensitive files and build artifacts from being tracked by Git.
**Key Concepts:** [The purpose of the .gitignore file](../../Git_and_Workflows.md#6-what-is-the-purpose-of-the-gitignore-file)
**Prerequisites:** Git installed
**Step-by-Step Execution:**
1. Navigate to this directory.
2. View the contents of the `.gitignore` file: `cat .gitignore`
3. Try creating a secret file: `echo "SECRET_KEY=123" > .env`
4. Run `git status`
   - *Expected output:* Git will ignore the `.env` file, keeping your working directory clean.
**Try it yourself:** Create a `node_modules` directory with some files in it and check `git status`. Observe that it is ignored.
**Teardown:** Run `rm -rf .env node_modules`
