# Alex - AI in Production Course Project Guide (Google Cloud)

## Project Overview

**Alex** (Agentic Learning Equities eXplainer) is a multi-agent enterprise-grade SaaS financial planning platform. This is the capstone project for Weeks 3 and 4 of the "AI in Production" course taught by Ed Donner on Udemy that deploys Agent solutions to production.

The user is a student on the course. You are working with the user to help them build Alex successfully. The user is working in Cursor (the VS Code fork), and they might be on a Windows PC, a Mac (intel or Apple silicon) or a Linux machine. All python code is run with uv and there are uv projects in every directory that needs it. The student is familiar with Google Cloud managed services (Cloud Run, Cloud Storage, IAM) and has been introduced to Terraform, uv, NextJS and docker. They should set budget alerts and regularly check billing in the Google Cloud console.

The student uses a Google Cloud project with appropriate IAM roles (service accounts with least-privilege roles per component—see **Reference project: InfraGuard AI** below). Local dev often uses `gcloud auth application-default login`; **Cloud Run, CI, and Docker** typically use a **service account JSON key** (`GOOGLE_APPLICATION_CREDENTIALS`) or Workload Identity—same pattern as `infraguad_ai`. Compute stays **fully managed** (Cloud Run, Cloud Functions, managed databases)—no pet VMs for the Alex app surface.

### Platform choice: Cloud Run first

