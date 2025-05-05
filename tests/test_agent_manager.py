import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
import sys
import os

# Add project root to allow importing the manager
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.agent.manager import AgentManager

class TestAgentManager(unittest.TestCase):

    def setUp(self):
        """Set up a mock agent executor for each test."""
        self.mock_executor = AsyncMock()
        # Define return values for mocked methods if needed, e.g.:
        self.mock_executor.ainvoke = AsyncMock(return_value={'messages': [MagicMock(content='Standard Response')]})
        self.mock_executor.abatch = AsyncMock(return_value=[
            {'messages': [MagicMock(content='Batch Response 1')]},
            {'messages': [MagicMock(content='Batch Response 2')]}
        ])

    def test_init_standard_mode(self):
        """Test initialization in Standard mode."""
        manager = AgentManager(self.mock_executor, mode='Standard')
        self.assertEqual(manager.mode, 'Standard')
        self.assertEqual(manager.batch_size, 10) # Default

    def test_init_batch_mode(self):
        """Test initialization in Batch mode."""
        manager = AgentManager(self.mock_executor, mode='Batch', batch_size=5)
        self.assertEqual(manager.mode, 'Batch')
        self.assertEqual(manager.batch_size, 5)

    def test_init_invalid_executor(self):
        """Test initialization with an executor missing methods."""
        invalid_executor = MagicMock()
        del invalid_executor.abatch # Remove a required method
        with self.assertRaises(ValueError):
            AgentManager(invalid_executor)
            
    def test_process_request_standard(self):
        """Test process_request in Standard mode invokes ainvoke."""
        manager = AgentManager(self.mock_executor, mode='Standard')
        query = "Test query standard"
        expected_payload = {"messages": [{"role": "user", "content": query}]}
        
        async def run_test():
            response = await manager.process_request(query)
            self.mock_executor.ainvoke.assert_called_once_with(expected_payload)
            self.assertEqual(response, 'Standard Response')
            self.assertEqual(manager.get_queue_size(), 0) # Queue should be empty
            
        asyncio.run(run_test())

    def test_process_request_batch(self):
        """Test process_request in Batch mode queues the request."""
        manager = AgentManager(self.mock_executor, mode='Batch')
        query = "Test query batch"
        
        async def run_test():
            response = await manager.process_request(query)
            self.mock_executor.ainvoke.assert_not_called()
            self.mock_executor.abatch.assert_not_called()
            self.assertEqual(manager.get_queue_size(), 1)
            self.assertEqual(manager.request_queue[0]['query'], query)
            self.assertTrue(response.startswith("Query ")) # Check for acknowledgement
            
        asyncio.run(run_test())

    def test_flush_batch_mode_empty_queue(self):
        """Test flush in Batch mode does nothing when queue is empty."""
        manager = AgentManager(self.mock_executor, mode='Batch')
        
        async def run_test():
            results = await manager.flush()
            self.assertIsNone(results)
            self.mock_executor.abatch.assert_not_called()
            
        asyncio.run(run_test())
        
    def test_flush_standard_mode(self):
        """Test flush in Standard mode does nothing."""
        manager = AgentManager(self.mock_executor, mode='Standard')
        # Add something to queue just to ensure it's ignored
        manager.request_queue.append({"query": "q", "payload": {}})
        
        async def run_test():
            results = await manager.flush()
            self.assertIsNone(results)
            self.mock_executor.abatch.assert_not_called()
            self.assertEqual(manager.get_queue_size(), 1) # Item should remain
            
        asyncio.run(run_test())

    def test_flush_batch_mode_single_batch(self):
        """Test flush in Batch mode processes a single batch."""
        queries = ["Query 1", "Query 2"]
        expected_payloads = [
            {"messages": [{"role": "user", "content": q}]} for q in queries
        ]
        # Adjust mock return value for this test
        self.mock_executor.abatch.return_value = [
            {'messages': [MagicMock(content='Resp 1')]},
            {'messages': [MagicMock(content='Resp 2')]}
        ]
        manager = AgentManager(self.mock_executor, mode='Batch', batch_size=5)

        async def run_test():
            for q in queries:
                 await manager.process_request(q)
            
            self.assertEqual(manager.get_queue_size(), 2)
            results = await manager.flush()
            
            self.mock_executor.abatch.assert_called_once_with(expected_payloads)
            self.assertEqual(manager.get_queue_size(), 0)
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0], {"query": "Query 1", "response": "Resp 1"})
            self.assertEqual(results[1], {"query": "Query 2", "response": "Resp 2"})
            
        asyncio.run(run_test())
        
    def test_flush_batch_mode_multiple_batches(self):
        """Test flush in Batch mode processes multiple batches correctly."""
        queries = ["Q1", "Q2", "Q3", "Q4"]
        expected_payloads_batch1 = [{"messages": [{"role": "user", "content": q}]} for q in queries[:2]]
        expected_payloads_batch2 = [{"messages": [{"role": "user", "content": q}]} for q in queries[2:]]
        
        # Mock abatch to return different responses based on input length perhaps, or just fixed sequence
        async def mock_abatch_logic(payloads):
            if len(payloads) == 2 and payloads[0]["messages"][0]["content"] == "Q1":
                return [{'messages': [MagicMock(content='R1')]},{ 'messages': [MagicMock(content='R2')]}]
            elif len(payloads) == 2 and payloads[0]["messages"][0]["content"] == "Q3":
                return [{'messages': [MagicMock(content='R3')]},{ 'messages': [MagicMock(content='R4')]}]
            return [] # Default empty
        self.mock_executor.abatch = AsyncMock(side_effect=mock_abatch_logic)
        
        manager = AgentManager(self.mock_executor, mode='Batch', batch_size=2) # Small batch size

        async def run_test():
            for q in queries:
                 await manager.process_request(q)
            
            self.assertEqual(manager.get_queue_size(), 4)
            results = await manager.flush()
            
            self.assertEqual(self.mock_executor.abatch.call_count, 2)
            self.mock_executor.abatch.assert_has_calls([
                call(expected_payloads_batch1),
                call(expected_payloads_batch2)
            ])
            self.assertEqual(manager.get_queue_size(), 0)
            self.assertEqual(len(results), 4)
            self.assertEqual(results[0], {"query": "Q1", "response": "R1"})
            self.assertEqual(results[1], {"query": "Q2", "response": "R2"})
            self.assertEqual(results[2], {"query": "Q3", "response": "R3"})
            self.assertEqual(results[3], {"query": "Q4", "response": "R4"})
            
        asyncio.run(run_test())
        
    def test_clear_queue(self):
        """Test that clear_queue empties the queue."""
        manager = AgentManager(self.mock_executor, mode='Batch')
        async def run_test():
            await manager.process_request("Query 1")
            self.assertEqual(manager.get_queue_size(), 1)
            manager.clear_queue()
            self.assertEqual(manager.get_queue_size(), 0)
        asyncio.run(run_test())
        

if __name__ == '__main__':
    unittest.main() 