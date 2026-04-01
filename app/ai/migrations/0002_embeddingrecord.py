from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ("app_ai", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="SELECT 1;",
        ),
        migrations.CreateModel(
            name="EmbeddingRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content_type", models.CharField(
                    choices=[
                        ("transaction", "Transaction"),
                        ("sku", "SKU"),
                        ("message", "Conversation Message"),
                        ("knowledge", "Knowledge Base"),
                    ],
                    db_index=True,
                    max_length=20,
                )),
                ("object_id", models.CharField(max_length=255)),
                ("org_id", models.CharField(db_index=True, max_length=255)),
                ("text", models.TextField()),
                ("embedding", pgvector.django.VectorField(dimensions=768)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "app_label": "app_ai",
                "unique_together": {("content_type", "object_id")},
            },
        ),
        migrations.AddIndex(
            model_name="embeddingrecord",
            index=pgvector.django.HnswIndex(
                ef_construction=64,
                fields=["embedding"],
                m=16,
                name="emb_hnsw_cosine_idx",
                opclasses=["vector_cosine_ops"],
            ),
        ),
    ]
