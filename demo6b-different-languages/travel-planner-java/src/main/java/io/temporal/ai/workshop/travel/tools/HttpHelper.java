// ABOUTME: Minimal blocking HTTP GET helper used by the travel tools.
// Runs inside Temporal activities, so plain blocking I/O is fine here.
package io.temporal.ai.workshop.travel.tools;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public final class HttpHelper {

    private static final HttpClient CLIENT =
            HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();

    // Wikimedia's REST API rejects requests with the default Java User-Agent
    // (HTTP 403). Its policy requires a descriptive UA identifying the app.
    // See https://meta.wikimedia.org/wiki/User-Agent_policy
    private static final String USER_AGENT =
            "temporal-ai-workshop-travel-planner/0.1 (https://github.com/temporal-community)";

    private HttpHelper() {}

    public static String get(String url) {
        HttpRequest request =
                HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .timeout(Duration.ofSeconds(5))
                        .header("User-Agent", USER_AGENT)
                        .GET()
                        .build();
        try {
            HttpResponse<String> response =
                    CLIENT.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() >= 400) {
                throw new RuntimeException("HTTP " + response.statusCode() + " from " + url);
            }
            return response.body();
        } catch (IOException e) {
            throw new RuntimeException("Request to " + url + " failed", e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("Request to " + url + " interrupted", e);
        }
    }
}
