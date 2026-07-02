from django.db import migrations
import django.db.models.deletion
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ('integration', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='EventosMatch',
            new_name='EventBridge',
        ),
        migrations.RenameModel(
            old_name='ArenaClientsMatch',
            new_name='ClientBridge',
        ),
        migrations.RenameModel(
            old_name='AtletaMatch',
            new_name='AthleteBridge',
        ),
        migrations.RenameModel(
            old_name='LutaMatch',
            new_name='FightBridge',
        ),
        migrations.AddField(
            model_name='eventbridge',
            name='age_group',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='eventbridge',
            name='sge_age_category',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.RemoveField(
            model_name='eventbridge',
            name='sge_event',
        ),
        migrations.AddField(
            model_name='eventbridge',
            name='sge_event',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='evento_sge_origin', to='sge.gestaoeventos'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='eventbridge',
            unique_together={('arena_event', 'age_group', 'sge_event', 'sge_age_category')},
        ),
        migrations.AlterField(
            model_name='clientbridge',
            name='eventos_match',
            field=models.ManyToManyField(blank=True, related_name='arena_client_eventos_match_origin', to='integration.eventbridge'),
        ),
    ]
