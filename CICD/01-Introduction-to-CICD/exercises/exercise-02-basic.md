# Exercise 02: Map the CI/CD Terminology 🟢

## 🎯 Objective

Solidify your understanding of CI/CD terminology by matching definitions and creating your own glossary.

## 📋 Prerequisites
- Completed reading Chapter 01 theory

## 📝 Instructions

### Part A: Match the Terms

Match each term on the left with its correct definition on the right:

| # | Term | | Definition |
|---|------|--|-----------|
| 1 | Pipeline | | A) A machine that executes pipeline jobs |
| 2 | Artifact | | B) Reverting to a previous working version |
| 3 | Runner | | C) A snapshot of changes saved to version control |
| 4 | Commit | | D) A series of automated steps from commit to deploy |
| 5 | Rollback | | E) The output of a build process (JAR, Docker image) |
| 6 | Trigger | | F) A logical grouping of jobs in a pipeline |
| 7 | Stage | | G) An event that starts a pipeline |
| 8 | Environment | | H) A target where software runs (dev, staging, prod) |

### Part B: Fill in the Blanks

Complete these sentences:

1. __________ means integrating code changes from multiple developers multiple times per day.
2. Continuous __________ requires manual approval before deploying to production.
3. Continuous __________ automatically deploys every passing change to production.
4. A __________ loop provides rapid results back to developers.
5. __________ is the culture that unifies Dev and Ops teams.

### Part C: Create Your Own Analogy

Write a real-world analogy (like the Pizza analogy from the chapter) that explains CI/CD using one of these themes:
- A car factory assembly line
- A newspaper printing press
- A restaurant kitchen
- Your own creative idea!

Write at least 5 sentences explaining how each step maps to CI/CD concepts.

## ✅ Expected Output / Solution

### Part A Answers:
1-D, 2-E, 3-A, 4-C, 5-B, 6-G, 7-F, 8-H

### Part B Answers:
1. **Continuous Integration**
2. **Delivery**
3. **Deployment**
4. **Feedback**
5. **DevOps**

### Part C Example:
> **The Car Factory Analogy:**
> CI/CD is like a modern car factory assembly line. Each worker (developer) adds a small part (code change) to the car on the conveyor belt (pipeline). After each part is added, a quality inspector (automated tests) checks that everything is still working. If a part doesn't fit (test fails), the line stops immediately and the issue is fixed. The car moves through stations (stages): frame assembly (build), electrical check (unit tests), paint job (packaging), and final inspection (integration tests). Once the car passes all inspections, it rolls off the line ready for the customer (production deployment).

## 🧠 Key Takeaway

Knowing the vocabulary is essential. When you hear "the pipeline is broken" or "deploy the artifact to staging," you'll know exactly what's being discussed.
