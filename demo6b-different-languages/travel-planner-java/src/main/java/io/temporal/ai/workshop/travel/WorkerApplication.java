// ABOUTME: Spring Boot entry point for the Java travel-planner worker.
// temporal-spring-boot-starter reads application.yaml to build the worker; the
// temporal-spring-ai auto-config registers the LLM-call activity onto it.
package io.temporal.ai.workshop.travel;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class WorkerApplication {
    public static void main(String[] args) {
        SpringApplication.run(WorkerApplication.class, args);
    }
}
