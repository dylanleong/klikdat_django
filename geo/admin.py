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
        all_commands = get_commands()
        geo_commands = []
        for cmd_name, app_name in all_commands.items():
            if app_name == 'geo':
                from django.core.management import load_command_class
                cmd_class = load_command_class(app_name, cmd_name)
                geo_commands.append({
                    'name': cmd_name,
                    'help': getattr(cmd_class, 'help', 'No description available'),
                })

        context = {
            **self.admin_site.each_context(request),
            'commands': geo_commands,
            'recent_tasks': ImportTask.objects.all()[:10],
            'title': 'Import Dashboard',
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
