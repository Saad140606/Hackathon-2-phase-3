"""OpenAI Agent service for natural language task management.

This service initializes and manages the OpenAI Agent for processing user messages
and orchestrating MCP tool calls.
"""

import os
import json
import logging
from typing import Any, Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
import cohere
import re

from src.services.task_service import TaskService

from src.models.conversation import Message
from src.config import settings

logger = logging.getLogger(__name__)


def translate_mcp_error(error_code: str, error_message: str) -> str:
    """Translate MCP error codes to user-friendly messages.

    Args:
        error_code: MCP error code (e.g., AUTHENTICATION_ERROR, AUTHORIZATION_ERROR)
        error_message: Technical error message from MCP

    Returns:
        User-friendly error message without technical codes
    """
    error_code_upper = error_code.upper()

    if "AUTHENTICATION" in error_code_upper or "UNAUTHORIZED" in error_code_upper:
        return "Your authentication token expired. Please log in again."
    elif "AUTHORIZATION" in error_code_upper or "FORBIDDEN" in error_code_upper:
        return "I don't see that task in your list."
    elif "NOT_FOUND" in error_code_upper or "NOT FOUND" in error_code_upper:
        return "I couldn't find the task you're looking for."
    elif "VALIDATION" in error_code_upper or "BAD REQUEST" in error_code_upper:
        return "That doesn't seem right. Can you try again?"
    elif "DATABASE" in error_code_upper or "CONNECTION" in error_code_upper:
        return "I'm having trouble reaching the database. Please try again in a moment."
    else:
        return "Something went wrong. Please try again later."


