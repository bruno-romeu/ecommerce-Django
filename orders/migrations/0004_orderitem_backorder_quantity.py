from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_orderitem_customization_details'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='backorder_quantity',
            field=models.PositiveIntegerField(default=0, verbose_name='Quantidade sob encomenda'),
        ),
    ]
