# Prompt Examples

Five prompts that show what this skill does best. Each one exercises a different feature combination:

| # | Pattern | Features showcased | Why this prompt benefits |
|---|---|---|---|
| 1 | **c4-container** | Plan-then-emit, grounding manifest, two-layer edges | Multi-tier system with 8–12 containers + ~15 edges — classic case where LLM coord math fails |
| 2 | **pipeline (LR)** | `auto_layout=elk`, Q401 crossings, font_fit | 20+ shapes with many cross-stage edges — auto-layout pays for itself |
| 3 | **bpmn-process swimlanes** | Container-relative coords, cross-lane edges | Most common bug surface: parent="1" on edges that should be parent="<pool>" |
| 4 | **erd-crowfoot** | Table compartments, cardinality edges, grounding | Schema diagrams need typed PK/FK + correct cardinality glyphs |
| 5 | **tenant-namespace** | Deeply nested containers, font_fit, scope styling | 3-level nesting (pool → tenant → namespace) — coord math breaks fast |

Copy/paste any of these as a starting point and adapt the source citations to your real artifacts.

---

## 1. C4 Container — internal payments platform

> Build a C4 Container diagram for our Payments Platform.
>
> **Containers (use `c4-container` pattern):**
> - Web App (React) — customer-facing UI
> - Mobile App (iOS/Android) — same customer surface
> - Public API (Node.js/Express) — REST + WebSocket
> - Admin Console (Next.js) — operations UI
> - Payments Service (Java/Spring) — domain logic for charge/refund
> - Webhook Worker (Python) — async outbound to merchants
> - Postgres — orders, transactions, ledger
> - Redis — session cache + idempotency keys
>
> **External systems (greyed boxes):**
> - Stripe (card processor) — `interfaces.xlsx:row 4`
> - SendGrid (email) — `interfaces.xlsx:row 7`
> - Sumsub (KYC) — `interfaces.xlsx:row 11`
>
> **Edges to show:**
> - Customer → Web App / Mobile App (HTTPS)
> - Web/Mobile/Admin → Public API (JSON/HTTPS)
> - Public API → Postgres (SQL), Redis (RESP)
> - Public API → Payments Service (gRPC)
> - Payments Service → Stripe (HTTPS) — `cite: payments-svc/charge.go:142`
> - Payments Service → Webhook Worker (RabbitMQ)
> - Webhook Worker → merchant endpoints (HTTPS) — `cite: assumption:per-merchant URL stored in DB`
>
> Source map (use these as `cite:` values):
> - HLA doc: `HLA-v3.md:§2.1` (system boundary), `§3.2` (containers), `§4` (data stores)
> - Interface registry: `interfaces.xlsx`
>
> Output: `01_Payments_Context/A_c4-container.drawio` + matching `.plan.json`.

**Why this prompt works well**

- Names the pattern explicitly (`c4-container`)
- Every entity has a `cite` source → grounding manifest passes
- Marks one assumption (per-merchant URL) → surfaces as G502 warning for review
- ~12 containers + ~10 edges → big enough that `critic_judge_loop: auto` fires (>15 shapes including externals)
- The dashed system boundary + two-layer edge rendering will keep edges behind icons

---

## 2. LR streaming pipeline — clickstream analytics

> Build an LR data pipeline diagram for our clickstream analytics flow. Use the `pipeline` pattern.
>
> **Sources (left column):**
> - Web SDK events → Kafka topic `events.raw`
> - Mobile SDK → same Kafka topic
> - Salesforce CDC → Kafka topic `crm.changes`
> - Stripe webhooks → Kafka topic `payments.events`
>
> **Processing (middle, layered):**
> - Flink Job `enrich` — joins events with user profile (Redis lookup)
> - Flink Job `dedupe` — dedupes by event_id + 5-min window
> - Flink Job `aggregate` — 1-min rollups by segment
>
> **Sinks (right column):**
> - Snowflake (raw + enriched)
> - Looker (live dashboards, materialized views)
> - PagerDuty (anomaly alerts via `alerts.high` topic)
> - S3 archive (Parquet, partitioned by date)
> - Customer Data Platform (Segment) — reverse ETL
>
> **Edge labels:** show partitioning key + format on each edge (e.g. `events.raw / Avro / user_id`).
>
> Source: `data-platform-design.md:§5.3 streaming topology`. Mark "PagerDuty alerts" with `cite: assumption:not yet provisioned, planning stage`.
>
> This will have ~20 shapes. Let `auto_layout=auto` fire — keep ELK output. Set `font_fit=grow` since labels are long.

