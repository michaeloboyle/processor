import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
from src.data_collection.web_scraper import LackawannaDataCollector
from src.data_collection.models import PropertyRecord, AppealRecord


class TestLackawannaDataCollector:
    
    @pytest.fixture
    def collector(self):
        return LackawannaDataCollector()
    
    @pytest.fixture
    def sample_property_data(self):
        return {
            'property_id': '12-345-67',
            'address': '123 Main St, Scranton, PA',
            'assessed_value': 125000,
            'market_value': 150000,
            'owner_name': 'John Doe',
            'property_type': 'Residential'
        }
    
    @pytest.fixture
    def sample_appeal_data(self):
        return {
            'appeal_id': 'AP-2024-001',
            'property_id': '12-345-67',
            'appeal_date': '2024-01-15',
            'status': 'Pending',
            'requested_value': 100000,
            'reason': 'Overassessment'
        }
    
    def test_collector_initialization(self, collector):
        assert collector.base_url == "https://lcao.lackawannacounty.org"
        assert collector.session_limit == 50
        assert collector.request_delay >= 2
        assert collector.request_delay <= 5
    
    @pytest.mark.asyncio
    async def test_fetch_property_data_success(self, collector, sample_property_data):
        with patch.object(collector, '_make_request') as mock_request:
            mock_request.return_value = sample_property_data
            
            result = await collector.fetch_property_data('12-345-67')
            
            assert isinstance(result, PropertyRecord)
            assert result.property_id == '12-345-67'
            assert result.assessed_value == 125000
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_appeals_data_success(self, collector, sample_appeal_data):
        with patch.object(collector, '_make_request') as mock_request:
            mock_request.return_value = [sample_appeal_data]
            
            result = await collector.fetch_appeals_data()
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], AppealRecord)
            assert result[0].appeal_id == 'AP-2024-001'
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, collector):
        with patch('asyncio.sleep') as mock_sleep:
            await collector._apply_rate_limiting()
            mock_sleep.assert_called_once()
            delay = mock_sleep.call_args[0][0]
            assert 2 <= delay <= 5
    
    @pytest.mark.asyncio
    async def test_session_limit_enforcement(self, collector):
        collector.request_count = 50
        
        with pytest.raises(Exception, match="Session request limit reached"):
            await collector._make_request('/test')
    
    @pytest.mark.asyncio
    async def test_anti_detection_measures(self, collector):
        with patch.object(collector, 'page') as mock_page:
            mock_page.set_user_agent = AsyncMock()
            mock_page.set_viewport = AsyncMock()
            mock_page.set_extra_http_headers = AsyncMock()
            
            await collector._setup_anti_detection()
            
            mock_page.set_user_agent.assert_called_once()
            mock_page.set_viewport.assert_called_once()
            mock_page.set_extra_http_headers.assert_called_once()
    
    def test_data_validation_property_record(self, sample_property_data):
        record = PropertyRecord(**sample_property_data)
        assert record.property_id == '12-345-67'
        assert record.assessed_value == 125000
    
    def test_data_validation_appeal_record(self, sample_appeal_data):
        record = AppealRecord(**sample_appeal_data)
        assert record.appeal_id == 'AP-2024-001'
        assert record.property_id == '12-345-67'
    
    @pytest.mark.asyncio
    async def test_batch_collection(self, collector):
        property_ids = ['12-345-67', '12-345-68', '12-345-69']
        
        with patch.object(collector, 'fetch_property_data') as mock_fetch:
            mock_fetch.return_value = PropertyRecord(
                property_id='test',
                address='test',
                assessed_value=100000,
                market_value=120000,
                owner_name='test',
                property_type='Residential'
            )
            
            results = await collector.collect_batch(property_ids)
            
            assert len(results) == 3
            assert mock_fetch.call_count == 3
    
    @pytest.mark.asyncio
    async def test_error_handling_network_failure(self, collector):
        with patch.object(collector, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Network error")
            
            with pytest.raises(Exception, match="Network error"):
                await collector.fetch_property_data('12-345-67')
    
    def test_data_export_to_dataframe(self, collector, sample_property_data):
        records = [PropertyRecord(**sample_property_data)]
        df = collector.to_dataframe(records)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert 'property_id' in df.columns
        assert df.iloc[0]['property_id'] == '12-345-67'