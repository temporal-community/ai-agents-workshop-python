// ABOUTME: Travel-planner agent workflow — runs a Spring AI ChatClient durably via temporal-spring-ai.
// Each LLM call and each tool call becomes its own Temporal activity (per-step durability).
package io.temporal.ai.workshop.travel;

import io.temporal.activity.ActivityOptions;
import io.temporal.ai.workshop.travel.tools.TravelTools;
import io.temporal.springai.chat.TemporalChatClient;
import io.temporal.springai.model.ActivityChatModel;
import io.temporal.workflow.Workflow;
import io.temporal.workflow.WorkflowInit;
import java.time.Duration;
import org.springframework.ai.chat.client.ChatClient;

public class TravelPlannerAgentWorkflowImpl implements TravelPlannerAgentWorkflow {

    private static final String SYSTEM_PROMPT =
            """
            You are a travel planning specialist. Help users understand destinations:
            their context (Wikipedia summary), country background (language, currency,
            region), and high-level practical information.

            If users are not asking about a specific destination, do not guess; instead
            ask for more specific information.

            Use the provided tools as needed. Answer concisely as plain text.
            """;

    private final ChatClient chatClient;

    @WorkflowInit
    public TravelPlannerAgentWorkflowImpl(TravelPlannerService.AskRequest request) {
        // Activity stub for the travel tools: each @Tool method becomes a durable
        // Temporal activity when the model calls it.
        TravelTools travelTools =
                Workflow.newActivityStub(
                        TravelTools.class,
                        ActivityOptions.newBuilder()
                                .setStartToCloseTimeout(Duration.ofSeconds(30))
                                .build());

        // ActivityChatModel routes the LLM call to the ChatModelActivity that the
        // temporal-spring-ai SpringAiPlugin auto-registers on this worker.
        ActivityChatModel activityChatModel = ActivityChatModel.forDefault();

        this.chatClient =
                TemporalChatClient.builder(activityChatModel)
                        .defaultSystem(SYSTEM_PROMPT)
                        .defaultTools(travelTools)
                        .build();
    }

    @Override
    public TravelPlannerService.AskResponse run(TravelPlannerService.AskRequest request) {
        String answer = chatClient.prompt().user(request.getQuestion()).call().content();
        return new TravelPlannerService.AskResponse(answer);
    }
}
