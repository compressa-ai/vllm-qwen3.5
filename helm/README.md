# Helm chart: qwen3-5

Deploys Qwen3.5 with vLLM and proxy (OpenAI-compatible API) on Kubernetes.

## Prerequisites

- Kubernetes cluster with GPU nodes (nvidia.com/gpu)
- Host paths for models and HF cache (or adjust to PVCs)
- Proxy image built and pushed (or use default name and build from repo)

## Install

```bash
# Create namespace
kubectl create namespace qwen35

# Optional: secret for Hugging Face token
kubectl create secret generic qwen35-hf --from-literal=HF_TOKEN=<token> -n qwen35

# Install with default values
helm install qwen35 ./qwen3-5 -n qwen35

# Or override values
helm install qwen35 ./qwen3-5 -n qwen35 -f my-values.yaml
```

## Key values (from .env_example)

| Value | Default | Description |
|-------|---------|-------------|
| `modelName` | Qwen_Qwen3.5-35B-A3B-FP8 | Model directory name under resourcesPath |
| `maxModelLen` | "128000" | vLLM max context length |
| `gpuMemoryUtilization` | "0.95" | vLLM GPU memory fraction |
| `resourcesPath` | /data/shared/CompressaAI/test_deploy | Host path for models |
| `hfHome` | /data/shared/CompressaAI/k_cache | Host path for HuggingFace cache |
| `existingSecret` | "" | Secret name containing HF_TOKEN |
| `proxy.service.type` | ClusterIP | Use NodePort and set externalPort for external access |

## Build proxy image

```bash
cd /path/to/qwen3-5
docker build -f proxy/Dockerfile -t <your-registry>/qwen35-proxy:latest .
docker push <your-registry>/qwen35-proxy:latest
```

Then set in values: `proxy.image.repository: <your-registry>/qwen35-proxy`

## Access

- **In-cluster:** `http://<release-name>-qwen3-5-proxy.<namespace>.svc.cluster.local:8000/v1/`
- **NodePort:** set `proxy.service.type: NodePort` and `proxy.service.externalPort: 10010`, then `http://<node-ip>:10010/v1/`

---

## k3s

Для k3s удобно использовать отдельный values-файл:

```bash
helm install qwen35 ./qwen3-5 -n qwen35 -f qwen3-5/values-k3s.yaml
```

**Отличия для k3s:**

| Аспект | Обычный K8s | k3s |
|--------|-------------|-----|
| **Ingress** | свой controller (nginx, etc.) | по умолчанию **Traefik** → в values-k3s задано `ingress.className: traefik` |
| **Доступ с хоста** | NodePort / LoadBalancer | **NodePort** или встроенный **servicelb** (Klipper), в values-k3s proxy уже NodePort 10010 |
| **GPU** | nvidia-device-plugin | тот же ресурс `nvidia.com/gpu`; нода часто с **taint** → в values-k3s добавлены **tolerations** под GPU |
| **Образы** | из registry | containerd; для приватного registry — `imagePullSecrets` или `k3s ctr images import` |
| **Тома** | hostPath или PVC | те же hostPath; при необходимости PVC — на k3s по умолчанию **local-path** |

При необходимости привязать под vLLM к конкретной GPU-ноде задайте в values (или в values-k3s):

```yaml
nodeSelector:
  nvidia.com/gpu: "true"
```
