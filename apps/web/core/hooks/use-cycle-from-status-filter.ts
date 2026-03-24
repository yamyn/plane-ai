/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useMemo } from "react";
import { useParams } from "next/navigation";
import type { TCycleStatusFilter } from "@plane/types";
import { useCycle } from "@/hooks/store/use-cycle";
import { useIssuesStore } from "@/hooks/use-issue-layout-store";

/**
 * Returns cycle_id if there's at least one cycle matching the cycle_status filter.
 * Used for auto-populating cycle when creating issues with Sprint Status filter active.
 */
export const useCycleFromStatusFilter = (): string | undefined => {
  const { projectId } = useParams();
  const { issuesFilter } = useIssuesStore();
  const { getProjectCycleDetails } = useCycle();

  const cycleStatus = issuesFilter?.issueFilters?.displayFilters?.cycle_status;

  return useMemo(() => {
    if (!cycleStatus?.length || !projectId) return undefined;

    const cycles = getProjectCycleDetails(projectId as string);
    if (!cycles) return undefined;

    const matchingCycles = cycles.filter((cycle) => {
      const status = cycle.status?.toLowerCase() as TCycleStatusFilter | undefined;
      return status && cycleStatus.includes(status);
    });

    // Return first matching cycle_id (if any)
    return matchingCycles.length > 0 ? matchingCycles[0].id : undefined;
  }, [cycleStatus, projectId, getProjectCycleDetails]);
};
