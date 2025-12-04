from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checkout', '0002_alter_payment_options_alter_shipping_options_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payment',
            old_name='transaction_id',
            new_name='preference_id',
        ),
        migrations.AddField(
            model_name='payment',
            name='mp_payment_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
