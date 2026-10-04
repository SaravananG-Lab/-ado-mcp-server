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
        """Build Claude prompt for story refinement using given context"""
        return f"""You are a Senior Technical Writer and Agile coach refining Azure DevOps user stories for clarity and testability.

STORY INFORMATION:

* Story Title: {story.get('title', 'N/A')}
* Current Description: {story.get('description', 'N/A')}
* Technical Requirement: {story.get('technical_requirement', 'N/A')}
* Requirement ID: {story.get('requirement_id', 'N/A')}
* Priority: {story.get('priority', 'Medium')}

REFINEMENT INSTRUCTIONS:

1. PRESERVE existing details - do not remove or change the original requirement
2. EXPAND with detailed functional and technical information where applicable
3. IDENTIFY missing information, assumptions, dependencies, and open questions
4. PREPARE clear, detailed, testable acceptance criteria using Given/When/Then format
5. COVER positive, negative, validation, error, security, integration, and audit scenarios when relevant
6. DO NOT invent business requirements - clearly mark all assumptions
7. DO NOT update ADO automatically - output is for review and approval

ACCEPTANCE CRITERIA FORMAT:
Use Given/When/Then BDD format where it improves clarity:
- Given [precondition]
- When [action]
- Then [expected result]

Include scenarios for:
- Positive path (happy path)
- Negative path (error handling)
- Validation scenarios
- Error conditions
- Security considerations
- Integration points
- Audit/logging requirements

OUTPUT:
Return ONLY valid JSON (no Markdown, no code fences):

{{
  "existing_story": "Original story title and description as-is",
  "expanded_story": "Enhanced description with technical details and functional requirements",
  "missing_information": [
    "Question 1 or missing detail",
    "Question 2 or missing detail"
  ],
  "assumptions": [
    "- Assumption 1 (clearly marked)",
    "- Assumption 2 (clearly marked)"
  ],
  "dependencies": [
    "Dependency 1",
    "Dependency 2"
  ],
  "acceptance_criteria": [
    "Given [precondition] When [action] Then [result]",
    "Given [precondition] When [action] Then [result]"
  ],
  "open_questions": [
    "Question for clarification?",
    "Question for approval?"
  ],
  "story_quality_assessment": {{
    "is_broad": false,
    "can_be_split": false,
    "clarity_level": "high/medium/low",
    "testing_complexity": "high/medium/low"
  }}
}}

RULES:
* Return only valid JSON
* Do not invent business requirements
* Clearly mark all assumptions with "ASSUMPTION:"
* Preserve original story intent and scope
* Each AC should be testable and measurable
* Include both happy path and error scenarios"""

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

            # Support both old and new response formats
            return {
                # Old format fields (for backward compatibility)
                "user_story": parsed.get("user_story", ""),
                "expanded_description": parsed.get("expanded_story", parsed.get("detailed_description", "")),
                "assumptions": parsed.get("assumptions", []),
                "acceptance_criteria": parsed.get("acceptance_criteria", []),
                "dependencies": parsed.get("dependencies", []),
                "story_quality": parsed.get("story_quality_assessment", parsed.get("story_quality", {})),

                # New refinement format fields
                "existing_story": parsed.get("existing_story", ""),
                "missing_information": parsed.get("missing_information", []),
                "open_questions": parsed.get("open_questions", [])
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

    def _generate_user_story(self, primary_text: str, title: str, technical_req: str) -> str:
        """Generate user story based on primary text (technical requirement or title)"""
        primary_lower = primary_text.lower()

        # Infer role and intent from primary text
        if any(x in primary_lower for x in ["support", "help", "assist", "aid"]):
            return f"As a user, I want {primary_text.lower()} support, so that my workflow is efficient."
        elif any(x in primary_lower for x in ["template", "generate", "create", "build"]):
            return f"As a developer, I want to {primary_text.lower()}, so that I can reduce manual effort."
        elif any(x in primary_lower for x in ["validat", "check", "verify", "enforce", "compliance"]):
            return f"As a system, I want to {primary_text.lower()}, so that data integrity and compliance are maintained."
        elif any(x in primary_lower for x in ["retry", "recovery", "failover", "backup", "resilience"]):
            return f"As a platform engineer, I want {primary_text.lower()} implemented, so that system resilience is improved."
        else:
            # Use actual requirement or title
            text_to_use = primary_text[:100] if len(primary_text) > 100 else primary_text
            return f"To meet the requirement, {text_to_use}."

    def _generate_description(self, primary_text: str, description: str, requirement_id: str) -> str:
        """Generate detailed description based on primary text (requirement or title)"""
        # Use existing description if available
        if description and len(description.strip()) > 20:
            return description

        primary_lower = primary_text.lower()
        req_prefix = f"({requirement_id}) " if requirement_id else ""

        if "template" in primary_lower:
            return f"{req_prefix}Implement {primary_text} to standardize and accelerate content generation. This feature provides reusable patterns and structures for consistent output."
        elif "validat" in primary_lower or "check" in primary_lower or "verify" in primary_lower:
            return f"{req_prefix}Add {primary_text} capability to ensure data quality and compliance. This includes verifying inputs against authoritative sources, enforcing business rules, and providing clear feedback on validation results."
        elif "retry" in primary_lower or "recovery" in primary_lower:
            return f"{req_prefix}Implement {primary_text} to improve system resilience. This includes automatic retry logic, exponential backoff, and graceful error handling."
        else:
            # Use technical requirement as-is if available, fallback to generic description
            return f"{req_prefix}{primary_text}" if "requirement" in requirement_id.lower() or len(primary_text) > 50 else f"Implement {primary_text} to enhance platform capabilities and improve user experience. This feature includes proper error handling, logging, and integration with existing systems."

    def _generate_assumptions(self, primary_text: str, priority: str) -> list:
        """Generate story-specific assumptions based on technical requirement"""
        primary_lower = primary_text.lower()
        assumptions = []

        # Generate assumptions based on story type
        if any(x in primary_lower for x in ["validat", "verify", "check", "audit", "against authoritative"]):
            assumptions = [
                "- Authoritative data sources are accessible and reliable",
                "- Business validation rules are documented and stable",
                "- Data quality standards are defined",
                "- Real-time or periodic data sync is acceptable",
                "- Error handling for source unavailability is acceptable"
            ]
        elif any(x in primary_lower for x in ["reconcil", "sync", "synchroniz", "align", "match"]):
            assumptions = [
                "- Source and target systems are accessible",
                "- Data mapping rules are well-defined",
                "- Conflict resolution strategy is determined",
                "- Acceptable sync frequency/latency is defined",
                "- Rollback capability is available"
            ]
        elif any(x in primary_lower for x in ["retry", "recover", "failover", "resilience", "failure"]):
            assumptions = [
                "- Failure modes and recovery strategies are defined",
                "- Monitoring and alerting infrastructure is in place",
                "- Acceptable downtime/RPO/RTO are established",
                "- Testing with failure scenarios is feasible",
                "- Circuit breaker patterns are appropriate"
            ]
        elif any(x in primary_lower for x in ["template", "generat", "format", "card", "document", "letter"]):
            assumptions = [
                "- Template structure and format are finalized",
                "- All required template variables are identified",
                "- Output format standards are established",
                "- Volume and performance targets defined",
                "- Backwards compatibility requirements understood"
            ]
        elif any(x in primary_lower for x in ["index", "search", "query", "find", "retriev"]):
            assumptions = [
                "- Data to be indexed is available and accessible",
                "- Search criteria/filters are well-defined",
                "- Query performance targets are established",
                "- Index update frequency is acceptable",
                "- Data consistency requirements are understood"
            ]
        elif any(x in primary_lower for x in ["score", "rank", "calculat", "comput", "gate", "weight"]):
            assumptions = [
                "- Calculation formula/algorithm is finalized",
                "- All input parameters are available",
                "- Precision and rounding rules are defined",
                "- Performance targets for calculations are established",
                "- Edge case handling approach is determined"
            ]
        elif any(x in primary_lower for x in ["select", "choice", "option", "decision", "logic", "rule"]):
            assumptions = [
                "- Decision rules and selection criteria are documented",
                "- All input parameters are available",
                "- Priority/conflict resolution is defined",
                "- User experience expectations are clear",
                "- Performance requirements for decision logic are known"
            ]
        else:
            # Generic assumptions
            assumptions = [
                "- Requirements are clearly defined and understood",
                "- Dependent systems are available and stable",
                "- Performance and scale targets are established",
                "- Security and compliance requirements are known",
                "- Testing approach and success criteria defined"
            ]

        # Add conditional assumptions based on priority
        if priority in ["P0", "P1"]:
            assumptions.append("- Backward compatibility with existing data/integrations required")

        # Add platform assumptions if mentioned
        if any(x in primary_lower for x in ["platform", "infrastructure", "deployment", "kubernetes", "azure"]):
            assumptions.insert(1, "- Azure cloud infrastructure and services are available")

        return assumptions if len(assumptions) > 1 else assumptions + ["- Standard development and testing practices apply"]

    def _generate_acceptance_criteria(self, primary_text: str, priority: str) -> list:
        """Generate context-specific acceptance criteria based on technical requirement"""
        primary_lower = primary_text.lower()

        # Extract key capability from technical requirement
        capability = self._extract_capability(primary_text)
        criteria = []

        # More comprehensive keyword matching with broader patterns
        if any(x in primary_lower for x in ["validat", "verify", "check", "audit", "compliance", "against authoritative"]):
            criteria = [
                f"- {capability} implemented and working correctly",
                "- Validation/verification logic handles all specified scenarios",
                "- Edge cases and error conditions properly handled",
                "- Results match business and technical requirements",
                "- Clear error messages and feedback provided",
                "- Integration with required data sources verified",
                "- Audit/logging of all validations complete",
                "- Unit and integration tests with >80% coverage"
            ]
        elif any(x in primary_lower for x in ["reconcil", "sync", "synchroniz", "align", "match", "compare"]):
            criteria = [
                f"- {capability} implemented correctly",
                "- Reconciliation/sync accurately identifies discrepancies",
                "- Data alignment matches source and target",
                "- Duplicate detection and resolution working",
                "- Exception handling for failed sync scenarios",
                "- Performance meets SLA for data volumes",
                "- Rollback and recovery procedures tested",
                "- Complete audit trail maintained"
            ]
        elif any(x in primary_lower for x in ["retry", "recover", "failover", "resilience", "fault", "failure"]):
            criteria = [
                f"- {capability} implemented",
                "- Retry logic handles transient failures correctly",
                "- Exponential backoff and timeout configured",
                "- Maximum retry limits enforced appropriately",
                "- Circuit breaker/fallback mechanisms working",
                "- Recovery procedures documented and tested",
                "- Failure scenarios tested thoroughly",
                "- Monitoring and alerting configured"
            ]
        elif any(x in primary_lower for x in ["template", "generat", "format", "card", "document", "letter"]):
            criteria = [
                f"- {capability} generated correctly",
                "- Output format matches specification exactly",
                "- All required fields and sections included",
                "- Formatting rules and styling applied correctly",
                "- Variable substitution working for all placeholders",
                "- Edge cases (empty fields, special chars) handled",
                "- Performance acceptable for typical volumes",
                "- User acceptance testing completed"
            ]
        elif any(x in primary_lower for x in ["index", "search", "query", "find", "retriev", "lookup"]):
            criteria = [
                f"- {capability} implemented",
                "- Index creation and updates functioning correctly",
                "- Search/query returns accurate results",
                "- Query performance meets requirements",
                "- Filtering and sorting work as specified",
                "- Large dataset scalability verified",
                "- Search relevance and accuracy validated",
                "- Index consistency and integrity verified"
            ]
        elif any(x in primary_lower for x in ["score", "rank", "calculat", "comput", "gate", "weight"]):
            criteria = [
                f"- {capability} calculation correct",
                "- All input parameters processed accurately",
                "- Calculation results match expected outcomes",
                "- Edge cases and boundary conditions tested",
                "- Precision/rounding handled per specification",
                "- Performance acceptable for scale",
                "- Calculation formula/logic documented clearly",
                "- Results audit trail maintained"
            ]
        elif any(x in primary_lower for x in ["select", "choice", "option", "decision", "logic", "rule"]):
            criteria = [
                f"- {capability} logic implemented",
                "- Selection/decision rules working correctly",
                "- All specified conditions evaluated properly",
                "- Appropriate options returned for each scenario",
                "- Edge cases and conflicts handled",
                "- User experience meets requirements",
                "- Performance acceptable",
                "- Comprehensive test coverage achieved"
            ]
        else:
            # Enhanced generic criteria that references the actual requirement
            criteria = [
                f"- {capability} implemented per specification",
                "- Functionality tested against all requirements",
                "- Code review completed and approved",
                "- Unit tests written with >80% code coverage",
                "- Integration testing with dependent systems",
                "- Performance and load testing completed",
                "- Documentation updated and reviewed",
                "- Ready for production deployment"
            ]

        return criteria

    def _extract_capability(self, text: str) -> str:
        """Extract main capability from technical requirement text"""
        text = text.strip()
        # Remove common prefixes
        for prefix in ["the cip platform shall implement", "cip shall", "shall", "implement"]:
            if text.lower().startswith(prefix):
                text = text[len(prefix):].strip()

        # Take first 50-80 chars of remaining text
        if len(text) > 80:
            text = text[:80].rsplit(' ', 1)[0]

        return text.strip(": –-").lower()

    def _generate_dependencies(self, primary_text: str, description: str) -> list:
        """Generate dependencies based on primary text"""
        dependencies = []

        primary_lower = primary_text.lower()

        if any(x in primary_lower for x in ["platform", "infrastructure", "deployment", "kubernetes"]):
            dependencies.append("Infrastructure setup and configuration")

        if any(x in primary_lower for x in ["integration", "api", "service"]):
            dependencies.append("API and service dependencies")

        if any(x in primary_lower for x in ["database", "storage", "persistence", "reconciliation"]):
            dependencies.append("Database schema and migration scripts")

        if any(x in primary_lower for x in ["security", "authentication", "authorization", "compliance"]):
            dependencies.append("Security and compliance review")

        return dependencies if dependencies else []

    def _expand_story(self, story_input: dict) -> dict:
        """Expand a story based on actual story content"""
        try:
            # Build the prompt for Claude
            prompt = self.expander.build_prompt(story_input)

            # Extract story details
            title = story_input.get("title", "").strip()
            description = story_input.get("description", "").strip()
            technical_req = story_input.get("technical_requirement", "").strip()
            requirement_id = story_input.get("requirement_id", "").strip()
            priority = story_input.get("priority", "Medium")

            # Use technical requirement as primary source if available
            primary_text = technical_req if technical_req else title

            # Generate context-aware expansion based on actual requirements
            user_story = self._generate_user_story(primary_text, title, technical_req)
            expanded_desc = self._generate_description(primary_text, description, requirement_id)
            assumptions = self._generate_assumptions(primary_text, priority)
            acceptance_criteria = self._generate_acceptance_criteria(primary_text, priority)
            dependencies = self._generate_dependencies(primary_text, description)

            result = {
                "story_id": story_input.get("story_id"),
                "user_story": user_story,
                "expanded_description": expanded_desc,
                "assumptions": assumptions,
                "acceptance_criteria": acceptance_criteria,
                "dependencies": dependencies,
                "story_quality": {
                    "is_broad": False,
                    "can_be_split": False,
                    "missing_information": [],
                    "potential_dependencies": []
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
