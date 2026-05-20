# GCP Shape Vocabulary (mxgraph.gcp2.*)

draw.io ships Google Cloud Platform icons under the `mxgraph.gcp2.*` shape namespace.

## Base style scaffold

```
sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#4284F3;gradientColor=none;fillColor=#4284F3;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.gcp2.<SERVICE>;
```

Size: 60×60. Label below.

---

## Compute

| Service | shape= |
|---|---|
| Compute Engine | `mxgraph.gcp2.compute_engine` |
| App Engine | `mxgraph.gcp2.app_engine` |
| Cloud Functions | `mxgraph.gcp2.cloud_functions` |
| Cloud Run | `mxgraph.gcp2.cloud_run` |
| GKE / Kubernetes Engine | `mxgraph.gcp2.kubernetes_engine` |
| Container Registry | `mxgraph.gcp2.container_registry` |
| Artifact Registry | `mxgraph.gcp2.artifact_registry` |
| Cloud Functions for Firebase | `mxgraph.gcp2.cloud_functions_for_firebase` |

---

## Storage

| Service | shape= |
|---|---|
| Cloud Storage | `mxgraph.gcp2.cloud_storage` |
| Persistent Disk | `mxgraph.gcp2.persistent_disk` |
| Filestore | `mxgraph.gcp2.filestore` |
| Transfer Appliance | `mxgraph.gcp2.transfer_appliance` |

---

## Database

| Service | shape= |
|---|---|
| Cloud SQL | `mxgraph.gcp2.cloud_sql` |
| Cloud Spanner | `mxgraph.gcp2.cloud_spanner` |
| Firestore | `mxgraph.gcp2.firestore` |
| Cloud Bigtable | `mxgraph.gcp2.cloud_bigtable` |
| BigQuery | `mxgraph.gcp2.bigquery` |
| Memorystore | `mxgraph.gcp2.cloud_memorystore` |
| Database Migration Service | `mxgraph.gcp2.database_migration_service` |

---

## Networking

| Service | shape= |
|---|---|
| Virtual Private Cloud | `mxgraph.gcp2.virtual_private_cloud` |
| Cloud Load Balancing | `mxgraph.gcp2.cloud_load_balancing` |
| Cloud DNS | `mxgraph.gcp2.cloud_dns` |
| Cloud CDN | `mxgraph.gcp2.cloud_cdn` |
| Cloud NAT | `mxgraph.gcp2.cloud_nat` |
| Cloud VPN | `mxgraph.gcp2.cloud_vpn` |
| Cloud Router | `mxgraph.gcp2.cloud_router` |
| Cloud Interconnect | `mxgraph.gcp2.cloud_interconnect` |
| Cloud Armor | `mxgraph.gcp2.cloud_armor` |
| Network Service Tiers | `mxgraph.gcp2.network_service_tiers` |

---

## Identity & Security

| Service | shape= |
|---|---|
| Cloud IAM | `mxgraph.gcp2.identity_and_access_management` |
| Identity Platform | `mxgraph.gcp2.identity_platform` |
| Cloud KMS | `mxgraph.gcp2.key_management_service` |
| Secret Manager | `mxgraph.gcp2.secret_manager` |
| Security Command Center | `mxgraph.gcp2.security_command_center` |
| Cloud DLP | `mxgraph.gcp2.cloud_data_loss_prevention_api` |

---

## Data & Analytics

| Service | shape= |
|---|---|
| Dataflow | `mxgraph.gcp2.cloud_dataflow` |
| Dataproc | `mxgraph.gcp2.cloud_dataproc` |
| Pub/Sub | `mxgraph.gcp2.cloud_pubsub` |
| Data Fusion | `mxgraph.gcp2.cloud_data_fusion` |
| Composer | `mxgraph.gcp2.cloud_composer` |
| Looker | `mxgraph.gcp2.looker` |
| Data Catalog | `mxgraph.gcp2.data_catalog` |

---

## AI / ML

| Service | shape= |
|---|---|
| Vertex AI | `mxgraph.gcp2.vertex_ai` |
| AutoML | `mxgraph.gcp2.cloud_automl` |
| Translation API | `mxgraph.gcp2.cloud_translation_api` |
| Speech-to-Text | `mxgraph.gcp2.cloud_speech_to_text_api` |
| Vision API | `mxgraph.gcp2.cloud_vision_api` |
| Natural Language API | `mxgraph.gcp2.cloud_natural_language_api` |
| Dialogflow | `mxgraph.gcp2.dialogflow` |

---

## DevOps / Operations

| Service | shape= |
|---|---|
| Cloud Build | `mxgraph.gcp2.cloud_build` |
| Cloud Deploy | `mxgraph.gcp2.cloud_deploy` |
| Cloud Logging | `mxgraph.gcp2.cloud_logging` |
| Cloud Monitoring | `mxgraph.gcp2.cloud_monitoring` |
| Cloud Trace | `mxgraph.gcp2.cloud_trace` |
| Error Reporting | `mxgraph.gcp2.error_reporting` |
| Cloud Profiler | `mxgraph.gcp2.cloud_profiler` |

---

## Container groups (GCP scopes)

```
points=[...];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.gcp2.virtual_private_cloud_vpc;strokeColor=#4284F3;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#4284F3;dashed=1;
```

Use for `Project`, `Region`, `Zone`, `VPC` containers.

---

## Color palette

Google Blue: `#4284F3`
Google Red: `#EA4335`
Google Yellow: `#FBBC05`
Google Green: `#34A853`

Standard pattern: blue for compute/network, red for identity/security, yellow for
storage, green for data/analytics.
