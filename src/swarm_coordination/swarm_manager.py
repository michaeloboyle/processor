import asyncio
import time
import yaml
from typing import Dict, Any, List, Tuple
from pathlib import Path
from .models import SwarmConfig, WorkflowResult, TaskResult, ValidationResult
from .agents import (
    DataCollectorAgent, 
    PatternAnalyzerAgent, 
    ProcessorAgent, 
    ValidatorAgent, 
    ReportGeneratorAgent
)
from ..data_collection.models import PropertyRecord, AppealRecord


class SwarmManager:
    
    def __init__(self, config: SwarmConfig = None):
        if config is None:
            self.config = self._load_config_from_yaml()
        else:
            self.config = config
        
        self.active_agents = {}
        self.task_queue = []
        self.completed_tasks = []
        self.workflow_start_time = None
    
    def _load_config_from_yaml(self) -> SwarmConfig:
        """Load configuration from the existing claude-flow/swarm-config.yml"""
        config_path = Path(__file__).parent.parent.parent / "claude-flow" / "swarm-config.yml"
        
        with open(config_path, 'r') as file:
            yaml_config = yaml.safe_load(file)
        
        # Convert YAML config to SwarmConfig
        return SwarmConfig(
            max_agents=yaml_config.get('max_agents', 15),
            topology=yaml_config.get('swarm_topology', 'mesh'),
            coordination_protocol=yaml_config.get('coordination_protocol', 'consensus'),
            processor_agents=yaml_config['specialized_agents']['processor_swarm']['agents'],
            validator_agents=yaml_config['specialized_agents']['validator_consensus']['agents']
        )
    
    async def start_swarm(self):
        """Initialize all agents based on configuration"""
        # Single specialized agents
        self.active_agents['data_collector'] = DataCollectorAgent("collector_001")
        self.active_agents['pattern_analyzer'] = PatternAnalyzerAgent("analyzer_001")
        self.active_agents['report_generator'] = ReportGeneratorAgent("reporter_001")
        
        # Processor swarm (8 agents)
        self.active_agents['processors'] = [
            ProcessorAgent(f"processor_{i:03d}")
            for i in range(1, self.config.processor_agents + 1)
        ]
        
        # Validator consensus (3 agents)
        self.active_agents['validators'] = [
            ValidatorAgent(f"validator_{i:03d}")
            for i in range(1, self.config.validator_agents + 1)
        ]
    
    async def execute_workflow(self) -> WorkflowResult:
        """Execute the complete workflow as defined in claude-flow config"""
        self.workflow_start_time = time.time()
        workflow_id = f"workflow_{int(self.workflow_start_time)}"
        
        try:
            # Following the data flow from swarm-config.yml:
            # collector → analyzer → processor_swarm → validator → reporter
            
            # 1. Data Collection
            property_records, appeal_records = await self._execute_data_collection()
            
            # 2. Pattern Analysis
            patterns = await self._execute_pattern_analysis({
                'property_records': [record.model_dump() for record in property_records],
                'appeal_records': [record.model_dump() for record in appeal_records]
            })
            
            # 3. Parallel Processing (processor swarm)
            processing_results = await self._execute_processing(appeal_records)
            
            # 4. Consensus Validation
            validation_result = await self._execute_validation(processing_results)
            
            # 5. Report Generation
            report = await self._execute_report_generation({
                'property_records': property_records,
                'appeal_records': appeal_records,
                'processing_results': processing_results,
                'validation_result': validation_result,
                'patterns': patterns
            })
            
            execution_time = time.time() - self.workflow_start_time
            
            return WorkflowResult(
                workflow_id=workflow_id,
                success=True,
                total_tasks=len(appeal_records) + 4,  # Appeals + 4 coordination tasks
                completed_tasks=len(appeal_records) + 4,
                failed_tasks=0,
                execution_time=execution_time,
                results={
                    'property_records': len(property_records),
                    'appeal_records': len(appeal_records),
                    'patterns': patterns,
                    'processing_results': len(processing_results),
                    'validation_confidence': validation_result.confidence,
                    'report': report
                }
            )
            
        except Exception as e:
            execution_time = time.time() - self.workflow_start_time
            return WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                total_tasks=0,
                completed_tasks=0,
                failed_tasks=1,
                execution_time=execution_time,
                errors=[str(e)]
            )
    
    async def _execute_data_collection(self) -> Tuple[List[PropertyRecord], List[AppealRecord]]:
        """Execute data collection using the data collector agent"""
        from .models import WorkflowTask
        
        collector = self.active_agents['data_collector']
        task = WorkflowTask(
            task_id="T001_data_collection",
            task_type="data_collection",
            parameters={"source": "lackawanna"}
        )
        
        result = await collector.execute_task(task)
        self.completed_tasks.append(result)
        
        # Convert back to model objects
        property_records = [
            PropertyRecord(**record) 
            for record in result.result.get('property_records', [])
        ]
        appeal_records = [
            AppealRecord(**record) 
            for record in result.result.get('appeal_records', [])
        ]
        
        return property_records, appeal_records
    
    async def _execute_pattern_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pattern analysis using the pattern analyzer agent"""
        from .models import WorkflowTask
        
        analyzer = self.active_agents['pattern_analyzer']
        task = WorkflowTask(
            task_id="T002_pattern_analysis",
            task_type="pattern_analysis",
            parameters={"data": data}
        )
        
        result = await analyzer.execute_task(task)
        self.completed_tasks.append(result)
        
        return result.result
    
    async def _execute_processing(self, appeal_records: List[AppealRecord]) -> List[TaskResult]:
        """Execute parallel processing using the processor swarm"""
        from .models import WorkflowTask
        
        processors = self.active_agents['processors']
        tasks = []
        
        # Distribute appeals across processors
        for i, appeal in enumerate(appeal_records):
            processor = processors[i % len(processors)]
            task = WorkflowTask(
                task_id=f"T003_process_appeal_{i:03d}",
                task_type="process_appeal",
                parameters={"appeal": appeal.model_dump()}
            )
            tasks.append(processor.execute_task(task))
        
        # Execute all processing tasks in parallel
        results = await asyncio.gather(*tasks)
        self.completed_tasks.extend(results)
        
        return results
    
    async def _execute_validation(self, processing_results: List[TaskResult]) -> ValidationResult:
        """Execute consensus validation using validator agents"""
        from .models import WorkflowTask
        
        validators = self.active_agents['validators']
        validation_tasks = []
        
        # All validators validate the same results for consensus
        for i, validator in enumerate(validators):
            task = WorkflowTask(
                task_id=f"T004_validation_{i:03d}",
                task_type="validation",
                parameters={"results": [result.result for result in processing_results]}
            )
            validation_tasks.append(validator.execute_task(task))
        
        # Execute all validations in parallel
        validation_results = await asyncio.gather(*validation_tasks)
        self.completed_tasks.extend(validation_results)
        
        # Calculate consensus
        confidence_scores = [
            result.result['validation_result']['confidence'] 
            for result in validation_results
        ]
        consensus_confidence = sum(confidence_scores) / len(confidence_scores)
        
        return ValidationResult(
            confidence=consensus_confidence,
            validated=consensus_confidence >= 0.7,
            consensus_score=consensus_confidence,
            validator_count=len(validators)
        )
    
    async def _execute_report_generation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report generation using the report generator agent"""
        from .models import WorkflowTask
        
        reporter = self.active_agents['report_generator']
        
        # Generate partial report first (for the "done deal" approach)
        partial_task = WorkflowTask(
            task_id="T005_partial_report",
            task_type="generate_partial_report",
            parameters={"data": {
                "processed_appeals": len(data.get('processing_results', [])),
                "total_appeals": len(data.get('appeal_records', [])),
                "approval_rate": 0.3,  # Mock calculation
                "average_reduction": 15000,  # Mock calculation
                "sample_appeals": data.get('processing_results', [])[:5]
            }}
        )
        
        partial_result = await reporter.execute_task(partial_task)
        self.completed_tasks.append(partial_result)
        
        return {
            'partial_report': partial_result.result,
            'report_status': 'partial_generated'
        }