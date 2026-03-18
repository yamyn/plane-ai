# Vercel Migration - TODO List

This document tracks features that are disabled or limited in the Vercel serverless deployment.

## Bundle Size Optimization

Vercel Lambda has a ~250MB limit. The following packages were removed to reduce bundle size:

### Removed Packages

| Package | Size | Reason | Impact |
|---------|------|--------|--------|
| `celery` | ~30MB | No persistent workers in serverless | Background tasks run synchronously |
| `django-celery-beat` | ~5MB | Depends on Celery | Scheduled jobs disabled |
| `django-celery-results` | ~5MB | Depends on Celery | Task results not persisted |
| `django-storages` | ~5MB | Using Vercel Blob instead | - |
| `boto3` | ~80MB | S3 not needed with Vercel Blob | - |
| `faker` | ~15MB | Dev/test dependency | Tests won't run |

---

## Disabled Features

### 1. Background Tasks (Celery)

**Status:** Mocked - runs synchronously
**File:** `plane/utils/celery_sync.py`
**Settings:** `CELERY_TASK_ALWAYS_EAGER = True` in `plane/settings/vercel.py`

All `.delay()` calls now execute synchronously. This means:
- Request may be slower (task runs in same request)
- Long-running tasks may timeout (Vercel has 10s limit on Hobby, 60s on Pro)
- Task failures will be logged but won't crash the request

**Affected Tasks:**
- `issue_activity.delay()` - Issue activity tracking
- `webhook_activity.delay()` - Webhook delivery
- `model_activity.delay()` - Model change tracking
- `recent_visited_task.delay()` - Recent visits tracking
- `track_event.delay()` - Analytics events
- `project_invitations.delay()` - Email notifications
- `workspace_seed.delay()` - Workspace initialization
- All email tasks (magic link, password reset, invitations)

**Future Solution:**
- [ ] Use Vercel Cron Jobs for scheduled cleanup tasks
- [ ] Use QStash or Inngest for async background jobs
- [ ] Consider Upstash Workflow for complex task chains

### 2. Scheduled Jobs (Celery Beat)

**Status:** Disabled
**Impact:** The following scheduled jobs will NOT run:

| Job | Schedule | Purpose |
|-----|----------|---------|
| `stack_email_notification` | Every 5 min | Batch email notifications |
| `instance_traces` | Every 6 hours | Instance telemetry |
| `hard_delete` | Daily 00:00 UTC | Permanent deletion of soft-deleted items |
| `archive_and_close_old_issues` | Daily 01:00 UTC | Auto-archive issues |
| `delete_old_s3_link` | Daily 01:30 UTC | Cleanup expired export links |
| `delete_unuploaded_file_asset` | Daily 02:00 UTC | Cleanup orphaned files |
| `delete_api_logs` | Daily 02:30 UTC | Cleanup old API logs |
| `delete_email_notification_logs` | Daily 02:45 UTC | Cleanup notification logs |
| `delete_page_versions` | Daily 03:00 UTC | Cleanup old page versions |
| `delete_issue_description_versions` | Daily 03:15 UTC | Cleanup old issue versions |
| `delete_webhook_logs` | Daily 03:30 UTC | Cleanup webhook logs |

**Future Solution:**
- [ ] Create Vercel Cron Jobs (`vercel.json` crons)
- [ ] Create HTTP endpoints for each cleanup task
- [ ] Set up cron schedule in Vercel dashboard

### 3. File Storage (S3/MinIO)

**Status:** Replaced with Vercel Blob
**File:** `plane/utils/storage/vercel_blob.py`
**Settings:** `STORAGES` in `plane/settings/vercel.py`

**What works:**
- File uploads via Vercel Blob API
- Presigned URLs for downloads

**What doesn't work:**
- S3-specific features (ACLs, bucket policies)
- Direct S3 SDK operations

### 4. MongoDB Logging

**Status:** Disabled
**Impact:** API request logging to MongoDB disabled

**Future Solution:**
- [ ] Use Vercel's built-in logging
- [ ] Or integrate with external logging service (Axiom, Logtail)

### 5. WebSocket / Live Server

**Status:** Not available on Vercel
**Impact:** Real-time collaboration features won't work

**Future Solution:**
- [ ] Use Vercel's Edge Functions with WebSocket (limited)
- [ ] Or use external service (Pusher, Ably, Liveblocks)
- [ ] Or deploy Live server separately on Railway/Render

### 6. Long-running Operations

**Status:** Limited by Vercel timeout (10s Hobby / 60s Pro)
**Impact:**
- Large file uploads may timeout
- Bulk operations may fail
- Large exports may timeout

**Affected endpoints:**
- Export to Excel/CSV (large projects)
- Bulk issue operations
- Large file attachments

---

## Files Modified for Vercel

1. `plane/settings/vercel.py` - Main Vercel settings with Celery mock
2. `plane/utils/celery_sync.py` - Synchronous task wrapper
3. `plane/utils/storage/vercel_blob.py` - Vercel Blob storage backend
4. `plane/settings/storage.py` - Lazy boto3 imports
5. `plane/settings/mongo.py` - Lazy pymongo imports
6. `plane/bgtasks/*.py` - Various tasks with lazy imports
7. `api/requirements.txt` - Reduced dependencies

---

## How to Restore Full Functionality

If moving away from Vercel to a platform with persistent workers (Railway, Render, self-hosted):

1. **Restore packages in requirements:**
   ```
   celery==5.4.0
   django_celery_beat==2.6.0
   django-celery-results==2.5.1
   django-storages==1.14.2
   boto3==1.34.96
   faker==25.0.0  # if needed for tests
   ```

2. **Use production settings instead of vercel:**
   ```
   DJANGO_SETTINGS_MODULE=plane.settings.production
   ```

3. **Start Celery worker:**
   ```
   celery -A plane worker -l info
   ```

4. **Start Celery beat:**
   ```
   celery -A plane beat -l info
   ```

---

## Testing Checklist

Before deploying, verify these work on Vercel:

- [ ] User registration/login
- [ ] Create workspace
- [ ] Create project
- [ ] Create/edit issues
- [ ] File attachments (small files)
- [ ] API authentication
- [ ] Password reset (email may be slow)
- [ ] Project invitations (email may be slow)

---

*Last updated: March 2024*
*Created during Vercel migration to track disabled features*