**Why this prompt works well**

- 4 sources × 3 jobs × 5 sinks ≈ 20+ vertices → `auto_layout=auto` fires ELK
- Many parallel edges → tests Q401 crossings; ELK orthogonal routing fixes it
- Long edge labels (`events.raw / Avro / user_id`) → benefit from font_fit
- Explicit `font_fit=grow` since ELK will enlarge cells

---

## 3. BPMN swimlanes — purchase requisition approval

> Build a BPMN process diagram for our purchase requisition approval flow. Use the `bpmn-process` pattern with 3 lanes.
>
> **Lanes (top → bottom):**
> - **Requester** — anyone in the org
> - **Manager** — direct line manager
> - **Finance** — AP team for spend >$5k
>
> **Flow:**
> 1. Requester: Start event "Need identified" → user task "Fill PR form"
> 2. Manager: user task "Review PR" → exclusive gateway "Approved?"
> 3. If No (Manager → Requester): send task "Notify rejection" → End event "Rejected"
> 4. If Yes: exclusive gateway "Spend > $5k?"
>    - If Yes (Manager → Finance): user task "Budget check" → service task "Create PO in NetSuite"
>    - If No (skip Finance): service task "Issue PO directly"
> 5. Both paths converge → Finance: service task "Process payment" → End event "PO complete"
>
> Source: `procurement-policy-v2.pdf:p.4-7` (the canonical flow). The "$5k threshold" branch from `policy:§3.1.2`.
>
> Output: `04_Procurement/A_PR_approval_bpmn.drawio`. Cross-lane edges must use `parent="<pool-id>"` per skill rules.

**Why this prompt works well**

- 3 lanes × 8 tasks/events = perfect swimlane stress test
- Cross-lane edges (Requester→Manager, Manager→Finance, Finance→Requester) are the #1 swimlane bug — explicitly calls out the `parent="<pool-id>"` rule
- Gateway branches mean diamond shapes + Yes/No labels (colored edges in style-dictionary)
- BPMN pattern auto-skips `auto_layout` (positional) so lane assignment stays semantic

---

## 4. ERD crow's-foot — multi-tenant SaaS schema

