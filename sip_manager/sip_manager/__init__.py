from .log import set_logging
from .account import Account
from .call import Call
from .agent import SipAgent
import threading
import logging
import time

logger = logging.getLogger(__name__)


from .events import EventType

def create_agent(config, agent_id=None):
    set_logging(config.log_level)
    # Set agent ID for namespacing
    agent_id = agent_id or f"agent-{threading.get_ident()}"
    
    # Enhance the agent with event methods
    from .events import register_listener, unregister_listener, EventType, emit_event
    
    # Use a shared Event object instead of thread_local
    agent_running = threading.Event()
    agent_initialized = threading.Event()
    agent_object = [None]  # Use a list to allow mutation from inside the thread
    
    def pjsua_thread_main():
        """
        Main function for the PJSUA thread.
        All PJSIP operations must happen in this thread.
        """
        try:
            # Create the agent in this thread
            logger.debug(f"Starting agent {agent_id} in PJSUA thread")
            
            # Initialize the agent in this thread
            agent = SipAgent(config)
            agent_object[0] = agent
            
            # Store the ID
            agent.id = agent_id
            
            # Add event methods to agent
            def register_namespaced_event(event_type, callback):
                def namespaced_callback(evt_type, **kwargs):
                    if kwargs.get('agent_id', agent.id) == agent.id:
                        return callback(evt_type, **kwargs)
                return register_listener(event_type, namespaced_callback)
            
            def emit_namespaced_event(event_type, **kwargs):
                kwargs['agent_id'] = agent.id
                return emit_event(event_type, **kwargs)
            
            agent.register_event = register_namespaced_event
            agent.unregister_event = unregister_listener
            agent.emit_event = emit_namespaced_event
            agent.EventType = EventType
            
            # Initialize account and other components
            agent.test_audio_routing()
            agent.register_account()
            
            # Signal that the agent is initialized
            agent_initialized.set()
            
            logger.info(f"Agent {agent.id} started successfully")
            emit_namespaced_event(EventType.AGENT_STARTED)
            
            # Set the running flag
            agent_running.set()
            
            agent.ep.utilTimerSchedule(config.welcome_message_length, None)

            # Main event loop - handle PJSIP events
            while agent_running.is_set():
                event_count = agent.ep.libHandleEvents(100)
                time.sleep(0.01)  # Small sleep to prevent CPU hogging
            
            # Cleanup
            logger.info(f"Shutting down agent {agent.id}")
            if hasattr(agent, 'account') and agent.account:
                agent.account.shutdown()
            agent.ep.libDestroy()
            logger.info(f"Agent {agent.id} shut down successfully")
            
        except Exception as e:
            logger.error(f"Error in PJSUA thread: {e}")
        finally:
            agent_running.clear()
            if agent_object[0]:
                agent_object[0].emit_event(EventType.AGENT_STOPPED)
    
    # Create a wrapper object to control the agent
    class AgentWrapper:
        def __init__(self):
            self.id = agent_id
            self._thread = None
            self.EventType = EventType
        
        def start_nonblocking(self):
            """Start the agent in a dedicated PJSUA thread"""
            if self._thread is not None and self._thread.is_alive():
                logger.warning("Agent already running")
                return False
            
            # Clear the flags before starting
            agent_running.clear()
            agent_initialized.clear()
            
            # Create and start a dedicated thread for PJSUA
            self._thread = threading.Thread(
                name="PJSUA-THREAD",
                target=pjsua_thread_main
            )
            self._thread.daemon = True
            self._thread.start()
            
            # Wait for agent to initialize
            if not agent_initialized.wait(timeout=5):
                logger.warning("Agent failed to initialize")
                return False
            
            logger.info(f"Agent {self.id} started in separate thread")
            return True
        
        def stop(self):
            """Stop the agent and its thread"""
            if not agent_running.is_set():
                logger.info("Agent not running")
                return
            
            logger.info(f"Stopping agent {self.id}")
            if agent_object[0]:
                agent_object[0].emit_event(EventType.AGENT_STOPPING)
            
            # Set flag to stop thread
            agent_running.clear()
            
            # Wait for thread to join
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
                if self._thread.is_alive():
                    logger.warning(f"Agent {self.id} thread did not exit cleanly")
                else:
                    logger.info(f"Agent {self.id} thread exited cleanly")
            
            self._thread = None
        
        def is_running(self):
            """Check if the agent is currently running"""
            return agent_running.is_set() and self._thread and self._thread.is_alive()
            
        def register_event(self, event_type, callback):
            """Register an event listener"""
            def namespaced_callback(evt_type, **kwargs):
                if kwargs.get('agent_id', self.id) == self.id:
                    return callback(evt_type, **kwargs)
            return register_listener(event_type, namespaced_callback)
        
        def unregister_event(self, event_type, callback):
            """Unregister an event listener"""
            return unregister_listener(event_type, callback)
        
        def emit_event(self, event_type, **kwargs):
            """Emit an event"""
            kwargs['agent_id'] = self.id
            return emit_event(event_type, **kwargs)
    
    return AgentWrapper()