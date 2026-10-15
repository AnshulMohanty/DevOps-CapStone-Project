{{/*
Base name for every object: "foundit" for a release called foundit, otherwise "<release>-foundit".
Services, the Ingress, the HPA, the frontend proxy target and the backend's DATABASE_URL all build
their names from these helpers, so they cannot drift apart.
*/}}
{{- define "foundit.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{ .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else -}}
{{ printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end -}}
{{- end }}

{{- define "foundit.backend" -}}{{ include "foundit.fullname" . }}-backend{{- end }}
{{- define "foundit.frontend" -}}{{ include "foundit.fullname" . }}-frontend{{- end }}
{{- define "foundit.postgres" -}}{{ include "foundit.fullname" . }}-postgres{{- end }}

{{/* Labels on every object (recommended Kubernetes labels). */}}
{{- define "foundit.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: foundit
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}

{{/*
Selector labels for one component - call with (dict "ctx" . "component" "backend").
Kept minimal and stable: a Deployment's selector can never be changed after creation.
*/}}
{{- define "foundit.selectorLabels" -}}
app.kubernetes.io/name: {{ .ctx.Chart.Name }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/* image reference: repository:tag, the tag defaulting to the chart's appVersion */}}
{{- define "foundit.image" -}}
{{ .image.repository }}:{{ .image.tag | default .ctx.Chart.AppVersion }}
{{- end }}

{{/* Security settings shared by the app containers (both images already run as non-root). */}}
{{- define "foundit.containerSecurity" -}}
allowPrivilegeEscalation: false
capabilities:
  drop: ["ALL"]
{{- end }}
