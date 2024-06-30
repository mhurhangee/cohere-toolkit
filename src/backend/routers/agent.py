from fastapi import APIRouter, Depends, Form, HTTPException, Request

from backend.config.routers import RouterName
from backend.config.tools import ALL_TOOLS
from backend.crud import agent as agent_crud
from backend.crud import agent_tool_metadata as agent_tool_metadata_crud
from backend.database_models.agent import Agent as AgentModel
from backend.database_models.agent_tool_metadata import (
    AgentToolMetadata as AgentToolMetadataModel,
)
from backend.database_models.database import DBSessionDep
from backend.schemas.agent import (
    Agent,
    AgentToolMetadata,
    CreateAgent,
    CreateAgentToolMetadata,
    DeleteAgent,
    DeleteAgentToolMetadata,
    UpdateAgent,
    UpdateAgentToolMetadata,
)
from backend.services.auth.utils import get_header_user_id
from backend.services.request_validators import (
    validate_create_agent_request,
    validate_update_agent_request,
    validate_user_header,
)

router = APIRouter(
    prefix="/v1/agents",
)
router.name = RouterName.AGENT


@router.post(
    "",
    response_model=Agent,
    dependencies=[
        Depends(validate_user_header),
        Depends(validate_create_agent_request),
    ],
)
def create_agent(session: DBSessionDep, agent: CreateAgent, request: Request) -> Agent:
    """
    Create an agent.

    Args:
        session (DBSessionDep): Database session.
        agent (CreateAgent): Agent data.
        request (Request): Request object.

    Returns:
        Agent: Created agent.

    Raises:
        HTTPException: If the agent creation fails.
    """
    user_id = get_header_user_id(request)

    agent_data = AgentModel(
        name=agent.name,
        description=agent.description,
        preamble=agent.preamble,
        temperature=agent.temperature,
        user_id=user_id,
        model=agent.model,
        deployment=agent.deployment,
        tools=agent.tools,
    )

    request.state.agent = agent_data
    try:
        created_agent = agent_crud.create_agent(session, agent_data)
        if agent.tools_metadata:
            for tool_metadata in agent.tools_metadata:
                agent_tool_metadata_data = AgentToolMetadataModel(
                    user_id=user_id,
                    agent_id=created_agent.id,
                    tool_name=tool_metadata.tool_name,
                    artifacts=tool_metadata.artifacts,
                )
                agent_tool_metadata_crud.create_agent_tool_metadata(
                    session, agent_tool_metadata_data
                )
        return created_agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[Agent])
async def list_agents(
    *, offset: int = 0, limit: int = 100, session: DBSessionDep, request: Request
) -> list[Agent]:
    """
    List all agents.

    Args:
        offset (int): Offset to start the list.
        limit (int): Limit of agents to be listed.
        session (DBSessionDep): Database session.
        request (Request): Request object.

    Returns:
        list[Agent]: List of agents.
    """
    try:
        return agent_crud.get_agents(session, offset=offset, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=Agent)
