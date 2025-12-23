import sys
from io import StringIO
from django.core.management import call_command
from django.utils import timezone
from .models import ImportTask

def run_management_command(task_id):
    """
    Task to run a management command asynchronously and capture its output.
    """
    try:
        task = ImportTask.objects.get(id=task_id)
    except ImportTask.DoesNotExist:
        return

    task.status = 'RUNNING'
    task.started_at = timezone.now()
    task.save()

    # Capture stdout and stderr
    out = StringIO()
    err = StringIO()
    
    # Backup original stdout/stderr to restore later if needed, 
    # though call_command allows passing streams.
    
    try:
        # Split parameters if any (simplified)
        params = task.parameters.split() if task.parameters else []
        
        # Execute command
        call_command(task.command_name, *params, stdout=out, stderr=err)
        
        task.status = 'COMPLETED'
        task.logs = out.getvalue()
        if err.getvalue():
            task.logs += "\nERRORS:\n" + err.getvalue()
            
    except Exception as e:
        task.status = 'FAILED'
        task.logs = out.getvalue() + f"\n\nEXCEPTION:\n{str(e)}"
        if err.getvalue():
             task.logs += "\n\nSTDERR:\n" + err.getvalue()
    
    task.completed_at = timezone.now()
    task.save()
