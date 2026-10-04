#!/usr/bin/env python3
"""
Story Expansion MCP Server
Provides Claude-powered story expansion as an MCP tool.
Can be used by any client to expand DevOps stories.
"""

import json
import sys
from typing import Any


class StoryExpander:
    """Core story expansion logic"""

    @staticmethod
    def build_prompt(story: dict) -> str:
        """Build Claude prompt for story expansion"""
        return f"""You are a Senior Agile Technical Writer. Expand the following Azure DevOps user story into a clear, implementation-ready Agile story while preserving the original intent and scope.

STORY INFORMATION:

* Story Title: {story.get('title', 'N/A')}
* Current Description: {story.get('description', 'N/A')}
* Epic: {story.get('epic', 'N/A')}
* Feature: {story.get('feature', 'N/A')}
* Priority: {story.get('priority', 'Medium')}
* Requirement ID: {story.get('requirement_id', 'N/A')}

INSTRUCTIONS:

1. Preserve the original business and technical intent. Do not add unrelated functionality.
2. Preserve the original Story Title unless it is clearly incomplete or misleading.
3. Use the standard Agile format "As a [user/role], I want [capability], so that [business value]" when a meaningful user/actor and business outcome can be identified.
4. For technical, infrastructure, DevOps, integration, or platform stories where the Agile format would be artificial, use a clear capability-oriented statement instead.
5. Keep the description focused on what needs to be delivered, why it is needed, expected behavior, and relevant integrations.
6. Identify only relevant assumptions. Do not invent technologies, versions, APIs, performance numbers, SLAs, or business rules.
7. Provide concise, testable acceptance criteria. Normally provide 3-8 criteria based on story complexity. Do not add criteria merely to reach a minimum number.
8. Include validation, error handling, security, integration, logging, monitoring, or performance criteria only when relevant.
9. Identify dependencies if applicable.
10. Flag the story if it is too broad, can be split, or has important missing information.
11. Keep acceptance criteria concise. Use simple numbered statements; use Given/When/Then only when it improves clarity.

OUTPUT:
Return ONLY valid JSON (no Markdown, no code fences):

{{
  "user_story": "As a [user/role], I want [capability], so that [business value].",
  "detailed_description": "2-3 concise paragraphs.",
  "assumptions": [
    "- Assumption 1",
    "- Assumption 2"
  ],
  "acceptance_criteria": [
    "1. Concise, testable criterion.",
    "2. Concise, testable criterion."
  ],
  "dependencies": [
    "Dependency 1 (if any)"
  ],
  "story_quality": {{
    "is_broad": false,
    "can_be_split": false,
    "missing_information": [],
    "potential_dependencies": []
  }}
}}

RULES:
* Return only valid JSON.
* Do not use Markdown or code fences.
* Do not invent requirements.
* Do not duplicate information unnecessarily.
* Keep the original story scope and intent unchanged."""

    @staticmethod
    def parse_response(content: str) -> dict:
        """Parse Claude's JSON response"""
        try:
            # Try to extract JSON from the response
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]

            parsed = json.loads(json_str.strip())
            return {
                "user_story": parsed.get("user_story", ""),
                "expanded_description": parsed.get("detailed_description", ""),
                "assumptions": parsed.get("assumptions", []),
                "acceptance_criteria": parsed.get("acceptance_criteria", []),
                "dependencies": parsed.get("dependencies", []),
                "story_quality": parsed.get("story_quality", {})
            }
        except Exception as e:
            raise Exception(f"Error parsing Claude response: {e}")


