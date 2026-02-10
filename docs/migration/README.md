# 🔄 Migration Documentation

Documentation for system migrations and major architectural changes.

## Files

### Azure to Local Migration
- **[MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)** - Complete Azure to Local mode migration
  - Replaced Azure Cosmos DB with SQLite
  - Replaced Azure Blob Storage with local filesystem
  - Replaced Azure Service Bus with background threads
  - Replaced Azure OpenAI with standard OpenAI API
  - Result: No Azure subscription needed!

## Migration Benefits

✅ **Zero Azure Costs** - Only pay for OpenAI API usage (~$0.15 per document)
✅ **Local Development** - Run on any laptop without cloud dependencies
✅ **Faster Iteration** - No network calls to Azure services
✅ **Backward Compatible** - Can still use Azure mode when needed

## Quick Links
- [Back to Documentation Index](../README.md)
- [Quick Start Guide](../../QUICK_START.md)
- [Local Development Setup](../setup/)
