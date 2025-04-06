call ..\localdeploy
move /y ./severed_realms_embeddings.json ./world/severed_realms_embeddings.json
@echo Done deploying.
evennia test --settings settings.py .