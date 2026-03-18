# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Celery Sync Wrapper for Vercel Serverless

This module provides a synchronous execution wrapper for Celery tasks
when running on Vercel serverless where Celery workers are not available.

TODO (Vercel Migration):
- This is a temporary solution for Vercel deployment
- Tasks are executed synchronously which may cause timeouts for long-running tasks
- Consider implementing:
  1. Vercel Cron Jobs for scheduled tasks
  2. Vercel Edge Functions for async processing
  3. External queue service (e.g., QStash, Inngest) for background jobs
"""

import logging
import functools
import os

logger = logging.getLogger(__name__)

# Check if we're in Vercel/sync mode without importing Django settings
# This allows the module to be imported before Django is fully configured
_CELERY_EAGER_MODE = os.environ.get('CELERY_TASK_ALWAYS_EAGER', '').lower() in ('true', '1', 'yes')


class SyncTaskResult:
    """Mock Celery AsyncResult for sync execution"""

    def __init__(self, result=None, task_id=None):
        self.result = result
        self.id = task_id or "sync-task"
        self.status = "SUCCESS"

    def get(self, timeout=None):
        return self.result

    def ready(self):
        return True

    def successful(self):
        return True


class SyncTask:
    """
    Wrapper that makes a function behave like a Celery task
    but executes synchronously.
    """

    def __init__(self, func):
        self.func = func
        self.name = f"{func.__module__}.{func.__name__}"
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def delay(self, *args, **kwargs):
        """
        Execute task synchronously instead of sending to Celery broker.
        In Vercel serverless, we don't have persistent workers.
        """
        # Execute synchronously
        try:
            result = self.func(*args, **kwargs)
            logger.debug(f"[SYNC] Task {self.name} executed successfully")
            return SyncTaskResult(result=result)
        except Exception as e:
            logger.warning(f"[SYNC] Task {self.name} failed: {e}")
            # Don't raise - background tasks shouldn't crash the request
            return SyncTaskResult(result=None)

    def apply_async(self, args=None, kwargs=None, **options):
        """Sync version of apply_async"""
        args = args or ()
        kwargs = kwargs or {}
        return self.delay(*args, **kwargs)

    def s(self, *args, **kwargs):
        """Signature - return self for chaining"""
        return self

    def si(self, *args, **kwargs):
        """Immutable signature - return self for chaining"""
        return self


def shared_task(_func=None, **task_kwargs):
    """
    Replacement for celery.shared_task decorator.

    In Vercel mode (CELERY_TASK_ALWAYS_EAGER=True), wraps the function
    to execute synchronously when .delay() is called.

    Usage remains the same:
        @shared_task
        def my_task(arg1, arg2):
            ...

        my_task.delay(arg1, arg2)
    """
    def decorator(func):
        # Always use sync wrapper in this module
        # This module is only used when Celery is mocked (Vercel mode)
        return SyncTask(func)

    if _func is not None:
        # Decorator used without arguments: @shared_task
        return decorator(_func)
    else:
        # Decorator used with arguments: @shared_task(bind=True)
        return decorator
