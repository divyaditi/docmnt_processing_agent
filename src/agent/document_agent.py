import logging
from typing import Dict, Any, TypedDict, Literal
from client.grok_client import GroqClient
from client.llamaparse_client import LlamaparseClient
from langgraph.graph import StateGraph, START, END

# Configure logger for this module
logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class DocumentState(TypedDict):
    """State schema for document processing workflow"""
    file_path: str
    markdown_content: str
    summarized_text: str
    user_feedback: str
    retries: int
    approved: bool
    status: str


class DocumentAgent:
    """Agent for processing and summarizing documents with dynamic human-in-the-loop loop"""
    
    def __init__(self):
        """Initialize the document agent"""
        self.groq_client = GroqClient()
        self.parser = LlamaparseClient()
        logger.info("DocumentAgent initialized with dynamic loop support")
    
    async def _get_user_approval(self) -> bool:
        """
        Get user approval from terminal (y/n).
        Runs input() in a thread to avoid blocking the async event loop.
        
        Returns:
            True if approved, False if rejected
        """
        import asyncio
        
        print("\n" + "="*70)
        print("HUMAN FEEDBACK REQUIRED")
        print("="*70)
        print("\nAre you satisfied with this summary? (yes/no)")
        print("  y  - Yes, I'm satisfied (end process)")
        print("  n  - No, try again (rerun summarization)")
        print("="*70 + "\n")
        
        while True:
            # Run input() in a thread to avoid blocking async loop
            user_input = await asyncio.to_thread(input, "Your choice (y/n): ")
            user_input = user_input.strip().lower()
            
            if user_input in ['y', 'yes']:
                logger.info("✅ User satisfied with summary")
                return True
            elif user_input in ['n', 'no']:
                logger.info("❌ User NOT satisfied - will retry")
                return False
            else:
                print("❌ Invalid input. Please enter 'y' (yes) or 'n' (no)")
    
    def _display_summary(self, summary: str) -> None:
        """Display summary to user"""
        print("\n" + "="*70)
        print("SUMMARY GENERATED")
        print("="*70 + "\n")
        print(summary)
        print("\n" + "="*70 + "\n")
    
    async def parse_document(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a PDF document using Llamaparse.
        
        Args:
            state: Dictionary containing file_path
            
        Returns:
            Updated state with markdown content
        """
        try:
            file_path = state.get("file_path")
            
            if not file_path:
                logger.error("No file_path provided in state")
                state["status"] = "error"
                return state
            
            logger.info(f"Parsing document: {file_path}")
            
            # Parse document with Llamaparse
            response = await self.parser.parse_document_from_path(file_path)
            
            # Response is a list of Document objects, get the first one
            if isinstance(response, list) and len(response) > 0:
                doc = response[0]
                markdown_text = doc.text_resource.text if hasattr(doc, 'text_resource') else str(doc)
            else:
                markdown_text = str(response)
            
            logger.info(f"Successfully extracted markdown: {len(markdown_text)} characters")
            
            # Return updated state
            state["markdown_content"] = markdown_text
            state["status"] = "parsed"
            
            return state
            
        except Exception as e:
            logger.error(f"Error parsing document: {str(e)}", exc_info=True)
            state["status"] = "error"
            state["user_feedback"] = f"Document parsing failed: {str(e)}"
            return state
    
    async def summarize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize document content using the Groq client.
        
        Args:
            state: Dictionary containing markdown_content
            
        Returns:
            Updated state with summarized text
        """
        try:
            markdown_content = state.get("markdown_content")
            
            if not markdown_content:
                logger.error("No markdown content provided in state")
                state["status"] = "error"
                state["user_feedback"] = "Markdown content is required"
                return state
            
            attempt = state.get("retries", 0) + 1
            logger.info(f"Invoking Groq API for summarization (attempt {attempt})")
            
            # Call Groq to summarize
            result = await self.groq_client.invoke_grok(markdown_content)
            
            # Extract summarized content
            if result.get("status") == "success":
                summarized_text = result.get("data", {}).get("summary", "")
                logger.info(f"Successfully summarized: {len(summarized_text)} characters")
                
                state["summarized_text"] = summarized_text
                state["status"] = "summarized"
                state["retries"] = attempt
                
                return state
            else:
                error_msg = result.get("data", {}).get("error", "Unknown error")
                logger.error(f"Summarization failed: {error_msg}")
                state["status"] = "error"
                state["user_feedback"] = f"Summarization error: {error_msg}"
                return state
                
        except Exception as e:
            logger.error(f"Exception in summarize function: {str(e)}", exc_info=True)
            state["status"] = "error"
            state["user_feedback"] = f"Summarization error: {str(e)}"
            return state
    
    async def request_approval(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request human approval for the summary.
        Displays summary and gets y/n feedback asynchronously.
        
        Args:
            state: Dictionary containing summarized_text
            
        Returns:
            Updated state with approval status
        """
        try:
            summarized_text = state.get("summarized_text")
            
            if not summarized_text:
                logger.error("No summarized text provided")
                state["status"] = "error"
                state["user_feedback"] = "Summarized text is required"
                return state
            
            logger.info("Requesting human approval for summary")
            
            # Display current attempt
            current_attempt = state.get("retries", 0)
            
            print(f"\n[Attempt {current_attempt}/{MAX_RETRIES}]")
            
            # Display summary
            self._display_summary(summarized_text)
            
            # Get approval from user (async, uses thread for input)
            is_approved = await self._get_user_approval()
            
            state["approved"] = is_approved
            
            if is_approved:
                state["status"] = "approved"
                logger.info(f"✅ Summary approved after {current_attempt} attempt(s)")
            else:
                state["status"] = "rejected"
                logger.info(f"❌ Summary rejected - may retry if attempts < {MAX_RETRIES}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error requesting approval: {str(e)}", exc_info=True)
            state["status"] = "error"
            state["user_feedback"] = f"Approval request failed: {str(e)}"
            return state
    
    def should_retry(self, state: Dict[str, Any]) -> Literal["summarize", "end"]:
        """
        Conditional edge: Decide whether to retry summarization or end.
        
        This creates a DYNAMIC LOOP that continues based on:
        1. User rejected (status == "rejected")
        2. Retries not exceeded (retries < MAX_RETRIES)
        
        Args:
            state: Current workflow state
            
        Returns:
            "summarize" to retry, "end" to finish
        """
        current_status = state.get("status")
        current_retries = state.get("retries", 0)
        
        logger.debug(f"Decision: status={current_status}, retries={current_retries}/{MAX_RETRIES}")
        
        # If approved, go to end
        if state.get("approved"):
            logger.info("✅ Proceeding to END (summary approved)")
            return "end"
        
        # If rejected and can retry, go back to summarize
        if current_status == "rejected" and current_retries < MAX_RETRIES:
            logger.info(f"🔄 Looping back to SUMMARIZE (attempt {current_retries + 1})")
            print("\n⏳ Retrying summarization...\n")
            return "summarize"
        
        # Otherwise end (either error or max retries reached)
        logger.info("⏹️  Proceeding to END (no more retries or error)")
        return "end"
    
    def build_graph(self):
        """
        Build the dynamic LangGraph workflow with conditional looping.
        
        Graph Structure:
        START → parse → summarize → approval → [decision] → loop back OR end
        """
        try:
            graph = StateGraph(DocumentState)
            
            # Add nodes
            graph.add_node("parse", self.parse_document)
            graph.add_node("summarize", self.summarize)
            graph.add_node("approval", self.request_approval)
            
            # Add edges
            graph.add_edge(START, "parse")
            graph.add_edge("parse", "summarize")
            graph.add_edge("summarize", "approval")
            
            # Add CONDITIONAL edge - this creates the dynamic loop
            graph.add_conditional_edges(
                "approval",
                self.should_retry,
                {
                    "summarize": "summarize",  # Loop back to summarize
                    "end": END                  # Exit to END
                }
            )
            
            logger.info("✅ Dynamic loop workflow built successfully")
            logger.info("   Flow: START → parse → summarize → approval → [DECISION]")
            logger.info("   Decision: Approved OR max_retries? → END")
            logger.info("   Decision: Not approved AND retries < 3? → loop to summarize")
            
            return graph.compile()
            
        except Exception as e:
            logger.error(f"Error building graph: {str(e)}", exc_info=True)
            raise

