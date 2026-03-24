/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import { useParams } from "next/navigation";
// plane imports
import { STATE_GROUPS } from "@plane/constants";
import { useTranslation } from "@plane/i18n";
import type { TGroupedIssues, TIssueMap, TStateGroups, TSubGroupedIssues } from "@plane/types";
import { Tooltip } from "@plane/ui";
// hooks
import { useProjectEstimates } from "@/hooks/store/estimates";
import { useProjectState } from "@/hooks/store/use-project-state";

type TEstimatesProgressBarProps = {
  groupedIssueIds: TGroupedIssues | TSubGroupedIssues | undefined;
  issuesMap: TIssueMap;
  isVisible: boolean;
};

export const EstimatesProgressBar = observer(function EstimatesProgressBar(props: TEstimatesProgressBarProps) {
  const { groupedIssueIds, issuesMap, isVisible } = props;
  const { projectId } = useParams();
  const { t } = useTranslation();
  const { areEstimateEnabledByProjectId, currentActiveEstimate } = useProjectEstimates();
  const { getStateById } = useProjectState();

  // Check if estimates are enabled
  const areEstimatesEnabled = projectId && areEstimateEnabledByProjectId(projectId.toString());

  // Flatten all issue IDs from grouped structure
  const getIssueIds = (): string[] => {
    if (!groupedIssueIds) return [];
    const ids: string[] = [];
    const processGroup = (group: Record<string, string[] | Record<string, string[]>>) => {
      Object.values(group).forEach((value) => {
        if (Array.isArray(value)) {
          ids.push(...value);
        } else if (typeof value === "object") {
          processGroup(value as Record<string, string[]>);
        }
      });
    };
    processGroup(groupedIssueIds as Record<string, string[] | Record<string, string[]>>);
    return ids;
  };

  // Calculate progress - no useMemo to allow MobX to track observable changes
  const calculateProgress = () => {
    let notStarted = 0;
    let inProgress = 0;
    let done = 0;
    let total = 0;

    const issueIds = getIssueIds();
    issueIds.forEach((issueId) => {
      const issue = issuesMap[issueId];
      if (!issue?.state_id) return;

      const state = getStateById(issue.state_id);
      if (!state) return;

      const stateGroup: TStateGroups = state.group;

      // Get estimate point value
      let value = 0;
      if (issue.estimate_point && currentActiveEstimate) {
        const estimatePoint = currentActiveEstimate.estimatePointById(issue.estimate_point);
        if (estimatePoint?.value) {
          value = parseFloat(estimatePoint.value) || 0;
        }
      }

      // Add to total (all non-cancelled issues)
      if (stateGroup !== "cancelled") {
        total += value;
      }

      // Categorize by state group
      if (stateGroup === "backlog" || stateGroup === "unstarted") {
        notStarted += value;
      } else if (stateGroup === "started") {
        inProgress += value;
      } else if (stateGroup === "completed") {
        done += value;
      }
    });

    return { notStarted, inProgress, done, total };
  };

  const progress = calculateProgress();

  if (!isVisible || !areEstimatesEnabled || !groupedIssueIds || progress.total === 0) return null;

  return (
    <div className="flex items-center gap-1.5 border-r border-subtle pr-3 mr-1">
      {/* Not started */}
      <Tooltip tooltipContent={t("project_cycles.not_started_points")}>
        <div className="flex items-center gap-1.5 rounded-md border border-subtle bg-surface-1 px-2 py-0.5 text-11 font-medium text-tertiary">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: STATE_GROUPS.backlog.color }} />
          <span>{progress.notStarted}</span>
        </div>
      </Tooltip>
      {/* In progress */}
      <Tooltip tooltipContent={t("project_cycles.in_progress_points")}>
        <div className="flex items-center gap-1.5 rounded-md border border-subtle bg-surface-1 px-2 py-0.5 text-11 font-medium text-tertiary">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: STATE_GROUPS.started.color }} />
          <span>{progress.inProgress}</span>
        </div>
      </Tooltip>
      {/* Done */}
      <Tooltip tooltipContent={t("project_cycles.done_points")}>
        <div className="flex items-center gap-1.5 rounded-md border border-subtle bg-surface-1 px-2 py-0.5 text-11 font-medium text-tertiary">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: STATE_GROUPS.completed.color }} />
          <span>{progress.done}</span>
        </div>
      </Tooltip>
      {/* Total */}
      <Tooltip tooltipContent={t("project_cycles.total_points")}>
        <div className="flex items-center gap-1.5 rounded-md border border-accent-primary/30 bg-accent-primary/10 px-2 py-0.5 text-11 font-medium text-accent-primary">
          <span>{progress.total}</span>
        </div>
      </Tooltip>
    </div>
  );
});