class AgentService:
    """Service for managing agent interactions with MCP tools.

    Supports OpenAI (legacy) and Cohere providers. When Cohere is used,
    the service sends a text prompt and returns generated text. Tool
    function-calling is not supported with Cohere in this compatibility
    wrapper — tool execution will be skipped and an empty `tool_calls`
    list will be returned.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, mcp_base_url: str = "http://localhost:8001", provider: str = "openai"):
        """Initialize the agent service for the chosen provider.

        Args:
            api_key: Provider API key (OpenAI or Cohere)
            model: Model name for the provider
            mcp_base_url: Base URL for MCP server
            provider: 'openai' or 'cohere'
        """
        logger.debug(f"Initializing AgentService provider={provider} model={model} mcp_base_url={mcp_base_url}")

        self.api_key = api_key
        self.model = model
        self.mcp_base_url = mcp_base_url
        self.provider = provider.lower()

        self.system_prompt = self._build_system_prompt()
        self.tools = self._register_mcp_tools()

        # Initialize provider client
        try:
            if self.provider == "cohere":
                if not self.api_key:
                    raise ValueError("Cohere API key not provided")
                self.client = cohere.Client(self.api_key)
            else:
                # Keep legacy behavior minimal: try to import OpenAI dynamically
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)

            logger.info(f"AgentService initialized for provider={self.provider}")
        except Exception as e:
            logger.error(f"Failed to initialize provider client: {e}", exc_info=True)
            self.client = None

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent.

        Returns:
            System prompt string explaining role, tools, and constraints
        """
        return """You are a friendly and helpful task management assistant. Your role is to help users manage their tasks through natural conversation.

**Available Tools:**
You have access to the following task management tools:

1. **add_task**: Create a new task
   - Parameters: title (required), description (optional)
   - Use when user wants to create, add, or make a new task

2. **list_tasks**: Retrieve user's tasks with optional filtering
   - Parameters: completed (optional boolean), page (optional), page_size (optional)
   - Use when user wants to see, view, list, or show their tasks

3. **complete_task**: Mark a task as completed
   - Parameters: task_id (required)
   - Use when user wants to complete, finish, or mark done a task

4. **update_task**: Modify task details
   - Parameters: task_id (required), title (optional), description (optional), is_completed (optional)
   - Use when user wants to edit, change, or update a task

5. **delete_task**: Permanently remove a task
   - Parameters: task_id (required)
   - Use when user wants to delete, remove, or get rid of a task

**Tool Chaining for Complex Requests:**
You can invoke multiple tools in sequence to handle complex requests:
- When a user asks to "list and delete" or "show and update", chain the tools appropriately
- Pass results from one tool to the next tool when needed
- If one tool fails, inform the user and try an alternative approach
- Example: "List my tasks and delete all completed ones"
  1. Call list_tasks to get the task list
  2. Filter for completed tasks
  3. Call delete_task for each completed task ID
  4. Show the user remaining tasks and confirm deletions

**Important Constraints:**
- You MUST use the tools to perform any task operations - you cannot create/modify/delete tasks directly
- Always confirm actions to the user after tool execution
- If a tool fails, explain the error in user-friendly terms and continue with other operations
- When listing tasks, present them in a clear, readable format
- If you need a task_id to complete/update/delete, first list the tasks to find the correct ID
- For multi-step operations, continue even if one step fails - aggregate all results at the end

**Tone and Style:**
- Be conversational and friendly
- Use natural language, avoid technical jargon
- Anticipate user needs and offer helpful suggestions
- Confirm successful actions clearly
- When handling multiple operations, provide clear summaries (e.g., "Deleted 3 tasks. 7 tasks remaining.")

Example interactions:
- User: "Add a task to buy groceries"
  You: [Use add_task tool] "I've added 'Buy groceries' to your task list!"

- User: "Show me my tasks"
  You: [Use list_tasks tool] "Here are your tasks: [list tasks in readable format]"

- User: "Mark the grocery task as done"
  You: [First list tasks to find ID, then use complete_task] "Great! I've marked 'Buy groceries' as completed."

- User: "List my tasks and delete all completed ones"
  You: [Use list_tasks, then delete_task for each completed task] "I've deleted 3 completed tasks. You have 7 tasks remaining."
"""

    def _register_mcp_tools(self) -> list[dict[str, Any]]:
        """Register MCP tools as OpenAI function definitions.

        Returns:
            List of OpenAI function tool definitions
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_task",
                    "description": "Create a new task for the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Task title (1-255 characters)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional task description"
                            }
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "Retrieve user's tasks with optional filtering and pagination",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "completed": {
                                "type": "boolean",
                                "description": "Filter by completion status (true for completed, false for incomplete, omit for all)"
                            },
                            "page": {
                                "type": "integer",
                                "description": "Page number (default: 1)"
                            },
                            "page_size": {
                                "type": "integer",
                                "description": "Items per page (1-100, default: 20)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_task",
                    "description": "Mark a task as completed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "UUID of the task to mark as complete"
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_task",
                    "description": "Update task title, description, or completion status",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "UUID of the task to update"
                            },
                            "title": {
                                "type": "string",
                                "description": "New task title (1-255 characters)"
                            },
                            "description": {
                                "type": "string",
                                "description": "New task description"
                            },
                            "is_completed": {
                                "type": "boolean",
                                "description": "New completion status"
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_task",
                    "description": "Permanently delete a task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "UUID of the task to delete"
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            }
        ]

    async def _execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        user_id: UUID,
        session: Session
    ) -> Dict[str, Any]:
        """Execute task tool using direct database operations.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            user_id: User ID for isolation
            session: Database session

        Returns:
            Tool execution result as dict
        """
        logger.info(f"Executing tool {tool_name} with parameters: {parameters}")

        try:
            if tool_name == "add_task":
                title = parameters.get("title")
                if not title:
                    raise ValueError("Title is required for add_task")
                description = parameters.get("description")
                task_dict = TaskService.create_task(session, user_id, title, description)
                logger.info(f"Successfully created task for {tool_name}")
                return task_dict

            elif tool_name == "list_tasks":
                completed = parameters.get("completed")
                if isinstance(completed, str):
                    completed = completed.lower() == 'true'
                page = int(parameters.get("page", 1))
                page_size = int(parameters.get("page_size", 20))
                result = TaskService.get_tasks(session, user_id, completed, page, page_size)
                logger.info(f"Successfully listed tasks for {tool_name}")
                return result

            elif tool_name == "complete_task":
                task_id_str = parameters.get("task_id")
                if not task_id_str:
                    raise ValueError("task_id is required for complete_task")
                task_id = UUID(task_id_str)
                result = TaskService.complete_task(session, user_id, task_id)
                logger.info(f"Successfully completed task {task_id} for {tool_name}")
                return result

            elif tool_name == "update_task":
                task_id_str = parameters.get("task_id")
                if not task_id_str:
                    raise ValueError("task_id is required for update_task")
                task_id = UUID(task_id_str)
                title = parameters.get("title")
                description = parameters.get("description")
                is_completed = parameters.get("is_completed")
                if isinstance(is_completed, str):
                    is_completed = is_completed.lower() == 'true'
                result = TaskService.update_task(session, user_id, task_id, title, description, is_completed)
                logger.info(f"Successfully updated task {task_id} for {tool_name}")
                return result

            elif tool_name == "delete_task":
                task_id_str = parameters.get("task_id")
                if not task_id_str:
                    raise ValueError("task_id is required for delete_task")
                task_id = UUID(task_id_str)
                result = TaskService.delete_task(session, user_id, task_id)
                logger.info(f"Successfully deleted task {task_id} for {tool_name}")
                return result

            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Tool execution failed for {tool_name}: {error_msg}")
            return {"success": False, "error": error_msg}

    async def process_user_message(
        self,
        user_message: str,
        conversation_history: list[Message],
        user_id: UUID,
        jwt_token: str,
        session: Session
    ) -> dict[str, Any]:
        """Process user message and invoke tools as needed.

        Args:
            user_message: Users text message
            conversation_history: Previous messages in conversation
            user_id: UUID of the user
            jwt_token: JWT token (unused now)
            session: Database session

        Returns:
            Dictionary with:
                - content: Agents text response
                - tool_calls: List of tool invocations with results
        """
        logger.info(f"Processing message from user {user_id}: {user_message[:100]}...")
        logger.debug(f"Conversation history contains {len(conversation_history)} messages")

        # Build a simple text prompt containing the system prompt, recent history, and the user message.
        prompt_parts = [self.system_prompt]

        # Add recent conversation history (last 10)
        for msg in conversation_history[-10:]:
            role = msg.role.value
            prompt_parts.append(f"{role.capitalize()}: {msg.content}")

        prompt_parts.append(f"User: {user_message}")
        prompt = "\n\n".join(prompt_parts)

        tool_calls_data: list[dict[str, Any]] = []

        # If using Cohere, send the prompt to Cohere generate endpoint and return plain text.
        if self.provider == "cohere":
            if not self.client:
                return {"content": "The AI assistant is temporarily unavailable.", "tool_calls": []}

            try:
                # Try Cohere Chat API (newer SDKs). If unavailable, fall back to generate().
                model_name = self.model or settings.cohere_model
                final_text = ""
                try:
                    # Build chat messages: system + recent history + user
                    chat_messages = [{"role": "system", "content": self.system_prompt}]
                    for msg in conversation_history[-10:]:
                        chat_messages.append({"role": msg.role.value, "content": msg.content})
                    chat_messages.append({"role": "user", "content": user_message})

                    # Prefer Chat API
                    resp = self.client.chat.create(model=model_name, messages=chat_messages, max_tokens=300)

                    # Robust extraction across SDK response shapes
                    if hasattr(resp, "choices") and len(resp.choices) > 0:
                        msg = resp.choices[0].message
                        if isinstance(msg, dict):
                            final_text = msg.get("content") or msg.get("text") or str(msg)
                        else:
                            final_text = getattr(msg, "content", None) or getattr(msg, "text", None) or str(msg)
                    elif hasattr(resp, "message"):
                        m = resp.message
                        final_text = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else None) or str(m)
                    else:
                        final_text = str(resp)

                except Exception:
                    # Fallback to older generate() API for older SDK versions
                    try:
                        resp = self.client.generate(model=model_name, prompt=prompt, max_tokens=300)
                    except TypeError:
                        resp = self.client.generate(model=model_name, inputs=prompt, max_tokens=300)

                    generations = getattr(resp, "generations", None)
                    if generations and len(generations) > 0:
                        gen0 = generations[0]
                        if hasattr(gen0, "text"):
                            final_text = gen0.text
                        elif isinstance(gen0, dict) and "text" in gen0:
                            final_text = gen0["text"]
                        else:
                            final_text = str(gen0)
                    else:
                        final_text = getattr(resp, "text", "") or str(resp)

                final_content = final_text.strip() or "I'm here to help with your tasks!"
                logger.info(f"Cohere response generated for user {user_id}")
                return {"content": final_content, "tool_calls": tool_calls_data}

            except Exception as e:
                logger.error(f"Cohere generate failed: {e}", exc_info=True)

                # Lightweight local fallback: attempt simple rule-based actions so the assistant
                # remains useful if Cohere is temporarily unavailable. This supports basic
                # 'add' and 'list' intents without external AI.
                try:
                    text = user_message.lower()

                    # DELETE intent (prioritized)
                    if re.search(r"\b(delete|remove)\b", text):
                        # Delete completed tasks (bulk)
                        if "completed" in text or "all completed" in text:
                            list_result = await self._execute_tool("list_tasks", {"completed": True}, user_id, session)
                            deleted = []
                            if isinstance(list_result, dict) and list_result.get("tasks"):
                                for t in list_result.get("tasks"):
                                    await self._execute_tool("delete_task", {"task_id": t["id"]}, user_id, session)
                                    deleted.append(t.get("title"))

                            content = f"Deleted {len(deleted)} completed tasks." if deleted else "No completed tasks found to delete."
                            return {"content": content, "tool_calls": [{"tool": "list_tasks", "parameters": {"completed": True}, "result": list_result}]}

                        # Delete by title (simple substring match)
                        m = re.search(r"(?:delete|remove)\s+(?:the\s+)?(.+)", text)
                        if m:
                            target = m.group(1).strip()
                            list_result = await self._execute_tool("list_tasks", {}, user_id, session)
                            found = None
                            if isinstance(list_result, dict) and list_result.get("tasks"):
                                for t in list_result.get("tasks"):
                                    if target in t.get("title", "").lower():
                                        found = t
                                        break

                            if found:
                                del_res = await self._execute_tool("delete_task", {"task_id": found["id"]}, user_id, session)
                                content = f"Deleted '{found.get('title')}'."
                                return {"content": content, "tool_calls": [{"tool": "delete_task", "parameters": {"task_id": found["id"]}, "result": del_res}]}
                            else:
                                return {"content": "I couldn't find a matching task to delete.", "tool_calls": []}

                    # COMPLETE intent
                    if re.search(r"\b(complete|done|finish|mark)\b", text):
                        m = re.search(r"(?:complete|mark)\s+(?:the\s+)?(.+?)(?:\s+as\s+done|$)", text)
                        target = m.group(1).strip() if m else None
                        list_result = await self._execute_tool("list_tasks", {}, user_id, session)
                        found = None
                        if target and isinstance(list_result, dict) and list_result.get("tasks"):
                            for t in list_result.get("tasks"):
                                if target in t.get("title", "").lower():
                                    found = t
                                    break

                        if found:
                            res = await self._execute_tool("complete_task", {"task_id": found["id"]}, user_id, session)
                            return {"content": f"Marked '{found.get('title')}' as completed.", "tool_calls": [{"tool": "complete_task", "parameters": {"task_id": found["id"]}, "result": res}]}
                        else:
                            return {"content": "I couldn't find that task to mark as completed.", "tool_calls": []}

                    # UPDATE / EDIT intent
                    if re.search(r"\b(update|change|edit)\b", text):
                        return {"content": "I can update tasks — please tell me which task and the new title/description.", "tool_calls": []}

                    # ADD intent (fallback if nothing else matched)
                    if re.search(r"\b(add|create|buy|remind me to|remember to)\b", text):
                        title = user_message.strip()
                        # truncate title to 255
                        title = title if len(title) <= 255 else title[:252] + "..."
                        result = await self._execute_tool("add_task", {"title": title}, user_id, session)
                        if result and result.get("id"):
                            content = f"I've added '{result.get('title', title)}' to your task list."
                        else:
                            content = "I created a task for you."

                        return {"content": content, "tool_calls": [{"tool": "add_task", "parameters": {"title": title}, "result": result}]}

                    # List tasks fallback
                    if "list" in text or "show" in text or "my tasks" in text:
                        list_result = await self._execute_tool("list_tasks", {}, user_id, session)
                        content = "Here are your tasks:\n"
                        if isinstance(list_result, dict) and list_result.get("tasks"):
                            for t in list_result.get("tasks"):
                                content += f"- {t.get('title')}\n"
                        else:
                            content += "(no tasks found)"

                        return {"content": content, "tool_calls": [{"tool": "list_tasks", "parameters": {}, "result": list_result}]}

                except Exception:
                    logger.exception("Fallback tool execution failed")

                # Final fallback: user-friendly unavailable message
                return {"content": "The AI assistant is temporarily unavailable.", "tool_calls": []}

        # Legacy OpenAI path (kept minimal for backwards compatibility)
        try:
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            for msg in conversation_history[-10:]:
                messages.append({"role": msg.role.value, "content": msg.content})
            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(model=self.model, messages=messages, tools=self.tools, tool_choice="auto")
            message = response.choices[0].message
            final_content = message.content or "I'm here to help with your tasks!"
            logger.info(f"OpenAI response generated for user {user_id}")
            return {"content": final_content, "tool_calls": []}

        except Exception as e:
            logger.error(f"Agent processing failed: {e}", exc_info=True)
            return {"content": "The AI assistant is temporarily unavailable.", "tool_calls": []}


async def get_agent_service() -> AgentService:
    """Dependency injection for AgentService.

    Returns:
        Configured AgentService instance
    """
    try:
        # Prefer Cohere if configured
        if settings.cohere_api_key:
            return AgentService(api_key=settings.cohere_api_key, model=settings.cohere_model, mcp_base_url=settings.mcp_base_url, provider="cohere")
        else:
            return AgentService(api_key=settings.openai_api_key, model=settings.openai_model, mcp_base_url=settings.mcp_base_url, provider="openai")
    except Exception as e:
        logger.error(f"Failed to initialize AgentService: {e}", exc_info=True)

        class DummyAgentService:
            async def process_user_message(self, *args, **kwargs):
                return {"content": "The AI assistant is temporarily unavailable. Please try again later.", "tool_calls": []}

        return DummyAgentService()
