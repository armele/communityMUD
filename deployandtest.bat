call ..\localdeploy
move /y ./%EMBEDDINGS% ./world/%EMBEDDINGS%
@echo Done deploying.
start "GenPC Server" call ..\startllm
evennia test --settings settings.py .