**Prefer [Cloud Run](https://cloud.google.com/run)** for HTTP services and containerized workloads: no servers to patch, scale-to-zero, pay per use, and one Dockerfile deploys consistently. Use **Cloud Functions** for small, event-driven handlers if the guides split responsibilities that way. Avoid Compute Engine **unless** a guide explicitly needs it—this track optimizes for **easy operations**, not VM babysitting.

### What Students Will Build

Students will deploy a complete production AI system featuring:
- **Multi-agent collaboration**: 5 specialized AI agents working together via orchestration
- **Serverless / managed architecture**: Cloud Run (and/or Cloud Functions), Cloud SQL (PostgreSQL), Pub/Sub, API Gateway or Cloud Load Balancing in front of services
- **Cost-optimized vector storage**: Cloud Storage–backed or managed vector options (see guides—not self-hosted OpenSearch clusters)
- **Real-time financial analysis**: Portfolio management, retirement projections, market research
- **Production-grade practices**: Observability, guardrails, security, monitoring
- **Full-stack application**: NextJS React frontend with Clerk authentication

### Learning Objectives

By completing this project, students will:
1. Deploy and manage production AI infrastructure on **Google Cloud**
2. Implement multi-agent systems using the OpenAI Agents SDK
3. Integrate **Vertex AI** (or compatible models via LiteLLM) for LLM capabilities
4. Build cost-effective embeddings and vector search (Vertex AI / pipelines per guide)
5. Create orchestration with **Pub/Sub** and **Cloud Run** (or Cloud Functions)
6. Deploy a complete full-stack SaaS application
7. Implement enterprise features: monitoring, observability, guardrails, security

### Commercial Product

Alex is a SaaS product that provides insights on users' equity portfolios through reports and charts. Alex is integrated with Clerk for user management and the database architecture keeps user data separate.

### Terraform + full app setup

This deployment aims for a **complete application on Google Cloud** with **Terraform for fast, repeatable provisioning** (independent modules under `terraform/*`, Google provider). Use `terraform.tfvars` per module with `project_id` and `region` aligned everywhere.

### Reference project: InfraGuard AI (`infraguad_ai`)

The sibling repo **`C:\Users\adebo\PROJECTS\infraguad_ai`** is the working reference for **Vertex AI**, **service accounts**, and **Terraform conventions** on this machine. Use it when wiring Alex—even though InfraGuard’s sample Terraform uses **Compute Engine + Artifact Registry** for their stack, while Alex standardizes on **Cloud Run** and managed services **without self-managed VMs**.

From InfraGuard, reuse these patterns for Alex:

| Topic | Pattern (see `infraguad_ai` README, `CONTEXT.md`, `terraform/`) |
|--------|-------------------------------------------------------------------|
| **Auth** | `GOOGLE_APPLICATION_CREDENTIALS` → path to a **service account JSON key**; `GCP_PROJECT_ID`, `GCP_REGION` (e.g. `us-central1`). ADC via `gcloud auth application-default login` is fine for dev; **containers and CI** typically use the JSON key or Workload Identity—not username/password. |
| **IAM** | Dedicated service account(s): at minimum roles such as **Vertex AI User** for inference; add **Artifact Registry** writer (push images), **Cloud Run Admin** / **Developer**, **Cloud SQL Client**, **Secret Manager Secret Accessor**, etc., as Terraform adds services—least privilege per deployable. |
| **APIs** | Enable required APIs on the GCP project (**Vertex AI API**, and if using Gemini via GenAI / agent flows, whatever **Agent Platform** or related APIs your SDK expects). InfraGuard’s `CONTEXT.md` warns that missing APIs can produce **404** responses that look like generic routing failures—check Console → APIs & Services first. |
| **Local Docker** | Mount a **single JSON key file** (e.g. repo `secrets/gcp-key.json` gitignored → `/run/secrets/gcp-key.json`). If the mount path is accidentally a **directory**, ADC fails in non-obvious ways. |
| **Terraform provider** | `hashicorp/google`, `~> 5.x`; `provider "google" { project = var.project_id region = var.region }` style variables (`variables.tf`, `terraform.tfvars.example`). |
| **Images** | **Artifact Registry** Docker repo (`{region}-docker.pkg.dev/${project_id}/${repo}`), then deploy those images to **Cloud Run** for Alex services. |

When the course guides conflict with InfraGuard’s layout (e.g. guides mention Lambda), implement the **GCP analogue** above and keep env/IAM consistent with `infraguad_ai` unless you deliberately isolate a second GCP project.

**Bootstrap Terraform for GCP**: `terraform/gcp/` (APIs, Artifact Registry, Cloud Storage bucket, Pub/Sub topics, Cloud SQL PostgreSQL + Secret Manager `DATABASE_URL`). Copy `terraform.tfvars.example` → `terraform.tfvars`, then `terraform init` / `apply`. Pair with **`.env.gcp.example`** → `.env` for app env vars (`VERTEX_MODEL_ID`, `DATABASE_URL`, `PLANNER_USE_HTTP_AGENTS`, Cloud Run URLs).

---

## Directory Structure

Guide filenames may still use historical labels (`2_sagemaker`, etc.); treat them as **logical steps**—implementation on GCP uses Vertex AI, Cloud Run, and Cloud Storage as specified in each guide.

```
alex/
├── guides/              # Step-by-step deployment guides (START HERE)
│   ├── 1_permissions.md
│   ├── 2_sagemaker.md   # → Vertex AI / embeddings (GCP analogue)
│   ├── 3_ingest.md
│   ├── 4_researcher.md
│   ├── 5_database.md
│   ├── 6_agents.md
│   ├── 7_frontend.md
│   ├── 8_enterprise.md
│   ├── architecture.md
│   └── agent_architecture.md
│
├── backend/             # Agent code and deployable services
│   ├── planner/         # Orchestrator agent
│   ├── tagger/          # Instrument classification agent
│   ├── reporter/        # Portfolio analysis agent
│   ├── charter/         # Visualization agent
│   ├── retirement/      # Retirement projection agent
│   ├── researcher/      # Market research service (typically Cloud Run)
│   ├── ingest/          # Document ingestion (Cloud Run or Cloud Functions)
│   ├── database/        # Shared database library
│   └── api/             # FastAPI backend for frontend
│
├── frontend/            # NextJS React application
│   ├── pages/
│   ├── components/
│   └── lib/
│
├── terraform/           # Infrastructure as Code (IMPORTANT: Independent directories)
│   ├── gcp/             # GCP bootstrap (Cloud SQL, GCS, Pub/Sub, Artifact Registry, APIs)
│   ├── 2_sagemaker/     # Historical AWS / swap for Vertex in GCP track
│   ├── 3_ingestion/     # Cloud Storage + ingest service
│   ├── 4_researcher/    # Cloud Run (researcher)
│   ├── 5_database/      # Cloud SQL for PostgreSQL (managed)
│   ├── 6_agents/        # Cloud Run services / Cloud Functions for agents
│   ├── 7_frontend/      # Cloud Storage + Cloud CDN, API in front
│   └── 8_enterprise/    # Cloud Monitoring, logging, alerts
│
└── scripts/             # Deployment and local development scripts
    ├── deploy.py        # Frontend deployment
    ├── run_local.py     # Local development
    └── destroy.py       # Cleanup script
```

---

## Course Structure: The 8 Guides

**IMPORTANT:** before working with the student, you MUST read all guides in the guides folder, in the correct order (1-8), to fully understand the project. Where a guide still mentions AWS by name, interpret it through the **GCP mapping** below.

### AWS → Google Cloud (quick mapping)

| Concept (AWS) | Google Cloud analogue |
|----------------|-------------------------|
| IAM users / roles | IAM principals, service accounts, predefined/custom roles |
| Lambda | Cloud Functions and/or **Cloud Run** (prefer Run for containers) |
| App Runner | **Cloud Run** |
| Aurora Serverless / RDS | **Cloud SQL** (PostgreSQL), private IP or Cloud SQL connector |
| S3 | **Cloud Storage** buckets |
| SQS | **Pub/Sub** topics and subscriptions |
| API Gateway | **API Gateway**, or HTTPS Load Balancer + Cloud Run |
| SageMaker | **Vertex AI** (endpoints, predictions, embeddings) |
| Bedrock | **Vertex AI** (Gemini and other models) via LiteLLM or native SDKs |
| CloudFront | **Cloud CDN** (often fronting Cloud Storage or Load Balancer) |
| CloudWatch | **Cloud Logging** + **Cloud Monitoring** |
| Secrets Manager | **Secret Manager** |
| EventBridge | **Cloud Scheduler** + Pub/Sub |

### Week 3: Research Infrastructure

**Day 3 - Foundations**
- **Guide 1: GCP Permissions** (`1_permissions.md`)
  - Set up IAM for the Alex project
  - Service accounts and least-privilege roles
  - `gcloud` CLI and application-default credentials

- **Guide 2: Embeddings / Vertex AI** (`2_sagemaker.md`)
  - Deploy a managed embedding endpoint (Vertex AI or HTTP service on Cloud Run)
  - Test embedding generation
  - Understand scale-to-zero vs always-on tradeoffs

**Day 4 - Vector Storage**
- **Guide 3: Ingestion Pipeline** (`3_ingest.md`)
  - Cloud Storage for documents and indexes (per guide)
  - Ingestion as Cloud Run or Cloud Functions
  - Secure HTTP API (API key or IAM)
  - Test document storage and search

**Day 5 - Research Agent**
- **Guide 4: Researcher Agent** (`4_researcher.md`)
  - Deploy autonomous research agent on **Cloud Run**
  - Use Vertex AI (Gemini or assigned model) for LLM calls
  - Integrate Playwright MCP server for web browsing where applicable
  - Cloud Scheduler (optional)
  - **IMPORTANT**: Keep region and model in config (`backend/researcher/server.py` or env)—no hardcoded secrets

### Week 4: Portfolio Management Platform

**Day 1 - Database**
- **Guide 5: Database & Infrastructure** (`5_database.md`)
  - **Cloud SQL** for PostgreSQL (managed instance—no EC2 DB VMs)
  - Connect via Cloud SQL connector / private IP as the guide specifies
  - Create database schema, load seed data (22 ETFs)
  - Shared database library

**Day 2 - Agent Orchestra**
- **Guide 6: AI Agent Orchestra** (`6_agents.md`)
  - Deploy agents as **Cloud Run services** (or Cloud Functions for thin handlers)
  - **Pub/Sub** for orchestration
  - Configure agent collaboration patterns
  - Test local and remote execution

**Day 3 - Frontend**
- **Guide 7: Frontend & API** (`7_frontend.md`)
  - Clerk authentication
  - NextJS static assets on Cloud Storage + Cloud CDN
  - FastAPI on Cloud Run (or Cloud Functions for API—guide-dependent)
  - Test portfolio management and AI analysis

**Day 4 - Enterprise Features**
- **Guide 8: Enterprise Grade** (`8_enterprise.md`)
  - Autoscaling and concurrency (Cloud Run settings)
  - Security (Cloud Armor, VPC-SC, IAM—per guide)
  - Dashboards and alerts in Cloud Monitoring
  - Guardrails, validation, LangFuse or equivalent observability

For context, students may have prior exposure to deploying containers and using Clerk with NextJS (Pages Router).

---

## IMPORTANT: Working with students - approach

Students might be on Windows PC, Mac (Intel or Apple Silicon) or Linux. Always use uv for ALL python code; there are uv projects in every directory. It is not a problem to have a uv project in a subdirectory of another uv project, although uv may show a warning.

Always do `uv add package` and `uv run module.py`, but NEVER `pip install xxx` and NEVER `python -c "code"` or `python -m module.py` or `python script.py`.
It is VERY IMPORTANT that you do not use the python command outside a uv project.
Try to lean away from shell scripts or Powershell scripts as they are platform dependent. Heavily favor writing python scripts (via uv) and managing files in the Cursor File Explorer, as this will be clear for all students.

## Working with Students: Core Principles

### Before starting, always read all the guides in the guides folder for the full background

### 1. **Always Establish Context First**

When a student asks for help:
1. **Ask which guide/day they're on** - This is critical for understanding what infrastructure they have deployed
2. **Ask what they're trying to accomplish** - Understand the goal before diving into code
3. **Ask what error or behavior they're seeing** - Get the actual error message, not their interpretation

### 2. **Diagnose Before Fixing** ⚠️ MOST IMPORTANT

**DO NOT jump to conclusions and write lots of code before the problem is truly understood.**

Common mistakes to avoid:
- Writing defensive code with `isinstance()` checks before understanding the root cause
- Adding try/except blocks that hide the real error
- Creating workarounds that mask the actual problem
- Making multiple changes at once (makes debugging impossible)

**Instead, follow this process:**
1. **Reproduce the issue** - Ask for exact error messages, logs, commands
2. **Identify root cause** - Use Cloud Logging, Google Cloud Console, error traces
3. **Verify understanding** - Explain what you think is happening and confirm with student
4. **Propose minimal fix** - Change one thing at a time
5. **Test and verify** - Confirm the fix works before moving on

### 3. **Common Root Causes (Check These First)**

Before writing any code, check these common issues:

**Docker Desktop Not Running** (common when building container images for Cloud Run)
- Packaging or `docker build` fails
- **Always ask**: "Is Docker Desktop running?"
- **Check**: `docker ps` succeeds

**GCP IAM / permissions**
- Missing roles on the service account (Vertex AI User, Cloud Run Admin, Cloud SQL Client, etc.—exact set per guide)
- APIs not enabled on the project (Vertex AI API, Cloud Run API, Pub/Sub API, …)

**Terraform Variables Not Set**
- Each terraform directory needs its `terraform.tfvars` (or equivalent) configured
- Missing variables cause cryptic errors
- **Check**: Does `terraform.tfvars` exist? Is `project_id` / region correct?

**Region mismatches**
- Vertex AI models and Cloud Run regions must be consistent where services call each other
- **Check**: Same region in `.env`, terraform, and Cloud Run service settings

**Model / quota issues**
- Vertex AI may require enabling APIs and sufficient quota
- **Check**: Cloud Console → APIs & Services, and Vertex AI model availability in region

### 4. **Model strategy (Vertex AI / LiteLLM)**

Use the **course-assigned model** (often Gemini via Vertex AI). Configure through environment variables and LiteLLM or the Vertex SDK as the codebase expects—avoid hardcoding regions or model IDs.

If the repo still shows Bedrock examples, translate to Vertex: LiteLLM supports `vertex_ai/` model strings; set `VERTEXAI_PROJECT`, `VERTEXAI_LOCATION`, and credentials per [LiteLLM Vertex docs](https://docs.litellm.ai/docs/providers/vertex).

### 5. **Testing Approach**

Each agent directory may have:
- `test_simple.py` - Local testing with mocks
- `test_full.py` - Deployment testing (actual Cloud Run / HTTP calls)

Students should:
1. Test locally first with `test_simple.py`
2. Deploy with terraform / `gcloud` / CI as the guide says
3. Test deployment with `test_full.py`

### 6. **Help Students Help Themselves**

Encourage students to:
- Read error messages carefully (Cloud Logging > Error Reporting)
- Verify resources in Google Cloud Console
- Use `terraform output` for URIs and connection strings
- Test incrementally
- Shut down or scale down costly resources when not in use (Cloud SQL, always-on Run min instances)

---

## Terraform Strategy

### Independent Directory Architecture

Each terraform subdirectory is **independent** with:
- Its own local state file (`terraform.tfstate`) unless you adopt remote state later
- Its own variable files
- No hard dependencies between directories (same educational pattern as before)

### Critical Requirements

**⚠️ Students MUST configure variables (e.g. `terraform.tfvars`) before `terraform apply`**

If variables are missing:
- Defaults may point at the wrong project or region
- APIs may not be enabled; applies fail with permission or API errors

### Terraform provider note

Use the **Google** provider (`google` / `google-beta`) for GCP resources—do not mix in AWS resources unless intentionally hybrid.

## Agent strategy - background on OpenAI Agents SDK

Each Agent subdirectory has a common structure with idiomatic patterns.

1. Entrypoint for the deployed service (historically `lambda_handler.py`—on GCP this may be FastAPI/Cloud Run `main` or a function entry)
2. `agent.py` for the Agent creation and code
3. `templates.py` for prompts

Alex uses OpenAI Agents SDK. The correct package name is `openai-agents` not `agents`: `uv add openai-agents`, then `from agents import Agent, Runner, trace`.

With LiteLLM on Vertex AI, model setup typically follows:

`model = LitellmModel(model="vertex_ai/<model_id>")`

(Structured outputs vs tools: same constraint as in the original course—one mode per agent if LiteLLM + provider limits apply.)

Example pattern (conceptually unchanged from AWS Bedrock version):

```python
    model, tools, task = create_agent(job_id, portfolio_data, user_preferences, db)

    with trace("Retirement Agent"):
        agent = Agent(
            name="Retirement Specialist",
            instructions=RETIREMENT_INSTRUCTIONS,
            model=model,
            tools=tools
        )

        result = await Runner.run(
            agent,
            input=task,
            max_turns=20,
        )

        response = result.final_output
```

Context for tools:

```python
with trace("Reporter Agent"):
        agent = Agent[ReporterContext](
            name="Report Writer", instructions=REPORTER_INSTRUCTIONS, model=model, tools=tools
        )

        result = await Runner.run(
            agent,
            input=task,
            context=context,
            max_turns=10,
        )

        response = result.final_output
```

Set **Vertex / LiteLLM** environment variables per project docs (e.g. `GOOGLE_APPLICATION_CREDENTIALS` or ADC, `VERTEXAI_PROJECT`, `VERTEXAI_LOCATION`)—not `AWS_REGION_NAME`.

---

## Common Issues and Troubleshooting

Most issues are **permissions, APIs, regions, or secrets**. Align `.env`, terraform, and Cloud Run service configuration.

### Issue 1: Docker / image build fails

**Symptoms**: `docker build` or packaging scripts fail

**Diagnosis**: Docker not running; wrong platform for Cloud Run (`linux/amd64` is typical).

**Solution**: Start Docker; use Cloud Run–compatible base images and platforms per guide.

### Issue 2: Vertex AI / model errors

**Symptoms**: 403, quota, or "model not found"

**Diagnosis**: API disabled, wrong region, billing, or IAM.

**Solution**: Enable Vertex AI API; assign Vertex AI User where needed; confirm model availability in region.

### Issue 3: Terraform apply fails

**Symptoms**: Resource creation errors, wrong project

**Root Cause**: Missing `terraform.tfvars`, wrong `project_id`, APIs not enabled

**Solution**: Fill variables; run `gcloud services enable ...` as prerequisites list; verify project in `gcloud config get-value project`

### Issue 4: Cloud Run service errors

**Symptoms**: 500s, timeouts, import errors

**Diagnosis**: Cloud Logging for the revision; missing env vars; Secret Manager binding; VPC connector for Cloud SQL

**Solution**: Fix Dockerfile and env; use Cloud SQL Auth Proxy / connector pattern from guide

### Issue 5: Cloud SQL connection fails

**Symptoms**: Connection refused, auth errors

**Diagnosis**: Instance not ready; wrong connection name; service account lacks **Cloud SQL Client**

**Solution**: Wait for instance; use connection string format `project:region:instance`; verify IAM and networking (private IP / connector)

---

## Technical Architecture Quick Reference

### Core Services by Guide (GCP)

**Guides 1-2**: Foundations  
- IAM, APIs, Vertex AI for embeddings

**Guide 3**: Vector storage  
- Cloud Storage; ingestion on Cloud Run or Cloud Functions

**Guide 4**: Research agent  
- **Cloud Run** (researcher); Artifact Registry for images

**Guide 5**: Database  
- **Cloud SQL** PostgreSQL; Secret Manager for passwords

**Guide 6**: Agent orchestra  
- Cloud Run (and/or Cloud Functions); **Pub/Sub** orchestration

**Guide 7**: Frontend  
- Cloud Storage + Cloud CDN; API on Cloud Run; Clerk

**Guide 8**: Enterprise  
- Cloud Monitoring, alerting, security products per guide

### Agent Collaboration Pattern

```
User Request → Pub/Sub → Planner (Orchestrator on Cloud Run)
                            ├─→ Tagger (if needed)
                            ├─→ Reporter ──┐
                            ├─→ Charter ───┼─→ Results → Database
                            └─→ Retirement ┘
```

### Cost Management

- Pause or delete Cloud SQL when not needed (largest recurring cost)
- Cloud Run scale-to-zero where possible; avoid unnecessary min instances
- Use `terraform destroy` per directory when tearing down labs
- Monitor in **Billing** → Reports and budgets

### Cleanup Process

```bash
# Destroy in reverse order (optional, but cleaner)
cd terraform/8_enterprise && terraform destroy
cd terraform/7_frontend && terraform destroy
cd terraform/6_agents && terraform destroy
cd terraform/5_database && terraform destroy   # Often largest savings
cd terraform/4_researcher && terraform destroy
cd terraform/3_ingestion && terraform destroy
cd terraform/2_sagemaker && terraform destroy
```

---

## Key Files Students Modify

### Configuration Files
- `.env` - Root environment variables
- `frontend/.env.local` - Frontend Clerk configuration
- `terraform/*/terraform.tfvars` - Each terraform directory (copy from `.example` if present)

### Code Students May Need to Update
- `backend/researcher/server.py` - Region and model via environment variables
- Agent templates in `backend/*/templates.py`
- Frontend pages for UI changes

---

## Getting Help

### For Students

1. **Follow the guide** for the GCP steps and troubleshooting
2. **Use Cloud Logging** and Error Reporting for server-side errors
3. **Verify** APIs enabled, IAM roles, and region consistency
4. **Contact the instructor** (Udemy / email as in course materials)

When asking for help, include: guide number, exact error text, command you ran, relevant log excerpts, what you tried.

### For Claude Code (AI Assistant)

0. **Prepare** - Read guides; apply GCP mapping where text still says AWS
1. **Establish context** - Guide, goal, what is deployed
2. **Get error details** - Logs, traces, config
3. **Diagnose first**
4. **Minimal fixes**
5. **Verify** with the student

**Remember**: Students are learning. Explain root cause, not only the fix.

---

### Course Context
- Instructor: Ed Donner
- Platform: Udemy
- Course: AI in Production
- Project: "Alex" - Capstone for Weeks 3-4 (this document: **Google Cloud** variant)

---

*This guide helps AI assistants support students on the Alex project. GCP / Cloud Run variant. Last updated: April 2026*