async def get_agent_by_id(
    agent_id: str, session: DBSessionDep, request: Request
) -> Agent:
    """
    Args:
        agent_id (str): Agent ID.
        session (DBSessionDep): Database session.

    Returns:
        Agent: Agent.

    Raises:
        HTTPException: If the agent with the given ID is not found.
    """
    try:
        agent = agent_crud.get_agent_by_id(session, agent_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not agent:
        raise HTTPException(
            status_code=400,
            detail=f"Agent with ID: {agent_id} not found.",
        )

    request.state.agent = agent
    return agent


@router.put(
    "/{agent_id}",
    response_model=Agent,
    dependencies=[
        Depends(validate_user_header),
        Depends(validate_update_agent_request),
    ],
)
async def update_agent(
    agent_id: str,
    new_agent: UpdateAgent,
    session: DBSessionDep,
    request: Request,
) -> Agent:
    """
    Update an agent by ID.

    Args:
        agent_id (str): Agent ID.
        new_agent (UpdateAgent): New agent data.
        session (DBSessionDep): Database session.
        request (Request): Request object.

    Returns:
        Agent: Updated agent.

    Raises:
        HTTPException: If the agent with the given ID is not found.
    """
    agent = agent_crud.get_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(
            status_code=400,
            detail=f"Agent with ID {agent_id} not found.",
        )

    try:
        agent = agent_crud.update_agent(session, agent, new_agent)
        request.state.agent = agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str, session: DBSessionDep, request: Request
) -> DeleteAgent:
    """
    Delete an agent by ID.

    Args:
        agent_id (str): Agent ID.
        session (DBSessionDep): Database session.
        request (Request): Request object.

    Returns:
        DeleteAgent: Empty response.

    Raises:
        HTTPException: If the agent with the given ID is not found.
    """
    agent = agent_crud.get_agent_by_id(session, agent_id)

    if not agent:
        raise HTTPException(
            status_code=400,
            detail=f"Agent with ID {agent_id} not found.",
        )

    request.state.agent = agent
    try:
        agent_crud.delete_agent(session, agent_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return DeleteAgent()


# Tool Metadata Endpoints


@router.get("/{agent_id}/tool-metadata", response_model=list[AgentToolMetadata])
async def list_agent_tool_metadata(
    agent_id: str, session: DBSessionDep, request: Request
) -> list[AgentToolMetadata]:
    """
    List all agent tool metadata by agent ID.

    Args:
        agent_id (str): Agent ID.
        session (DBSessionDep): Database session.
        request (Request): Request object.

    Returns:
        list[AgentToolMetadata]: List of agent tool metadata.

    Raises:
        HTTPException: If the agent tool metadata retrieval fails.
    """
    try:
        return agent_tool_metadata_crud.get_all_agent_tool_metadata_by_agent_id(
            session, agent_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{agent_id}/tool-metadata",
    response_model=AgentToolMetadata,
)
def create_agent_tool_metadata(
    session: DBSessionDep,
    agent_id: str,
    agent_tool_metadata: CreateAgentToolMetadata,
    request: Request,
) -> AgentToolMetadata:
    """
    Create an agent tool metadata.

    Args:
        session (DBSessionDep): Database session.
        agent_id (str): Agent ID.
        agent_tool_metadata (CreateAgentToolMetadata): Agent tool metadata data.
        request (Request): Request object.

    Returns:
        AgentToolMetadata: Created agent tool metadata.

    Raises:
        HTTPException: If the agent tool metadata creation fails.
    """
    user_id = get_header_user_id(request)

    agent_tool_metadata_data = AgentToolMetadataModel(
        user_id=user_id,
        agent_id=agent_id,
        tool_name=agent_tool_metadata.tool_name,
        artifacts=agent_tool_metadata.artifacts,
    )

    request.state.agent_tool_metadata = agent_tool_metadata_data
    try:
        created_agent_tool_metadata = (
            agent_tool_metadata_crud.create_agent_tool_metadata(
                session, agent_tool_metadata_data
            )
        )
        request.state.agent_tool_metadata = agent_tool_metadata_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return created_agent_tool_metadata


@router.put("/{agent_id}/tool-metadata/{agent_tool_metadata_id}")
async def update_agent_tool_metadata(
    agent_id: str,
    agent_tool_metadata_id: str,
    session: DBSessionDep,
    new_agent_tool_metadata: UpdateAgentToolMetadata,
    request: Request,
) -> AgentToolMetadata:
    """
    Update an agent tool metadata by ID.

    Args:
        agent_id (str): Agent ID.
        agent_tool_metadata_id (str): Agent tool metadata ID.
        session (DBSessionDep): Database session.
        new_agent_tool_metadata (UpdateAgentToolMetadata): New agent tool metadata data.
        request (Request): Request object.

    Returns:
        AgentToolMetadata: Updated agent tool metadata.

    Raises:
        HTTPException: If the agent tool metadata with the given ID is not found.
        HTTPException: If the agent tool metadata update fails.
    """
    agent_tool_metadata = agent_tool_metadata_crud.get_agent_tool_metadata_by_id(
        session, agent_tool_metadata_id
    )
    if not agent_tool_metadata:
        raise HTTPException(
            status_code=400,
            detail=f"Agent tool metadata with ID {agent_tool_metadata_id} not found.",
        )

    try:
        agent_tool_metadata_crud.update_agent_tool_metadata(
            session, agent_tool_metadata, new_agent_tool_metadata
        )
        request.state.agent_tool_metadata = agent_tool_metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return agent_tool_metadata


@router.delete("/{agent_id}/tool-metadata/{agent_tool_metadata_id}")
async def delete_agent_tool_metadata(
    agent_id: str, agent_tool_metadata_id: str, session: DBSessionDep, request: Request
) -> DeleteAgentToolMetadata:
    """
    Delete an agent tool metadata by ID.

    Args:
        agent_id (str): Agent ID.
        agent_tool_metadata_id (str): Agent tool metadata ID.
        session (DBSessionDep): Database session.
        request (Request): Request object.

    Returns:
        DeleteAgentToolMetadata: Empty response.

    Raises:
        HTTPException: If the agent tool metadata with the given ID is not found.
        HTTPException: If the agent tool metadata deletion fails.
    """
    agent_tool_metadata = agent_tool_metadata_crud.get_agent_tool_metadata_by_id(
        session, agent_tool_metadata_id
    )
    if not agent_tool_metadata:
        raise HTTPException(
            status_code=400,
            detail=f"Agent tool metadata with ID {agent_tool_metadata_id} not found.",
        )

    request.state.agent_tool_metadata = agent_tool_metadata
    try:
        agent_tool_metadata_crud.delete_agent_tool_metadata_by_id(
            session, agent_tool_metadata_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return DeleteAgentToolMetadata()
