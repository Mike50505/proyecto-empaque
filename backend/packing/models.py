import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q

class BalanceGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Part(models.Model):
    number = models.CharField(max_length=120)
    universe_id = models.CharField(max_length=120, blank=True, null=True, unique=True)
    customer = models.CharField(max_length=150, blank=True)
    scope = models.CharField(max_length=150, blank=True)
    diameter = models.CharField(max_length=100, blank=True)
    attributes = models.JSONField(default=dict)
    provisional = models.BooleanField(default=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    def __str__(self): return self.number

class IntegrationState(models.Model):
    name = models.CharField(max_length=50, unique=True)
    cursor = models.TextField(blank=True)
    last_sync = models.DateTimeField(null=True)
    error = models.CharField(max_length=200, blank=True)

class Employee(models.Model):
    payroll = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=150)
    active = models.BooleanField(default=True)
    inspector = models.BooleanField(default=False)
    def __str__(self): return f'{self.payroll} · {self.name}'

class Shift(models.Model):
    code = models.CharField(max_length=40, unique=True)
    starts_at = models.TimeField(null=True, blank=True)
    ends_at = models.TimeField(null=True, blank=True)
    def __str__(self): return self.code

class Program(models.Model):
    group = models.ForeignKey(BalanceGroup, on_delete=models.PROTECT)
    client = models.CharField(max_length=150)
    scope = models.CharField(max_length=150, blank=True)
    year = models.PositiveIntegerField()
    week = models.PositiveIntegerField()
    starts_on = models.DateField()
    ends_on = models.DateField()
    reference = models.CharField(max_length=150, unique=True)
    published = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(week__gte=1, week__lte=53), name='valid_week')]
        permissions = [('plan', 'Gestionar planeación'), ('capture', 'Capturar empaque'), ('release', 'Liberar empaque'), ('consult', 'Consultar balances')]
    def __str__(self): return f'{self.reference} · {self.year}/S{self.week}'

class Demand(models.Model):
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name='lines')
    part = models.ForeignKey(Part, on_delete=models.PROTECT)
    reference = models.CharField(max_length=150)
    original = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    priority = models.PositiveIntegerField(default=2)
    due_on = models.DateField(null=True, blank=True)
    carry_to = models.DateField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    attributes_snapshot = models.JSONField(default=dict)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['program', 'reference'], name='unique_program_line')]

class Capture(models.Model):
    key = models.UUIDField(default=uuid.uuid4, unique=True)
    fingerprint = models.CharField(max_length=64)
    target = models.ForeignKey(Demand, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    effective_at = models.DateTimeField()
    operational_date = models.DateField()
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT)
    packer = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True, blank=True, related_name='packed')
    packer_payroll = models.CharField(max_length=40, blank=True)
    inspector = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True, blank=True, related_name='inspected')
    inspector_payroll = models.CharField(max_length=40, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    released = models.BooleanField(default=False)
    release_mode = models.CharField(max_length=20)
    released_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='released_captures')
    voided = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(quantity__gt=0), name='positive_capture')]
        indexes = [models.Index(fields=['operational_date', 'shift'])]

class OpeningBalance(models.Model):
    demand = models.ForeignKey(Demand, on_delete=models.PROTECT)
    applied = models.PositiveIntegerField(default=0)
    credit = models.PositiveIntegerField(default=0)
    cutoff = models.DateTimeField()
    evidence = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class Allocation(models.Model):
    capture = models.ForeignKey(Capture, on_delete=models.PROTECT, null=True, blank=True, related_name='allocations')
    opening = models.ForeignKey(OpeningBalance, on_delete=models.PROTECT, null=True, blank=True, related_name='allocations')
    demand = models.ForeignKey(Demand, on_delete=models.PROTECT, related_name='allocations')
    quantity = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(quantity__gt=0), name='positive_allocation'), models.CheckConstraint(condition=(Q(capture__isnull=False, opening__isnull=True) | Q(capture__isnull=True, opening__isnull=False)), name='one_allocation_source')]

class Revision(models.Model):
    demand = models.ForeignKey(Demand, on_delete=models.PROTECT)
    before = models.PositiveIntegerField()
    after = models.PositiveIntegerField()
    reason = models.TextField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class Audit(models.Model):
    kind = models.CharField(max_length=50)
    object_id = models.CharField(max_length=100)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.TextField(blank=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class WeekTransfer(models.Model):
    key = models.UUIDField(unique=True)
    demand = models.ForeignKey(Demand, on_delete=models.PROTECT, related_name='week_transfers')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    from_start = models.DateField()
    to_start = models.DateField()
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class ImportBatch(models.Model):
    digest = models.CharField(max_length=64)
    file = models.FileField(upload_to='imports/%Y/%m')
    mode = models.CharField(max_length=25)
    mapping = models.JSONField(default=dict)
    preview = models.JSONField(default=dict)
    applied = models.BooleanField(default=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['digest','mode','mapping'], name='unique_import_operation')]

class Snapshot(models.Model):
    date = models.DateField()
    scope = models.JSONField(default=dict)
    version = models.PositiveIntegerField()
    payload = models.JSONField()
    cutoff = models.DateTimeField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class ClosedPeriod(models.Model):
    date = models.DateField(unique=True)
    reason = models.TextField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

class CorrectionRequest(models.Model):
    capture = models.ForeignKey(Capture, on_delete=models.PROTECT)
    reason = models.TextField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
