from import_export import resources, fields, widgets
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from .models import VehicleType, Make, Model, SellerType
from .models_attributes import VehicleAttribute, VehicleAttributeOption

class VehicleAttributeResource(resources.ModelResource):
    # Customize the vehicle_types field to handle ManyToMany relationship
    # This allows using names (e.g., "Car, Van") instead of IDs
    vehicle_types = fields.Field(
        column_name='vehicle_types',
        attribute='vehicle_types',
        widget=ManyToManyWidget(VehicleType, field='vehicle_type', separator=',')
    )

    class Meta:
        model = VehicleAttribute
        fields = ('id', 'name', 'slug', 'attribute_type', 'is_required', 'vehicle_types')
        export_order = ('id', 'name', 'slug', 'attribute_type', 'is_required', 'vehicle_types')
        import_id_fields = ('slug',)  # Use slug as the unique identifier for updates

class VehicleAttributeOptionResource(resources.ModelResource):
    attribute = fields.Field(
        column_name='attribute',
        attribute='attribute',
        widget=ForeignKeyWidget(VehicleAttribute, 'slug')
    )

    class Meta:
        model = VehicleAttributeOption
        fields = ('id', 'attribute', 'label', 'value')
        export_order = ('attribute', 'label', 'value', 'id')
        import_id_fields = ('id',) # Or maybe (attribute, value) but id is safer for updates. 
        # Actually, for options, usually re-importing might be adding new ones.
        # Let's stick to 'id' for now as it's standard, but if user wants to use attribute+value as key, they can.
        # Given the unique_together constraint on (attribute, value), maybe importing without ID should use those as lookup?
        # But 'import_id_fields' defaults to 'id'. If we want to allow updating by composite key, it's harder.
        # Let's stick to default 'id' for updates, and new records if no ID. 
        import_id_fields = ('id',)


class MakeResource(resources.ModelResource):
    vehicle_types = fields.Field(
        column_name='vehicle_types',
        attribute='vehicle_types',
        widget=ManyToManyWidget(VehicleType, field='vehicle_type', separator=',')
    )

    class Meta:
        model = Make
        fields = ('id', 'make', 'vehicle_types')
        export_order = ('id', 'make', 'vehicle_types')
        import_id_fields = ('make',)


class ModelResource(resources.ModelResource):
    make = fields.Field(
        column_name='make',
        attribute='make',
        widget=ForeignKeyWidget(Make, 'make')
    )
    vehicle_type = fields.Field(
        column_name='vehicle_type',
        attribute='vehicle_type',
        widget=ForeignKeyWidget(VehicleType, 'vehicle_type')
    )

    class Meta:
        model = Model
        fields = ('id', 'model', 'make', 'vehicle_type')
        export_order = ('id', 'make', 'model', 'vehicle_type')
        import_id_fields = ('id',)


class VehicleTypeResource(resources.ModelResource):
    class Meta:
        model = VehicleType
        fields = ('id', 'vehicle_type', 'schema')
        export_order = ('id', 'vehicle_type', 'schema')
        import_id_fields = ('vehicle_type',)


class SellerTypeResource(resources.ModelResource):
    class Meta:
        model = SellerType
        fields = ('id', 'seller_type')
        export_order = ('id', 'seller_type')
        import_id_fields = ('seller_type',)

