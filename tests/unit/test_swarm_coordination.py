import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.swarm_coordination.swarm_manager import SwarmManager
from src.swarm_coordination.agents import (
    DataCollectorAgent, 
    PatternAnalyzerAgent, 
    ProcessorAgent, 
    ValidatorAgent, 
    ReportGeneratorAgent
)
from src.swarm_coordination.models import (
    SwarmConfig, 
    TaskResult, 
    AgentStatus, 
    WorkflowTask,
    ValidationResult
)
from src.data_collection.models import PropertyRecord, AppealRecord


class TestSwarmManager:
    
    @pytest.fixture
    def swarm_config(self):
        return SwarmConfig(
            max_agents=15,
            topology="mesh",
            coordination_protocol="consensus",
            processor_agents=8,
            validator_agents=3
        )
    
    @pytest.fixture
    def swarm_manager(self, swarm_config):
        return SwarmManager(swarm_config)
    
    @pytest.fixture
    def sample_property_records(self):
        return [
            PropertyRecord(
                property_id="12-345-67",
                address="123 Main St",
                assessed_value=125000,
                market_value=150000,
                owner_name="John Doe",
                property_type="Residential"
            ),
            PropertyRecord(
                property_id="12-345-68",
                address="456 Oak Ave",
                assessed_value=200000,
                market_value=220000,
                owner_name="Jane Smith",
                property_type="Residential"
            )
        ]
    
    @pytest.fixture
    def sample_appeal_records(self):
        return [
            AppealRecord(
                appeal_id="AP-2024-001",
                property_id="12-345-67",
                appeal_date="2024-01-15",
                status="Pending",
                requested_value=100000,
                reason="Overassessment"
            )
        ]
    
    def test_swarm_manager_initialization(self, swarm_manager, swarm_config):
        assert swarm_manager.config == swarm_config
        assert swarm_manager.active_agents == {}
        assert swarm_manager.task_queue == []
        assert swarm_manager.completed_tasks == []
    
    @pytest.mark.asyncio
    async def test_start_swarm(self, swarm_manager):
        await swarm_manager.start_swarm()
        
        assert len(swarm_manager.active_agents) == 5  # 5 types of agents
        assert 'data_collector' in swarm_manager.active_agents
        assert 'pattern_analyzer' in swarm_manager.active_agents
        assert 'processors' in swarm_manager.active_agents
        assert 'validators' in swarm_manager.active_agents
        assert 'report_generator' in swarm_manager.active_agents
        
        # Check processor swarm has 8 agents
        assert len(swarm_manager.active_agents['processors']) == 8
        # Check validator consensus has 3 agents
        assert len(swarm_manager.active_agents['validators']) == 3
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, swarm_manager, sample_property_records, sample_appeal_records):
        with patch.object(swarm_manager, '_execute_data_collection') as mock_collection:
            with patch.object(swarm_manager, '_execute_pattern_analysis') as mock_analysis:
                with patch.object(swarm_manager, '_execute_processing') as mock_processing:
                    with patch.object(swarm_manager, '_execute_validation') as mock_validation:
                        with patch.object(swarm_manager, '_execute_report_generation') as mock_report:
                            
                            mock_collection.return_value = (sample_property_records, sample_appeal_records)
                            mock_analysis.return_value = {'patterns': ['overassessment_trend']}
                            mock_processing.return_value = [TaskResult(task_id='1', agent_id='processor_001', status='completed', result={})]
                            mock_validation.return_value = ValidationResult(confidence=0.95, validated=True)
                            mock_report.return_value = {'report_id': 'R001', 'status': 'generated'}
                            
                            result = await swarm_manager.execute_workflow()
                            
                            assert result.success == True
                            mock_collection.assert_called_once()
                            mock_analysis.assert_called_once()
                            mock_processing.assert_called_once()
                            mock_validation.assert_called_once()
                            mock_report.assert_called_once()


class TestDataCollectorAgent:
    
    @pytest.fixture
    def agent(self):
        return DataCollectorAgent(agent_id="collector_001")
    
    @pytest.mark.asyncio
    async def test_collect_data_task(self, agent):
        with patch.object(agent, '_scrape_property_data') as mock_scrape:
            mock_scrape.return_value = [
                PropertyRecord(
                    property_id="12-345-67",
                    address="123 Main St",
                    assessed_value=125000,
                    market_value=150000,
                    owner_name="John Doe",
                    property_type="Residential"
                )
            ]
            
            result = await agent.execute_task(WorkflowTask(
                task_id="T001",
                task_type="data_collection",
                parameters={"source": "lackawanna"}
            ))
            
            assert result.status == "completed"
            assert "property_records" in result.result
            mock_scrape.assert_called_once()


