#!/usr/bin/env python3
"""
MCP Client - Communicate with Story Expansion MCP Server
Provides a simple interface for expanding stories via MCP.
"""

import json
import subprocess
import sys
from typing import Dict, Optional
from pathlib import Path


class MCPClient:
    """Client for communicating with MCP servers"""

    def __init__(self, mcp_server_path: str):
        """
        Initialize MCP client

        Args:
            mcp_server_path: Path to the MCP server script (e.g., story_expansion_mcp.py)
        """
        self.mcp_server_path = mcp_server_path
        self.process = None
        self.request_id = 0

    def start(self):
        """Start the MCP server process"""
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.mcp_server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            print(f"[INFO] MCP server started: {self.mcp_server_path}")
        except Exception as e:
            raise Exception(f"Failed to start MCP server: {e}")

    def stop(self):
        """Stop the MCP server process"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print("[INFO] MCP server stopped")
            except Exception as e:
                print(f"[WARNING] Failed to stop MCP server gracefully: {e}")
                self.process.kill()

    def call_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """
        Call a tool via MCP

        Args:
            tool_name: Name of the tool (e.g., "expand_story")
            tool_input: Input parameters for the tool

        Returns:
            Tool result
        """
        if not self.process:
            self.start()

        # Build JSON-RPC request
        self.request_id += 1
        request = {
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "input": tool_input
            }
        }

        try:
            # Send request
            json.dump(request, self.process.stdin)
            self.process.stdin.write('\n')
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                raise Exception("MCP server disconnected")

            response = json.loads(response_line)

            # Check for errors
            if "error" in response:
                raise Exception(f"MCP error: {response['error']['message']}")

            return response.get("result", {})

        except Exception as e:
            raise Exception(f"Failed to call MCP tool '{tool_name}': {e}")

    def list_tools(self) -> Dict:
        """List available tools from MCP server"""
        if not self.process:
            self.start()

        self.request_id += 1
        request = {
            "id": self.request_id,
            "method": "tools/list"
        }

        try:
            json.dump(request, self.process.stdin)
            self.process.stdin.write('\n')
            self.process.stdin.flush()

            response_line = self.process.stdout.readline()
            response = json.loads(response_line)

            return response.get("result", {})

        except Exception as e:
            raise Exception(f"Failed to list MCP tools: {e}")

    def expand_story(self, story_id: str, title: str, description: str = "",
                     epic: str = "", feature: str = "", priority: str = "Medium",
                     requirement_id: str = "", technical_requirement: str = "",
                     delivery_phase: str = "") -> Dict:
        """
        Expand a story using the MCP server

        Args:
            story_id: Story ID
            title: Story title
            description: Current description
            epic: Epic name
            feature: Feature name
            priority: Priority (P0-P3)
            requirement_id: Requirement ID
            technical_requirement: Technical requirement details
            delivery_phase: Delivery phase

        Returns:
            Dict with expanded_description, assumptions, acceptance_criteria
        """
        story_input = {
            "story_id": story_id,
            "title": title,
            "description": description,
            "epic": epic,
            "feature": feature,
            "priority": priority,
            "requirement_id": requirement_id,
            "technical_requirement": technical_requirement,
            "delivery_phase": delivery_phase
        }

        return self.call_tool("expand_story", story_input)


class SimpleMCPClient:
    """Simplified MCP client - uses Claude Code context instead of subprocess"""

    @staticmethod
    def expand_story(story: Dict) -> Dict:
        """
        Expand story using Claude (simulated for MCP context)

        In actual use with Claude Code, this would use the MCP context
        to call Claude for expansion.
        """
        # This is a placeholder that returns sample expansion
        # In production, this would call actual Claude via MCP
        return {
            "story_id": story.get("story_id"),
            "expanded_description": f"""Based on the story '{story.get('title')}', here's the detailed description.

The {story.get('epic', 'platform')} requires implementation of {story.get('feature', 'this capability')} to support the workflow. This involves configuring the necessary infrastructure components, ensuring proper integration with existing systems, and maintaining compliance with operational requirements.

The implementation includes:
- Configuration of infrastructure components
- Integration with dependent services
- Monitoring and observability setup
- Documentation and training materials""",
            "assumptions": """- Cloud provider is Azure with AKS for orchestration
- Kubernetes version 1.24+
- Network isolation via VPCs or virtual networks
- Minimum 2 replicas for high availability
- 90-day retention for operational data
- Encryption at rest and in transit required""",
            "acceptance_criteria": """1. [ ] Infrastructure component deployed and accessible
2. [ ] Integration tests pass with dependent services
3. [ ] Monitoring dashboards configured and alerting active
4. [ ] Load testing confirms performance targets met
5. [ ] Documentation completed and peer-reviewed
6. [ ] Security scan passes with 0 high/critical findings
7. [ ] Disaster recovery procedure tested
8. [ ] User acceptance testing completed"""
        }


if __name__ == "__main__":
    # Test the MCP client
    print("Testing MCP Client...")

    client = MCPClient("story_expansion_mcp.py")

    try:
        # Start server
        client.start()

        # List tools
        print("\nAvailable tools:")
        tools = client.list_tools()
        print(json.dumps(tools, indent=2))

        # Expand a sample story
        print("\nExpanding sample story...")
        result = client.expand_story(
            story_id="CIP-PA-285",
            title="Kafka Cluster Provisioning",
            epic="Event-Driven Architecture",
            feature="Kafka Infrastructure",
            priority="P0"
        )
        print(json.dumps(result, indent=2))

    finally:
        client.stop()
