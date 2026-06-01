# ABOUTME: Caller-side Nexus service stub for the travel planner — the handler lives in Java.
# The Python orchestrator only needs this interface to build the nexus_operation_as_tool tool.

from __future__ import annotations

import nexusrpc
from pydantic import BaseModel


# Nexus operation I/O. The JSON field names ("question"/"answer") are the
# cross-language wire contract: the Java handler's Jackson POJOs must match
# these exactly. See travel-planner-java/.../TravelPlannerService.java.
class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str


@nexusrpc.service
class TravelPlannerService:
    # The service name defaults to the class name ("TravelPlannerService") and
    # the operation name to this attribute name ("ask_travel_planner"). Both
    # strings must match the Java @Service / @Operation names byte-for-byte.
    ask_travel_planner: nexusrpc.Operation[AskRequest, AskResponse]
