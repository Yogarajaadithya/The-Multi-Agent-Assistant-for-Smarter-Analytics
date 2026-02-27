"""
Enhanced Logging Utility for Multi-Agent System
=================================================
Provides structured logging with timing, error tracking, and agent-specific logs.
Date: December 30, 2025
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps
import traceback
import sys

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%H:%M:%S'
)


class AgentLogger:
    """
    Enhanced logger for multi-agent system with structured logging.
    Tracks timing, errors, and provides formatted output for frontend.
    """
    
    def __init__(self, agent_name: str):
        """Initialize agent-specific logger."""
        self.agent_name = agent_name
        self.logger = logging.getLogger(agent_name)
        self.logs: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        
    def _create_log_entry(
        self,
        level: str,
        message: str,
        details: Optional[str] = None,
        stack_trace: Optional[str] = None,
        duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create structured log entry."""
        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message,
            "agent": self.agent_name,
            "duration": duration,
            "details": details,
            "stackTrace": stack_trace
        }
    
    def start_timer(self):
        """Start timing an operation."""
        self.start_time = time.time()
    
    def stop_timer(self) -> float:
        """Stop timer and return duration in milliseconds."""
        if self.start_time:
            duration = (time.time() - self.start_time) * 1000
            self.start_time = None
            return duration
        return 0
    
    def info(self, message: str, details: Optional[str] = None):
        """Log info message."""
        self.logger.info(message)
        log_entry = self._create_log_entry("INFO", message, details)
        self.logs.append(log_entry)
        return log_entry
    
    def success(self, message: str, duration: Optional[float] = None, details: Optional[str] = None):
        """Log success message with optional timing."""
        self.logger.info(f"✓ {message}")
        log_entry = self._create_log_entry("SUCCESS", message, details, duration=duration)
        self.logs.append(log_entry)
        return log_entry
    
    def warning(self, message: str, details: Optional[str] = None):
        """Log warning message."""
        self.logger.warning(message)
        log_entry = self._create_log_entry("WARNING", message, details)
        self.logs.append(log_entry)
        return log_entry
    
    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        include_trace: bool = True
    ):
        """Log error message with optional exception details."""
        self.logger.error(message, exc_info=error is not None)
        
        details = None
        stack_trace = None
        
        if error:
            details = f"{type(error).__name__}: {str(error)}"
            if include_trace:
                stack_trace = ''.join(traceback.format_exception(
                    type(error), error, error.__traceback__
                ))
        
        log_entry = self._create_log_entry("ERROR", message, details, stack_trace)
        self.logs.append(log_entry)
        return log_entry
    
    def critical(
        self,
        message: str,
        error: Optional[Exception] = None,
        include_trace: bool = True
    ):
        """Log critical error message."""
        self.logger.critical(message, exc_info=error is not None)
        
        details = None
        stack_trace = None
        
        if error:
            details = f"{type(error).__name__}: {str(error)}"
            if include_trace:
                stack_trace = ''.join(traceback.format_exception(
                    type(error), error, error.__traceback__
                ))
        
        log_entry = self._create_log_entry("CRITICAL", message, details, stack_trace)
        self.logs.append(log_entry)
        return log_entry
    
    def debug(self, message: str, details: Optional[str] = None):
        """Log debug message."""
        self.logger.debug(message)
        log_entry = self._create_log_entry("DEBUG", message, details)
        self.logs.append(log_entry)
        return log_entry
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Get all logs for this agent."""
        return self.logs
    
    def clear_logs(self):
        """Clear all logs."""
        self.logs.clear()
    
    def timed_operation(self, operation_name: str):
        """
        Decorator for timing operations.
        
        Usage:
            @logger.timed_operation("SQL Query Execution")
            def execute_query():
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.start_timer()
                self.info(f"Starting {operation_name}...")
                try:
                    result = func(*args, **kwargs)
                    duration = self.stop_timer()
                    self.success(
                        f"Completed {operation_name}",
                        duration=duration,
                        details=f"Operation took {duration/1000:.2f}s"
                    )
                    return result
                except Exception as e:
                    duration = self.stop_timer()
                    self.error(
                        f"Failed {operation_name}",
                        error=e,
                        include_trace=True
                    )
                    raise
            return wrapper
        return decorator
    
    async def async_timed_operation(self, operation_name: str):
        """
        Async decorator for timing operations.
        
        Usage:
            @logger.async_timed_operation("Async SQL Query")
            async def execute_query():
                ...
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                self.start_timer()
                self.info(f"Starting {operation_name}...")
                try:
                    result = await func(*args, **kwargs)
                    duration = self.stop_timer()
                    self.success(
                        f"Completed {operation_name}",
                        duration=duration,
                        details=f"Operation took {duration/1000:.2f}s"
                    )
                    return result
                except Exception as e:
                    duration = self.stop_timer()
                    self.error(
                        f"Failed {operation_name}",
                        error=e,
                        include_trace=True
                    )
                    raise
            return wrapper
        return decorator


class SystemLogger:
    """
    System-wide logger that aggregates logs from all agents.
    """
    
    def __init__(self):
        """Initialize system logger."""
        self.logger = logging.getLogger("System")
        self.agent_loggers: Dict[str, AgentLogger] = {}
        self.system_logs: List[Dict[str, Any]] = []
    
    def get_agent_logger(self, agent_name: str) -> AgentLogger:
        """Get or create agent-specific logger."""
        if agent_name not in self.agent_loggers:
            self.agent_loggers[agent_name] = AgentLogger(agent_name)
        return self.agent_loggers[agent_name]
    
    def log(self, level: str, message: str, details: Optional[str] = None):
        """Log system-wide message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "details": details
        }
        self.system_logs.append(log_entry)
        
        # Also log to standard logger
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
        
        return log_entry
    
    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Get all logs from system and all agents."""
        all_logs = list(self.system_logs)
        for agent_logger in self.agent_loggers.values():
            all_logs.extend(agent_logger.get_logs())
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x.get('timestamp', ''))
        return all_logs
    
    def clear_all_logs(self):
        """Clear all logs."""
        self.system_logs.clear()
        for agent_logger in self.agent_loggers.values():
            agent_logger.clear_logs()
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors."""
        all_logs = self.get_all_logs()
        errors = [log for log in all_logs if log['level'] in ['ERROR', 'CRITICAL']]
        warnings = [log for log in all_logs if log['level'] == 'WARNING']
        
        return {
            "total_errors": len(errors),
            "total_warnings": len(warnings),
            "error_logs": errors,
            "warning_logs": warnings
        }
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """Get performance metrics for each agent."""
        metrics = {}
        for agent_name, agent_logger in self.agent_loggers.items():
            logs = agent_logger.get_logs()
            durations = [log['duration'] for log in logs if log.get('duration')]
            
            metrics[agent_name] = {
                "total_operations": len(logs),
                "successes": len([log for log in logs if log['level'] == 'SUCCESS']),
                "errors": len([log for log in logs if log['level'] in ['ERROR', 'CRITICAL']]),
                "warnings": len([log for log in logs if log['level'] == 'WARNING']),
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                "total_duration_ms": sum(durations)
            }
        
        return metrics


# Global system logger instance
system_logger = SystemLogger()


def get_agent_logger(agent_name: str) -> AgentLogger:
    """Get agent-specific logger from global system logger."""
    return system_logger.get_agent_logger(agent_name)


def get_all_logs() -> List[Dict[str, Any]]:
    """Get all logs from the system."""
    return system_logger.get_all_logs()


def clear_all_logs():
    """Clear all logs."""
    system_logger.clear_all_logs()


def get_error_summary() -> Dict[str, Any]:
    """Get error summary."""
    return system_logger.get_error_summary()


def get_agent_performance() -> Dict[str, Any]:
    """Get agent performance metrics."""
    return system_logger.get_agent_performance()
