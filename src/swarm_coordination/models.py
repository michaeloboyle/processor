from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SwarmConfig(BaseModel):
    max_agents: int = Field(default=15, description="Maximum number of agents in swarm")
    topology: str = Field(default="mesh", description="Swarm topology")
    coordination_protocol: str = Field(default="consensus", description="Coordination protocol")
    processor_agents: int = Field(default=8, description="Number of processor agents")
    validator_agents: int = Field(default=3, description="Number of validator agents")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")


class WorkflowTask(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Type of task to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    priority: int = Field(default=1, description="Task priority (1-10)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_agent: Optional[str] = Field(default=None, description="Assigned agent ID")


class TaskResult(BaseModel):
    task_id: str = Field(..., description="Task identifier")
    agent_id: str = Field(..., description="Agent that executed the task")
    status: TaskStatus = Field(..., description="Task completion status")
    result: Dict[str, Any] = Field(default_factory=dict, description="Task result data")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    validated: bool = Field(..., description="Whether validation passed")
    consensus_score: Optional[float] = Field(default=None, description="Consensus score from multiple validators")
    validator_count: int = Field(default=1, description="Number of validators involved")
    details: Dict[str, Any] = Field(default_factory=dict, description="Validation details")


class AgentInfo(BaseModel):
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type of agent")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current agent status")
    current_task: Optional[str] = Field(default=None, description="Currently assigned task ID")
    tasks_completed: int = Field(default=0, description="Number of completed tasks")
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")


class SwarmState(BaseModel):
    active_agents: Dict[str, AgentInfo] = Field(default_factory=dict)
    pending_tasks: List[WorkflowTask] = Field(default_factory=list)
    completed_tasks: List[TaskResult] = Field(default_factory=list)
    failed_tasks: List[TaskResult] = Field(default_factory=list)
    total_processed: int = Field(default=0, description="Total tasks processed")
    success_rate: float = Field(default=0.0, description="Success rate (0.0-1.0)")


class WorkflowResult(BaseModel):
    workflow_id: str = Field(..., description="Workflow identifier")
    success: bool = Field(..., description="Whether workflow completed successfully")
    total_tasks: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    failed_tasks: int = Field(..., description="Number of failed tasks")
    execution_time: float = Field(..., description="Total execution time in seconds")
    results: Dict[str, Any] = Field(default_factory=dict, description="Workflow results")
    errors: List[str] = Field(default_factory=list, description="Error messages")