// ABOUTME: Implements the travel tools by calling the same public REST APIs as the Python Strands agent.
// Wikipedia REST summary + REST Countries. Returns raw JSON/text for the model to interpret.
package io.temporal.ai.workshop.travel.tools;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import org.springframework.stereotype.Component;

@Component("travelToolsImpl")
public class TravelToolsImpl implements TravelTools {

    @Override
    public String getWikipediaSummary(String topic) {
        // Wikipedia REST titles use %20 (not "+") for spaces in the path segment.
        String encoded = URLEncoder.encode(topic, StandardCharsets.UTF_8).replace("+", "%20");
        return HttpHelper.get("https://en.wikipedia.org/api/rest_v1/page/summary/" + encoded);
    }

    @Override
    public String getCountryInfo(String country) {
        String encoded = URLEncoder.encode(country, StandardCharsets.UTF_8).replace("+", "%20");
        return HttpHelper.get("https://restcountries.com/v3.1/name/" + encoded);
    }
}
