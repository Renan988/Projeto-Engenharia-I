"""
Issue #19 - Adaptação do modelo de Funcionário ao Supabase Auth.

- Remove a coluna `senha` (e o hash de senha) da tabela FUNCIONARIO.
- Adiciona o vínculo único com a identidade do Supabase Auth (`supabaseUserId`).

Funciona em banco limpo (0001 -> 0002) e em bancos já existentes: os hashes de
senha antigos são descartados, e os perfis passam a ser vinculados à identidade
Supabase no primeiro login autenticado (ver backend/README.md).
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funcionarios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='funcionario',
            name='supabase_user_id',
            field=models.UUIDField(
                blank=True,
                db_column='supabaseUserId',
                help_text='Identificador único da identidade autenticada em auth.users.',
                null=True,
                unique=True,
                verbose_name='ID do Usuário no Supabase Auth',
            ),
        ),
        migrations.RemoveField(
            model_name='funcionario',
            name='password',
        ),
    ]
