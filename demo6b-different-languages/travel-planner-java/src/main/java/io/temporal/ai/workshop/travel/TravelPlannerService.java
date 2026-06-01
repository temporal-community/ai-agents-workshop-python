// ABOUTME: Cross-language Nexus service interface — the Python orchestrator is the caller.
// Service/operation names and JSON field names MUST match the Python travel_planner_service.py.
package io.temporal.ai.workshop.travel;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;

// Service name MUST equal the Python @nexusrpc.service class name "TravelPlannerService".
// (The unqualified interface name already is that; name= is stated for an explicit contract.)
@Service(name = "TravelPlannerService")
public interface TravelPlannerService {

    // JSON shape MUST match Pydantic AskRequest{ question: str }.
    class AskRequest {
        private final String question;

        @JsonCreator
        public AskRequest(@JsonProperty("question") String question) {
            this.question = question;
        }

        @JsonProperty("question")
        public String getQuestion() {
            return question;
        }
    }

    // JSON shape MUST match Pydantic AskResponse{ answer: str }.
    class AskResponse {
        private final String answer;

        @JsonCreator
        public AskResponse(@JsonProperty("answer") String answer) {
            this.answer = answer;
        }

        @JsonProperty("answer")
        public String getAnswer() {
            return answer;
        }
    }

    // Operation name MUST equal the Python operation name "ask_travel_planner".
    // The Java method default would be "askTravelPlanner", so override it explicitly.
    @Operation(name = "ask_travel_planner")
    AskResponse askTravelPlanner(AskRequest request);
}
