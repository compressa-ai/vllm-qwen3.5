FROM vllm/vllm-openai:latest

# Qwen3.5-MoE requires transformers >= 5.2.0 (qwen3_5_moe architecture)
RUN pip install --upgrade "transformers>=5.2.0"
