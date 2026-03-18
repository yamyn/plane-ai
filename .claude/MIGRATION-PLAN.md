# Plane Migration Plan

## Goal
Simplify the project while keeping it functional. Move everything to Vercel-native stack.

---

## Phase 1: Stabilize Python on Vercel (CURRENT)
**Status:** In Progress

- [x] Fix Django settings for Vercel
- [x] Mock Celery for sync execution
- [x] Remove heavy dependencies (boto3, celery packages, faker)
- [x] Run migrations on Neon DB
- [ ] Fix remaining deployment errors
- [ ] Verify core functionality works

**Outcome:** Working baseline to migrate from

---

## Phase 2: NestJS Backend PRD
**Status:** Not Started

Create detailed PRD for NestJS API:

### 2.1 Prisma Schema
- Map all Django models (~80) to Prisma schema
- Define relations
- Plan migration strategy for existing data

### 2.2 API Specification
- Document all endpoints (~200+)
- Request/Response DTOs
- Authentication flows
- Permission system

### 2.3 Architecture
- Module structure
- Service layer design
- Guard system (permissions)
- Queue system (Bull for background jobs)

---

## Phase 3: NestJS MVP
**Status:** Not Started

Core functionality first:

### Models (Priority Order)
1. User, Profile
2. Workspace, WorkspaceMember
3. Project, ProjectMember
4. Issue, IssueComment, IssueActivity
5. Cycle, Module
6. State, Label, Priority

### Features
- [ ] Authentication (JWT + refresh tokens)
- [ ] Workspace CRUD
- [ ] Project CRUD
- [ ] Issue CRUD
- [ ] Basic permissions

### Deployment
- Vercel serverless functions
- Prisma with Neon PostgreSQL
- Upstash Redis for caching

---

## Phase 4: Full Migration
**Status:** Not Started

- [ ] Migrate all remaining endpoints
- [ ] File uploads (Vercel Blob)
- [ ] Webhooks
- [ ] Background jobs (Vercel Cron + Bull)
- [ ] Data migration script (Python → NestJS)
- [ ] API compatibility layer (if needed)

---

## Phase 5: Web Consolidation
**Status:** Not Started
**Prerequisite:** NestJS backend working

Merge all web repositories into single app:
- web (main app)
- admin
- space

Benefits:
- Single codebase
- Shared components
- Easier deployment
- Consistent UX

---

## Tech Stack (Target)

| Layer | Current | Target |
|-------|---------|--------|
| Backend | Django + DRF | NestJS + Prisma |
| Database | PostgreSQL | PostgreSQL (Neon) |
| Cache | Redis | Redis (Upstash) |
| Queue | Celery + Redis | Bull + Redis / Vercel Cron |
| Storage | S3/MinIO | Vercel Blob |
| Auth | Django + JWT | Passport.js + JWT |
| Frontend | Next.js | Next.js (consolidated) |
| Hosting | Docker/Self-hosted | Vercel |

---

## Notes

- Python feels uncomfortable for the team (not Python developers)
- Vercel is the target platform - should use Vercel-native solutions
- NestJS chosen because:
  - TypeScript (team's strength)
  - Similar architecture to Django (modules, services, guards)
  - First-class Vercel support
  - Prisma is modern and developer-friendly

---

*Created: March 2024*
*Last Updated: March 2024*
