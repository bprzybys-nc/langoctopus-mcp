import asyncio
import logging
from typing import List, Dict, Any, Literal, Optional

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages agent interactions, supporting Standard and Batch processing modes."""
    
    def __init__(self, agent_executor: Any, mode: Literal['Standard', 'Batch'] = 'Standard', batch_size: int = 10, request_timeout: int = 120):
        """
        Initializes the AgentManager.

        Args:
            agent_executor: The pre-configured agent executor (e.g., from create_react_agent).
            mode: The processing mode ('Standard' or 'Batch'). Defaults to 'Standard'.
            batch_size: The maximum number of requests to send in a single batch (Batch mode only).
            request_timeout: Timeout in seconds for agent invoke/batch calls.
        """
        if not hasattr(agent_executor, 'ainvoke') or not hasattr(agent_executor, 'abatch'):
            raise ValueError("agent_executor must support both 'ainvoke' and 'abatch' methods.")
            
        self.agent_executor = agent_executor
        self.mode = mode
        self.batch_size = max(1, batch_size) # Ensure batch size is at least 1
        self.request_queue: List[Dict[str, Any]] = []
        self.request_timeout = request_timeout # Store timeout
        logger.info(f"AgentManager initialized in {self.mode} mode with batch size {self.batch_size} and timeout {self.request_timeout}s")

    async def process_request(self, query: str) -> Optional[str]:
        """
        Processes a single user query based on the current mode.

        Args:
            query: The user's query string.

        Returns:
            In 'Standard' mode: The agent's response string.
            In 'Batch' mode: An acknowledgement string or None.
            Returns None if processing fails in Standard mode.
        """
        request_payload = {"messages": [{"role": "user", "content": query}]}
        # Define config with timeout for invoke
        config = {"configurable": {"request_timeout": self.request_timeout}}

        if self.mode == 'Standard':
            logger.debug(f"Processing query in Standard mode: '{query}'")
            try:
                # Pass config to ainvoke
                response = await self.agent_executor.ainvoke(request_payload, config=config)
                # Extract content robustly
                response_content = self._extract_response_content(response)
                logger.debug(f"Standard mode response: {response_content}")
                return response_content
            except asyncio.TimeoutError:
                logger.error(f"Timeout error during standard agent invocation for query '{query}' after {self.request_timeout}s", exc_info=True)
                return f"Error: Agent request timed out after {self.request_timeout}s"
            except Exception as e:
                logger.error(f"Error during standard agent invocation for query '{query}': {e}", exc_info=True)
                return f"Error processing query: {e}" # Return error message
        elif self.mode == 'Batch':
            logger.debug(f"Adding query to batch queue: '{query}'")
            # Store the original query along with the payload for result matching later
            self.request_queue.append({"query": query, "payload": request_payload})
            return f"Query '{query[:30]}...' added to batch."
        else:
            logger.warning(f"Unknown mode: {self.mode}. Cannot process request.")
            return "Error: Unknown processing mode."

    async def flush(self) -> Optional[List[Dict[str, Any]]]:
        """
        Processes all queued requests in Batch mode.
        Does nothing in Standard mode or if the queue is empty.

        Returns:
            A list of dictionaries, each containing 'query' and 'response', 
            or None if not in Batch mode or queue is empty.
        """
        if self.mode != 'Batch' or not self.request_queue:
            logger.info(f"Flush called in {self.mode} mode or with empty queue. No action taken.")
            return None

        logger.info(f"Flushing batch queue with {len(self.request_queue)} requests (batch size: {self.batch_size})...")
        
        results = []
        queued_requests = self.request_queue.copy() # Work on a copy
        self.request_queue.clear()
        # Define config with timeout and concurrency for batch
        config = {
            "configurable": {"request_timeout": self.request_timeout},
            "max_concurrency": 5
        }
        
        try:
            # Process in batches
            for i in range(0, len(queued_requests), self.batch_size):
                batch = queued_requests[i:i + self.batch_size]
                batch_payloads = [req["payload"] for req in batch]
                original_queries = [req["query"] for req in batch]
                logger.debug(f"Processing batch {i // self.batch_size + 1} with {len(batch)} requests. Applying timeout: {self.request_timeout}s, max_concurrency: {config.get('max_concurrency')}.")
                
                batch_responses = []
                error_occurred = False
                try:
                    logger.info(f"Attempting agent_executor.abatch for batch {i // self.batch_size + 1}...")
                    # Pass config to abatch
                    batch_responses = await self.agent_executor.abatch(batch_payloads, config=config)
                    logger.info(f"agent_executor.abatch for batch {i // self.batch_size + 1} completed.")
                except asyncio.TimeoutError:
                    logger.error(f"Timeout error during agent batch invocation (Batch {i // self.batch_size + 1}) after {self.request_timeout}s", exc_info=True)
                    error_occurred = True
                    error_response = f"Error: Agent batch request timed out after {self.request_timeout}s"
                    # Create error results for this specific timed-out batch
                    for idx, query in enumerate(original_queries):
                        results.append({"query": query, "response": error_response})
                except Exception as batch_exc:
                    logger.error(f"Error during agent batch invocation (Batch {i // self.batch_size + 1}): {batch_exc}", exc_info=True)
                    error_occurred = True
                    error_response = f"Error during batch execution: {batch_exc}"
                    # Create error results for this specific failed batch
                    for idx, query in enumerate(original_queries):
                        results.append({"query": query, "response": error_response})
                
                # Only process responses if no error occurred in abatch
                if not error_occurred:
                    if len(batch_responses) != len(batch):
                        logger.error(f"Mismatch between batch request count ({len(batch)}) and response count ({len(batch_responses)}). Results may be incomplete.")

                    # Correlate responses back to original queries
                    for idx, response in enumerate(batch_responses):
                        query = original_queries[idx] if idx < len(original_queries) else "Unknown query (index mismatch)"
                        response_content = self._extract_response_content(response)
                        results.append({"query": query, "response": response_content})
                        logger.debug(f"Batch response for '{query[:30]}...': {response_content}")
            
            logger.info("Batch queue flushed.")
            return results
        except Exception as e: # Catch errors outside the batch loop (e.g., initial setup)
            logger.error(f"Unexpected error during flush operation: {e}", exc_info=True)
            # Return whatever results were processed plus error markers for the rest
            error_response = f"Error during flush setup: {e}"
            processed_queries = {r['query'] for r in results}
            for req in queued_requests:
                 if req['query'] not in processed_queries:
                      results.append({"query": req["query"], "response": error_response})
            return results

    def _extract_response_content(self, response: Any) -> str:
        """Helper method to robustly extract content from agent response."""
        try:
            if response and isinstance(response, dict) and 'messages' in response and isinstance(response['messages'], list) and len(response['messages']) > 0:
                last_message = response['messages'][-1]
                if hasattr(last_message, 'content'):
                    return str(last_message.content)
                elif isinstance(last_message, dict) and 'content' in last_message:
                    return str(last_message['content'])
            # Add more checks if other response structures are possible
            logger.warning(f"Could not extract content from message structure: {response}")
            return "Error: Could not parse response content."
        except Exception as e:
            logger.error(f"Exception extracting response content: {e} from response: {response}", exc_info=True)
            return f"Error parsing response: {e}"

    def get_queue_size(self) -> int:
        """Returns the current number of items in the batch queue."""
        return len(self.request_queue)

    def clear_queue(self):
        """Clears the batch request queue."""
        logger.info("Clearing agent request queue.")
        self.request_queue.clear() 