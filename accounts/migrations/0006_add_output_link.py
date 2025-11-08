from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_project_screenshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='output_link',
            field=models.URLField(blank=True),
        ),
    ]