import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.report_generation.report_generator import UniversalReportGenerator
from src.report_generation.models import ReportConfig, ReportData, ReportResult
from src.data_collection.models import PropertyRecord, AppealRecord


class TestUniversalReportGenerator:
    
    @pytest.fixture
    def report_config(self):
        return ReportConfig(
            report_type="lackawanna_appeals",
            output_format="html",
            include_charts=True,
            include_statistics=True,
            template="professional"
        )
    
    @pytest.fixture
    def sample_data(self):
        property_records = [
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
        
        appeal_records = [
            AppealRecord(
                appeal_id="AP-2024-001",
                property_id="12-345-67",
                appeal_date="2024-01-15",
                status="Pending",
                requested_value=100000,
                reason="Overassessment"
            ),
            AppealRecord(
                appeal_id="AP-2024-002",
                property_id="12-345-68",
                appeal_date="2024-01-20",
                status="Approved",
                requested_value=180000,
                reason="Overassessment"
            )
        ]
        
        processing_results = [
            {
                "appeal_id": "AP-2024-001",
                "recommendation": "Approve reduction",
                "confidence_score": 0.85,
                "estimated_value": 110000,
                "reasoning": "Assessment appears inflated"
            },
            {
                "appeal_id": "AP-2024-002",
                "recommendation": "Partial reduction",
                "confidence_score": 0.75,
                "estimated_value": 190000,
                "reasoning": "Moderate adjustment warranted"
            }
        ]
        
        return ReportData(
            property_records=property_records,
            appeal_records=appeal_records,
            processing_results=processing_results,
            patterns=["overassessment_trend", "residential_focus"],
            statistics={
                "total_appeals": 2,
                "approval_rate": 0.5,
                "average_reduction": 12500
            }
        )
    
    @pytest.fixture
    def generator(self, report_config):
        return UniversalReportGenerator(report_config)
    
    def test_generator_initialization(self, generator, report_config):
        assert generator.config == report_config
        assert generator.templates is not None
        assert generator.formatters is not None
    
    def test_generate_partial_report(self, generator, sample_data):
        result = generator.generate_partial_report(sample_data)
        
        assert isinstance(result, ReportResult)
        assert result.report_type == "partial"
        assert result.success == True
        assert "executive_summary" in result.content
        assert "sample_results" in result.content
        assert "teaser_message" in result.content
        
        # Should contain limited sample data
        assert len(result.content["sample_results"]) <= 5
    
    def test_generate_complete_report(self, generator, sample_data):
        result = generator.generate_complete_report(sample_data)
        
        assert isinstance(result, ReportResult)
        assert result.report_type == "complete"
        assert result.success == True
        assert "executive_summary" in result.content
        assert "detailed_analysis" in result.content
        assert "all_recommendations" in result.content
        assert "methodology" in result.content
        
        # Should contain all data
        assert len(result.content["all_recommendations"]) == 2
    
    def test_html_formatting(self, generator, sample_data):
        generator.config.output_format = "html"
        result = generator.generate_complete_report(sample_data)
        
        assert result.format == "html"
        assert "<html>" in result.formatted_content
        assert "<body>" in result.formatted_content
        assert "Lackawanna County" in result.formatted_content
    
    def test_pdf_formatting(self, generator, sample_data):
        generator.config.output_format = "pdf"
        result = generator.generate_complete_report(sample_data)
        
        assert result.format == "pdf"
        assert result.formatted_content is not None
    
    def test_json_formatting(self, generator, sample_data):
        generator.config.output_format = "json"
        result = generator.generate_complete_report(sample_data)
        
        assert result.format == "json"
        assert '"report_type"' in result.formatted_content
        assert '"executive_summary"' in result.formatted_content
    
    def test_statistics_calculation(self, generator, sample_data):
        stats = generator._calculate_statistics(sample_data)
        
        assert "total_properties" in stats
        assert "total_appeals" in stats
        assert "appeal_rate" in stats
        assert "approval_rate" in stats
        assert "average_assessed_value" in stats
        assert "estimated_total_savings" in stats
        
        assert stats["total_properties"] == 2
        assert stats["total_appeals"] == 2
        assert stats["appeal_rate"] == 1.0  # 2 appeals / 2 properties
    
    def test_chart_generation(self, generator, sample_data):
        generator.config.include_charts = True
        charts = generator._generate_charts(sample_data)
        
        assert "appeal_status_distribution" in charts
        assert "recommendation_distribution" in charts
        assert "value_comparison" in charts
        
        # Charts should contain data
        assert charts["appeal_status_distribution"]["data"] is not None
    
    def test_executive_summary_generation(self, generator, sample_data):
        summary = generator._generate_executive_summary(sample_data, "complete")
        
        assert "key_findings" in summary
        assert "total_processed" in summary
        assert "recommendations_generated" in summary
        assert "estimated_savings" in summary
        assert "confidence_level" in summary
        
        assert summary["total_processed"] == 2
        assert summary["recommendations_generated"] == 2
    
    def test_teaser_message_generation(self, generator, sample_data):
        teaser = generator._generate_teaser_message(sample_data)
        
        assert "complete_analysis_available" in teaser
        assert "sample_size" in teaser
        assert "total_potential" in teaser
        assert "next_steps" in teaser
        
        assert "contact us" in teaser["next_steps"].lower()
    
    def test_methodology_section(self, generator, sample_data):
        methodology = generator._generate_methodology_section()
        
        assert "data_sources" in methodology
        assert "processing_approach" in methodology
        assert "validation_process" in methodology
        assert "agent_coordination" in methodology
        
        assert "Claude agent swarms" in methodology["processing_approach"]
    
    def test_error_handling_invalid_data(self, generator):
        with pytest.raises(ValueError, match="ReportData is required"):
            generator.generate_partial_report(None)
    
    def test_error_handling_unsupported_format(self, generator, sample_data):
        generator.config.output_format = "unsupported"
        result = generator.generate_partial_report(sample_data)
        
        assert result.success == False
        assert "Unsupported format" in result.error_message
    
    def test_template_customization(self, generator, sample_data):
        generator.config.template = "municipal"
        result = generator.generate_partial_report(sample_data)
        
        assert result.success == True
        assert "municipal" in result.content.get("template_applied", "")
    
    def test_multi_format_export(self, generator, sample_data):
        formats = ["html", "json", "pdf"]
        results = []
        
        for fmt in formats:
            generator.config.output_format = fmt
            result = generator.generate_partial_report(sample_data)
            results.append(result)
        
        # All formats should be generated successfully
        assert all(result.success for result in results)
        assert len(set(result.format for result in results)) == 3
    
    def test_performance_metrics(self, generator, sample_data):
        start_time = datetime.utcnow()
        result = generator.generate_complete_report(sample_data)
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        assert result.success == True
        assert generation_time < 1.0  # Should generate quickly for test data
        assert "generation_time" in result.metadata
    
    def test_report_validation(self, generator, sample_data):
        result = generator.generate_complete_report(sample_data)
        
        # Validate report structure
        assert generator._validate_report_structure(result.content)
        
        # Validate data consistency
        assert generator._validate_data_consistency(result.content, sample_data)
    
    def test_incremental_report_updates(self, generator, sample_data):
        # Generate initial partial report
        partial_result = generator.generate_partial_report(sample_data)
        
        # Add more data
        new_appeal = AppealRecord(
            appeal_id="AP-2024-003",
            property_id="12-345-69",
            appeal_date="2024-01-25",
            status="Pending",
            requested_value=150000,
            reason="Overassessment"
        )
        sample_data.appeal_records.append(new_appeal)
        
        # Generate updated report
        updated_result = generator.generate_partial_report(sample_data)
        
        assert updated_result.content["statistics"]["total_appeals"] == 3
        assert updated_result.content["statistics"]["total_appeals"] > partial_result.content["statistics"]["total_appeals"]