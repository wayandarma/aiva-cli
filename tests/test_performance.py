#!/usr/bin/env python3
"""
Performance Tests for AIVA CLI

Tests performance characteristics including generation times,
API rate limits, bottleneck identification, and concurrent usage.
"""

import pytest
import sys
import time
import asyncio
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the aiva_cli directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'aiva_cli'))

from core.pipeline import generate_content
from models.text_model import generate_text
from models.image_model import generate_image


class TestPerformance:
    """Performance test cases for AIVA CLI."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for performance testing."""
        config = Mock()
        config.gemini_api_key = "test_api_key"
        config.models = Mock()
        config.models.text_model = "gemini-1.5-flash"
        config.models.image_model = "imagen-3.0-generate-001"
        config.models.temperature = 0.7
        config.models.max_tokens = 2048
        config.models.timeout = 30
        config.script_length = 300
        config.segment_duration = 8
        config.max_retries = 3
        config.output_dir = "test_output"
        config.model_dump.return_value = {
            "gemini_api_key": "test_api_key",
            "models": {
                "text_model": "gemini-1.5-flash",
                "image_model": "imagen-3.0-generate-001",
                "temperature": 0.7,
                "max_tokens": 2048,
                "timeout": 30
            },
            "script_length": 300,
            "segment_duration": 8,
            "max_retries": 3,
            "output_dir": "test_output"
        }
        return config
    
    @pytest.fixture
    def performance_agents(self):
        """Mock agents with realistic timing delays."""
        def slow_script_agent():
            time.sleep(0.1)  # Simulate API call
            return Mock(raw="Generated script")
        
        def slow_segmenter_agent():
            time.sleep(0.05)  # Simulate processing
            return Mock(raw="Segmented content")
        
        def slow_prompt_agent():
            time.sleep(0.2)  # Simulate prompt generation
            return Mock(raw="Generated prompts")
        
        def slow_image_agent():
            time.sleep(0.3)  # Simulate image generation
            return Mock(raw="Generated images")
        
        return {
            'script_agent': Mock(side_effect=slow_script_agent),
            'segmenter_agent': Mock(side_effect=slow_segmenter_agent),
            'prompt_gen_agent': Mock(side_effect=slow_prompt_agent),
            'image_render_agent': Mock(side_effect=slow_image_agent)
        }
    
    @patch('core.pipeline.Crew')
    @patch('core.pipeline.create_agents')
    @patch('core.pipeline.create_tasks')
    @patch('core.pipeline.os.makedirs')
    @patch('core.pipeline.json.dump')
    def test_generation_time_measurement(self, mock_json_dump, mock_makedirs,
                                       mock_create_tasks, mock_create_agents,
                                       mock_crew_class, mock_config, performance_agents):
        """Test measurement of content generation times."""
        mock_create_agents.return_value = performance_agents
        mock_create_tasks.return_value = [Mock() for _ in range(4)]
        
        mock_crew = Mock()
        mock_crew_class.return_value = mock_crew
        
        # Simulate realistic execution time
        def slow_kickoff():
            time.sleep(0.5)  # Simulate total processing time
            return Mock(
                raw="Timed generation completed",
                tasks_output=[Mock(raw="Output") for _ in range(4)]
            )
        
        mock_crew.kickoff.side_effect = slow_kickoff
        
        # Measure execution time
        start_time = time.time()
        
        result = generate_content(
            topic="Performance Test",
            video_type="educational",
            out_dir="test_output",
            config=mock_config
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify execution completed
        assert result is not None
        
        # Verify timing is reasonable (should be > 0.5s due to mock delays)
        assert execution_time >= 0.5
        assert execution_time < 10.0  # Should not take too long in test
        
        print(f"Generation time: {execution_time:.2f} seconds")
    
    def test_text_model_performance(self, mock_config):
        """Test text model performance characteristics."""
        with patch('models.text_model.genai') as mock_genai:
            # Mock model with timing
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            def timed_generate(prompt):
                time.sleep(0.1)  # Simulate API latency
                mock_response = Mock()
                mock_response.text = "Generated text response"
                return mock_response
            
            mock_model.generate_content.side_effect = timed_generate
            
            # Test multiple generations
            prompts = [
                "Generate a script about AI",
                "Create content about space",
                "Write about technology"
            ]
            
            times = []
            for prompt in prompts:
                start_time = time.time()
                
                result = generate_text(prompt, mock_config)
                
                end_time = time.time()
                times.append(end_time - start_time)
                
                assert result is not None
            
            # Verify consistent timing
            avg_time = sum(times) / len(times)
            assert avg_time >= 0.1  # At least our mock delay
            assert avg_time < 1.0   # Should not be too slow
            
            print(f"Average text generation time: {avg_time:.3f} seconds")
    
    def test_image_model_performance(self, mock_config):
        """Test image model performance characteristics."""
        with patch('models.image_model.genai') as mock_genai:
            # Mock model with timing
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            def timed_generate_image(prompt):
                time.sleep(0.2)  # Simulate longer image generation
                mock_response = Mock()
                mock_response.candidates = [Mock()]
                mock_response.candidates[0].content = Mock()
                mock_response.candidates[0].content.parts = [Mock()]
                mock_response.candidates[0].content.parts[0].inline_data = Mock()
                mock_response.candidates[0].content.parts[0].inline_data.data = b"fake_image_data"
                return mock_response
            
            mock_model.generate_content.side_effect = timed_generate_image
            
            # Test image generation timing
            start_time = time.time()
            
            with patch('builtins.open', create=True), \
                 patch('models.image_model.base64.b64decode', return_value=b"decoded_data"):
                
                result = generate_image(
                    "A futuristic AI laboratory",
                    "test_output.png",
                    mock_config
                )
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            assert result is not None
            assert generation_time >= 0.2  # At least our mock delay
            
            print(f"Image generation time: {generation_time:.3f} seconds")
    
    @patch('core.pipeline.Crew')
    @patch('core.pipeline.create_agents')
    @patch('core.pipeline.create_tasks')
    @patch('core.pipeline.os.makedirs')
    @patch('core.pipeline.json.dump')
    def test_concurrent_generation_performance(self, mock_json_dump, mock_makedirs,
                                             mock_create_tasks, mock_create_agents,
                                             mock_crew_class, mock_config):
        """Test performance under concurrent usage."""
        mock_agents = {
            'script_agent': Mock(),
            'segmenter_agent': Mock(),
            'prompt_gen_agent': Mock(),
            'image_render_agent': Mock()
        }
        mock_create_agents.return_value = mock_agents
        mock_create_tasks.return_value = [Mock() for _ in range(4)]
        
        mock_crew = Mock()
        mock_crew_class.return_value = mock_crew
        
        def concurrent_kickoff():
            time.sleep(0.1)  # Simulate processing
            return Mock(
                raw="Concurrent generation completed",
                tasks_output=[Mock(raw="Output") for _ in range(4)]
            )
        
        mock_crew.kickoff.side_effect = concurrent_kickoff
        
        # Test concurrent executions
        topics = ["AI", "Space", "Technology", "Science", "Future"]
        
        def generate_single(topic):
            return generate_content(
                topic=topic,
                video_type="educational",
                out_dir="test_output",
                config=mock_config
            )
        
        start_time = time.time()
        
        # Run concurrent generations
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(generate_single, topic) for topic in topics]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all completed
        assert len(results) == len(topics)
        assert all(result is not None for result in results)
        
        # Concurrent execution should be faster than sequential
        sequential_time_estimate = len(topics) * 0.1  # 0.1s per generation
        assert total_time < sequential_time_estimate * 1.5  # Allow some overhead
        
        print(f"Concurrent generation time: {total_time:.3f} seconds for {len(topics)} topics")
    
    def test_api_rate_limit_simulation(self, mock_config):
        """Test behavior under simulated API rate limits."""
        with patch('models.text_model.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            call_count = 0
            
            def rate_limited_generate(prompt):
                nonlocal call_count
                call_count += 1
                
                if call_count <= 2:
                    # First few calls succeed quickly
                    time.sleep(0.05)
                    mock_response = Mock()
                    mock_response.text = f"Response {call_count}"
                    return mock_response
                else:
                    # Later calls are rate limited
                    time.sleep(0.5)  # Simulate rate limit delay
                    mock_response = Mock()
                    mock_response.text = f"Rate limited response {call_count}"
                    return mock_response
            
            mock_model.generate_content.side_effect = rate_limited_generate
            
            # Test multiple rapid calls
            times = []
            for i in range(5):
                start_time = time.time()
                
                result = generate_text(f"Prompt {i}", mock_config)
                
                end_time = time.time()
                times.append(end_time - start_time)
                
                assert result is not None
            
            # Verify rate limiting effect
            early_times = times[:2]
            later_times = times[2:]
            
            avg_early = sum(early_times) / len(early_times)
            avg_later = sum(later_times) / len(later_times)
            
            # Later calls should be significantly slower
            assert avg_later > avg_early * 5
            
            print(f"Early calls avg: {avg_early:.3f}s, Later calls avg: {avg_later:.3f}s")
    
    @patch('core.pipeline.Crew')
    @patch('core.pipeline.create_agents')
    @patch('core.pipeline.create_tasks')
    def test_bottleneck_identification(self, mock_create_tasks, mock_create_agents,
                                     mock_crew_class, mock_config):
        """Test identification of performance bottlenecks."""
        # Create agents with different performance characteristics
        fast_agent = Mock()
        slow_agent = Mock()
        
        def fast_operation():
            time.sleep(0.01)
            return Mock(raw="Fast result")
        
        def slow_operation():
            time.sleep(0.3)  # Bottleneck
            return Mock(raw="Slow result")
        
        mock_agents = {
            'script_agent': fast_agent,
            'segmenter_agent': fast_agent,
            'prompt_gen_agent': fast_agent,
            'image_render_agent': slow_agent  # This is the bottleneck
        }
        
        mock_create_agents.return_value = mock_agents
        mock_create_tasks.return_value = [Mock() for _ in range(4)]
        
        mock_crew = Mock()
        mock_crew_class.return_value = mock_crew
        
        # Simulate crew execution with bottleneck
        def bottleneck_kickoff():
            # Fast operations
            fast_operation()
            fast_operation()
            fast_operation()
            # Slow operation (bottleneck)
            slow_operation()
            
            return Mock(
                raw="Bottleneck test completed",
                tasks_output=[Mock(raw="Output") for _ in range(4)]
            )
        
        mock_crew.kickoff.side_effect = bottleneck_kickoff
        
        with patch('core.pipeline.os.makedirs'), \
             patch('core.pipeline.json.dump'):
            
            start_time = time.time()
            
            result = generate_content(
                topic="Bottleneck Test",
                video_type="educational",
                out_dir="test_output",
                config=mock_config
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert result is not None
            
            # Total time should be dominated by the slow operation
            assert total_time >= 0.3  # At least the bottleneck time
            
            print(f"Bottleneck test time: {total_time:.3f} seconds")
    
    def test_memory_usage_monitoring(self, mock_config):
        """Test memory usage during content generation."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('models.text_model.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            # Simulate memory-intensive operation
            def memory_intensive_generate(prompt):
                # Simulate large response
                large_text = "Generated content " * 1000
                mock_response = Mock()
                mock_response.text = large_text
                return mock_response
            
            mock_model.generate_content.side_effect = memory_intensive_generate
            
            # Generate multiple large responses
            for i in range(10):
                result = generate_text(f"Large prompt {i}", mock_config)
                assert result is not None
            
            # Check memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
            
            # Memory increase should be reasonable
            assert memory_increase < 100  # Should not use more than 100MB extra
    
    @pytest.mark.slow
    def test_stress_test_multiple_generations(self, mock_config):
        """Stress test with multiple rapid generations."""
        with patch('core.pipeline.Crew') as mock_crew_class, \
             patch('core.pipeline.create_agents') as mock_create_agents, \
             patch('core.pipeline.create_tasks') as mock_create_tasks, \
             patch('core.pipeline.os.makedirs'), \
             patch('core.pipeline.json.dump'):
            
            mock_agents = {
                'script_agent': Mock(),
                'segmenter_agent': Mock(),
                'prompt_gen_agent': Mock(),
                'image_render_agent': Mock()
            }
            mock_create_agents.return_value = mock_agents
            mock_create_tasks.return_value = [Mock() for _ in range(4)]
            
            mock_crew = Mock()
            mock_crew_class.return_value = mock_crew
            mock_crew.kickoff.return_value = Mock(
                raw="Stress test result",
                tasks_output=[Mock(raw="Output") for _ in range(4)]
            )
            
            # Stress test parameters
            num_generations = 20
            topics = [f"Topic {i}" for i in range(num_generations)]
            
            start_time = time.time()
            successful_generations = 0
            
            for topic in topics:
                try:
                    result = generate_content(
                        topic=topic,
                        video_type="educational",
                        out_dir="test_output",
                        config=mock_config
                    )
                    if result is not None:
                        successful_generations += 1
                except Exception as e:
                    print(f"Generation failed for {topic}: {e}")
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify stress test results
            success_rate = successful_generations / num_generations
            avg_time_per_generation = total_time / num_generations
            
            print(f"Stress test: {successful_generations}/{num_generations} successful")
            print(f"Success rate: {success_rate:.1%}")
            print(f"Average time per generation: {avg_time_per_generation:.3f}s")
            
            # Should have high success rate
            assert success_rate >= 0.9  # At least 90% success
            assert avg_time_per_generation < 1.0  # Should be reasonably fast


if __name__ == "__main__":
    pytest.main([__file__, "-v"])