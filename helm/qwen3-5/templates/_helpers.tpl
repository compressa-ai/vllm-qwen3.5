{{/*
Expand the name of the chart.
*/}}
{{- define "qwen35.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "qwen35.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Proxy fullname
*/}}
{{- define "qwen35.proxy.fullname" -}}
{{- printf "%s-%s-proxy" .Release.Name (include "qwen35.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
vLLM backend fullname (used as LLM_HOST by proxy)
*/}}
{{- define "qwen35.vllm.fullname" -}}
{{- printf "%s-%s-vllm" .Release.Name (include "qwen35.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Model path for vLLM (no trailing slash)
*/}}
{{- define "qwen35.modelPath" -}}
{{- printf "/app/resources/models/models/%s" .Values.modelName | trimSuffix "/" }}
{{- end }}