> Build an ERD with crow's-foot cardinality for the core multi-tenant SaaS schema. Use the `erd-crowfoot` pattern.
>
> **Entities (with PK underlined, FK italic):**
>
> - **Tenant** — `tenant_id` PK, name, plan, created_at — `cite: schema.sql:CREATE TABLE tenants`
> - **User** — `user_id` PK, *tenant_id* FK, email, role, last_login_at — `cite: schema.sql:CREATE TABLE users`
> - **Workspace** — `workspace_id` PK, *tenant_id* FK, name — `cite: schema.sql:CREATE TABLE workspaces`
> - **Project** — `project_id` PK, *workspace_id* FK, *owner_user_id* FK, name — `cite: schema.sql:CREATE TABLE projects`
> - **Membership** — `membership_id` PK, *workspace_id* FK, *user_id* FK, role — `cite: schema.sql:CREATE TABLE memberships`
> - **APIKey** — `api_key_id` PK, *user_id* FK, key_hash, scopes, revoked_at — `cite: schema.sql:CREATE TABLE api_keys`
>
> **Relationships (use crow's-foot edges with correct cardinality):**
> - Tenant 1..* User
> - Tenant 1..* Workspace
> - Workspace 1..* Project
> - Workspace *..* User (through Membership — show the join entity)
> - User 1..* APIKey
> - User 0..* Project (as owner)
>
> Place entities so foreign-key relationships flow left-to-right where possible. Color tenant container in `#E3F2FD` (light blue) and group all tenant-scoped entities visually inside it.

**Why this prompt works well**

- 6 entities × ~7 relationships = realistic schema
- Specific PK / FK formatting (underline / italic) tests the `fontStyle=4`/`fontStyle=2` style fragments
- Many-to-many through Membership tests crow's-foot on both ends of a single edge
- Source citations at the column level → strict grounding manifest
- Container grouping (tenant-scoped entities) tests container-relative coords

---

## 5. Multi-tenant Kafka deployment — tenant-namespace pattern

> Build a multi-tenant Kafka/Flink deployment diagram for 3 tenants on shared infrastructure. Use the `tenant-namespace` pattern.
>
> **Outer container:** Kafka Cluster "prod-us-east-1" — `cite: terraform/kafka/cluster.tf`
>
> **Three tenant containers inside:**
>
> **Tenant A — Acme Corp** (cite: `tenants.yaml:acme`)
> - Namespace `acme.events` containing topics: `orders`, `inventory`, `shipping`
> - Flink job `acme-fraud-detector`
> - Postgres sub-container with tables: `acme_orders`, `acme_audit`
>
> **Tenant B — Beta Industries** (cite: `tenants.yaml:beta`)
> - Namespace `beta.events` containing topics: `transactions`, `users`
> - Flink job `beta-recommender`
> - Postgres sub-container with tables: `beta_users`, `beta_recs`
>
> **Tenant C — Charlie & Co** (cite: `tenants.yaml:charlie`)
> - Namespace `charlie.events` containing topics: `clicks`, `sessions`, `conversions`, `cohorts`
> - Two Flink jobs: `charlie-realtime-agg`, `charlie-batch-rollup`
> - Postgres sub-container with tables: `charlie_clicks_raw`, `charlie_agg_1m`
>
> **Cross-tenant edges (dashed, with `parent="<cluster-id>"` since LCA is the cluster):**
> - Acme Flink → `acme.events.orders` (consumes)
> - Acme Flink → `acme_audit` (writes)
> - Beta Flink → all topics in its namespace
> - Charlie's realtime-agg → `clicks` and `sessions`, writes to `charlie_agg_1m`
>
> All tenant Postgres sub-containers stay color-coded distinctly. Mark "production cluster size" with `cite: assumption:3 brokers + 2 zk, sized for 50K msg/s aggregate`.

**Why this prompt works well**

- 3 levels of nesting (cluster → tenant → namespace → topics) → most demanding container-coords test in the suite
- Each tenant's edges have their LCA = the cluster → great `parent="<lca>"` test
- ~30+ shapes → `critic_judge_loop` definitely fires; `auto_layout=auto` triggers ELK
- Multiple Postgres sub-containers with distinct colors → tests scope styles + per-tenant grouping
- Long topic/table names test font_fit (would otherwise overflow narrow topic boxes)

---

## How to use these prompts in your workflow

1. Pick the example closest to your need.
2. Replace the source citations (`HLA-v3.md:§...`, `terraform/...`, etc.) with **your actual artifacts**. This is what makes the F3 grounding manifest meaningful.
3. Adjust the entity / lane counts to your real system.
4. Drop into your Claude Code or Cowork session; the skill will pick up the pattern name (`c4-container`, `pipeline`, `bpmn-process`, `erd-crowfoot`, `tenant-namespace`) and select the matching template.
5. The validator + fit-fonts will run automatically per the feature flags.

## Anti-examples (don't do this)

| Bad prompt | Why it fails |
|---|---|
| "Make a diagram of our system" | No pattern named; the skill has to guess. Won't trigger templates correctly. |
| "Architecture diagram with all the services" | No source citations → grounding manifest will G501 reject every shape. |
| "Same as the last one but with X" | Skill state isn't retained between sessions. Reference the source file or template path. |
| "Make the boxes bigger" without coord context | Better: "increase shape height from 60 to 100, container width to 1600" — specific deltas. |
| "Use cool colors" | Style-dictionary has an allowlist. Subjective requests fail W105. Better: "use the scope_green container style". |
