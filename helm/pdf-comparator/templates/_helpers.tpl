{{- define "pdf-comparator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "pdf-comparator.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "pdf-comparator.labels" -}}
app.kubernetes.io/name: {{ include "pdf-comparator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
