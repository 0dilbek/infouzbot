from tortoise import Model, fields

class User(Model):
    id = fields.IntField(pk=True)
    tg_id = fields.IntField(unique=True)
    username = fields.CharField(max_length=255)
    first_name = fields.CharField(max_length=255)
    last_name = fields.CharField(max_length=255)
    phone_number = fields.CharField(max_length=255)

    role = fields.CharField(max_length=255)
    

class Location(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField()
    street = fields.ForeignKeyField("models.Street", related_name="locations")

    lat = fields.FloatField()
    lon = fields.FloatField()

    created_by = fields.ForeignKeyField("models.User", related_name="created_locations")
    owner = fields.ForeignKeyField("models.User", related_name="owned_locations")

class PhoneNumbers(Model):
    location = fields.ForeignKeyField("models.Location", related_name="phone_numbers")
    phone_number = fields.CharField(max_length=255)

class Street(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    region = fields.ForeignKeyField("models.Region", related_name="streets")

class Region(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)

class Images(Model):
    location = fields.ForeignKeyField("models.Location", related_name="images")
    image_local_path = fields.CharField(max_length=255)
    image_tg_file_id = fields.CharField(max_length=255)
    image_url = fields.CharField(max_length=500, null=True)
    is_main = fields.BooleanField(default=False)
    
class LocationTags(Model):
    location = fields.ForeignKeyField("models.Location", related_name="tags")
    tag = fields.ForeignKeyField("models.Tag", related_name="locations")

class TagGroup(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)

class Tag(Model):
    name = fields.CharField(max_length=255)
    tag_group = fields.ForeignKeyField("models.TagGroup", related_name="tags")
    
