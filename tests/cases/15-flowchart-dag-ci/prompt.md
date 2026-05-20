# Flowchart DAG – CI/CD Pipeline

Create a flowchart for a CI/CD deployment pipeline using directed acyclic graph layout. Include decision diamonds for quality gates and failure paths that loop back to earlier stages.

## Shapes

1. **Start** (terminal/rounded) – Pipeline trigger
2. **Git Push** (process) – Developer pushes code to repository
3. **Lint Check** (process) – Run ESLint, Prettier, and static analysis
4. **Lint Pass?** (decision) – Did linting pass without errors?
5. **Unit Tests** (process) – Run unit test suite with Jest
6. **Integration Tests** (process) – Run integration tests against test DB
7. **Tests Pass?** (decision) – Did all tests pass?
8. **Build Docker Image** (process) – Build container image with Dockerfile
9. **Push to Registry** (process) – Push image to container registry (ECR)
10. **Deploy to Staging** (process) – Deploy to staging environment via Helm
11. **Smoke Tests** (process) – Run smoke tests against staging
12. **Smoke Pass?** (decision) – Did smoke tests pass?
13. **Deploy to Production** (process) – Blue-green deploy to production
14. **Health Check** (process) – Verify production health endpoints
15. **Notify Team** (process) – Send Slack notification with results
16. **End** (terminal/rounded) – Pipeline complete

## Edges (Flow)

1. Start → Git Push
2. Git Push → Lint Check
3. Lint Check → Lint Pass?
4. Lint Pass? → Unit Tests [label: "Yes"]
5. Lint Pass? → Notify Team [label: "No"]
6. Unit Tests → Integration Tests
7. Integration Tests → Tests Pass?
8. Tests Pass? → Build Docker Image [label: "Yes"]
9. Tests Pass? → Notify Team [label: "No"]
10. Build Docker Image → Push to Registry
11. Push to Registry → Deploy to Staging
12. Deploy to Staging → Smoke Tests
13. Smoke Tests → Smoke Pass?
14. Smoke Pass? → Deploy to Production [label: "Yes"]
15. Smoke Pass? → Notify Team [label: "No"]
16. Deploy to Production → Health Check
17. Health Check → Notify Team
18. Notify Team → End

Use a top-to-bottom flow with decision diamonds branching left/right for Yes/No paths. Color-code: green for success paths, red for failure paths.
