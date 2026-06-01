// ABOUTME: Nexus handler that starts the travel-planner workflow (WorkflowRunOperation).
// Registered on the worker via application.yaml's nexus-service-beans (bean "travelPlannerServiceImpl").
package io.temporal.ai.workshop.travel;

import io.nexusrpc.handler.OperationHandler;
import io.nexusrpc.handler.OperationImpl;
import io.nexusrpc.handler.ServiceImpl;
import io.temporal.client.WorkflowOptions;
import io.temporal.nexus.Nexus;
import io.temporal.nexus.WorkflowRunOperation;
import java.util.UUID;
import org.springframework.stereotype.Component;

@Component("travelPlannerServiceImpl")
@ServiceImpl(service = TravelPlannerService.class)
public class TravelPlannerServiceImpl {

    // Method name matches the interface operation method (askTravelPlanner); the
    // wire-level operation name comes from the @Operation annotation on the interface.
    @OperationImpl
    public OperationHandler<TravelPlannerService.AskRequest, TravelPlannerService.AskResponse>
            askTravelPlanner() {
        // Start the agent workflow and hand back its result. The workflow runs on
        // the same task queue this Nexus operation is handled on (travel-planner-agent-tq),
        // where TravelPlannerAgentWorkflowImpl is registered.
        return WorkflowRunOperation.fromWorkflowMethod(
                (context, details, request) ->
                        Nexus.getOperationContext()
                                        .getWorkflowClient()
                                        .newWorkflowStub(
                                                TravelPlannerAgentWorkflow.class,
                                                WorkflowOptions.newBuilder()
                                                        .setWorkflowId("travel-planner-" + UUID.randomUUID())
                                                        .build())
                                ::run);
    }
}