class MCPServer:
    """MCP Server for story expansion"""

    def __init__(self):
        self.expander = StoryExpander()
        self.request_id = None

    def handle_request(self, request: dict) -> dict:
        """Handle incoming MCP request"""
        self.request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        try:
            if method == "tools/list":
                return self._handle_tools_list()
            elif method == "tools/call":
                return self._handle_tool_call(params)
            else:
                return self._error(f"Unknown method: {method}")
        except Exception as e:
            return self._error(str(e))

    def _handle_tools_list(self) -> dict:
        """List available tools"""
        return {
            "id": self.request_id,
            "result": {
                "tools": [
                    {
                        "name": "expand_story",
                        "description": "Expand a DevOps story with detailed description, assumptions, and acceptance criteria",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "story_id": {
                                    "type": "string",
                                    "description": "Story ID (e.g., CIP-PA-285)"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Story title"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Current story description"
                                },
                                "epic": {
                                    "type": "string",
                                    "description": "Epic name (e.g., Event-Driven Architecture)"
                                },
                                "feature": {
                                    "type": "string",
                                    "description": "Feature name"
                                },
                                "priority": {
                                    "type": "string",
                                    "description": "Priority (P0, P1, P2, P3)"
                                },
                                "requirement_id": {
                                    "type": "string",
                                    "description": "Requirement ID"
                                }
                            },
                            "required": ["story_id", "title"]
                        }
                    }
                ]
            }
        }

    def _handle_tool_call(self, params: dict) -> dict:
        """Handle tool call"""
        tool_name = params.get("name")
        tool_input = params.get("input", {})

        if tool_name == "expand_story":
            return self._expand_story(tool_input)
        else:
            return self._error(f"Unknown tool: {tool_name}")

    def _expand_story(self, story_input: dict) -> dict:
        """Expand a story"""
        try:
            # This is where Claude would be called
            # For now, return a placeholder that shows the structure
            prompt = self.expander.build_prompt(story_input)

            # In a real MCP setup, this would call Claude API
            # For testing/demo, return a sample with new prompt structure
            result = {
                "story_id": story_input.get("story_id"),
                "user_story": f"As a platform engineer, I want {story_input.get('feature', 'this capability')} implemented, so that the {story_input.get('epic', 'platform')} operates reliably.",
                "expanded_description": f"""The {story_input.get('epic', 'platform')} requires implementation of {story_input.get('feature', 'this capability')} to support the workflow.

This involves configuring necessary infrastructure components, ensuring proper integration with existing systems, and maintaining compliance with operational requirements.

The implementation includes: configuration of infrastructure, integration with dependent services, monitoring and observability, and documentation.""",
                "assumptions": [
                    "- Azure AKS is the container orchestration platform",
                    "- Kubernetes version 1.24+",
                    "- Network isolation via VPCs",
                    "- Minimum 2 replicas for high availability",
                    "- 90-day retention for operational data",
                    "- Encryption at rest and in transit required"
                ],
                "acceptance_criteria": [
                    "1. Component deployed and accessible",
                    "2. Integration tests pass with dependent services",
                    "3. Monitoring dashboards configured",
                    "4. Load testing confirms performance targets",
                    "5. Documentation completed",
                    "6. Security scan passes with 0 high/critical findings",
                    "7. Disaster recovery procedure tested",
                    "8. User acceptance testing completed"
                ],
                "dependencies": [
                    "Azure infrastructure provisioning",
                    "Network and security configuration"
                ],
                "story_quality": {
                    "is_broad": True,
                    "can_be_split": True,
                    "missing_information": ["Acceptance criteria specifics", "Performance thresholds"],
                    "potential_dependencies": ["Infrastructure provisioning", "Security review"]
                }
            }

            return {
                "id": self.request_id,
                "result": result
            }
        except Exception as e:
            return self._error(f"Failed to expand story: {e}")

    def _error(self, message: str) -> dict:
        """Return error response"""
        return {
            "id": self.request_id,
            "error": {
                "code": -32603,
                "message": message
            }
        }


def main():
    """Main entry point - run MCP server"""
    server = MCPServer()

    print("[INFO] Story Expansion MCP Server started", file=sys.stderr)

    try:
        while True:
            # Read JSON-RPC request from stdin
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            response = server.handle_request(request)

            # Send JSON-RPC response to stdout
            json.dump(response, sys.stdout)
            sys.stdout.write('\n')
            sys.stdout.flush()

    except KeyboardInterrupt:
        print("[INFO] Server stopped", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