class TestPatternAnalyzerAgent:
    
    @pytest.fixture
    def agent(self):
        return PatternAnalyzerAgent(agent_id="analyzer_001")
    
    @pytest.fixture
    def sample_data(self):
        return {
            'property_records': [
                {'assessed_value': 125000, 'market_value': 150000, 'property_type': 'Residential'},
                {'assessed_value': 200000, 'market_value': 220000, 'property_type': 'Residential'},
                {'assessed_value': 300000, 'market_value': 280000, 'property_type': 'Commercial'}
            ],
            'appeal_records': [
                {'reason': 'Overassessment', 'requested_value': 100000, 'status': 'Pending'},
                {'reason': 'Overassessment', 'requested_value': 180000, 'status': 'Approved'}
            ]
        }
    
    @pytest.mark.asyncio
    async def test_pattern_analysis(self, agent, sample_data):
        result = await agent.execute_task(WorkflowTask(
            task_id="T002",
            task_type="pattern_analysis",
            parameters={"data": sample_data}
        ))
        
        assert result.status == "completed"
        assert "patterns" in result.result
        assert "statistics" in result.result


class TestProcessorAgent:
    
    @pytest.fixture
    def agent(self):
        return ProcessorAgent(agent_id="processor_001")
    
    @pytest.mark.asyncio
    async def test_process_appeal(self, agent):
        appeal_data = {
            'appeal_id': 'AP-2024-001',
            'property_id': '12-345-67',
            'assessed_value': 125000,
            'market_value': 150000,
            'requested_value': 100000,
            'reason': 'Overassessment'
        }
        
        result = await agent.execute_task(WorkflowTask(
            task_id="T003",
            task_type="process_appeal",
            parameters={"appeal": appeal_data}
        ))
        
        assert result.status == "completed"
        assert "recommendation" in result.result
        assert "confidence_score" in result.result


class TestValidatorAgent:
    
    @pytest.fixture
    def agent(self):
        return ValidatorAgent(agent_id="validator_001")
    
    @pytest.mark.asyncio
    async def test_validate_results(self, agent):
        processing_results = [
            {'appeal_id': 'AP-2024-001', 'recommendation': 'Approve reduction', 'confidence_score': 0.85},
            {'appeal_id': 'AP-2024-002', 'recommendation': 'Deny appeal', 'confidence_score': 0.92}
        ]
        
        result = await agent.execute_task(WorkflowTask(
            task_id="T004",
            task_type="validation",
            parameters={"results": processing_results}
        ))
        
        assert result.status == "completed"
        assert "validation_result" in result.result
        assert result.result["validation_result"]["confidence"] >= 0.0
        assert result.result["validation_result"]["confidence"] <= 1.0


class TestReportGeneratorAgent:
    
    @pytest.fixture
    def agent(self):
        return ReportGeneratorAgent(agent_id="reporter_001")
    
    @pytest.mark.asyncio
    async def test_generate_partial_report(self, agent):
        validated_results = {
            'processed_appeals': 10,
            'total_appeals': 100,
            'approval_rate': 0.3,
            'average_reduction': 15000,
            'sample_appeals': [
                {'appeal_id': 'AP-2024-001', 'recommendation': 'Approve reduction'},
                {'appeal_id': 'AP-2024-002', 'recommendation': 'Deny appeal'}
            ]
        }
        
        result = await agent.execute_task(WorkflowTask(
            task_id="T005",
            task_type="generate_partial_report",
            parameters={"data": validated_results}
        ))
        
        assert result.status == "completed"
        assert "report" in result.result
        assert "report_type" in result.result
        assert result.result["report_type"] == "partial"
    
    @pytest.mark.asyncio
    async def test_generate_complete_report(self, agent):
        all_results = {
            'processed_appeals': 100,
            'total_appeals': 100,
            'detailed_recommendations': [{'appeal_id': f'AP-2024-{i:03d}'} for i in range(1, 101)]
        }
        
        result = await agent.execute_task(WorkflowTask(
            task_id="T006",
            task_type="generate_complete_report",
            parameters={"data": all_results}
        ))
        
        assert result.status == "completed"
        assert "report" in result.result
        assert "report_type" in result.result
        assert result.result["report_type"] == "complete"


class TestSwarmCoordination:
    
    @pytest.mark.asyncio
    async def test_consensus_mechanism(self):
        validators = [ValidatorAgent(f"validator_{i}") for i in range(3)]
        
        test_data = {'appeal_id': 'AP-2024-001', 'recommendation': 'Approve reduction'}
        
        results = []
        for validator in validators:
            result = await validator.execute_task(WorkflowTask(
                task_id=f"T00{validators.index(validator) + 1}",
                task_type="validation",
                parameters={"results": [test_data]}
            ))
            results.append(result.result["validation_result"]["confidence"])
        
        # Test consensus: average confidence should be reasonable
        average_confidence = sum(results) / len(results)
        assert 0.0 <= average_confidence <= 1.0
        
        # Test that all validators provided results
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_parallel_processing(self):
        processors = [ProcessorAgent(f"processor_{i}") for i in range(8)]
        
        appeals = [
            {
                'appeal_id': f'AP-2024-{i:03d}', 
                'property_id': f'12-345-{i:02d}',
                'assessed_value': 100000,
                'market_value': 120000,
                'requested_value': 90000,
                'reason': 'Overassessment'
            }
            for i in range(1, 9)
        ]
        
        # Simulate parallel processing
        tasks = []
        for i, (processor, appeal) in enumerate(zip(processors, appeals)):
            task = processor.execute_task(WorkflowTask(
                task_id=f"T{i:03d}",
                task_type="process_appeal",
                parameters={"appeal": appeal}
            ))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All processors should complete their tasks
        assert len(results) == 8
        assert all(result.status == "completed" for result in results)