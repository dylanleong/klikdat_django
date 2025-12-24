from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import get_commands
from django_q.tasks import async_task
from .models import IpAsn, ImportTask

@admin.register(IpAsn)
class IpAsnAdmin(admin.ModelAdmin):
    list_display = ('start_ip', 'end_ip', 'asn', 'country_code', 'organization')
    search_fields = ('start_ip', 'end_ip', 'organization')

@admin.register(ImportTask)
class ImportTaskAdmin(admin.ModelAdmin):
    list_display = ('command_name', 'status', 'started_at', 'completed_at', 'created_at')
    list_filter = ('status', 'command_name')
    readonly_fields = ('command_name', 'parameters', 'status', 'started_at', 'completed_at', 'logs', 'created_at')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.import_dashboard), name='geo_import_dashboard'),
            path('trigger/', self.admin_site.admin_view(self.trigger_import), name='geo_import_trigger'),
        ]
        return custom_urls + urls

    def import_dashboard(self, request):
        # Get all management commands from the 'geo' app
        # Get all management commands from relevant apps
        all_commands = get_commands()
        import_commands = []
        target_apps = ['geo', 'vehicles']
        
        for cmd_name, app_name in all_commands.items():
            if app_name in target_apps:
                from django.core.management import load_command_class
                cmd_class = load_command_class(app_name, cmd_name)
                # Only include commands that look like import/ingestion scripts
                if 'import' in cmd_name or 'ingest' in cmd_name or 'migrate' in cmd_name or 'calculate' in cmd_name:
                     import_commands.append({
                        'name': cmd_name,
                        'app': app_name,
                        'help': getattr(cmd_class, 'help', 'No description available'),
                    })
        
        # Sort by app then name
        import_commands.sort(key=lambda x: (x['app'], x['name']))

        context = {
            **self.admin_site.each_context(request),
            'commands': import_commands,
            'recent_tasks': ImportTask.objects.all()[:10],
            'title': 'Global Import Dashboard',
        }
        return render(request, 'admin/geo/import_dashboard.html', context)

    def trigger_import(self, request):
        if request.method == 'POST':
            command_name = request.POST.get('command')
            if command_name:
                # Create the task record
                task = ImportTask.objects.create(
                    command_name=command_name,
                    status='PENDING'
                )
                # Enqueue the task using Django Q
                from .tasks import run_management_command
                async_task(run_management_command, task.id)
                
                messages.success(request, f'Import task for "{command_name}" has been enqueued.')
            else:
                messages.error(request, 'No command specified.')
        
        return redirect('admin:geo_import_dashboard')
