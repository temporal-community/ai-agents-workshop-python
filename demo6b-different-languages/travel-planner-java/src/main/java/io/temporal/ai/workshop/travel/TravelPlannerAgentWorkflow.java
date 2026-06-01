// ABOUTME: Workflow interface for the travel-planner sub-agent (started via Nexus).
// Takes the Nexus request and returns its response so the operation result flows straight back.
package io.temporal.ai.workshop.travel;

import io.temporal.workflow.WorkflowInterface;
import io.temporal.workflow.WorkflowMethod;

@WorkflowInterface
public interface TravelPlannerAgentWorkflow {
    @WorkflowMethod
    TravelPlannerService.AskResponse run(TravelPlannerService.AskRequest request);
}
